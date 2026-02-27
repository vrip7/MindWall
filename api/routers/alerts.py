"""
MindWall — Alerts Router
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

GET/PATCH /api/alerts/* — Alert management endpoints.
"""

import json
from typing import Optional

import structlog
from fastapi import APIRouter, Request, HTTPException, Query

from ..schemas.alert import (
    AlertSummary,
    AlertDetail,
    AlertAcknowledgeRequest,
    AlertPaginatedResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("", response_model=AlertPaginatedResponse)
async def get_alerts(
    request: Request,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> AlertPaginatedResponse:
    """Get paginated list of alerts with optional filters."""
    alert_repo = request.app.state.alert_repo

    result = await alert_repo.get_paginated(
        severity=severity,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset,
    )

    items = []
    for alert in result["items"]:
        analysis = alert.analysis
        items.append(AlertSummary(
            id=alert.id,
            analysis_id=alert.analysis_id,
            severity=alert.severity,
            acknowledged=alert.acknowledged,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at,
            created_at=alert.created_at,
            recipient_email=analysis.recipient_email if analysis else None,
            sender_email=analysis.sender_email if analysis else None,
            subject=analysis.subject if analysis else None,
            manipulation_score=analysis.manipulation_score if analysis else None,
            explanation=analysis.explanation if analysis else None,
            recommended_action=analysis.recommended_action if analysis else None,
        ))

    return AlertPaginatedResponse(
        items=items,
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.get("/{alert_id}", response_model=AlertDetail)
async def get_alert_detail(request: Request, alert_id: int) -> AlertDetail:
    """Get full alert detail with dimension breakdown."""
    alert_repo = request.app.state.alert_repo

    alert = await alert_repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    analysis = alert.analysis
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found for alert")

    # Parse JSON fields
    dimension_scores = {}
    if analysis.dimension_scores:
        try:
            dimension_scores = json.loads(analysis.dimension_scores)
        except json.JSONDecodeError:
            dimension_scores = {}

    prefilter_signals = []
    if analysis.prefilter_signals:
        try:
            prefilter_signals = json.loads(analysis.prefilter_signals)
        except json.JSONDecodeError:
            prefilter_signals = []

    return AlertDetail(
        id=alert.id,
        analysis_id=alert.analysis_id,
        severity=alert.severity,
        acknowledged=alert.acknowledged,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
        recipient_email=analysis.recipient_email,
        sender_email=analysis.sender_email,
        sender_display_name=analysis.sender_display_name,
        subject=analysis.subject,
        manipulation_score=analysis.manipulation_score,
        dimension_scores=dimension_scores,
        explanation=analysis.explanation or "",
        recommended_action=analysis.recommended_action or "proceed",
        channel=analysis.channel,
        received_at=analysis.received_at,
        analyzed_at=analysis.analyzed_at,
        prefilter_triggered=analysis.prefilter_triggered,
        prefilter_signals=prefilter_signals,
        processing_time_ms=analysis.processing_time_ms or 0,
    )


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(
    request: Request,
    alert_id: int,
    payload: AlertAcknowledgeRequest,
):
    """Mark an alert as acknowledged."""
    alert_repo = request.app.state.alert_repo

    alert = await alert_repo.acknowledge(
        alert_id=alert_id,
        acknowledged_by=payload.acknowledged_by,
    )

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    logger.info(
        "alert.acknowledged",
        alert_id=alert_id,
        acknowledged_by=payload.acknowledged_by,
    )

    return {"status": "acknowledged", "alert_id": alert_id}
