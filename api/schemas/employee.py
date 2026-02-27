"""
MindWall — Employee Schemas
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Pydantic models for employee-related endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EmployeeSummary(BaseModel):
    """Summary view of an employee."""
    id: int
    email: str
    display_name: Optional[str] = None
    department: Optional[str] = None
    risk_score: float
    created_at: datetime
    updated_at: datetime


class EmployeeCreateRequest(BaseModel):
    """Request to create a new employee."""
    email: str = Field(..., description="Employee email address")
    display_name: Optional[str] = Field(None, description="Employee display name")
    department: Optional[str] = Field(None, description="Department name")


class EmployeePaginatedResponse(BaseModel):
    """Paginated list of employees."""
    items: List[EmployeeSummary]
    total: int
    limit: int
    offset: int


class ThreatSenderInfo(BaseModel):
    """Information about a threatening sender."""
    sender_email: str
    avg_score: float
    count: int


class EmployeeRiskProfile(BaseModel):
    """Full risk profile for an employee."""
    email: str
    display_name: Optional[str] = None
    department: Optional[str] = None
    rolling_risk_score: float
    total_analyses: int
    top_threat_senders: List[ThreatSenderInfo]
    recent_analyses: List[Dict[str, Any]]
