"""
MindWall — Alert Schemas
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Pydantic models for alert-related endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AlertSummary(BaseModel):
    """Summary view of an alert for list endpoints."""
    id: int
    analysis_id: int
    severity: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    # Joined from analysis
    recipient_email: Optional[str] = None
    sender_email: Optional[str] = None
    subject: Optional[str] = None
    manipulation_score: Optional[float] = None
    explanation: Optional[str] = None
    recommended_action: Optional[str] = None


class AlertDetail(BaseModel):
    """Full alert detail with dimension breakdown."""
    id: int
    analysis_id: int
    severity: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    # Full analysis data
    recipient_email: str
    sender_email: str
    sender_display_name: Optional[str] = None
    subject: Optional[str] = None
    manipulation_score: float
    dimension_scores: Dict[str, float]
    explanation: str
    recommended_action: str
    channel: str
    received_at: Optional[datetime] = None
    analyzed_at: datetime
    prefilter_triggered: bool
    prefilter_signals: List[str]
    processing_time_ms: int


class AlertAcknowledgeRequest(BaseModel):
    """Request to acknowledge an alert."""
    acknowledged_by: str = Field(..., description="Name or email of the person acknowledging")


class AlertPaginatedResponse(BaseModel):
    """Paginated list of alerts."""
    items: List[AlertSummary]
    total: int
    limit: int
    offset: int


class AlertCountsResponse(BaseModel):
    """Unacknowledged alert counts by severity."""
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0
    total: int = 0
