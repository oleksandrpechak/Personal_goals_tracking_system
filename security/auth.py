"""
Telegram command authorization.

Provides a decorator that restricts bot command handlers to the
configured owner chat only.  Unauthorized attempts are silently
ignored and logged as warnings.
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Coroutine

from telegram import Update
from telegram.ext import ContextTypes

from config import TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


def owner_only(
    handler: Callable[..., Coroutine[Any, Any, None]],
) -> Callable[..., Coroutine[Any, Any, None]]:
    """
    Decorator that ensures a Telegram command handler is only executed
    when the message originates from ``TELEGRAM_CHAT_ID``.

    Usage::

        @owner_only
        async def secret_command(update, context):
            ...

    Unauthorized callers receive no reply; the attempt is logged.
    """

    @functools.wraps(handler)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_chat.id if update.effective_chat else None

        if str(chat_id) != str(TELEGRAM_CHAT_ID):
            logger.warning(
                "Unauthorized command attempt — chat_id=%s, command=%s, user=%s",
                chat_id,
                update.message.text if update.message else "?",
                update.effective_user.username if update.effective_user else "?",
            )
            return  # silently ignore

        await handler(update, context)

    return wrapper
