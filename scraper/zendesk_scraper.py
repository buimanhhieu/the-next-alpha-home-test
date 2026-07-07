"""
Zendesk Help Center API scraper for support.optisigns.com.

Uses the public Zendesk API (no auth needed for public articles).
Endpoint: GET /api/v2/help_center/en-us/articles.json
"""
import logging
import time
import requests
from typing import Generator, Dict, Any
from config import ZENDESK_ARTICLES_URL, ARTICLES_PER_PAGE, MAX_ARTICLES

logger = logging.getLogger(__name__)


class Article:
    """Represents a single help-center article fetched from Zendesk."""

    def __init__(self, data: Dict[str, Any]):
        self.id: int              = data["id"]
        self.title: str           = data["title"]
        self.html_url: str        = data["html_url"]
        self.body_html: str       = data.get("body", "")
        self.updated_at: str      = data["updated_at"]   # ISO-8601
        self.section_id: int      = data.get("section_id", 0)
        self.slug: str            = self._make_slug()

    def _make_slug(self) -> str:
        """Create a filesystem-safe slug from the article title."""
        import re
        slug = self.title.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"\s+", "-", slug.strip())
        slug = slug[:80]   # limit length
        return slug or f"article-{self.id}"


class ZendeskScraper:
    """
    Fetches articles from the Zendesk Help Center API.

    Paginates automatically until MAX_ARTICLES is reached or there are no
    more pages.  Retries on transient HTTP errors.
    """

    RETRY_ATTEMPTS = 3
    RETRY_DELAY    = 2   # seconds

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept":     "application/json",
            "User-Agent": "SupportBotScraper/1.0",
        })

    # ── Public API ────────────────────────────────────────────────────────────

    def fetch_articles(self) -> list[Article]:
        """
        Return a list of Article objects (up to MAX_ARTICLES).
        Logs progress page by page.
        """
        articles: list[Article] = []
        next_url = f"{ZENDESK_ARTICLES_URL}?per_page={ARTICLES_PER_PAGE}&sort_by=updated_at&sort_order=desc"

        page = 1
        while next_url and len(articles) < MAX_ARTICLES:
            logger.info("[Scraper] Fetching page %d – %s", page, next_url)
            data = self._get_json(next_url)

            raw_articles = data.get("articles", [])
            for raw in raw_articles:
                if len(articles) >= MAX_ARTICLES:
                    break
                # Skip draft or bodyless articles
                if raw.get("draft") or not raw.get("body"):
                    continue
                articles.append(Article(raw))

            next_url = data.get("next_page")
            page += 1
            if next_url:
                time.sleep(0.3)   # be polite to the server

        logger.info("[Scraper] Collected %d articles total.", len(articles))
        return articles

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_json(self, url: str) -> Dict[str, Any]:
        for attempt in range(1, self.RETRY_ATTEMPTS + 1):
            try:
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as exc:
                logger.warning(
                    "[Scraper] Request error (attempt %d/%d): %s",
                    attempt, self.RETRY_ATTEMPTS, exc
                )
                if attempt < self.RETRY_ATTEMPTS:
                    time.sleep(self.RETRY_DELAY * attempt)
        raise RuntimeError(f"Failed to fetch {url} after {self.RETRY_ATTEMPTS} attempts")
