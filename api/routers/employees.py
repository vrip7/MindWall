"""
MindWall — Employees Router
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

GET/POST /api/employees/* — Employee management, email account config, and risk profile endpoints.
"""

import json
from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, Request, HTTPException, Query
from sqlalchemy import select, text

from ..core.config import get_settings
from ..db.models import Employee
from ..schemas.employee import (
    EmployeeSummary,
    EmployeePaginatedResponse,
    EmployeeCreateRequest,
    EmployeeCreateResponse,
    EmployeeRiskProfile,
    ProxyConnectionInfo,
    ThreatSenderInfo,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("", response_model=EmployeePaginatedResponse)
async def get_employees(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by_risk: bool = Query(True, description="Sort by risk score descending"),
) -> EmployeePaginatedResponse:
    """Get paginated employee list with rolling risk scores."""
    employee_repo = request.app.state.employee_repo
    analysis_repo = request.app.state.analysis_repo

    result = await employee_repo.get_all(
        limit=limit,
        offset=offset,
        sort_by_risk=sort_by_risk,
    )

    # Batch-load per-employee counts
    emails = [emp.email for emp in result["items"]]
    email_counts = await analysis_repo.get_email_counts_by_recipients(emails)

    # Check which employees have email accounts configured
    configured_emails: set[str] = set()
    if emails:
        session_factory = request.app.state.session_factory
        async with session_factory() as session:
            placeholders = ", ".join(f":e{i}" for i in range(len(emails)))
            params = {f"e{i}": email for i, email in enumerate(emails)}
            acct_result = await session.execute(
                text(f"SELECT email FROM email_accounts WHERE email IN ({placeholders})"),
                params,
            )
            configured_emails = {row[0] for row in acct_result.fetchall()}

    items = [
        EmployeeSummary(
            id=emp.id,
            email=emp.email,
            display_name=emp.display_name,
            department=emp.department,
            risk_score=emp.risk_score,
            total_emails=email_counts.get(emp.email, {}).get("total", 0),
            flagged_emails=email_counts.get(emp.email, {}).get("flagged", 0),
            email_account_configured=emp.email in configured_emails,
            created_at=emp.created_at,
            updated_at=emp.updated_at,
        )
        for emp in result["items"]
    ]

    return EmployeePaginatedResponse(
        items=items,
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.post("", response_model=EmployeeCreateResponse, status_code=201)
async def create_employee(
    request: Request,
    payload: EmployeeCreateRequest,
) -> EmployeeCreateResponse:
    """Create a new employee and optionally configure their email account."""
    employee_repo = request.app.state.employee_repo
    config = get_settings()

    try:
        employee = await employee_repo.create_employee(
            email=payload.email,
            display_name=payload.display_name,
            department=payload.department,
        )
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"Employee already exists or error: {str(e)}")

    # Create email account if IMAP/SMTP configuration was provided
    email_configured = False
    proxy_connection = None

    if payload.imap_host and payload.smtp_host and payload.username and payload.password:
        session_factory = request.app.state.session_factory
        now = datetime.utcnow().isoformat()

        async with session_factory() as session:
            existing = await session.execute(
                text("SELECT id FROM email_accounts WHERE email = :email"),
                {"email": payload.email},
            )
            row = existing.fetchone()

            acct_params = {
                "email": payload.email,
                "display_name": payload.display_name,
                "imap_host": payload.imap_host,
                "imap_port": payload.imap_port,
                "smtp_host": payload.smtp_host,
                "smtp_port": payload.smtp_port,
                "username": payload.username,
                "password": payload.password,
                "use_tls": payload.use_tls,
                "updated_at": now,
            }

            if row:
                await session.execute(
                    text("""
                        UPDATE email_accounts
                        SET display_name = :display_name, imap_host = :imap_host,
                            imap_port = :imap_port, smtp_host = :smtp_host,
                            smtp_port = :smtp_port, username = :username,
                            password = :password, use_tls = :use_tls,
                            enabled = 1, updated_at = :updated_at
                        WHERE email = :email
                    """),
                    acct_params,
                )
            else:
                acct_params["created_at"] = now
                await session.execute(
                    text("""
                        INSERT INTO email_accounts
                            (email, display_name, imap_host, imap_port,
                             smtp_host, smtp_port, username, password,
                             use_tls, enabled, created_at, updated_at)
                        VALUES
                            (:email, :display_name, :imap_host, :imap_port,
                             :smtp_host, :smtp_port, :username, :password,
                             :use_tls, 1, :created_at, :updated_at)
                    """),
                    acct_params,
                )

            await session.commit()

        email_configured = True
        proxy_connection = ProxyConnectionInfo(
            imap_proxy_host="localhost",
            imap_proxy_port=config.proxy_imap_port,
            smtp_proxy_host="localhost",
            smtp_proxy_port=config.proxy_smtp_port,
            username=payload.username,
        )
        logger.info("employee.email_account_created", email=payload.email)

    return EmployeeCreateResponse(
        employee=EmployeeSummary(
            id=employee.id,
            email=employee.email,
            display_name=employee.display_name,
            department=employee.department,
            risk_score=employee.risk_score,
            email_account_configured=email_configured,
            created_at=employee.created_at,
            updated_at=employee.updated_at,
        ),
        email_account_configured=email_configured,
        proxy_connection=proxy_connection,
    )


@router.delete("/{employee_id}", status_code=204)
async def delete_employee(
    request: Request,
    employee_id: int,
):
    """Delete an employee and their associated email account."""
    employee_repo = request.app.state.employee_repo
    session_factory = request.app.state.session_factory

    # Fetch employee email before deletion for cleanup
    async with session_factory() as session:
        result = await session.execute(
            select(Employee.email).where(Employee.id == employee_id)
        )
        row = result.fetchone()
        employee_email = row[0] if row else None

    deleted = await employee_repo.delete_employee(employee_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Also remove the associated email account
    if employee_email:
        async with session_factory() as session:
            await session.execute(
                text("DELETE FROM email_accounts WHERE email = :email"),
                {"email": employee_email},
            )
            await session.commit()
        logger.info("employee.email_account_cleaned", email=employee_email)

    return None


@router.get("/{email}/proxy-info")
async def get_employee_proxy_info(
    request: Request,
    email: str,
):
    """Get proxy connection info for an employee's configured email account."""
    session_factory = request.app.state.session_factory
    config = get_settings()

    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT username, imap_host, imap_port, smtp_host, smtp_port, use_tls, enabled "
                "FROM email_accounts WHERE email = :email"
            ),
            {"email": email},
        )
        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No email account configured for this employee")

    return {
        "imap_proxy_host": "localhost",
        "imap_proxy_port": config.proxy_imap_port,
        "smtp_proxy_host": "localhost",
        "smtp_proxy_port": config.proxy_smtp_port,
        "username": row[0],
        "original_imap": f"{row[1]}:{row[2]}",
        "original_smtp": f"{row[3]}:{row[4]}",
        "use_tls": bool(row[5]),
        "enabled": bool(row[6]),
    }


@router.get("/{email}/risk-profile", response_model=EmployeeRiskProfile)
async def get_employee_risk_profile(
    request: Request,
    email: str,
) -> EmployeeRiskProfile:
    """Get full risk profile including sender baselines for an employee."""
    employee_repo = request.app.state.employee_repo

    profile = await employee_repo.get_risk_profile(email)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee = profile["employee"]

    # Serialize recent analyses and compute avg dimension scores
    recent_analyses_data = []
    dim_totals = {}
    dim_counts = {}
    flagged_count = 0
    for analysis in profile.get("recent_analyses", []):
        dim_scores = {}
        if analysis.dimension_scores:
            try:
                dim_scores = json.loads(analysis.dimension_scores)
            except json.JSONDecodeError:
                dim_scores = {}

        for k, v in dim_scores.items():
            if isinstance(v, (int, float)):
                dim_totals[k] = dim_totals.get(k, 0.0) + float(v)
                dim_counts[k] = dim_counts.get(k, 0) + 1

        if analysis.manipulation_score and analysis.manipulation_score >= 35:
            flagged_count += 1

        recent_analyses_data.append({
            "id": analysis.id,
            "sender_email": analysis.sender_email,
            "subject": analysis.subject,
            "manipulation_score": analysis.manipulation_score,
            "severity": _severity(analysis.manipulation_score),
            "channel": analysis.channel,
            "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
            "explanation": analysis.explanation,
            "recommended_action": analysis.recommended_action,
            "dimension_scores": dim_scores,
        })

    avg_dim_scores = {
        k: round(dim_totals[k] / dim_counts[k], 2)
        for k in dim_totals if dim_counts.get(k, 0) > 0
    }

    top_senders = [
        ThreatSenderInfo(**s) for s in profile.get("top_threat_senders", [])
    ]

    return EmployeeRiskProfile(
        email=employee.email,
        display_name=employee.display_name,
        department=employee.department,
        rolling_risk_score=profile["rolling_risk_score"],
        total_emails=profile["total_analyses"],
        flagged_emails=flagged_count,
        total_analyses=profile["total_analyses"],
        avg_dimension_scores=avg_dim_scores,
        top_threat_senders=top_senders,
        recent_analyses=recent_analyses_data,
    )


def _severity(score: Optional[float]) -> str:
    """Determine severity from score."""
    if score is None:
        return "low"
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"
