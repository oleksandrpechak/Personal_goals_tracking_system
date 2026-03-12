"""
Weekly review report logic.

The `send_weekly_review` function is called by the scheduler every Friday.
"""

from __future__ import annotations

import logging

from bot.telegram_bot import send_message
from db.queries import (
    get_outreach_summary,
    get_weekly_contacted_count,
    get_weekly_opportunity_count,
    get_weekly_productivity_score,
)

logger = logging.getLogger(__name__)


async def send_weekly_review() -> None:
    """
    Compose and send the weekly review summary to Telegram.

    Scheduled to run every Friday at 18:00 (configurable in config.py).
    """
    try:
        found = get_weekly_opportunity_count()
        contacted = get_weekly_contacted_count()
        outreach = get_outreach_summary()
        score = get_weekly_productivity_score()
    except Exception:
        logger.exception("Failed to query weekly stats")
        await send_message("⚠️ Weekly review failed — could not fetch data.")
        return

    outreach_lines = "\n".join(
        f"  • {row['status']}: {row['count']}" for row in outreach
    ) or "  (no outreach data)"

    text = (
        "📋 *Weekly Review*\n\n"
        f"🔎 Opportunities discovered: *{found}*\n"
        f"📞 Opportunities contacted:  *{contacted}*\n\n"
        f"📬 Outreach breakdown:\n{outreach_lines}\n\n"
        f"🏆 *Weekly Productivity Score: {score}*\n\n"
        "Reflect:\n"
        "• What worked this week?\n"
        "• What didn't?\n"
        "• What will you change next week?"
    )

    try:
        await send_message(text)
        logger.info("Weekly review sent.")
    except Exception:
        logger.exception("Failed to send weekly review")
