"""
In-memory rate limiter for Telegram bot commands.

Uses a sliding-window counter per ``chat_id`` to prevent spam.
Configurable via ``MAX_COMMANDS`` and ``WINDOW_SECONDS``.
"""

from __future__ import annotations

import time
import logging
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

# ── Defaults ─────────────────────────────────────────────────────────────────

MAX_COMMANDS: int = 10
"""Maximum number of commands allowed within the sliding window."""

WINDOW_SECONDS: int = 60
"""Length of the sliding window in seconds."""

# ── Internal state ───────────────────────────────────────────────────────────

_timestamps: dict[int, list[float]] = defaultdict(list)
_lock = Lock()


def is_rate_limited(chat_id: int) -> bool:
    """
    Check whether *chat_id* has exceeded the allowed command rate.

    Removes expired timestamps from the window before checking.

    Args:
        chat_id: Telegram chat/user ID.

    Returns:
        ``True`` if the user should be throttled, ``False`` otherwise.
    """
    now = time.monotonic()
    cutoff = now - WINDOW_SECONDS

    with _lock:
        # Prune expired entries
        _timestamps[chat_id] = [
            ts for ts in _timestamps[chat_id] if ts > cutoff
        ]

        if len(_timestamps[chat_id]) >= MAX_COMMANDS:
            logger.warning(
                "Rate limit exceeded for chat_id=%d (%d commands in %ds)",
                chat_id,
                len(_timestamps[chat_id]),
                WINDOW_SECONDS,
            )
            return True

        _timestamps[chat_id].append(now)
        return False


def reset(chat_id: int | None = None) -> None:
    """
    Clear rate-limit history.

    Args:
        chat_id: Reset a specific user, or all users if ``None``.
    """
    with _lock:
        if chat_id is None:
            _timestamps.clear()
        else:
            _timestamps.pop(chat_id, None)
