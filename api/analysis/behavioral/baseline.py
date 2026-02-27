"""
MindWall — Per-Sender Behavioral Baseline Engine
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Maintains and queries per-sender communication baselines for behavioral
deviation detection. Updates baselines incrementally with each new email.
"""

import json
import re
from datetime import datetime
from typing import Optional, Dict, Any

import structlog

from ...db.repositories.baseline_repo import BaselineRepository

logger = structlog.get_logger(__name__)


class BaselineEngine:
    """
    Manages per-sender behavioral baselines.
    Tracks word count, sentence length, send timing, formality
    and updates incrementally using exponential moving averages.
    """

    FORMALITY_MARKERS = [
        r"\b(dear|sincerely|regards|respectfully|kindly|hereby|pursuant)\b",
        r"\b(please\s+find|attached\s+herewith|as\s+per|for\s+your\s+reference)\b",
        r"\b(best\s+regards|warm\s+regards|yours\s+(truly|faithfully|sincerely))\b",
    ]

    INFORMAL_MARKERS = [
        r"\b(hey|hi|yo|sup|gonna|wanna|gotta|lol|haha|btw|fyi|thx|ty)\b",
        r"\b(awesome|cool|sweet|dude|bro|mate|cheers)\b",
    ]

    # Exponential moving average smoothing factor
    EMA_ALPHA = 0.15

    def __init__(self, baseline_repo: BaselineRepository):
        self.repo = baseline_repo

    async def get_baseline(
        self,
        recipient_email: str,
        sender_email: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the sender's behavioral baseline for a given recipient.

        Returns:
            Baseline dict with avg_word_count, avg_sentence_length,
            typical_hours, formality_score, etc. or None if no baseline exists.
        """
        baseline_row = await self.repo.get_baseline(recipient_email, sender_email)
        if baseline_row is None:
            return None

        typical_hours = []
        if baseline_row.typical_hours:
            try:
                typical_hours = json.loads(baseline_row.typical_hours)
            except (json.JSONDecodeError, TypeError):
                typical_hours = []

        return {
            "avg_word_count": baseline_row.avg_word_count or 0.0,
            "avg_sentence_length": baseline_row.avg_sentence_length or 0.0,
            "typical_hours": typical_hours,
            "formality_score": baseline_row.formality_score or 0.5,
            "sample_count": baseline_row.sample_count or 0,
        }

    async def update_baseline(
        self,
        recipient_email: str,
        sender_email: str,
        body: str,
        received_at: Optional[datetime] = None,
    ) -> None:
        """
        Update the sender's behavioral baseline with data from a new email.
        Uses exponential moving average for smooth incremental updates.
        """
        # Compute metrics for this email
        word_count = len(body.split())
        sentences = re.split(r'[.!?]+', body)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_len = word_count / max(len(sentences), 1)
        formality = self._compute_formality(body)
        send_hour = received_at.hour if received_at else None

        existing = await self.repo.get_baseline(recipient_email, sender_email)

        if existing is None:
            # Create new baseline
            typical_hours = json.dumps([send_hour]) if send_hour is not None else "[]"
            await self.repo.upsert_baseline(
                recipient_email=recipient_email,
                sender_email=sender_email,
                avg_word_count=float(word_count),
                avg_sentence_length=round(avg_sentence_len, 2),
                typical_hours=typical_hours,
                formality_score=round(formality, 4),
                sample_count=1,
            )
            logger.info(
                "baseline.created",
                recipient=recipient_email,
                sender=sender_email,
            )
        else:
            # Update with EMA
            alpha = self.EMA_ALPHA
            new_avg_wc = (alpha * word_count) + ((1 - alpha) * (existing.avg_word_count or 0))
            new_avg_sl = (alpha * avg_sentence_len) + ((1 - alpha) * (existing.avg_sentence_length or 0))
            new_formality = (alpha * formality) + ((1 - alpha) * (existing.formality_score or 0.5))

            # Update typical hours
            try:
                hours_list = json.loads(existing.typical_hours or "[]")
            except (json.JSONDecodeError, TypeError):
                hours_list = []

            if send_hour is not None and send_hour not in hours_list:
                hours_list.append(send_hour)
                # Keep only the most common 8 hours
                if len(hours_list) > 8:
                    hours_list = hours_list[-8:]

            await self.repo.upsert_baseline(
                recipient_email=recipient_email,
                sender_email=sender_email,
                avg_word_count=round(new_avg_wc, 2),
                avg_sentence_length=round(new_avg_sl, 2),
                typical_hours=json.dumps(sorted(hours_list)),
                formality_score=round(new_formality, 4),
                sample_count=(existing.sample_count or 0) + 1,
            )
            logger.debug(
                "baseline.updated",
                recipient=recipient_email,
                sender=sender_email,
                sample_count=(existing.sample_count or 0) + 1,
            )

    def _compute_formality(self, text: str) -> float:
        """
        Compute a formality score (0.0 = very informal, 1.0 = very formal).
        Uses pattern matching on formal/informal linguistic markers.
        """
        text_lower = text.lower()
        formal_hits = sum(
            1 for pattern in self.FORMALITY_MARKERS
            if re.search(pattern, text_lower, re.IGNORECASE)
        )
        informal_hits = sum(
            1 for pattern in self.INFORMAL_MARKERS
            if re.search(pattern, text_lower, re.IGNORECASE)
        )

        total = formal_hits + informal_hits
        if total == 0:
            return 0.5  # Neutral

        return round(formal_hits / total, 4)
