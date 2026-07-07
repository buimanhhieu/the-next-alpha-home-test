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

# ── Ensure the scraper package directory is on PYTHONPATH ────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from config import (
    ARTICLES_DIR,
    LOG_LEVEL,
    OPENAI_API_KEY,
)
from zendesk_scraper import ZendeskScraper
from markdown_converter import html_to_markdown
from delta_tracker import DeltaTracker, DeltaStatus
from openai_uploader import (
    get_or_create_vector_store,
    get_or_create_assistant,
    upload_file,
    delete_file,
    get_vector_store_stats,
    chat_with_assistant,
)

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline(test_mode: bool = False):
    logger.info("=" * 60)
    logger.info("OptiSigns Support Bot – Sync Pipeline Starting")
    logger.info("=" * 60)

    # Validate config
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set. Please configure your .env file.")
        sys.exit(1)

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

    # ── Step 5: Upload to OpenAI ──────────────────────────────────────────────
    logger.info("[Step 4] Uploading changed files to OpenAI …")
    vs_id    = get_or_create_vector_store()
    asst_id  = get_or_create_assistant(vs_id)

    upload_count = 0
    error_count  = 0

    # Handle Added articles
    for article_id, md, article, path, result in added_list:
        try:
            file_id = upload_file(path, vs_id)
            tracker.mark_synced(
                article_id=article_id,
                slug=article.slug,
                url=article.html_url,
                markdown=md,
                updated_at=article.updated_at,
                openai_file_id=file_id,
            )
            upload_count += 1
            logger.info("[Upload] ✅ Added  '%s'  →  %s", article.title, file_id)
        except Exception as exc:
            error_count += 1
            logger.error("[Upload] ❌ Failed to upload '%s': %s", article.title, exc)

    # Handle Updated articles
    for article_id, md, article, path, result in updated_list:
        try:
            # Delete old file first
            old_file_id = tracker.get_openai_file_id(article_id)
            if old_file_id:
                delete_file(old_file_id, vs_id)
                logger.debug("[Upload] Deleted old file %s for '%s'", old_file_id, article.title)

            file_id = upload_file(path, vs_id)
            tracker.mark_synced(
                article_id=article_id,
                slug=article.slug,
                url=article.html_url,
                markdown=md,
                updated_at=article.updated_at,
                openai_file_id=file_id,
            )
            upload_count += 1
            logger.info("[Upload] 🔄 Updated '%s'  →  %s", article.title, file_id)
        except Exception as exc:
            error_count += 1
            logger.error("[Upload] ❌ Failed to update '%s': %s", article.title, exc)

    tracker.close()

    # ── Step 6: Stats ─────────────────────────────────────────────────────────
    stats = get_vector_store_stats(vs_id)
    total_files = stats.get("total_files", upload_count)

    logger.info("=" * 60)
    logger.info("Sync Complete")
    logger.info("  Files uploaded this run : %d", upload_count)
    logger.info("  Files in vector store   : %d", total_files)
    logger.info("  Errors                  : %d", error_count)
    logger.info("  Added   : %d", len(added_list))
    logger.info("  Updated : %d", len(updated_list))
    logger.info("  Skipped : %d", skipped_count)
    logger.info("  Assistant ID            : %s", asst_id)
    logger.info("  Vector Store ID         : %s", vs_id)
    logger.info("=" * 60)

    # ── Step 7 (optional): Test Question ─────────────────────────────────────
    if test_mode:
        test_question = "How do I add a YouTube video?"
        logger.info("[Test] Asking assistant: '%s'", test_question)
        result = chat_with_assistant(asst_id, test_question)
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
