"""
MindWall — Authentication Router
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

POST /auth/login — Validate dashboard credentials and return the API key.
"""

import hmac

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    """Dashboard login credentials."""
    username: str
    password: str


@router.post("/login")
async def login(request: Request, payload: LoginRequest):
    """
    Validate dashboard credentials.
    Returns the API secret key on success so the frontend can
    attach it as X-MindWall-Key for subsequent requests.
    """
    settings = request.app.state.settings

    username_ok = hmac.compare_digest(payload.username, settings.dashboard_username)
    password_ok = hmac.compare_digest(payload.password, settings.dashboard_password)

    if not username_ok or not password_ok:
        logger.warning("auth.login_failed", username=payload.username)
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid username or password"},
        )

    logger.info("auth.login_success", username=payload.username)
    return {"api_key": settings.api_secret_key}
