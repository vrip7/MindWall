"""
MindWall — IMAP Command/Response Parser
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Parses IMAP commands and responses per RFC 3501 to identify
FETCH responses containing message bodies.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class IMAPFetchData:
    """Parsed data from an IMAP FETCH response."""
    uid: Optional[str] = None
    message_id: Optional[str] = None
    subject: Optional[str] = None
    from_address: Optional[str] = None
    from_display: Optional[str] = None
    to_address: Optional[str] = None
    body: Optional[str] = None
    received_date: Optional[str] = None
    flags: List[str] = field(default_factory=list)
    is_complete: bool = False


class IMAPParser:
    """
    Parser for IMAP protocol commands and responses.
    Identifies FETCH responses containing RFC822 or BODY content.
    """

    # Pattern to match FETCH response start
    FETCH_PATTERN = re.compile(
        r'^\*\s+(\d+)\s+FETCH\s+\(', re.IGNORECASE
    )

    # Pattern to match UID in FETCH response
    UID_PATTERN = re.compile(r'UID\s+(\d+)', re.IGNORECASE)

    # Pattern to match BODY/RFC822 data
    BODY_PATTERN = re.compile(
        r'(?:BODY\[(?:TEXT|1(?:\.1)?|)\]|RFC822(?:\.TEXT)?)\s+\{(\d+)\}',
        re.IGNORECASE,
    )

    # Pattern to match ENVELOPE data
    ENVELOPE_PATTERN = re.compile(r'ENVELOPE\s+\(', re.IGNORECASE)

    # Pattern to match Subject from headers
    SUBJECT_PATTERN = re.compile(r'^Subject:\s*(.+)', re.IGNORECASE | re.MULTILINE)

    # Pattern to match From header
    FROM_PATTERN = re.compile(
        r'^From:\s*(?:"?([^"<]*)"?\s*)?<?([^>\s]+)>?',
        re.IGNORECASE | re.MULTILINE,
    )

    # Pattern to match To header
    TO_PATTERN = re.compile(
        r'^To:\s*(?:"?([^"<]*)"?\s*)?<?([^>\s]+)>?',
        re.IGNORECASE | re.MULTILINE,
    )

    # Pattern to match Date header
    DATE_PATTERN = re.compile(r'^Date:\s*(.+)', re.IGNORECASE | re.MULTILINE)

    def is_fetch_response(self, line: str) -> bool:
        """Check if a line is the start of a FETCH response."""
        return bool(self.FETCH_PATTERN.match(line.strip()))

    def has_body_data(self, line: str) -> Optional[int]:
        """
        Check if a FETCH line contains body data.
        Returns the byte count if found, None otherwise.
        """
        match = self.BODY_PATTERN.search(line)
        if match:
            return int(match.group(1))
        return None

    def extract_uid(self, line: str) -> Optional[str]:
        """Extract UID from a FETCH response line."""
        match = self.UID_PATTERN.search(line)
        return match.group(1) if match else None

    def parse_headers(self, raw_text: str) -> IMAPFetchData:
        """
        Parse email headers from raw text to extract metadata.
        """
        data = IMAPFetchData()

        subject_match = self.SUBJECT_PATTERN.search(raw_text)
        if subject_match:
            data.subject = subject_match.group(1).strip()

        from_match = self.FROM_PATTERN.search(raw_text)
        if from_match:
            data.from_display = (from_match.group(1) or "").strip()
            data.from_address = from_match.group(2).strip()

        to_match = self.TO_PATTERN.search(raw_text)
        if to_match:
            data.to_address = to_match.group(2).strip()

        date_match = self.DATE_PATTERN.search(raw_text)
        if date_match:
            data.received_date = date_match.group(1).strip()

        return data
