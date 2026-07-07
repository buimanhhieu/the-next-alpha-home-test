"""
Delta tracker using SQLite.

Schema:
    article_sync (
        id          TEXT PRIMARY KEY,   -- Zendesk article ID (string)
        slug        TEXT,
        url         TEXT,
        content_hash TEXT,             -- SHA-256 of Markdown content
        updated_at  TEXT,              -- ISO-8601 from Zendesk
        openai_file_id TEXT,           -- file id returned by OpenAI Files API
        synced_at   TEXT               -- ISO-8601 of last successful upload
    )

Delta logic:
    • url NOT in DB       → Added
    • url in DB, hash changed  → Updated
    • url in DB, hash same     → Skipped
"""
import hashlib
import logging
import os
import sqlite3
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from config import DELTA_DB_PATH

logger = logging.getLogger(__name__)


class DeltaStatus(Enum):
    ADDED   = "added"
    UPDATED = "updated"
    SKIPPED = "skipped"


@dataclass
class DeltaResult:
    status: DeltaStatus
    article_id: str
    old_hash: Optional[str] = None
    new_hash: str = ""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DeltaTracker:
    """
    Persists article metadata in SQLite and reports delta on each sync run.
    """

    def __init__(self):
        os.makedirs(os.path.dirname(DELTA_DB_PATH), exist_ok=True)
        self._conn = sqlite3.connect(DELTA_DB_PATH, check_same_thread=False)
        self._create_table()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ── Public API ────────────────────────────────────────────────────────────

    def check(self, article_id: str, url: str, markdown: str) -> DeltaResult:
        """
        Compare article against stored state and return DeltaResult.
        Does NOT persist anything – call mark_synced() after successful upload.
        """
        new_hash = _sha256(markdown)
        row = self._fetch(article_id)

        if row is None:
            return DeltaResult(DeltaStatus.ADDED, article_id, None, new_hash)

        old_hash = row["content_hash"]
        if old_hash == new_hash:
            return DeltaResult(DeltaStatus.SKIPPED, article_id, old_hash, new_hash)

        return DeltaResult(DeltaStatus.UPDATED, article_id, old_hash, new_hash)

    def mark_synced(
        self,
        article_id: str,
        slug: str,
        url: str,
        markdown: str,
        updated_at: str,
        openai_file_id: str = "",
    ):
        """Upsert the record after a successful upload."""
        content_hash = _sha256(markdown)
        synced_at    = datetime.now(timezone.utc).isoformat()

        self._conn.execute(
            """
            INSERT INTO article_sync
                (id, slug, url, content_hash, updated_at, openai_file_id, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                slug           = excluded.slug,
                url            = excluded.url,
                content_hash   = excluded.content_hash,
                updated_at     = excluded.updated_at,
                openai_file_id = excluded.openai_file_id,
                synced_at      = excluded.synced_at
            """,
            (article_id, slug, url, content_hash, updated_at, openai_file_id, synced_at),
        )
        self._conn.commit()

    def get_openai_file_id(self, article_id: str) -> Optional[str]:
        """Return previously stored OpenAI file id (for deletion on update)."""
        row = self._fetch(article_id)
        return row["openai_file_id"] if row else None

    def all_records(self) -> list[dict]:
        cur = self._conn.execute("SELECT * FROM article_sync")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    # ── Private helpers ───────────────────────────────────────────────────────

    def _create_table(self):
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS article_sync (
                id             TEXT PRIMARY KEY,
                slug           TEXT,
                url            TEXT,
                content_hash   TEXT,
                updated_at     TEXT,
                openai_file_id TEXT DEFAULT '',
                synced_at      TEXT
            )
            """
        )
        self._conn.commit()

    def _fetch(self, article_id: str) -> Optional[dict]:
        cur = self._conn.execute(
            "SELECT * FROM article_sync WHERE id = ?", (str(article_id),)
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
