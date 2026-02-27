"""
MindWall — Dashboard Schemas
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Pydantic models for dashboard endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """Organization-wide threat summary statistics."""
    total_analyses: int
    average_score: float
    high_risk_count: int
    critical_count: int
    average_processing_ms: float
    unacknowledged_alerts: Dict[str, int]


class TimelineEntry(BaseModel):
    """Single entry in the threat timeline."""
    analysis_id: int
    analyzed_at: datetime
    manipulation_score: float
    severity: str
    sender_email: str
    recipient_email: str
    subject: Optional[str] = None
    channel: str


class TimelineResponse(BaseModel):
    """Threat score timeline response."""
    entries: List[TimelineEntry]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
