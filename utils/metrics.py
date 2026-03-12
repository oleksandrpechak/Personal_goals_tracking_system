"""
Lightweight in-memory runtime metrics.

Provides atomic counters for tracking key system events without
any external dependency (no Redis, no Prometheus).

Usage::

    from utils.metrics import metrics
    metrics.inc("jobs_found", 5)
    metrics.inc("messages_sent")
    print(metrics.snapshot())
"""

from __future__ import annotations

import threading
import time
from typing import Any


class Metrics:
    """Thread-safe in-memory counters with an uptime clock."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {
            "jobs_found": 0,
            "jobs_inserted": 0,
            "jobs_skipped_duplicate": 0,
            "messages_sent": 0,
            "errors": 0,
            "commands_handled": 0,
            "commands_rate_limited": 0,
            "cleanup_deleted": 0,
        }
        self._started_at: float = time.time()

    # ── Mutators ─────────────────────────────────────────────────────────

    def inc(self, key: str, delta: int = 1) -> None:
        """Increment *key* by *delta* (default 1)."""
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + delta

    def reset(self) -> None:
        """Zero all counters (does not reset uptime)."""
        with self._lock:
            for k in self._counters:
                self._counters[k] = 0

    # ── Accessors ────────────────────────────────────────────────────────

    def get(self, key: str) -> int:
        """Return the current value of *key*."""
        with self._lock:
            return self._counters.get(key, 0)

    def uptime_seconds(self) -> int:
        """Return seconds since the Metrics instance was created."""
        return int(time.time() - self._started_at)

    def snapshot(self) -> dict[str, Any]:
        """Return a copy of all counters plus uptime."""
        with self._lock:
            data = dict(self._counters)
        data["uptime_seconds"] = self.uptime_seconds()
        return data


# Module-level singleton
metrics = Metrics()
