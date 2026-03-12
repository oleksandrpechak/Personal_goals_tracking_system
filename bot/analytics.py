"""
Opportunity analytics for the Personal Productivity Tracker.

Thin analytics layer that aggregates data from the repository
into structured dicts ready for consumption by Telegram handlers or the CLI.

Results are backed by the repository's 5-minute cache.
"""

from __future__ import annotations

import logging
from typing import TypedDict

from db.repository import OpportunityRepository

logger = logging.getLogger(__name__)


class OpportunityStats(TypedDict):
    opportunities: int
    contacted: int
    contact_rate: float


def _contact_rate(total: int, contacted: int) -> float:
    """Return the contact rate as a percentage, guarding against division by zero."""
    if total == 0:
        return 0.0
    return round((contacted / total) * 100, 1)


def get_weekly_opportunities() -> OpportunityStats:
    """Return weekly opportunity statistics (single DB query, cached)."""
    s = OpportunityRepository.weekly_stats()
    return {
        "opportunities": s["found"],
        "contacted": s["contacted"],
        "contact_rate": _contact_rate(s["found"], s["contacted"]),
    }


def get_monthly_opportunities() -> OpportunityStats:
    """Return monthly opportunity statistics (single DB query, cached)."""
    s = OpportunityRepository.monthly_stats()
    return {
        "opportunities": s["found"],
        "contacted": s["contacted"],
        "contact_rate": _contact_rate(s["found"], s["contacted"]),
    }


def get_contact_rate() -> float:
    """Return the overall monthly contact rate as a percentage."""
    stats = get_monthly_opportunities()
    return stats["contact_rate"]
