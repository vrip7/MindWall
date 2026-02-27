"""
MindWall — WebSocket Event Types
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Event type definitions and serializers for WebSocket messages.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AlertEvent(BaseModel):
    """WebSocket event payload for a new alert."""
    event: str = "new_alert"
    alert_id: int
    analysis_id: int
    recipient_email: str
    sender_email: str
    subject: Optional[str] = None
    manipulation_score: float
    severity: str
    explanation: str
    recommended_action: str
    dimension_scores: Dict[str, float]
    timestamp: datetime = None

    def model_post_init(self, __context: Any) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class ConnectionEvent(BaseModel):
    """WebSocket event for connection status."""
    event: str = "connection"
    status: str  # "connected" | "disconnected"
    message: str = ""
