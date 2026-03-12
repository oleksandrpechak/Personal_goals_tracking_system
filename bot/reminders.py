"""
Daily reminder logic.

The `send_daily_reminder` function is called by the scheduler every morning.
"""

from __future__ import annotations

import datetime
import logging

from bot.telegram_bot import send_message

logger = logging.getLogger(__name__)


async def send_daily_reminder() -> None:
    """
    Compose and send the daily focus reminder to Telegram.

    Scheduled to run every day at 09:00 (configurable in config.py).
    """
    today = datetime.date.today().strftime("%A, %d %B %Y")

    text = (
        f"📌 *Daily Focus — {today}*\n\n"
        "1️⃣  Complete one *sales / outreach* task\n"
        "2️⃣  Ship one *product improvement*\n"
        "3️⃣  Finish one *learning* task\n\n"
        "_Don't pretend you'll remember later._"
    )

    try:
        await send_message(text)
        logger.info("Daily reminder sent.")
    except Exception:
        logger.exception("Failed to send daily reminder")
