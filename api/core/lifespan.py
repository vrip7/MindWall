"""
MindWall — Application Lifespan Events
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Handles startup/shutdown lifecycle events for the FastAPI application.
"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .config import get_settings
from ..db.database import create_engine_and_session, run_migrations
from ..analysis.llm_client import OllamaClient
from ..analysis.pipeline import AnalysisPipeline
from ..db.repositories.analysis_repo import AnalysisRepository
from ..db.repositories.alert_repo import AlertRepository
from ..db.repositories.baseline_repo import BaselineRepository
from ..db.repositories.employee_repo import EmployeeRepository
from ..websocket.manager import WebSocketManager

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    settings = get_settings()

    logger.info("mindwall.startup", version="1.0.0")

    # Initialize database engine and session factory
    engine, session_factory = await create_engine_and_session(settings.database_url)
    await run_migrations(engine)

    # Initialize Ollama LLM client
    llm_client = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout=settings.ollama_timeout_seconds,
    )

    # Initialize WebSocket manager
    ws_manager = WebSocketManager()

    # Initialize repositories
    analysis_repo = AnalysisRepository(session_factory)
    alert_repo = AlertRepository(session_factory)
    baseline_repo = BaselineRepository(session_factory)
    employee_repo = EmployeeRepository(session_factory)

    # Initialize analysis pipeline
    pipeline = AnalysisPipeline(
        llm=llm_client,
        analysis_repo=analysis_repo,
        alert_repo=alert_repo,
        baseline_repo=baseline_repo,
        ws_manager=ws_manager,
    )

    # Store in app state for dependency injection
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.llm_client = llm_client
    app.state.ws_manager = ws_manager
    app.state.pipeline = pipeline
    app.state.analysis_repo = analysis_repo
    app.state.alert_repo = alert_repo
    app.state.baseline_repo = baseline_repo
    app.state.employee_repo = employee_repo
    app.state.settings = settings

    logger.info("mindwall.ready", ollama_url=settings.ollama_base_url, model=settings.ollama_model)

    yield

    # Shutdown
    logger.info("mindwall.shutdown")
    await llm_client.close()
    await engine.dispose()
    logger.info("mindwall.shutdown.complete")
