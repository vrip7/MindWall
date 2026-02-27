"""
MindWall — Request ID Tracing Middleware
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Generates and propagates unique request IDs for distributed tracing.
"""

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates a unique request ID for each incoming request.
    The ID is added to response headers and structlog context for tracing.
    """

    async def dispatch(self, request: Request, call_next):
        # Use existing request ID from header or generate a new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Bind to structlog context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
