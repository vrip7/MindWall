"""
MindWall — Cross-Channel Coordination Detector
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Detects evidence of coordinated multi-channel social engineering attacks
by analyzing temporal patterns across different communication channels.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import structlog

from ...db.repositories.analysis_repo import AnalysisRepository

logger = structlog.get_logger(__name__)


class CrossChannelDetector:
    """
    Detects coordinated multi-channel attacks by identifying patterns
    where the same sender contacts the same recipient through multiple
    channels in a short time window with escalating manipulation tactics.
    """

    # Time window to consider as coordinated (in hours)
    COORDINATION_WINDOW_HOURS = 24

    # Minimum number of channels for coordination signal
    MIN_CHANNELS_FOR_SIGNAL = 2

    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo

    async def detect(
        self,
        recipient_email: str,
        sender_email: str,
        current_channel: str,
        received_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Check for cross-channel coordination signals.

        Args:
            recipient_email: The recipient's email address.
            sender_email: The sender's email address.
            current_channel: Current channel ('imap' or 'gmail_web').
            received_at: When the current message was received.

        Returns:
            Dict with coordination_detected (bool), score (0-100),
            channels_used (list), and recent_analysis_count (int).
        """
        if received_at is None:
            received_at = datetime.utcnow()

        window_start = received_at - timedelta(hours=self.COORDINATION_WINDOW_HOURS)

        # Query recent analyses from this sender to this recipient
        recent_analyses = await self.analysis_repo.get_recent_by_sender_recipient(
            recipient_email=recipient_email,
            sender_email=sender_email,
            since=window_start,
        )

        if not recent_analyses:
            return {
                "coordination_detected": False,
                "score": 0.0,
                "channels_used": [current_channel],
                "recent_analysis_count": 0,
            }

        # Collect unique channels
        channels = set()
        channels.add(current_channel)
        for analysis in recent_analyses:
            if analysis.channel:
                channels.add(analysis.channel)

        coordination_detected = len(channels) >= self.MIN_CHANNELS_FOR_SIGNAL
        analysis_count = len(recent_analyses)

        # Score based on number of channels and frequency
        score = 0.0
        if coordination_detected:
            # Multi-channel bonus
            score += (len(channels) - 1) * 25.0
            # Frequency bonus (more messages in the window = more suspicious)
            score += min(analysis_count * 10.0, 30.0)
            # Check for escalation pattern
            scores = [a.manipulation_score for a in recent_analyses if a.manipulation_score is not None]
            if len(scores) >= 2 and scores[-1] > scores[0]:
                score += 20.0  # Escalation detected

        score = min(100.0, max(0.0, score))

        result = {
            "coordination_detected": coordination_detected,
            "score": round(score, 2),
            "channels_used": sorted(channels),
            "recent_analysis_count": analysis_count,
        }

        if coordination_detected:
            logger.warning(
                "cross_channel.detected",
                recipient=recipient_email,
                sender=sender_email,
                channels=sorted(channels),
                score=round(score, 2),
            )

        return result
