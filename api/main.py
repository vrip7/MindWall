"""
MindWall — FastAPI Core Engine
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Application factory and entrypoint for the MindWall analysis API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.lifespan import lifespan
from .core.logging import configure_logging
from .middleware.auth import APIKeyAuthMiddleware
from .middleware.request_id import RequestIDMiddleware
from .routers import analyze, dashboard, alerts, employees, settings, websocket


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = get_settings()
    configure_logging(config.log_level)

    app = FastAPI(
        title="MindWall API",
        description="Cognitive Firewall — AI-Powered Human Manipulation Detection Engine",
        version="1.0.0",
        docs_url="/docs" if config.log_level == "DEBUG" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    # CORS — allow dashboard and extension origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "chrome-extension://*",
            "moz-extension://*",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(APIKeyAuthMiddleware, api_secret_key=config.api_secret_key)

    # Register routers
    app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
    app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
    app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
    app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
    app.include_router(websocket.router, tags=["WebSocket"])

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "service": "mindwall-api", "version": "1.0.0"}

    return app


app = create_app()
