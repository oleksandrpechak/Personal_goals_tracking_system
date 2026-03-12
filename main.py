"""
Entry point for the Personal Productivity Tracker.

Starts:
  1. APScheduler (daily reminder + weekly review)
  2. Telegram bot polling (handles /progress, /help, /start)

Usage:
    python main.py
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from automation.scheduler import create_scheduler
from bot.telegram_bot import build_application
from config import DEBUG, LOG_LEVEL, validate_environment
from db.database import close_connection
from utils.logger import setup_logging

# ── Logging ──────────────────────────────────────────────────────────────────

_level = getattr(logging, LOG_LEVEL, logging.INFO)
setup_logging(level=_level)
logger = logging.getLogger(__name__)


# ── Graceful shutdown ────────────────────────────────────────────────────────

def _handle_signal(sig: int, _frame) -> None:
    logger.info("Received signal %s — shutting down …", signal.Signals(sig).name)
    close_connection()
    sys.exit(0)


async def main() -> None:
    """Bootstrap the scheduler and Telegram bot."""
    validate_environment()
    logger.info("Environment validated — all required variables present.")

    if DEBUG:
        logger.warning("⚠️  Running in DEBUG mode — do not use in production!")
    else:
        logger.info("Production mode active (DEBUG=false).")

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # 1. Start the scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler is running.")

    # 2. Start the Telegram bot (blocking — runs the asyncio loop)
    app = build_application()
    logger.info("Starting Telegram bot polling …")

    # Initialize and start polling
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("Bot is online. Press Ctrl+C to stop.")

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Stopping …")
        finally:
            await app.updater.stop()
            await app.stop()
            scheduler.shutdown(wait=False)
            close_connection()
            logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
