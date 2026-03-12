"""
Log sanitization utilities.

Provides a logging filter and helper functions to ensure that sensitive
values (tokens, passwords, connection strings) are never emitted to logs.
"""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import urlparse, urlunparse


# ── Patterns that match common secret formats ────────────────────────────────

_SENSITIVE_ENV_KEYS = (
    "TELEGRAM_BOT_TOKEN",
    "DATABASE_URL",
    "API_SECRET_KEY",
)

_URL_PASSWORD_RE = re.compile(
    r"(?P<scheme>[a-zA-Z+]+)://(?P<user>[^:@]+):(?P<password>[^@]+)@"
)


def mask_url(url: str) -> str:
    """
    Replace user and password in a database / HTTP URL with ``***``.

    Example::

        postgres://alice:s3cret@host/db  →  postgres://***:***@host/db
    """
    try:
        parsed = urlparse(url)
        if parsed.password or parsed.username:
            masked = parsed._replace(
                netloc=f"***:***@{parsed.hostname}"
                + (f":{parsed.port}" if parsed.port else "")
            )
            return urlunparse(masked)
    except Exception:
        pass
    # Fallback regex for non-standard schemes (e.g. postgres+psycopg2://)
    return _URL_PASSWORD_RE.sub(r"\g<scheme>://***:***@", url)


def _build_secret_values() -> set[str]:
    """
    Collect the raw values of known-secret environment variables so they
    can be redacted from log output.
    """
    secrets: set[str] = set()
    for key in _SENSITIVE_ENV_KEYS:
        val = os.getenv(key, "")
        if val:
            secrets.add(val)
            # Also add the password portion of URLs
            parsed = urlparse(val)
            if parsed.password:
                secrets.add(parsed.password)
            if parsed.username:
                secrets.add(parsed.username)
    return secrets


class SensitiveDataFilter(logging.Filter):
    """
    A :class:`logging.Filter` that replaces known secret values in every
    log record with ``***REDACTED***``.

    Attach it to any handler::

        handler.addFilter(SensitiveDataFilter())
    """

    def __init__(self) -> None:
        super().__init__()
        self._secrets: set[str] = _build_secret_values()

    def refresh_secrets(self) -> None:
        """Re-read environment variables (e.g. after a reload)."""
        self._secrets = _build_secret_values()

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask secrets in the log message and return ``True`` (never drops)."""
        if self._secrets:
            msg = record.getMessage()
            for secret in self._secrets:
                if secret in msg:
                    msg = msg.replace(secret, "***REDACTED***")
            # Overwrite the message so the formatter uses the sanitised version
            record.msg = msg
            record.args = None
        return True
