"""
OpenAI uploader.

Responsibilities:
  1. Ensure a Vector Store named VECTOR_STORE_NAME exists (create once, reuse).
  2. Ensure an Assistant named ASSISTANT_NAME exists (create once, reuse).
  3. Upload a Markdown file to the Files API.
  4. Attach the file to the Vector Store.
  5. Delete old file from Files API + Vector Store when an article is Updated.
  6. Log: files uploaded, total chunks embedded.

OpenAI docs:
  https://platform.openai.com/docs/api-reference/files
  https://platform.openai.com/docs/api-reference/vector-stores
  https://platform.openai.com/docs/api-reference/assistants
"""
import logging
import os
import time
from typing import Optional

import openai

from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    VECTOR_STORE_NAME,
    ASSISTANT_NAME,
    ASSISTANT_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

# ── Module-level state (cached across calls) ──────────────────────────────────
_vector_store_id: Optional[str] = None
_assistant_id:    Optional[str] = None


def _get_client() -> openai.OpenAI:
    return openai.OpenAI(api_key=OPENAI_API_KEY)


# ── Vector Store ──────────────────────────────────────────────────────────────

def get_or_create_vector_store() -> str:
    """Return the id of our Vector Store, creating it if necessary."""
    global _vector_store_id
    if _vector_store_id:
        return _vector_store_id

    client = _get_client()

    # Search existing stores
    stores = client.beta.vector_stores.list()
    for vs in stores.data:
        if vs.name == VECTOR_STORE_NAME:
            _vector_store_id = vs.id
            logger.info("[OpenAI] Reusing existing vector store '%s' (%s)",
                        VECTOR_STORE_NAME, vs.id)
            return _vector_store_id

    # Create new
    vs = client.beta.vector_stores.create(name=VECTOR_STORE_NAME)
    _vector_store_id = vs.id
    logger.info("[OpenAI] Created vector store '%s' (%s)", VECTOR_STORE_NAME, vs.id)
    return _vector_store_id


# ── Assistant ─────────────────────────────────────────────────────────────────

def get_or_create_assistant(vector_store_id: str) -> str:
    """Return the id of the OptiBot assistant, creating it if necessary."""
    global _assistant_id
    if _assistant_id:
        return _assistant_id

    client = _get_client()

    assistants = client.beta.assistants.list(limit=100)
    for asst in assistants.data:
        if asst.name == ASSISTANT_NAME:
            _assistant_id = asst.id
            logger.info("[OpenAI] Reusing existing assistant '%s' (%s)",
                        ASSISTANT_NAME, asst.id)
            # Make sure it's linked to our vector store
            _ensure_assistant_linked(client, asst.id, vector_store_id)
            return _assistant_id

    # Create new
    asst = client.beta.assistants.create(
        name=ASSISTANT_NAME,
        instructions=ASSISTANT_SYSTEM_PROMPT,
        model=OPENAI_MODEL,
        tools=[{"type": "file_search"}],
        tool_resources={
            "file_search": {"vector_store_ids": [vector_store_id]}
        },
    )
    _assistant_id = asst.id
    logger.info("[OpenAI] Created assistant '%s' (%s)", ASSISTANT_NAME, asst.id)
    return _assistant_id


def _ensure_assistant_linked(client: openai.OpenAI, assistant_id: str, vs_id: str):
    """Make sure the assistant has our vector store attached."""
    asst = client.beta.assistants.retrieve(assistant_id)
    tr = asst.tool_resources
    if tr and tr.file_search:
        current_ids = tr.file_search.vector_store_ids or []
        if vs_id in current_ids:
            return

    client.beta.assistants.update(
        assistant_id,
        tool_resources={"file_search": {"vector_store_ids": [vs_id]}},
    )
    logger.info("[OpenAI] Linked vector store %s to assistant %s", vs_id, assistant_id)


# ── File Upload ───────────────────────────────────────────────────────────────

def upload_file(markdown_path: str, vector_store_id: str) -> str:
    """
    Upload a .md file to OpenAI Files API and attach it to the vector store.

    Returns the OpenAI file id.
    """
    client = _get_client()

    with open(markdown_path, "rb") as f:
        filename = os.path.basename(markdown_path)
        response = client.files.create(file=(filename, f, "text/plain"), purpose="assistants")

    file_id = response.id
    logger.debug("[OpenAI] Uploaded file '%s' → file_id=%s", filename, file_id)

    # Attach to vector store
    client.beta.vector_stores.files.create(
        vector_store_id=vector_store_id,
        file_id=file_id,
    )
    logger.debug("[OpenAI] Attached %s to vector store %s", file_id, vector_store_id)
    return file_id


def delete_file(file_id: str, vector_store_id: str):
    """
    Remove a file from the vector store AND delete it from Files API.
    Called when an article is Updated (old version must be replaced).
    """
    if not file_id:
        return
    client = _get_client()
    try:
        client.beta.vector_stores.files.delete(
            vector_store_id=vector_store_id, file_id=file_id
        )
    except Exception as exc:
        logger.warning("[OpenAI] Could not remove %s from vector store: %s", file_id, exc)

    try:
        client.files.delete(file_id)
        logger.debug("[OpenAI] Deleted file %s from Files API", file_id)
    except Exception as exc:
        logger.warning("[OpenAI] Could not delete file %s: %s", file_id, exc)


# ── Stats helper ──────────────────────────────────────────────────────────────

def get_vector_store_stats(vector_store_id: str) -> dict:
    """Return basic stats about the vector store."""
    client = _get_client()
    try:
        vs = client.beta.vector_stores.retrieve(vector_store_id)
        fc = vs.file_counts
        return {
            "total_files":    fc.total,
            "completed_files": fc.completed,
            "failed_files":   fc.failed,
            "in_progress":    fc.in_progress,
        }
    except Exception as exc:
        logger.warning("[OpenAI] Could not retrieve vector store stats: %s", exc)
        return {}


# ── Chat helper (for testing) ─────────────────────────────────────────────────

def chat_with_assistant(assistant_id: str, user_message: str) -> dict:
    """
    Send a message to the assistant and return {'reply': str, 'citations': list}.
    Used in tests / manual verification.
    """
    client = _get_client()

    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message,
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

    if run.status != "completed":
        return {"reply": f"Run ended with status: {run.status}", "citations": []}

    messages = client.beta.threads.messages.list(thread_id=thread.id, order="asc")
    last_msg = None
    for msg in messages.data:
        if msg.role == "assistant":
            last_msg = msg

    if last_msg is None:
        return {"reply": "No response from assistant.", "citations": []}

    reply_text = ""
    citations  = []

    for content_block in last_msg.content:
        if content_block.type == "text":
            val         = content_block.text.value
            annotations = content_block.text.annotations

            # Replace annotation markers with citation numbers
            for i, ann in enumerate(annotations, start=1):
                val = val.replace(ann.text, f"[{i}]")
                if ann.type == "file_citation":
                    try:
                        cited_file = client.files.retrieve(ann.file_citation.file_id)
                        citations.append(f"[{i}] {cited_file.filename}")
                    except Exception:
                        citations.append(f"[{i}] (file id: {ann.file_citation.file_id})")

            reply_text += val

    return {"reply": reply_text, "citations": citations}
