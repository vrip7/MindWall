"""
MindWall — Behavioral Deviation Scorer
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Computes deviation scores by comparing current email characteristics
against the sender's established behavioral baseline.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DeviationContext:
    """Result of deviation scoring against sender baseline."""
    deviation_score: float = 0.0
    word_count_deviation: float = 0.0
    sentence_length_deviation: float = 0.0
    timing_deviation: float = 0.0
    formality_deviation: float = 0.0
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class DeviationScorer:
    """
    Scores how much the current email deviates from the sender's
    established behavioral baseline across multiple dimensions.
    """

    # Deviation thresholds (percentage deviation from baseline)
    WORD_COUNT_WEIGHT = 0.30
    SENTENCE_LENGTH_WEIGHT = 0.15
    TIMING_WEIGHT = 0.25
    FORMALITY_WEIGHT = 0.30

    def score(
        self,
        body: str,
        received_at: Optional[datetime],
        baseline: Optional[Dict[str, Any]],
    ) -> DeviationContext:
        """
        Compute deviation score (0-100) comparing email to sender baseline.

        Args:
            body: Plain-text email body.
            received_at: When the email was received.
            baseline: Sender baseline dict from BaselineEngine, or None.

        Returns:
            DeviationContext with scores and details.
        """
        if baseline is None or baseline.get("sample_count", 0) < 3:
            # Not enough data for meaningful deviation scoring
            return DeviationContext(deviation_score=0.0)

        word_count = len(body.split())
        sentences = re.split(r'[.!?]+', body)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_len = word_count / max(len(sentences), 1)

        # Word count deviation
        baseline_wc = baseline.get("avg_word_count", 0)
        if baseline_wc > 0:
            wc_deviation_pct = abs(word_count - baseline_wc) / baseline_wc
            wc_score = min(100.0, wc_deviation_pct * 100)
        else:
            wc_score = 0.0

        # Sentence length deviation
        baseline_sl = baseline.get("avg_sentence_length", 0)
        if baseline_sl > 0:
            sl_deviation_pct = abs(avg_sentence_len - baseline_sl) / baseline_sl
            sl_score = min(100.0, sl_deviation_pct * 100)
        else:
            sl_score = 0.0

        # Timing deviation
        timing_score = 0.0
        if received_at is not None:
            typical_hours = baseline.get("typical_hours", [])
            if typical_hours and isinstance(typical_hours, list):
                send_hour = received_at.hour
                if send_hour not in typical_hours:
                    # Compute minimum distance to any typical hour
                    min_distance = min(
                        min(abs(send_hour - h), 24 - abs(send_hour - h))
                        for h in typical_hours
                    )
                    # Scale: 6+ hours away = max deviation
                    timing_score = min(100.0, (min_distance / 6.0) * 100)

        # Formality deviation
        formality_score = 0.0
        baseline_formality = baseline.get("formality_score", 0.5)
        current_formality = self._quick_formality(body)
        formality_diff = abs(current_formality - baseline_formality)
        formality_score = min(100.0, formality_diff * 200)  # 0.5 diff = 100

        # Weighted aggregate
        aggregate = (
            wc_score * self.WORD_COUNT_WEIGHT +
            sl_score * self.SENTENCE_LENGTH_WEIGHT +
            timing_score * self.TIMING_WEIGHT +
            formality_score * self.FORMALITY_WEIGHT
        )

        aggregate = round(min(100.0, max(0.0, aggregate)), 2)

        context = DeviationContext(
            deviation_score=aggregate,
            word_count_deviation=round(wc_score, 2),
            sentence_length_deviation=round(sl_score, 2),
            timing_deviation=round(timing_score, 2),
            formality_deviation=round(formality_score, 2),
            details={
                "current_word_count": word_count,
                "baseline_word_count": baseline_wc,
                "current_avg_sentence_length": round(avg_sentence_len, 2),
                "baseline_avg_sentence_length": baseline_sl,
                "send_hour": received_at.hour if received_at else None,
                "typical_hours": baseline.get("typical_hours", []),
            },
        )

        logger.debug(
            "deviation.scored",
            aggregate=aggregate,
            word_count_dev=round(wc_score, 2),
            timing_dev=round(timing_score, 2),
            formality_dev=round(formality_score, 2),
        )

        return context

    @staticmethod
    def _quick_formality(text: str) -> float:
        """Quick formality estimation for deviation comparison."""
        text_lower = text.lower()
        formal_markers = [
            "dear", "sincerely", "regards", "respectfully", "kindly",
            "hereby", "pursuant", "attached herewith", "please find",
        ]
        informal_markers = [
            "hey", "hi", "yo", "gonna", "wanna", "gotta", "lol",
            "haha", "btw", "fyi", "thx", "awesome", "cool",
        ]
        formal_count = sum(1 for m in formal_markers if m in text_lower)
        informal_count = sum(1 for m in informal_markers if m in text_lower)
        total = formal_count + informal_count
        if total == 0:
            return 0.5
        return round(formal_count / total, 4)
