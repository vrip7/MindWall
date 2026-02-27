"""
MindWall — Settings Router
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

GET/PUT /api/settings — System configuration management.
"""

from typing import Optional

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter()


class SystemSettings(BaseModel):
    """Current system settings."""
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: int
    alert_medium_threshold: float
    alert_high_threshold: float
    alert_critical_threshold: float
    log_level: str
    workers: int


class SettingsUpdateRequest(BaseModel):
    """Request to update system settings (partial update)."""
    ollama_timeout_seconds: Optional[int] = Field(None, ge=5, le=120)
    alert_medium_threshold: Optional[float] = Field(None, ge=0, le=100)
    alert_high_threshold: Optional[float] = Field(None, ge=0, le=100)
    alert_critical_threshold: Optional[float] = Field(None, ge=0, le=100)
    log_level: Optional[str] = Field(None, pattern="^(DEBUG|INFO|WARNING|ERROR)$")


@router.get("", response_model=SystemSettings)
async def get_settings(request: Request) -> SystemSettings:
    """Get current system settings."""
    settings = request.app.state.settings

    return SystemSettings(
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        ollama_timeout_seconds=settings.ollama_timeout_seconds,
        alert_medium_threshold=settings.alert_medium_threshold,
        alert_high_threshold=settings.alert_high_threshold,
        alert_critical_threshold=settings.alert_critical_threshold,
        log_level=settings.log_level,
        workers=settings.workers,
    )


@router.put("", response_model=SystemSettings)
async def update_settings(
    request: Request,
    payload: SettingsUpdateRequest,
) -> SystemSettings:
    """
    Update system settings.
    Note: Some settings require service restart to take effect.
    Runtime-modifiable settings are applied immediately.
    """
    settings = request.app.state.settings

    if payload.ollama_timeout_seconds is not None:
        settings.ollama_timeout_seconds = payload.ollama_timeout_seconds
        # Update LLM client timeout
        request.app.state.llm_client.timeout = payload.ollama_timeout_seconds

    if payload.alert_medium_threshold is not None:
        settings.alert_medium_threshold = payload.alert_medium_threshold
    if payload.alert_high_threshold is not None:
        settings.alert_high_threshold = payload.alert_high_threshold
    if payload.alert_critical_threshold is not None:
        settings.alert_critical_threshold = payload.alert_critical_threshold
    if payload.log_level is not None:
        settings.log_level = payload.log_level

    logger.info("settings.updated", changes=payload.model_dump(exclude_none=True))

    return SystemSettings(
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        ollama_timeout_seconds=settings.ollama_timeout_seconds,
        alert_medium_threshold=settings.alert_medium_threshold,
        alert_high_threshold=settings.alert_high_threshold,
        alert_critical_threshold=settings.alert_critical_threshold,
        log_level=settings.log_level,
        workers=settings.workers,
    )
