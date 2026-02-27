"""
MindWall — Dashboard Router
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

GET /api/dashboard/* — Endpoints for organization-wide threat dashboard.
"""

from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, Request, Query

from ..schemas.dashboard import DashboardSummary, TimelineEntry, TimelineResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(request: Request) -> DashboardSummary:
    """Get organization-wide threat summary statistics."""
    analysis_repo = request.app.state.analysis_repo
    alert_repo = request.app.state.alert_repo

    stats = await analysis_repo.get_summary_stats()
    unack_counts = await alert_repo.get_unacknowledged_count()

    return DashboardSummary(
        total_analyses=stats["total_analyses"],
        average_score=stats["average_score"],
        high_risk_count=stats["high_risk_count"],
        critical_count=stats["critical_count"],
        average_processing_ms=stats["average_processing_ms"],
        unacknowledged_alerts=unack_counts,
    )


@router.get("/timeline", response_model=TimelineResponse)
async def get_threat_timeline(
    request: Request,
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return"),
) -> TimelineResponse:
    """Get threat score timeline within a date range."""
    analysis_repo = request.app.state.analysis_repo

    analyses = await analysis_repo.get_timeline(
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    entries = []
    for analysis in analyses:
        severity = "low"
        if analysis.manipulation_score:
            score = analysis.manipulation_score
            if score >= 80:
                severity = "critical"
            elif score >= 60:
                severity = "high"
            elif score >= 35:
                severity = "medium"

        entries.append(TimelineEntry(
            analysis_id=analysis.id,
            analyzed_at=analysis.analyzed_at,
            manipulation_score=analysis.manipulation_score or 0.0,
            severity=severity,
            sender_email=analysis.sender_email,
            recipient_email=analysis.recipient_email,
            subject=analysis.subject,
            channel=analysis.channel,
        ))

    return TimelineResponse(
        entries=entries,
        start_date=start_date,
        end_date=end_date,
    )
