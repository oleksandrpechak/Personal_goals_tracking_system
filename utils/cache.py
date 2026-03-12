"""
Simple in-memory TTL cache.

Provides a lightweight ``@timed_cache`` decorator for expensive
queries (analytics, dashboard) without introducing Redis or any
external service.

Default TTL: 300 seconds (5 minutes).
"""

from __future__ import annotations

import functools
import threading
import time
from typing import Any, Callable


class TimedCache:
    """
    Thread-safe in-memory cache with per-key TTL expiry.

    Usage::

        cache = TimedCache(ttl=300)
        cache.set("key", value)
        cache.get("key")       # returns value or None
        cache.invalidate()     # clears everything
    """

    def __init__(self, ttl: int = 300) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        """Return cached value or ``None`` if missing / expired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        """Store *value* under *key* with the configured TTL."""
        with self._lock:
            self._store[key] = (time.monotonic() + self._ttl, value)

    def invalidate(self, key: str | None = None) -> None:
        """Drop a specific *key* or the entire cache if ``None``."""
        with self._lock:
            if key is None:
                self._store.clear()
            else:
                self._store.pop(key, None)


# Module-level default cache instance (5-minute TTL)
_default_cache = TimedCache(ttl=300)


def timed_cache(ttl: int = 300) -> Callable:
    """
    Decorator that caches a function's return value for *ttl* seconds.

    The cache key is built from the function name and its arguments.

    Args:
        ttl: Time-to-live in seconds (default 300 = 5 minutes).
    """
    cache = TimedCache(ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            cached = cache.get(key)
            if cached is not None:
                return cached
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        return wrapper

    return decorator
