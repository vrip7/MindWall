"""
MindWall — Rule-Based Pre-Filter
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Zero-GPU, sub-5ms rule-based fast filter that detects common manipulation
signals before invoking the LLM. Reduces unnecessary GPU load.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PreFilterResult:
    """Result of the pre-filter evaluation."""
    triggered: bool = False
    signals: list[str] = field(default_factory=list)
    score_boost: float = 0.0


class PreFilter:
    """
    Rule-based pre-filter engine.
    Applies regex and keyword pattern matching to identify common
    social engineering signals without GPU inference.
    """

    # Urgency patterns
    URGENCY_PATTERNS = [
        re.compile(r"\b(immediate(ly)?|urgent(ly)?|asap|right\s+away|time[\s\-]sensitive)\b", re.IGNORECASE),
        re.compile(r"\b(act\s+now|don'?t\s+delay|expires?\s+(today|soon|in\s+\d+))\b", re.IGNORECASE),
        re.compile(r"\b(within\s+\d+\s+(hour|minute|hr|min)s?|deadline\s+(is\s+)?(today|tomorrow|tonight))\b", re.IGNORECASE),
        re.compile(r"\b(last\s+chance|final\s+(notice|warning|reminder))\b", re.IGNORECASE),
    ]

    # Authority patterns
    AUTHORITY_PATTERNS = [
        re.compile(r"\b(ceo|cfo|cto|coo|president|director|board\s+member)\b", re.IGNORECASE),
        re.compile(r"\b(on\s+behalf\s+of|authorized\s+by|per\s+(the\s+)?(ceo|director|management))\b", re.IGNORECASE),
        re.compile(r"\b(executive\s+order|compliance\s+requirement|legal\s+obligation)\b", re.IGNORECASE),
        re.compile(r"\b(law\s+enforcement|federal|government\s+agency|irs|fbi|sec)\b", re.IGNORECASE),
    ]

    # Fear / threat patterns
    FEAR_PATTERNS = [
        re.compile(r"\b(account\s+(will\s+be\s+)?(suspend|terminat|delet|clos|lock|block))\b", re.IGNORECASE),
        re.compile(r"\b(legal\s+action|lawsuit|prosecution|arrest|penalty|fine)\b", re.IGNORECASE),
        re.compile(r"\b(failure\s+to\s+(comply|respond)|consequences|disciplinary)\b", re.IGNORECASE),
        re.compile(r"\b(unauthorized\s+access|security\s+breach|compromised)\b", re.IGNORECASE),
    ]

    # Suspicious request patterns
    SUSPICIOUS_REQUEST_PATTERNS = [
        re.compile(r"\b(wire\s+transfer|bank\s+transfer|bitcoin|cryptocurrency|gift\s+card)\b", re.IGNORECASE),
        re.compile(r"\b(password|credential|social\s+security|ssn|login\s+detail)\b", re.IGNORECASE),
        re.compile(r"\b(click\s+(here|this\s+link|below)|verify\s+your\s+(account|identity))\b", re.IGNORECASE),
        re.compile(r"\b(update\s+your\s+(payment|billing|bank)|confirm\s+your\s+(identity|details))\b", re.IGNORECASE),
        re.compile(r"\b(do\s+not\s+(share|tell|mention|inform)|keep\s+this\s+(confidential|secret|between\s+us))\b", re.IGNORECASE),
    ]

    # Emotional manipulation patterns
    EMOTIONAL_PATTERNS = [
        re.compile(r"\b(please\s+help|desperate(ly)?|begging|I\s+need\s+you\s+to)\b", re.IGNORECASE),
        re.compile(r"\b(disappointed\s+in\s+you|let\s+(me|us|the\s+team)\s+down)\b", re.IGNORECASE),
        re.compile(r"\b(only\s+you\s+can|counting\s+on\s+you|trust(ing)?\s+you)\b", re.IGNORECASE),
    ]

    # Spoofed sender patterns
    SPOOFED_SENDER_PATTERNS = [
        re.compile(r"[a-z0-9]+\.(com|org|net)-[a-z]+\.[a-z]{2,}", re.IGNORECASE),  # paypal.com-verify.xyz
        re.compile(r"(support|admin|helpdesk|security|noreply)@[^.]+\.[a-z]{2,}", re.IGNORECASE),
    ]

    def evaluate(
        self,
        subject: str,
        body: str,
        sender_email: str,
        received_at: Optional[datetime] = None,
    ) -> PreFilterResult:
        """
        Evaluate email content against rule-based filters.
        Returns signals detected and whether the prefilter was triggered.
        """
        result = PreFilterResult()
        combined_text = f"{subject} {body}"

        # Check urgency
        for pattern in self.URGENCY_PATTERNS:
            if pattern.search(combined_text):
                result.signals.append("urgency_language_detected")
                result.score_boost += 5.0
                break

        # Check authority impersonation
        for pattern in self.AUTHORITY_PATTERNS:
            if pattern.search(combined_text):
                result.signals.append("authority_reference_detected")
                result.score_boost += 8.0
                break

        # Check fear/threat language
        for pattern in self.FEAR_PATTERNS:
            if pattern.search(combined_text):
                result.signals.append("fear_threat_language_detected")
                result.score_boost += 7.0
                break

        # Check suspicious requests
        suspicious_count = 0
        for pattern in self.SUSPICIOUS_REQUEST_PATTERNS:
            if pattern.search(combined_text):
                suspicious_count += 1
        if suspicious_count > 0:
            result.signals.append(f"suspicious_request_detected(count={suspicious_count})")
            result.score_boost += min(suspicious_count * 5.0, 20.0)

        # Check emotional manipulation
        for pattern in self.EMOTIONAL_PATTERNS:
            if pattern.search(combined_text):
                result.signals.append("emotional_manipulation_detected")
                result.score_boost += 4.0
                break

        # Check spoofed sender
        for pattern in self.SPOOFED_SENDER_PATTERNS:
            if pattern.search(sender_email):
                result.signals.append("spoofed_sender_pattern")
                result.score_boost += 10.0
                break

        # Check for timing anomaly (emails sent at unusual hours)
        if received_at is not None:
            hour = received_at.hour
            if hour < 5 or hour > 23:
                result.signals.append(f"unusual_send_hour({hour})")
                result.score_boost += 3.0

        # Check for all-caps subject (shouting)
        if subject and len(subject) > 5 and subject == subject.upper():
            result.signals.append("all_caps_subject")
            result.score_boost += 3.0

        # Check for excessive exclamation/question marks
        exclamation_count = combined_text.count("!")
        if exclamation_count > 3:
            result.signals.append(f"excessive_exclamation_marks({exclamation_count})")
            result.score_boost += 2.0

        result.triggered = len(result.signals) > 0

        if result.triggered:
            logger.info(
                "prefilter.triggered",
                signals=result.signals,
                score_boost=result.score_boost,
                sender_email=sender_email,
            )

        return result
