"""
Retry helper with exponential backoff.

Designed for external calls (HTTP scraping, API requests) where
transient failures are expected.

Usage::

    from utils.retry import with_retry

    @with_retry(max_attempts=3, delays=(2, 5, 10))
    def fetch_page(url: str) -> str:
        ...
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, Sequence

logger = logging.getLogger(__name__)

DEFAULT_DELAYS: tuple[int, ...] = (2, 5, 10)


def with_retry(
    max_attempts: int = 3,
    delays: Sequence[int] = DEFAULT_DELAYS,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable:
    """
    Decorator that retries the wrapped function with exponential backoff.

    Args:
        max_attempts: Maximum number of tries (including the first).
        delays:       Sequence of sleep durations between retries (seconds).
                      If there are fewer entries than retries, the last
                      value is reused.
        exceptions:   Exception types that trigger a retry.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__,
                            max_attempts,
                            exc,
                        )
                        raise
                    delay = delays[min(attempt - 1, len(delays) - 1)]
                    logger.warning(
                        "%s attempt %d/%d failed (%s) — retrying in %ds",
                        func.__name__,
                        attempt,
                        max_attempts,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
            raise last_exc  # type: ignore[misc]  # unreachable in practice

        return wrapper

    return decorator
