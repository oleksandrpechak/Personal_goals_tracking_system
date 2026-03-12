"""
HTTPS enforcement middleware for FastAPI / Starlette.

Rejects requests where ``X-Forwarded-Proto`` is not ``https``
(common behind reverse proxies like nginx, Cloudflare, AWS ALB).

Attach to any FastAPI app via::

    app.add_middleware(HTTPSEnforcementMiddleware)
"""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    class HTTPSEnforcementMiddleware(BaseHTTPMiddleware):
        """
        Reject non-HTTPS requests based on the ``X-Forwarded-Proto`` header.

        Health-check paths are exempt so that load balancers can probe
        over plain HTTP internally.
        """

        EXEMPT_PATHS: set[str] = {"/health", "/healthz"}

        async def dispatch(
            self, request: Request, call_next: Callable
        ) -> JSONResponse:
            if request.url.path in self.EXEMPT_PATHS:
                return await call_next(request)

            forwarded_proto = request.headers.get("x-forwarded-proto", "https")

            if forwarded_proto != "https":
                logger.warning(
                    "Rejected non-HTTPS request from %s (X-Forwarded-Proto=%s)",
                    request.client.host if request.client else "unknown",
                    forwarded_proto,
                )
                return JSONResponse(
                    {"detail": "HTTPS is required."},
                    status_code=403,
                )

            return await call_next(request)

except ImportError:
    HTTPSEnforcementMiddleware = None  # type: ignore[misc,assignment]
    logger.debug("starlette not installed — HTTPSEnforcementMiddleware unavailable")
