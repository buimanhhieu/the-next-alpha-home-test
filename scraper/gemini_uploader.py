"""
Gemini-based uploader (100% FREE alternative to OpenAI).

Architecture:
  - Gemini Files API   → upload .md files (free, 2GB limit)
  - ChromaDB (local)   → vector store for semantic search (free, runs in-memory)
  - Gemini Embeddings  → embed documents (free tier)
  - Gemini 1.5 Flash   → answer questions with citations (free tier)

Free tier limits (as of 2025):
  - Gemini 1.5 Flash:  15 RPM, 1 million tokens/day
  - Gemini Embeddings: 1500 RPM
  - Files API:         2 GB storage, files live 48h (re-upload each sync)

No credit card required – just a Google account.
Get key at: https://aistudio.google.com/app/apikey
"""
import json
import logging
import os
import time
import mimetypes
import requests
from typing import Optional

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_BASE    = "https://generativelanguage.googleapis.com"
GEMINI_MODEL   = os.getenv("GEMINI_CHAT_MODEL",  "gemini-2.0-flash")
EMBED_MODEL    = os.getenv("GEMINI_EMBED_MODEL",  "models/text-embedding-004")

ASSISTANT_SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
Tone: helpful, factual, concise.
Only answer using uploaded docs.
Max 5 bullet points.
Else link to the doc.
Cite up to 3 Article URL lines."""


# ── Gemini Files API ──────────────────────────────────────────────────────────

def upload_file_to_gemini(md_path: str) -> dict:
    """
    Upload a Markdown file to Gemini Files API.
    Returns: {"file_uri": "...", "name": "files/xxx"}
    """
    filename = os.path.basename(md_path)
    file_size = os.path.getsize(md_path)

    # Step 1 – Initiate resumable upload
    init_url = (
        f"{GEMINI_BASE}/upload/v1beta/files"
        f"?key={GEMINI_API_KEY}&uploadType=resumable"
    )
    init_headers = {
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command":  "start",
        "X-Goog-Upload-Header-Content-Type": "text/plain",
        "X-Goog-Upload-Header-Content-Length": str(file_size),
        "Content-Type": "application/json",
    }
    init_body = json.dumps({"file": {"display_name": filename}})
    r = requests.post(init_url, headers=init_headers, data=init_body, timeout=15)
    r.raise_for_status()
    upload_url = r.headers.get("X-Goog-Upload-URL")
    if not upload_url:
        raise RuntimeError(f"No upload URL returned for {filename}")

    # Step 2 – Upload the actual bytes
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
    file_uri  = data["file"]["uri"]
    file_name = data["file"]["name"]
    logger.debug("[Gemini] Uploaded '%s' → %s", filename, file_name)
    return {"file_uri": file_uri, "name": file_name}


def delete_file_from_gemini(file_name: str):
    """Delete a file from Gemini Files API by its name (e.g. 'files/xxx')."""
    if not file_name:
        return
    url = f"{GEMINI_BASE}/v1beta/{file_name}?key={GEMINI_API_KEY}"
    try:
        r = requests.delete(url, timeout=10)
        if r.status_code in (200, 204):
            logger.debug("[Gemini] Deleted file %s", file_name)
        else:
            logger.warning("[Gemini] Delete returned %d for %s", r.status_code, file_name)
    except Exception as exc:
        logger.warning("[Gemini] Could not delete %s: %s", file_name, exc)


# ── Gemini Embeddings (for local ChromaDB) ────────────────────────────────────

def embed_text(text: str) -> list[float]:
    """Get embedding vector from Gemini text-embedding-004."""
    # Model name for URL must NOT include 'models/' prefix in the path segment
    model = EMBED_MODEL.replace("models/", "")
    url = f"{GEMINI_BASE}/v1beta/models/{model}:embedContent?key={GEMINI_API_KEY}"
    body = {
        "model": EMBED_MODEL,
        "content": {"parts": [{"text": text[:8000]}]},  # safe limit
    }
    r = requests.post(url, json=body, timeout=15)
    r.raise_for_status()
    return r.json()["embedding"]["values"]


# ── Local ChromaDB vector store ───────────────────────────────────────────────

def _get_chroma_collection():
    """Return (or create) a persistent ChromaDB collection."""
    try:
        import chromadb
    except ImportError:
        raise ImportError(
            "chromadb is not installed. Run: pip install chromadb"
        )
    db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma")
    os.makedirs(db_path, exist_ok=True)
    client = chromadb.PersistentClient(path=db_path)
    return client.get_or_create_collection(
        name="optisigns_docs",
        metadata={"hnsw:space": "cosine"},
    )


def upsert_to_chroma(article_id: str, markdown: str, url: str, title: str):
    """Embed and upsert a document chunk into ChromaDB."""
    col = _get_chroma_collection()
    embedding = embed_text(markdown[:8000])
    col.upsert(
        ids=[article_id],
        embeddings=[embedding],
        documents=[markdown[:8000]],
        metadatas=[{"url": url, "title": title}],
    )


def delete_from_chroma(article_id: str):
    """Remove a document from ChromaDB."""
    try:
        col = _get_chroma_collection()
        col.delete(ids=[article_id])
    except Exception as exc:
        logger.warning("[Chroma] Could not delete %s: %s", article_id, exc)


def search_chroma(query: str, top_k: int = 3) -> list[dict]:
    """Semantic search – returns list of {document, url, title}."""
    col = _get_chroma_collection()
    q_emb = embed_text(query)
    results = col.query(
        query_embeddings=[q_emb],
        n_results=min(top_k, col.count()),
        include=["documents", "metadatas"],
    )
    docs = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        docs.append({"document": doc, "url": meta.get("url", ""), "title": meta.get("title", "")})
    return docs


# ── Gemini Chat with RAG ──────────────────────────────────────────────────────

def chat_with_gemini(user_message: str) -> dict:
    """
    Answer a question using RAG:
      1. Semantic search over ChromaDB
      2. Build prompt with retrieved context
      3. Call Gemini 1.5 Flash
      4. Return reply + source URLs as citations
    """
    # Step 1 – Retrieve relevant docs
    docs = search_chroma(user_message, top_k=3)
    if not docs:
        return {
            "reply":     "I couldn't find relevant documentation for your question.",
            "citations": [],
        }

    # Step 2 – Build RAG prompt
    context_parts = []
    for i, d in enumerate(docs, start=1):
        context_parts.append(
            f"[Source {i}]: {d['url']}\n{d['title']}\n\n{d['document'][:2000]}"
        )
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""{ASSISTANT_SYSTEM_PROMPT}

--- Documentation Context ---
{context}
--- End Context ---

User question: {user_message}

Answer (cite Source URLs at the end):"""

    # Step 3 – Call Gemini
    url = f"{GEMINI_BASE}/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }
    r = requests.post(url, json=body, timeout=30)
    r.raise_for_status()
    reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]

    citations = [f"[{i+1}] {d['url']}" for i, d in enumerate(docs)]
    return {"reply": reply, "citations": citations}


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    try:
        col = _get_chroma_collection()
        return {"total_docs_in_vector_store": col.count()}
    except Exception:
        return {"total_docs_in_vector_store": 0}
