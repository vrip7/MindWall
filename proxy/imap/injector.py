"""
MindWall — Risk Score Injector
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Injects risk score indicators into email subject lines within
IMAP FETCH responses before returning to the email client.
"""

import re
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class RiskScoreInjector:
    """
    Injects MindWall risk score indicators into email subject lines.
    Modifies the Subject header in IMAP responses to prepend a visual
    risk indicator that the user can see in their email client.
    """

    SEVERITY_BADGES = {
        "low": "",
        "medium": "[⚠ MW:MEDIUM]",
        "high": "[🔴 MW:HIGH]",
        "critical": "[🚨 MW:CRITICAL]",
    }

    SUBJECT_PATTERN = re.compile(
        r'^(Subject:\s*)(.*)',
        re.IGNORECASE | re.MULTILINE,
    )

    def inject_score(
        self,
        raw_response: str,
        score: float,
        severity: str,
    ) -> str:
        """
        Inject a risk score badge into the Subject line of an IMAP response.

        Args:
            raw_response: Raw IMAP FETCH response text.
            score: Aggregate manipulation score (0-100).
            severity: Severity level string.

        Returns:
            Modified response with risk badge in subject.
        """
        badge = self.SEVERITY_BADGES.get(severity, "")
        if not badge:
            return raw_response

        def replace_subject(match):
            prefix = match.group(1)
            original_subject = match.group(2)
            return f"{prefix}{badge} {original_subject}"

        modified = self.SUBJECT_PATTERN.sub(replace_subject, raw_response, count=1)
        return modified

    def format_header(self, score: float, severity: str) -> str:
        """
        Generate an X-MindWall-Score header for injection.

        Returns:
            Formatted header line to be inserted into the email.
        """
        return f"X-MindWall-Score: {score:.1f}\r\nX-MindWall-Severity: {severity}\r\n"
