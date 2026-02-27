"""
MindWall — MIME Email Parser
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Parses MIME-encoded emails to extract text and HTML content parts.
"""

import email
import email.policy
from dataclasses import dataclass
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ParsedEmail:
    """Result of MIME parsing."""
    text_content: Optional[str] = None
    html_content: Optional[str] = None
    subject: Optional[str] = None
    from_address: Optional[str] = None
    from_display: Optional[str] = None
    to_address: Optional[str] = None
    date: Optional[str] = None
    message_id: Optional[str] = None
    content_type: Optional[str] = None


class MIMEParser:
    """
    MIME email parser that extracts text/plain and text/html content
    from email messages.
    """

    def parse(self, raw_email: str) -> ParsedEmail:
        """
        Parse a raw MIME email string into structured content.

        Args:
            raw_email: Raw email content string (RFC 2822 format).

        Returns:
            ParsedEmail with extracted text and HTML content.
        """
        result = ParsedEmail()

        try:
            msg = email.message_from_string(raw_email, policy=email.policy.default)

            # Extract headers
            result.subject = str(msg.get("Subject", ""))
            result.message_id = str(msg.get("Message-ID", ""))
            result.date = str(msg.get("Date", ""))
            result.content_type = msg.get_content_type()

            # Parse From address
            from_header = msg.get("From", "")
            if from_header:
                addr = email.utils.parseaddr(str(from_header))
                result.from_display = addr[0] if addr[0] else None
                result.from_address = addr[1] if addr[1] else None

            # Parse To address
            to_header = msg.get("To", "")
            if to_header:
                addr = email.utils.parseaddr(str(to_header))
                result.to_address = addr[1] if addr[1] else None

            # Extract body content
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))

                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue

                    if content_type == "text/plain" and result.text_content is None:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            try:
                                result.text_content = payload.decode(charset, errors="replace")
                            except (LookupError, UnicodeDecodeError):
                                result.text_content = payload.decode("utf-8", errors="replace")

                    elif content_type == "text/html" and result.html_content is None:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            try:
                                result.html_content = payload.decode(charset, errors="replace")
                            except (LookupError, UnicodeDecodeError):
                                result.html_content = payload.decode("utf-8", errors="replace")
            else:
                # Non-multipart message
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    try:
                        decoded_payload = payload.decode(charset, errors="replace")
                    except (LookupError, UnicodeDecodeError):
                        decoded_payload = payload.decode("utf-8", errors="replace")

                    if content_type == "text/html":
                        result.html_content = decoded_payload
                    else:
                        result.text_content = decoded_payload

        except Exception as e:
            logger.error("mime_parser.error", error=str(e))
            # Fallback: treat entire input as plain text
            result.text_content = raw_email

        return result
