"""
MindWall — Email Accounts Router
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

CRUD for email account configurations used by the IMAP/SMTP proxy.
"""

from datetime import datetime
from typing import List, Optional

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

logger = structlog.get_logger(__name__)

router = APIRouter()


class EmailAccountCreate(BaseModel):
    """Request to create/update an email account configuration."""
    email: str = Field(..., description="Email address")
    display_name: Optional[str] = None
    imap_host: str = Field(..., description="IMAP server hostname (e.g. imap.gmail.com)")
    imap_port: int = Field(993, ge=1, le=65535)
    smtp_host: str = Field(..., description="SMTP server hostname (e.g. smtp.gmail.com)")
    smtp_port: int = Field(587, ge=1, le=65535)
    username: str = Field(..., description="Login username (usually the email)")
    password: str = Field(..., description="App password or account password")
    use_tls: bool = True
    enabled: bool = True


class EmailAccountResponse(BaseModel):
    """Email account without the password exposed."""
    id: int
    email: str
    display_name: Optional[str] = None
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    username: str
    use_tls: bool
    enabled: bool
    created_at: str
    updated_at: str


@router.get("", response_model=List[EmailAccountResponse])
async def list_email_accounts(request: Request):
    """List all configured email accounts (passwords redacted)."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        result = await session.execute(
            text("SELECT id, email, display_name, imap_host, imap_port, "
                 "smtp_host, smtp_port, username, use_tls, enabled, "
                 "created_at, updated_at FROM email_accounts ORDER BY id")
        )
        rows = result.fetchall()

    return [
        EmailAccountResponse(
            id=r[0], email=r[1], display_name=r[2],
            imap_host=r[3], imap_port=r[4],
            smtp_host=r[5], smtp_port=r[6],
            username=r[7], use_tls=bool(r[8]), enabled=bool(r[9]),
            created_at=str(r[10]), updated_at=str(r[11]),
        )
        for r in rows
    ]


@router.post("", response_model=EmailAccountResponse, status_code=201)
async def create_email_account(request: Request, payload: EmailAccountCreate):
    """Create or update an email account configuration."""
    session_factory = request.app.state.session_factory
    now = datetime.utcnow().isoformat()

    async with session_factory() as session:
        # Upsert — replace if email already exists
        existing = await session.execute(
            text("SELECT id FROM email_accounts WHERE email = :email"),
            {"email": payload.email},
        )
        row = existing.fetchone()

        if row:
            await session.execute(
                text("""
                    UPDATE email_accounts
                    SET display_name = :display_name, imap_host = :imap_host,
                        imap_port = :imap_port, smtp_host = :smtp_host,
                        smtp_port = :smtp_port, username = :username,
                        password = :password, use_tls = :use_tls,
                        enabled = :enabled, updated_at = :updated_at
                    WHERE email = :email
                """),
                {**payload.model_dump(), "updated_at": now},
            )
            account_id = row[0]
        else:
            result = await session.execute(
                text("""
                    INSERT INTO email_accounts
                        (email, display_name, imap_host, imap_port,
                         smtp_host, smtp_port, username, password,
                         use_tls, enabled, created_at, updated_at)
                    VALUES
                        (:email, :display_name, :imap_host, :imap_port,
                         :smtp_host, :smtp_port, :username, :password,
                         :use_tls, :enabled, :created_at, :updated_at)
                """),
                {**payload.model_dump(), "created_at": now, "updated_at": now},
            )
            account_id = result.lastrowid

        await session.commit()

        # Fetch the created/updated record
        result = await session.execute(
            text("SELECT id, email, display_name, imap_host, imap_port, "
                 "smtp_host, smtp_port, username, use_tls, enabled, "
                 "created_at, updated_at FROM email_accounts WHERE id = :id"),
            {"id": account_id},
        )
        r = result.fetchone()

    logger.info("email_accounts.saved", email=payload.email)
    return EmailAccountResponse(
        id=r[0], email=r[1], display_name=r[2],
        imap_host=r[3], imap_port=r[4],
        smtp_host=r[5], smtp_port=r[6],
        username=r[7], use_tls=bool(r[8]), enabled=bool(r[9]),
        created_at=str(r[10]), updated_at=str(r[11]),
    )


@router.get("/lookup/{username}")
async def lookup_email_account(request: Request, username: str):
    """Internal: Resolve upstream server config by login username.

    Used by the IMAP/SMTP proxy to auto-resolve upstream host/port when
    the email client authenticates against the proxy.
    """
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT email, imap_host, imap_port, smtp_host, smtp_port, "
                "username, password, use_tls, enabled "
                "FROM email_accounts WHERE username = :username AND enabled = 1"
            ),
            {"username": username},
        )
        row = result.fetchone()

    if not row:
        return JSONResponse(status_code=404, content={"detail": "Account not found"})

    return {
        "email": row[0],
        "imap_host": row[1],
        "imap_port": row[2],
        "smtp_host": row[3],
        "smtp_port": row[4],
        "username": row[5],
        "password": row[6],
        "use_tls": bool(row[7]),
        "enabled": bool(row[8]),
    }


@router.delete("/{account_id}")
async def delete_email_account(request: Request, account_id: int):
    """Delete an email account configuration."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        result = await session.execute(
            text("DELETE FROM email_accounts WHERE id = :id"),
            {"id": account_id},
        )
        await session.commit()

        if result.rowcount == 0:
            return JSONResponse(status_code=404, content={"detail": "Account not found"})

    logger.info("email_accounts.deleted", account_id=account_id)
    return {"status": "deleted", "id": account_id}
