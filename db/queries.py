"""
SQL query functions for the Personal Productivity Tracker.

These are thin wrappers that delegate to the repository layer
(``db.repository``).  Existing callers continue to work without changes.
"""

from __future__ import annotations

import logging
from typing import Any

from db.repository import OpportunityRepository, OutreachRepository

logger = logging.getLogger(__name__)


# ── Opportunity logging (Task 4 — uses ON CONFLICT in the repository) ────────

def opportunity_exists(url: str) -> bool:
    """Check whether an opportunity with the given *url* already exists."""
    return OpportunityRepository.exists(url)


def log_opportunity(title: str, url: str, source: str) -> str | None:
    """
    Insert a new opportunity (deduplication via DB UNIQUE constraint).

    Returns the UUID of the new row, or ``None`` for duplicates.
    """
    return OpportunityRepository.insert(title, url, source)


# ── Weekly review stats (Task 5 — single aggregated query) ───────────────────

def get_weekly_opportunity_count() -> int:
    return OpportunityRepository.weekly_stats()["found"]


def get_weekly_contacted_count() -> int:
    return OpportunityRepository.weekly_stats()["contacted"]


# ── Monthly progress stats (Task 5 — single aggregated query) ────────────────

def get_monthly_opportunity_count() -> int:
    return OpportunityRepository.monthly_stats()["found"]


def get_monthly_contacted_count() -> int:
    return OpportunityRepository.monthly_stats()["contacted"]


# ── Outreach helpers ─────────────────────────────────────────────────────────

def get_outreach_summary() -> list[dict[str, Any]]:
    return OutreachRepository.summary()


def get_outreach_pipeline() -> dict[str, int]:
    return OutreachRepository.pipeline()


# ── Today's opportunities ────────────────────────────────────────────────────

def get_today_opportunities(limit: int = 10) -> list[dict[str, str]]:
    return OpportunityRepository.today(limit=limit)


# ── Weekly productivity score ────────────────────────────────────────────────

def get_weekly_productivity_score() -> int:
    return OpportunityRepository.weekly_productivity_score()
