"""
MindWall — Dashboard Router
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

GET /api/dashboard/* — Endpoints for organization-wide threat dashboard.
"""

from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, Request, Query

from ..schemas.dashboard import (
    DashboardSummary,
    HeatmapData,
    TimelineEntry,
    TimelineResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(request: Request) -> DashboardSummary:
    """Get organization-wide threat summary statistics."""
    analysis_repo = request.app.state.analysis_repo
    alert_repo = request.app.state.alert_repo
    employee_repo = request.app.state.employee_repo

    stats = await analysis_repo.get_summary_stats()
    unack_counts = await alert_repo.get_unacknowledged_count()
    employee_count = await employee_repo.get_count()
    avg_dim_scores = await analysis_repo.get_avg_dimension_scores()
    heatmap_raw = await analysis_repo.get_heatmap_data()

    return DashboardSummary(
        total_analyses=stats["total_analyses"],
        average_score=stats["average_score"],
        high_risk_count=stats["high_risk_count"],
        critical_count=stats["critical_count"],
        average_processing_ms=stats["average_processing_ms"],
        unacknowledged_alerts=unack_counts,
        employee_count=employee_count,
        avg_dimension_scores=avg_dim_scores,
        heatmap_data=HeatmapData(**heatmap_raw),
    )


@router.get("/timeline", response_model=TimelineResponse)
async def get_threat_timeline(
    request: Request,
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return"),
) -> TimelineResponse:
    """Get aggregated threat score timeline within a date range."""
    analysis_repo = request.app.state.analysis_repo

    buckets = await analysis_repo.get_timeline_aggregated(
        start_date=start_date,
        end_date=end_date,
    )

    entries = [
        TimelineEntry(
            bucket=b["bucket"],
            avg_score=b["avg_score"],
            count=b["count"],
        )
        for b in buckets
    ]

    return TimelineResponse(
        entries=entries,
        start_date=start_date,
        end_date=end_date,
    )
