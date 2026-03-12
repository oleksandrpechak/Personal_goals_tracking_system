"""
Configuration module for the Personal Productivity Tracker.

All sensitive values are loaded from environment variables.
Create a .env file in the project root with your actual values.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ─────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# ── Database (Supabase PostgreSQL) ───────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# ── API Security ─────────────────────────────────────────────────────────────
API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "")

# ── Production safeguards ────────────────────────────────────────────────────
DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# ── Scheduling ───────────────────────────────────────────────────────────────
DAILY_REMINDER_HOUR: int = int(os.getenv("DAILY_REMINDER_HOUR", "9"))
DAILY_REMINDER_MINUTE: int = int(os.getenv("DAILY_REMINDER_MINUTE", "0"))

WEEKLY_REVIEW_DAY: str = os.getenv("WEEKLY_REVIEW_DAY", "fri")  # APScheduler day-of-week
WEEKLY_REVIEW_HOUR: int = int(os.getenv("WEEKLY_REVIEW_HOUR", "18"))
WEEKLY_REVIEW_MINUTE: int = int(os.getenv("WEEKLY_REVIEW_MINUTE", "0"))

DAILY_DIGEST_HOUR: int = int(os.getenv("DAILY_DIGEST_HOUR", "20"))
DAILY_DIGEST_MINUTE: int = int(os.getenv("DAILY_DIGEST_MINUTE", "0"))


# ── Environment validation ───────────────────────────────────────────────────

_REQUIRED_VARS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "DATABASE_URL", "API_SECRET_KEY")


def validate_environment() -> None:
    """
    Check that all required environment variables are set and non-empty.

    Raises:
        EnvironmentError: If any required variable is missing or blank.
    """
    missing: list[str] = [
        var for var in _REQUIRED_VARS if not os.getenv(var)
    ]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please set them in your .env file or shell environment."
        )
