"""
MindWall — Dashboard Schemas
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Pydantic models for dashboard endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class HeatmapData(BaseModel):
    """Risk heatmap grid data."""
    data: List[List[Optional[float]]]
    row_labels: List[str]
    col_labels: List[str]


class DashboardSummary(BaseModel):
    """Organization-wide threat summary statistics."""
    total_analyses: int
    average_score: float
    high_risk_count: int
    critical_count: int
    average_processing_ms: float
    unacknowledged_alerts: Dict[str, int]
    employee_count: int
    avg_dimension_scores: Dict[str, float]
    heatmap_data: HeatmapData


class TimelineEntry(BaseModel):
    """Aggregated time-bucket entry for the threat timeline."""
    bucket: datetime
    avg_score: float
    count: int


class TimelineResponse(BaseModel):
    """Threat score timeline response."""
    entries: List[TimelineEntry]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
