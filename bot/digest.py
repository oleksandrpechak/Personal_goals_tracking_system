"""
Daily opportunity digest logic.

The `send_daily_digest` function is called by the scheduler every evening.
"""

from __future__ import annotations

import datetime
import logging

from bot.telegram_bot import send_message
from db.queries import get_today_opportunities

logger = logging.getLogger(__name__)


async def send_daily_digest() -> None:
    """
    Compose and send the daily opportunity digest to Telegram.

    Lists up to 10 new opportunities discovered today.
    Scheduled to run every day at 20:00 (configurable in config.py).
    """
    today = datetime.date.today().strftime("%A, %d %B %Y")

    try:
        opportunities = get_today_opportunities(limit=10)
    except Exception:
        logger.exception("Failed to query today's opportunities")
        await send_message("⚠️ Daily digest failed — could not fetch data.")
        return

    if opportunities:
        items = "\n".join(
            f"  • {opp['title']} — {opp['url']}" for opp in opportunities
        )
    else:
        items = "  (no new opportunities today)"

    text = (
        f"📰 *Daily Opportunity Digest — {today}*\n\n"
        f"New opportunities discovered today:\n{items}"
    )

    try:
        await send_message(text)
        logger.info("Daily digest sent (%d opportunities).", len(opportunities))
    except Exception:
        logger.exception("Failed to send daily digest")
