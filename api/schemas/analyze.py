"""
MindWall — Analysis Request/Response Schemas
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Pydantic models for the /api/analyze endpoint.
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request schema for email analysis."""
    message_uid: str = Field(..., description="IMAP UID or extension-generated ID")
    recipient_email: str = Field(..., description="Recipient's email address")
    sender_email: str = Field(..., description="Sender's email address")
    sender_display_name: str = Field(default="", description="Sender's display name")
    subject: str = Field(default="", description="Email subject line")
    body: str = Field(..., description="Plain-text email body content")
    channel: str = Field(..., description="Communication channel: 'imap' or 'gmail_web'")
    received_at: Optional[datetime] = Field(default=None, description="When the email was received (UTC)")


class AnalyzeResponse(BaseModel):
    """Response schema for email analysis results."""
    analysis_id: int = Field(..., description="Database ID of the analysis record")
    manipulation_score: float = Field(..., ge=0, le=100, description="Aggregate manipulation score (0-100)")
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    explanation: str = Field(..., description="Plain-English explanation of detected manipulation")
    recommended_action: str = Field(..., description="Recommended action: proceed, verify, or block")
    dimension_scores: Dict[str, float] = Field(..., description="12-dimension manipulation scores")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
