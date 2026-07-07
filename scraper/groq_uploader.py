"""
Groq-based chat (FREE, generous rate limits).

Architecture:
  ┌──────────────────────────────────────────────────────────────────┐
  │  Embedding: ChromaDB built-in (all-MiniLM-L6-v2) - LOCAL, FREE  │
  │  Vector DB: ChromaDB persistent on disk - LOCAL, FREE           │
  │  Chat LLM : Groq API (Llama 4 / Llama 3.3) - FREE tier        │
  └──────────────────────────────────────────────────────────────────┘

Groq free tier limits:
  - 30 RPM, 14,400 RPD (requests per day)
  - 6,000 tokens/min
  - No credit card required

Get key at: https://console.groq.com
"""
import logging
import os
import requests

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
GROQ_BASE    = "https://api.groq.com/openai/v1"
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma")

ASSISTANT_SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
Tone: helpful, factual, concise.
Only answer using uploaded docs.
Max 5 bullet points.
Else link to the doc.
Cite up to 3 Article URL lines."""


# ── ChromaDB (shared với gemini_uploader) ─────────────────────────────────────

def _get_chroma_collection():
    import chromadb
    from chromadb.utils import embedding_functions
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(
        name="optisigns_docs",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_to_chroma(article_id: str, markdown: str, url: str, title: str):
    """Upsert a document into ChromaDB (embedding is computed locally)."""
    col = _get_chroma_collection()
    col.upsert(
        ids=[article_id],
        documents=[markdown[:8000]],
        metadatas=[{"url": url, "title": title}],
    )
    logger.debug("[Chroma] Upserted '%s' (%s)", title[:60], article_id)


def delete_from_chroma(article_id: str):
    """Remove a document from ChromaDB."""
    try:
        col = _get_chroma_collection()
        col.delete(ids=[article_id])
        logger.debug("[Chroma] Deleted %s", article_id)
    except Exception as exc:
        logger.warning("[Chroma] Could not delete %s: %s", article_id, exc)


def search_chroma(query: str, top_k: int = 3) -> list[dict]:
    col = _get_chroma_collection()
    count = col.count()
    if count == 0:
        return []
    results = col.query(
        query_texts=[query],
        n_results=min(top_k, count),
        include=["documents", "metadatas"],
    )
    docs = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        docs.append({
            "document": doc,
            "url":   meta.get("url",   ""),
            "title": meta.get("title", ""),
        })
    return docs


def get_stats() -> dict:
    try:
        col = _get_chroma_collection()
        return {"total_docs_in_vector_store": col.count()}
    except Exception:
        return {"total_docs_in_vector_store": 0}


# ── Groq Chat with RAG ─────────────────────────────────────────────────────────

def chat_with_groq(user_message: str) -> dict:
    """
    RAG pipeline using Groq:
      1. ChromaDB semantic search (local)
      2. Build context prompt
      3. Call Groq (Llama 4 Scout – fast & free)
      4. Return reply + source URLs as citations
    """
    if not GROQ_API_KEY:
        return {
            "reply":     "GROQ_API_KEY not set. Add it to your .env file.",
            "citations": [],
        }

    # Step 1 – Semantic search (local)
    docs = search_chroma(user_message, top_k=3)
    if not docs:
        return {
            "reply":     "No documents found. Run: python3 main.py",
            "citations": [],
        }

    # Step 2 – Build RAG prompt
    context_parts = []
    for i, d in enumerate(docs, start=1):
        context_parts.append(
            f"[Source {i}]\nURL: {d['url']}\nTitle: {d['title']}\n\n{d['document'][:2000]}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # Step 3 – Call Groq (OpenAI-compatible API)
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role":    "system",
                "content": ASSISTANT_SYSTEM_PROMPT,
            },
            {
                "role":    "user",
                "content": (
                    f"Use ONLY the following documentation to answer.\n\n"
                    f"{context}\n\n"
                    f"Question: {user_message}\n\n"
                    f"After your answer, list Article URLs used as: 'Article URL: <url>'"
                ),
            },
        ],
        "temperature":  0.2,
        "max_tokens":   1024,
    }

    r = requests.post(f"{GROQ_BASE}/chat/completions",
                      headers=headers, json=body, timeout=30)
    r.raise_for_status()
    reply = r.json()["choices"][0]["message"]["content"]

    citations = [f"[{i+1}] {d['url']}" for i, d in enumerate(docs)]
    return {"reply": reply, "citations": citations}
