"""
Structured logging configuration for the Personal Productivity Tracker.

Provides a pre-configured logger factory and a one-call setup function
that should be invoked once at application startup (in main.py).
"""

from __future__ import annotations

import logging
import sys

from utils.sanitizer import SensitiveDataFilter


_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger with a consistent format and secret-redacting filter.

    Safe to call multiple times — only the first invocation takes effect.

    Args:
        level: The minimum log level to emit (default ``logging.INFO``).
    """
    global _configured
    if _configured:
        return

    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT))
    handler.addFilter(SensitiveDataFilter())

    root.addHandler(handler)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger that inherits the root configuration.

    Usage::

        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Scheduler started")
        logger.warning("Telegram API slow")
        logger.error("Database connection lost")

    Args:
        name: Typically ``__name__`` of the calling module.
    """
    return logging.getLogger(name)
