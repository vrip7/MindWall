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
    total_emails: int = 0
    flagged_emails: int = 0
    email_account_configured: bool = False
    created_at: datetime
    updated_at: datetime


class EmployeeCreateRequest(BaseModel):
    """Request to create a new employee with optional email account configuration."""
    email: str = Field(..., description="Employee email address")
    display_name: Optional[str] = Field(None, description="Employee display name")
    department: Optional[str] = Field(None, description="Department name")
    # Email account configuration (created when imap_host is provided)
    imap_host: Optional[str] = Field(None, description="IMAP server hostname (e.g. imap.gmail.com)")
    imap_port: int = Field(993, ge=1, le=65535)
    smtp_host: Optional[str] = Field(None, description="SMTP server hostname (e.g. smtp.gmail.com)")
    smtp_port: int = Field(587, ge=1, le=65535)
    username: Optional[str] = Field(None, description="Email login username")
    password: Optional[str] = Field(None, description="Email password or app password")
    use_tls: bool = Field(True, description="Use TLS for connections")


class ProxyConnectionInfo(BaseModel):
    """Proxy connection settings to configure in the email client."""
    imap_proxy_host: str
    imap_proxy_port: int
    smtp_proxy_host: str
    smtp_proxy_port: int
    username: str


class EmployeeCreateResponse(BaseModel):
    """Response after creating an employee."""
    employee: EmployeeSummary
    email_account_configured: bool = False
    proxy_connection: Optional[ProxyConnectionInfo] = None


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
    total_emails: int = 0
    flagged_emails: int = 0
    total_analyses: int
    avg_dimension_scores: Dict[str, float] = {}
    top_threat_senders: List[ThreatSenderInfo]
    recent_analyses: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]] = []
