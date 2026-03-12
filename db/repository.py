"""
Repository layer — centralised database access.

All SQL lives here.  Other modules import repository classes instead
of building SQL themselves.  Each method uses ``get_cursor()`` so
transactions are managed automatically.

Includes:
  • ``OpportunityRepository`` — opportunities table
  • ``OutreachRepository``    — outreach_targets table
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from db.database import get_cursor
from utils.cache import timed_cache
from utils.metrics import metrics

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# OpportunityRepository
# ═════════════════════════════════════════════════════════════════════════════

class OpportunityRepository:
    """All queries against the *opportunities* table."""

    # ── Write ────────────────────────────────────────────────────────────

    @staticmethod
    def insert(title: str, url: str, source: str) -> str | None:
        """
        Insert a new opportunity using ``ON CONFLICT DO NOTHING``.

        Deduplication is enforced by the ``UNIQUE(url)`` constraint.

        Returns:
            The UUID of the new row, or ``None`` if it was a duplicate.
        """
        opportunity_id = str(uuid.uuid4())
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO opportunities (id, source, title, url, created_at, contacted)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
                RETURNING id
                """,
                (opportunity_id, source, title, url, datetime.utcnow(), False),
            )
            row = cur.fetchone()

        if row is None:
            logger.info("Duplicate opportunity skipped — %s", url)
            metrics.inc("jobs_skipped_duplicate")
            return None

        logger.info("Logged opportunity %s — %s", opportunity_id, title)
        metrics.inc("jobs_inserted")
        return opportunity_id

    # ── Aggregated weekly stats (single query) ───────────────────────────

    @staticmethod
    @timed_cache(ttl=300)
    def weekly_stats() -> dict[str, int]:
        """
        Return weekly opportunity counts in one DB round-trip.

        Keys: ``found``, ``contacted``.
        """
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*)                              AS found,
                    COUNT(*) FILTER (WHERE contacted)     AS contacted
                FROM opportunities
                WHERE created_at >= NOW() - INTERVAL '7 days'
                """
            )
            row = cur.fetchone()
        return {
            "found": int(row["found"]),
            "contacted": int(row["contacted"]),
        }

    # ── Aggregated monthly stats (single query) ──────────────────────────

    @staticmethod
    @timed_cache(ttl=300)
    def monthly_stats() -> dict[str, int]:
        """
        Return monthly opportunity counts in one DB round-trip.

        Keys: ``found``, ``contacted``.
        """
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*)                              AS found,
                    COUNT(*) FILTER (WHERE contacted)     AS contacted
                FROM opportunities
                WHERE date_trunc('month', created_at) = date_trunc('month', NOW())
                """
            )
            row = cur.fetchone()
        return {
            "found": int(row["found"]),
            "contacted": int(row["contacted"]),
        }

    # ── Today's opportunities ────────────────────────────────────────────

    @staticmethod
    @timed_cache(ttl=300)
    def today(limit: int = 10) -> list[dict[str, str]]:
        """Return up to *limit* opportunities created today."""
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT title, url
                FROM opportunities
                WHERE created_at::date = CURRENT_DATE
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
        return [{"title": r["title"], "url": r["url"]} for r in rows]

    # ── Productivity score ───────────────────────────────────────────────

    @staticmethod
    def weekly_productivity_score() -> int:
        """``(found × 2) + (contacted × 3)``."""
        s = OpportunityRepository.weekly_stats()
        return (s["found"] * 2) + (s["contacted"] * 3)

    # ── URL existence check (still useful for callers outside insert) ────

    @staticmethod
    def exists(url: str) -> bool:
        """Return ``True`` if a row with *url* exists."""
        with get_cursor() as cur:
            cur.execute(
                "SELECT 1 FROM opportunities WHERE url = %s LIMIT 1",
                (url,),
            )
            return cur.fetchone() is not None

    # ── Last opportunity timestamp ───────────────────────────────────────

    @staticmethod
    def last_created_at() -> datetime | None:
        """Return the ``created_at`` of the most recent opportunity, or ``None``."""
        with get_cursor() as cur:
            cur.execute(
                "SELECT MAX(created_at) AS latest FROM opportunities"
            )
            row = cur.fetchone()
        return row["latest"] if row and row["latest"] else None

    # ── Cleanup (Task 13) ────────────────────────────────────────────────

    @staticmethod
    def cleanup_old(days: int = 180) -> int:
        """
        Delete opportunities older than *days* days.

        Returns:
            Number of rows deleted.
        """
        with get_cursor() as cur:
            cur.execute(
                "DELETE FROM opportunities WHERE created_at < NOW() - make_interval(days => %s)",
                (days,),
            )
            deleted = cur.rowcount
        if deleted:
            logger.info("Cleaned up %d opportunities older than %d days", deleted, days)
            metrics.inc("cleanup_deleted", deleted)
        return deleted


# ═════════════════════════════════════════════════════════════════════════════
# OutreachRepository
# ═════════════════════════════════════════════════════════════════════════════

class OutreachRepository:
    """All queries against the *outreach_targets* table."""

    @staticmethod
    @timed_cache(ttl=300)
    def summary() -> list[dict[str, Any]]:
        """Return outreach targets grouped by status."""
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT status, COUNT(*) AS cnt
                FROM outreach_targets
                GROUP BY status
                ORDER BY cnt DESC
                """
            )
            rows = cur.fetchall()
        return [{"status": r["status"], "count": r["cnt"]} for r in rows]

    @staticmethod
    @timed_cache(ttl=300)
    def pipeline() -> dict[str, int]:
        """Return counts for ``pending``, ``contacted``, ``converted``."""
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN LOWER(status) = 'pending'   THEN 1 ELSE 0 END), 0) AS pending,
                    COALESCE(SUM(CASE WHEN LOWER(status) = 'contacted' THEN 1 ELSE 0 END), 0) AS contacted,
                    COALESCE(SUM(CASE WHEN LOWER(status) = 'converted' THEN 1 ELSE 0 END), 0) AS converted
                FROM outreach_targets
                """
            )
            row = cur.fetchone()
        return {
            "pending": int(row["pending"]),
            "contacted": int(row["contacted"]),
            "converted": int(row["converted"]),
        }
