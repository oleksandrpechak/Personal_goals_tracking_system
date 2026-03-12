"""
API key authentication middleware for FastAPI / Starlette.

Validates the ``X-API-KEY`` header against ``config.API_SECRET_KEY``.
Attach to any FastAPI app via::

    app.add_middleware(APIKeyMiddleware)

If the project does not use FastAPI, this module is importable but inert.
"""

from __future__ import annotations

import logging
from typing import Callable

from config import API_SECRET_KEY

logger = logging.getLogger(__name__)

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    class APIKeyMiddleware(BaseHTTPMiddleware):
        """
        Starlette/FastAPI middleware that enforces ``X-API-KEY`` authentication.

        * Requests to ``/health`` are exempt (useful for load balancers).
        * All other requests must carry a valid ``X-API-KEY`` header.
        """

        EXEMPT_PATHS: set[str] = {"/health", "/healthz"}

        async def dispatch(
            self, request: Request, call_next: Callable
        ) -> JSONResponse:
            if request.url.path in self.EXEMPT_PATHS:
                return await call_next(request)

            api_key = request.headers.get("X-API-KEY", "")

            if not API_SECRET_KEY:
                logger.error("API_SECRET_KEY is not configured — rejecting request")
                return JSONResponse(
                    {"detail": "Server misconfigured."}, status_code=500
                )

            if api_key != API_SECRET_KEY:
                logger.warning(
                    "Unauthorized API request from %s — invalid or missing X-API-KEY",
                    request.client.host if request.client else "unknown",
                )
                return JSONResponse(
                    {"detail": "Invalid or missing API key."}, status_code=401
                )

            return await call_next(request)

except ImportError:
    # Starlette / FastAPI not installed — provide a no-op placeholder so
    # imports don't break in projects that don't use an HTTP server.
    APIKeyMiddleware = None  # type: ignore[misc,assignment]
    logger.debug("starlette not installed — APIKeyMiddleware unavailable")


# ── Standalone helper (usable without FastAPI) ───────────────────────────────

def require_api_key(provided_key: str) -> bool:
    """
    Validate *provided_key* against the configured ``API_SECRET_KEY``.

    Args:
        provided_key: The key supplied by the caller.

    Returns:
        ``True`` if valid, ``False`` otherwise.
    """
    if not API_SECRET_KEY:
        logger.error("API_SECRET_KEY is not set — all keys rejected")
        return False
    return provided_key == API_SECRET_KEY
