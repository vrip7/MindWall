"""
MindWall — FETCH Interceptor
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Intercepts IMAP FETCH responses containing email bodies, extracts the content,
sends it to the MindWall API for analysis, and injects risk scores.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

import httpx
import structlog

from .parser import IMAPParser
from .injector import RiskScoreInjector
from ..mime.parser import MIMEParser
from ..mime.sanitizer import HTMLSanitizer

logger = structlog.get_logger(__name__)


class FetchInterceptor:
    """
    IMAP FETCH response interceptor.
    Detects email body content in FETCH responses and submits
    to the MindWall analysis API.
    """

    def __init__(self, api_base_url: str, api_secret_key: str):
        self.api_base_url = api_base_url.rstrip("/")
        self.api_secret_key = api_secret_key
        self.parser = IMAPParser()
        self.mime_parser = MIMEParser()
        self.sanitizer = HTMLSanitizer()
        self.injector = RiskScoreInjector()
        self._http_client = httpx.AsyncClient(
            base_url=self.api_base_url,
            timeout=httpx.Timeout(35.0, connect=5.0),
        )
        self._accumulating = False
        self._accumulated_bytes = b""
        self._expected_bytes = 0
        self._current_uid = None
        self._current_meta = {}

    async def process_line(self, line: str) -> Optional[str]:
        """
        Process a single line from the upstream IMAP response.
        Intercepts FETCH body data for analysis.

        Returns the line (potentially modified with risk score injection).
        """
        if self._accumulating:
            # We're accumulating body bytes
            encoded_line = line.encode("utf-8", errors="replace") if isinstance(line, str) else line
            self._accumulated_bytes += encoded_line
            if len(self._accumulated_bytes) >= self._expected_bytes:
                # Body complete — analyze
                body_text = self._accumulated_bytes[:self._expected_bytes].decode(
                    "utf-8", errors="replace"
                )
                self._accumulating = False

                # Parse & sanitize MIME content
                parsed = self.mime_parser.parse(body_text)
                clean_text = self.sanitizer.sanitize(parsed.text_content or parsed.html_content or "")

                if clean_text and len(clean_text.strip()) > 20:
                    # Submit to API asynchronously (don't block mail delivery)
                    asyncio.create_task(
                        self._submit_for_analysis(
                            body=clean_text,
                            uid=self._current_uid,
                            meta=self._current_meta,
                        )
                    )

                return line
            return line

        # Check if this is a FETCH response with body data
        if isinstance(line, str) and self.parser.is_fetch_response(line):
            uid = self.parser.extract_uid(line)
            body_bytes = self.parser.has_body_data(line)

            if body_bytes:
                self._accumulating = True
                self._accumulated_bytes = b""
                self._expected_bytes = body_bytes
                self._current_uid = uid or str(uuid.uuid4())

                # Extract metadata from the FETCH line
                headers_data = self.parser.parse_headers(line)
                self._current_meta = {
                    "subject": headers_data.subject or "",
                    "from_address": headers_data.from_address or "",
                    "from_display": headers_data.from_display or "",
                    "to_address": headers_data.to_address or "",
                    "received_date": headers_data.received_date or "",
                }

                logger.debug(
                    "interceptor.body_detected",
                    uid=self._current_uid,
                    expected_bytes=body_bytes,
                )

        return line

    async def _submit_for_analysis(
        self,
        body: str,
        uid: str,
        meta: dict,
    ) -> None:
        """Submit extracted email content to the MindWall analysis API."""
        try:
            received_at = None
            if meta.get("received_date"):
                try:
                    from dateutil.parser import parse as parse_date
                    received_at = parse_date(meta["received_date"]).isoformat()
                except Exception:
                    received_at = datetime.utcnow().isoformat()

            payload = {
                "message_uid": uid,
                "recipient_email": meta.get("to_address", "unknown@unknown"),
                "sender_email": meta.get("from_address", "unknown@unknown"),
                "sender_display_name": meta.get("from_display", ""),
                "subject": meta.get("subject", ""),
                "body": body[:8000],  # Limit body size
                "channel": "imap",
                "received_at": received_at,
            }

            response = await self._http_client.post(
                "/api/analyze",
                json=payload,
                headers={"X-MindWall-Key": self.api_secret_key},
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    "interceptor.analysis_complete",
                    uid=uid,
                    score=result.get("manipulation_score"),
                    severity=result.get("severity"),
                )
            else:
                logger.warning(
                    "interceptor.analysis_failed",
                    uid=uid,
                    status=response.status_code,
                )

        except Exception as e:
            logger.error("interceptor.analysis_error", uid=uid, error=str(e))
