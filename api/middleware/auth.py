"""
MindWall — API Key Authentication Middleware
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Validates the X-MindWall-Key header for all API requests from internal services.
"""

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = structlog.get_logger(__name__)

# Paths that do not require authentication
PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/favicon.ico",
}

# WebSocket paths handled separately
WEBSOCKET_PATHS = {
    "/ws/alerts",
}


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates the X-MindWall-Key header against the
    configured API secret key. All internal services share this key.
    """

    def __init__(self, app, api_secret_key: str):
        super().__init__(app)
        self.api_secret_key = api_secret_key

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow public paths without auth
        if path in PUBLIC_PATHS:
            return await call_next(request)

        # Allow WebSocket upgrades (auth checked at WebSocket level if needed)
        if path in WEBSOCKET_PATHS:
            return await call_next(request)

        # Allow CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Validate API key
        api_key = request.headers.get("X-MindWall-Key")
        if not api_key:
            logger.warning("auth.missing_key", path=path, method=request.method)
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing X-MindWall-Key header"},
            )

        if api_key != self.api_secret_key:
            logger.warning("auth.invalid_key", path=path, method=request.method)
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key"},
            )

        return await call_next(request)
