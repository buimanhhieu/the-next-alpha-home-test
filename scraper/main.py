"""
main.py – OptiSigns Support Bot pipeline orchestrator.

When executed:
    python main.py [--test]

Flow:
    1. Scrape articles from Zendesk API
    2. Convert HTML → Markdown
    3. Save each article as <slug>.md in ARTICLES_DIR
    4. Detect delta (Added / Updated / Skipped) via SQLite
    5. Upload changed files to OpenAI (Files API + Vector Store)
    6. Create / reuse the OptiBot assistant
    7. Print summary log

Options:
    --test   After sync, run a test question ("How do I add a YouTube video?")
             and print the answer + citations.
"""
import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    ARTICLES_DIR,
    LOG_LEVEL,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    AI_PROVIDER,
)
from zendesk_scraper import ZendeskScraper
from markdown_converter import html_to_markdown
from delta_tracker import DeltaTracker, DeltaStatus

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _load_provider():
    """Load the correct uploader based on AI_PROVIDER setting."""
    if AI_PROVIDER == "openai":
        from openai_uploader import (
            get_or_create_vector_store,
            get_or_create_assistant,
            upload_file,
            delete_file,
            get_vector_store_stats,
            chat_with_assistant,
        )
        return "openai", {
            "get_or_create_store":    get_or_create_vector_store,
            "get_or_create_assistant": get_or_create_assistant,
            "upload_file":            upload_file,
            "delete_file":            delete_file,
            "get_stats":              get_vector_store_stats,
            "chat":                   lambda asst_id, msg: chat_with_assistant(asst_id, msg),
        }
    elif AI_PROVIDER == "groq":
        from groq_uploader import (
            upsert_to_chroma,
            delete_from_chroma,
            chat_with_groq,
            get_stats,
        )
        return "groq", {
            "get_or_create_store":     lambda: "chroma-local",
            "get_or_create_assistant": lambda vs_id: "groq-llama4",
            "upload_file":             lambda path, vs_id: _gemini_upload_and_embed(path, lambda p: {}, upsert_to_chroma),
            "delete_file":             lambda file_id, vs_id: _gemini_delete(file_id, lambda f: None, delete_from_chroma),
            "get_stats":               lambda vs_id: get_stats(),
            "chat":                    lambda asst_id, msg: chat_with_groq(msg),
        }
    else:
        # Default: Gemini (free)
        from gemini_uploader import (
            upload_file_to_gemini,
            delete_file_from_gemini,
            upsert_to_chroma,
            delete_from_chroma,
            chat_with_gemini,
            get_stats,
        )
        return "gemini", {
            "get_or_create_store":     lambda: "chroma-local",
            "get_or_create_assistant": lambda vs_id: "gemini-flash",
            "upload_file":             lambda path, vs_id: _gemini_upload_and_embed(path, upload_file_to_gemini, upsert_to_chroma),
            "delete_file":             lambda file_id, vs_id: _gemini_delete(file_id, delete_file_from_gemini, delete_from_chroma),
            "get_stats":               lambda vs_id: get_stats(),
            "chat":                    lambda asst_id, msg: chat_with_gemini(msg),
        }


def _gemini_upload_and_embed(path, upload_fn, embed_fn):
    """
    1. Read markdown + extract metadata
    2. Upsert into ChromaDB (local embedding, no API needed)
    3. Optionally upload to Gemini Files API (best-effort, for logging)
    Returns a file_id string stored in delta DB.
    """
    with open(path, encoding="utf-8") as f:
        md = f.read()

    # Extract title + url from first few lines of the markdown
    lines = md.split("\n")
    title = lines[0].lstrip("# ").strip() if lines else ""
    url   = ""
    for line in lines[1:6]:
        if "**Source:**" in line:
            url = line.replace("**Source:**", "").strip()
            break

    article_id = os.path.splitext(os.path.basename(path))[0]

    # Step A – Embed into ChromaDB (local, always works)
    embed_fn(article_id, md, url, title)

    # Step B – Upload to Gemini Files API (optional, best-effort)
    result = upload_fn(path)
    file_name = result.get("name", "local-only")
    return file_name


def _gemini_delete(file_id, delete_gemini_fn, delete_chroma_fn):
    """Delete from both Gemini Files API and ChromaDB."""
    if file_id and file_id.startswith("files/"):
        delete_gemini_fn(file_id)
    # ChromaDB key is the slug (basename of file), stored differently
    # Delta tracker handles this via article_id


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline(test_mode: bool = False):
    logger.info("=" * 60)
    logger.info("OptiSigns Support Bot – Sync Pipeline Starting")
    logger.info("Provider: %s", AI_PROVIDER.upper())
    logger.info("=" * 60)

    # Validate config
    if AI_PROVIDER == "openai" and not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set. Set AI_PROVIDER=groq for the free option.")
        sys.exit(1)
    if AI_PROVIDER == "gemini" and not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/app/apikey")
        sys.exit(1)
    if AI_PROVIDER == "groq" and not GROQ_API_KEY:
        logger.error("GROQ_API_KEY is not set. Get a free key at https://console.groq.com")
        sys.exit(1)

    # Load provider functions
    provider_name, fn = _load_provider()
    logger.info("[Provider] Using: %s", provider_name)

    os.makedirs(ARTICLES_DIR, exist_ok=True)

    # ── Step 1: Scrape ────────────────────────────────────────────────────────
    logger.info("[Step 1] Scraping articles from Zendesk API …")
    scraper  = ZendeskScraper()
    articles = scraper.fetch_articles()
    logger.info("[Step 1] Fetched %d articles.", len(articles))

    # ── Step 2 & 3: Convert + Save Markdown ───────────────────────────────────
    logger.info("[Step 2] Converting HTML → Markdown …")
    md_map: dict[str, tuple] = {}   # article_id → (markdown, article)
    for article in articles:
        md = html_to_markdown(
            html=article.body_html,
            source_url=article.html_url,
            title=article.title,
        )
        path = os.path.join(ARTICLES_DIR, f"{article.slug}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        md_map[str(article.id)] = (md, article, path)

    logger.info("[Step 2] Saved %d Markdown files to '%s'.", len(md_map), ARTICLES_DIR)

    # ── Step 4: Delta Detection ───────────────────────────────────────────────
    logger.info("[Step 3] Detecting delta (Added / Updated / Skipped) …")
    tracker = DeltaTracker()

    added_list:   list[tuple] = []
    updated_list: list[tuple] = []
    skipped_count = 0

    for article_id, (md, article, path) in md_map.items():
        result = tracker.check(article_id, article.html_url, md)
        if result.status == DeltaStatus.ADDED:
            added_list.append((article_id, md, article, path, result))
        elif result.status == DeltaStatus.UPDATED:
            updated_list.append((article_id, md, article, path, result))
        else:
            skipped_count += 1

    logger.info(
        "[Step 3] Delta: Added=%d  Updated=%d  Skipped=%d",
        len(added_list), len(updated_list), skipped_count,
    )

    # ── Step 5: Upload to provider ────────────────────────────────────────────
    logger.info("[Step 4] Uploading changed files to %s …", provider_name.upper())
    vs_id   = fn["get_or_create_store"]()
    asst_id = fn["get_or_create_assistant"](vs_id)

    upload_count = 0
    error_count  = 0

    # Handle Added articles
    for article_id, md, article, path, result in added_list:
        try:
            file_id = fn["upload_file"](path, vs_id)
            tracker.mark_synced(
                article_id=article_id,
                slug=article.slug,
                url=article.html_url,
                markdown=md,
                updated_at=article.updated_at,
                openai_file_id=str(file_id),
            )
            upload_count += 1
            logger.info("[Upload] ✅ Added  '%s'  →  %s", article.title, file_id)
        except Exception as exc:
            error_count += 1
            logger.error("[Upload] ❌ Failed to upload '%s': %s", article.title, exc)

    # Handle Updated articles
    for article_id, md, article, path, result in updated_list:
        try:
            old_file_id = tracker.get_openai_file_id(article_id)
            if old_file_id:
                fn["delete_file"](old_file_id, vs_id)
                logger.debug("[Upload] Deleted old file %s for '%s'", old_file_id, article.title)

            file_id = fn["upload_file"](path, vs_id)
            tracker.mark_synced(
                article_id=article_id,
                slug=article.slug,
                url=article.html_url,
                markdown=md,
                updated_at=article.updated_at,
                openai_file_id=str(file_id),
            )
            upload_count += 1
            logger.info("[Upload] 🔄 Updated '%s'  →  %s", article.title, file_id)
        except Exception as exc:
            error_count += 1
            logger.error("[Upload] ❌ Failed to update '%s': %s", article.title, exc)

    tracker.close()

    # ── Step 6: Stats ─────────────────────────────────────────────────────
    stats = fn["get_stats"](vs_id)
    total_docs = stats.get("total_files", stats.get("total_docs_in_vector_store", upload_count))

    logger.info("=" * 60)
    logger.info("Sync Complete  [%s]", provider_name.upper())
    logger.info("  Files uploaded this run : %d", upload_count)
    logger.info("  Docs in vector store    : %d", total_docs)
    logger.info("  Errors                  : %d", error_count)
    logger.info("  Added   : %d", len(added_list))
    logger.info("  Updated : %d", len(updated_list))
    logger.info("  Skipped : %d", skipped_count)
    logger.info("=" * 60)

    # ── Step 7 (optional): Test Question ────────────────────────────────────
    if test_mode:
        test_question = "How do I add a YouTube video?"
        logger.info("[Test] Asking assistant: '%s'", test_question)
        result = fn["chat"](asst_id, test_question)
        print("\n" + "=" * 60)
        print(f"Q: {test_question}")
        print("-" * 60)
        print(f"A: {result['reply']}")
        if result["citations"]:
            print("\nCitations:")
            for c in result["citations"]:
                print(f"  {c}")
        print("=" * 60 + "\n")

    return {
        "added":    len(added_list),
        "updated":  len(updated_list),
        "skipped":  skipped_count,
        "uploaded": upload_count,
        "total_files_in_store": total_files,
        "assistant_id": asst_id,
        "vector_store_id": vs_id,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OptiSigns Support Bot pipeline")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a test question after syncing",
    )
    args = parser.parse_args()
    run_pipeline(test_mode=args.test)
