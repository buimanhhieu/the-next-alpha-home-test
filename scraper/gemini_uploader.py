"""
Gemini-based uploader (100% FREE alternative to OpenAI).

Architecture:
  ┌──────────────────────────────────────────────────────────────────┐
  │  Embedding: ChromaDB built-in (all-MiniLM-L6-v2) - LOCAL, FREE  │
  │  Vector DB: ChromaDB persistent on disk - LOCAL, FREE           │
  │  Chat LLM : Gemini 2.0 Flash via API - FREE tier               │
  │  Files API: Gemini Files API (optional, for logging) - FREE     │
  └──────────────────────────────────────────────────────────────────┘

Free tier limits (Gemini 2.0 Flash as of 2025):
  - 15 RPM, 1 million tokens/day
  - No credit card required

Get key at: https://aistudio.google.com/app/apikey
"""
import logging
import os
import requests

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_BASE    = "https://generativelanguage.googleapis.com"
GEMINI_MODEL   = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma")

ASSISTANT_SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
Tone: helpful, factual, concise.
Only answer using uploaded docs.
Max 5 bullet points.
Else link to the doc.
Cite up to 3 Article URL lines."""


# ── ChromaDB local vector store (NO external API needed for embeddings) ────────

def _get_chroma_collection():
    """
    Return a persistent ChromaDB collection using the built-in local embedding
    model (all-MiniLM-L6-v2). Runs completely offline – no API key required.
    """
    import chromadb
    from chromadb.utils import embedding_functions

    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Built-in local embedding – downloads ~80MB model on first run, then cached
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
    """
    Semantic search over ChromaDB.
    Returns list of {document, url, title}.
    """
    col = _get_chroma_collection()
    count = col.count()
    if count == 0:
        return []

    results = col.query(
        query_texts=[query],          # embedding computed locally
        n_results=min(top_k, count),
        include=["documents", "metadatas"],
    )
    docs = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        docs.append({
            "document": doc,
            "url":      meta.get("url",   ""),
            "title":    meta.get("title", ""),
        })
    return docs


# ── Gemini Files API (optional – used for logging/tracing only) ────────────────

def upload_file_to_gemini(md_path: str) -> dict:
    """
    Upload a Markdown file to Gemini Files API.
    This is optional – the file is already embedded into ChromaDB locally.
    Returns: {"file_uri": "...", "name": "files/xxx"}

    If upload fails (bad key, quota), returns a dummy value so the pipeline
    continues – ChromaDB is the source of truth for search.
    """
    if not GEMINI_API_KEY:
        return {"file_uri": "", "name": "local-only"}

    import json
    filename  = os.path.basename(md_path)
    file_size = os.path.getsize(md_path)

    try:
        init_url = (
            f"{GEMINI_BASE}/upload/v1beta/files"
            f"?key={GEMINI_API_KEY}&uploadType=resumable"
        )
        init_headers = {
            "X-Goog-Upload-Protocol":              "resumable",
            "X-Goog-Upload-Command":               "start",
            "X-Goog-Upload-Header-Content-Type":   "text/plain",
            "X-Goog-Upload-Header-Content-Length": str(file_size),
            "Content-Type":                        "application/json",
        }
        init_body = json.dumps({"file": {"display_name": filename}})
        r = requests.post(init_url, headers=init_headers, data=init_body, timeout=15)
        r.raise_for_status()
        upload_url = r.headers.get("X-Goog-Upload-URL")

        with open(md_path, "rb") as f:
            content = f.read()
        upload_headers = {
            "Content-Length":        str(file_size),
            "X-Goog-Upload-Offset":  "0",
            "X-Goog-Upload-Command": "upload, finalize",
        }
        r2 = requests.post(upload_url, headers=upload_headers, data=content, timeout=30)
        r2.raise_for_status()
        data = r2.json()
        return {"file_uri": data["file"]["uri"], "name": data["file"]["name"]}

    except Exception as exc:
        logger.debug("[Gemini Files] Upload skipped for '%s': %s", filename, exc)
        return {"file_uri": "", "name": "local-only"}


def delete_file_from_gemini(file_name: str):
    """Delete a file from Gemini Files API (best-effort)."""
    if not file_name or file_name == "local-only" or not GEMINI_API_KEY:
        return
    url = f"{GEMINI_BASE}/v1beta/{file_name}?key={GEMINI_API_KEY}"
    try:
        requests.delete(url, timeout=10)
    except Exception:
        pass


# ── Gemini Chat with RAG ───────────────────────────────────────────────────────

def chat_with_gemini(user_message: str) -> dict:
    """
    Answer a question using RAG:
      1. ChromaDB semantic search (local embedding)
      2. Build context prompt
      3. Call Gemini 2.0 Flash for the answer
      4. Return reply + source URLs as citations
    """
    if not GEMINI_API_KEY:
        return {
            "reply":     "GEMINI_API_KEY not set. Please add it to your .env file.",
            "citations": [],
        }

    # Step 1 – Local semantic search
    docs = search_chroma(user_message, top_k=3)
    if not docs:
        return {
            "reply":     "No documents found. Run the pipeline first: python3 main.py",
            "citations": [],
        }

    # Step 2 – Build RAG prompt
    context_parts = []
    for i, d in enumerate(docs, start=1):
        context_parts.append(
            f"[Source {i}]: {d['url']}\nTitle: {d['title']}\n\n{d['document'][:2000]}"
        )
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""{ASSISTANT_SYSTEM_PROMPT}

--- Documentation Context ---
{context}
--- End Context ---

User question: {user_message}

Answer (cite Source URLs at the end as 'Article URL: <url>'):"""

    # Step 3 – Gemini chat (with retry on 429)
    url = f"{GEMINI_BASE}/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
    }

    import time
    for attempt in range(5):
        r = requests.post(url, json=body, timeout=30)
        if r.status_code == 429:
            wait = 15 * (attempt + 1)   # 15s, 30s, 45s, 60s, 75s
            logger.warning("[Gemini] Rate limit (429). Waiting %ds before retry %d/5…", wait, attempt + 1)
            time.sleep(wait)
            continue
        r.raise_for_status()
        break
    else:
        return {
            "reply":     "Rate limit reached. Please wait 1 minute and run: python3 test_assistant.py",
            "citations": citations,
        }

    reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return {"reply": reply, "citations": citations}



# ── Stats ──────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    try:
        col = _get_chroma_collection()
        return {"total_docs_in_vector_store": col.count()}
    except Exception:
        return {"total_docs_in_vector_store": 0}
