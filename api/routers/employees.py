"""
MindWall — Employees Router
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

GET/POST /api/employees/* — Employee management and risk profile endpoints.
"""

import json
from typing import Optional

import structlog
from fastapi import APIRouter, Request, HTTPException, Query

from ..schemas.employee import (
    EmployeeSummary,
    EmployeePaginatedResponse,
    EmployeeCreateRequest,
    EmployeeRiskProfile,
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

    result = await employee_repo.get_all(
        limit=limit,
        offset=offset,
        sort_by_risk=sort_by_risk,
    )

    items = [
        EmployeeSummary(
            id=emp.id,
            email=emp.email,
            display_name=emp.display_name,
            department=emp.department,
            risk_score=emp.risk_score,
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


@router.post("", response_model=EmployeeSummary, status_code=201)
async def create_employee(
    request: Request,
    payload: EmployeeCreateRequest,
) -> EmployeeSummary:
    """Create a new employee record."""
    employee_repo = request.app.state.employee_repo

    try:
        employee = await employee_repo.create_employee(
            email=payload.email,
            display_name=payload.display_name,
            department=payload.department,
        )
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"Employee already exists or error: {str(e)}")

    return EmployeeSummary(
        id=employee.id,
        email=employee.email,
        display_name=employee.display_name,
        department=employee.department,
        risk_score=employee.risk_score,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
    )


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

    # Serialize recent analyses
    recent_analyses_data = []
    for analysis in profile.get("recent_analyses", []):
        dim_scores = {}
        if analysis.dimension_scores:
            try:
                dim_scores = json.loads(analysis.dimension_scores)
            except json.JSONDecodeError:
                dim_scores = {}

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

    top_senders = [
        ThreatSenderInfo(**s) for s in profile.get("top_threat_senders", [])
    ]

    return EmployeeRiskProfile(
        email=employee.email,
        display_name=employee.display_name,
        department=employee.department,
        rolling_risk_score=profile["rolling_risk_score"],
        total_analyses=profile["total_analyses"],
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
