"""
Centralized task registry for scheduled jobs.

Every scheduled task is registered here.  The scheduler iterates
this registry instead of importing individual modules directly.

Adding a new task is a one-line change.
"""

from __future__ import annotations

import logging
from typing import Any

from bot.digest import send_daily_digest
from bot.reminders import send_daily_reminder
from bot.reports import send_weekly_review
from db.repository import OpportunityRepository

logger = logging.getLogger(__name__)


# ── Cleanup wrapper (sync → scheduler-compatible async) ──────────────────────

async def run_cleanup() -> None:
    """Delete opportunities older than 180 days."""
    try:
        deleted = OpportunityRepository.cleanup_old(days=180)
        logger.info("Cleanup task complete — %d rows deleted", deleted)
    except Exception:
        logger.exception("Cleanup task failed")


# ── Task type ────────────────────────────────────────────────────────────────

TaskEntry = dict[str, Any]
"""
Each entry contains:
    func:    async callable to execute
    trigger: dict of APScheduler CronTrigger kwargs
    name:    human-readable label
"""

# ── Registry ─────────────────────────────────────────────────────────────────

TASKS: dict[str, TaskEntry] = {
    "daily_reminder": {
        "func": send_daily_reminder,
        "trigger": {"hour": 9, "minute": 0},
        "name": "Daily Focus Reminder",
    },
    "daily_digest": {
        "func": send_daily_digest,
        "trigger": {"hour": 20, "minute": 0},
        "name": "Daily Opportunity Digest",
    },
    "weekly_review": {
        "func": send_weekly_review,
        "trigger": {"day_of_week": "fri", "hour": 18, "minute": 0},
        "name": "Weekly Review Report",
    },
    "data_cleanup": {
        "func": run_cleanup,
        "trigger": {"day_of_week": "sun", "hour": 3, "minute": 0},
        "name": "Old Data Cleanup (180 days)",
    },
}
