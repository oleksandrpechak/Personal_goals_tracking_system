"""
APScheduler configuration for recurring tasks.

Jobs are loaded from the centralized task registry (``automation.tasks``).
Config overrides from ``config.py`` are applied on top of registry defaults.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from automation.tasks import TASKS
from config import (
    DAILY_DIGEST_HOUR,
    DAILY_DIGEST_MINUTE,
    DAILY_REMINDER_HOUR,
    DAILY_REMINDER_MINUTE,
    WEEKLY_REVIEW_DAY,
    WEEKLY_REVIEW_HOUR,
    WEEKLY_REVIEW_MINUTE,
)

logger = logging.getLogger(__name__)

# Config overrides keyed by task ID.  Values patch the trigger dict.
_CONFIG_OVERRIDES: dict[str, dict] = {
    "daily_reminder": {"hour": DAILY_REMINDER_HOUR, "minute": DAILY_REMINDER_MINUTE},
    "daily_digest":   {"hour": DAILY_DIGEST_HOUR,   "minute": DAILY_DIGEST_MINUTE},
    "weekly_review":  {
        "day_of_week": WEEKLY_REVIEW_DAY,
        "hour": WEEKLY_REVIEW_HOUR,
        "minute": WEEKLY_REVIEW_MINUTE,
    },
}


def create_scheduler() -> AsyncIOScheduler:
    """
    Build and return an ``AsyncIOScheduler`` with jobs from the task registry.

    The caller is responsible for calling ``scheduler.start()``.
    """
    scheduler = AsyncIOScheduler()

    for task_id, entry in TASKS.items():
        trigger_kwargs = dict(entry["trigger"])
        # Apply config overrides if present
        if task_id in _CONFIG_OVERRIDES:
            trigger_kwargs.update(_CONFIG_OVERRIDES[task_id])

        scheduler.add_job(
            entry["func"],
            trigger=CronTrigger(**trigger_kwargs),
            id=task_id,
            name=entry["name"],
            replace_existing=True,
        )
        logger.info("Scheduled [%s] %s — %s", task_id, entry["name"], trigger_kwargs)

    return scheduler
