"""
MindWall — Upstream SMTP Connection
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Forwards outbound SMTP messages to the real upstream SMTP server.
"""

import asyncio
import ssl
import smtplib
from typing import List, Optional

import structlog

logger = structlog.get_logger(__name__)


class SMTPUpstream:
    """
    Manages connections to upstream SMTP servers for message forwarding.
    Supports TLS/STARTTLS for secure communication.
    """

    def __init__(
        self,
        host: str,
        port: int = 587,
        use_tls: bool = True,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.use_tls = use_tls
        self.username = username
        self.password = password

    async def send(
        self,
        mail_from: str,
        rcpt_tos: List[str],
        data: bytes,
    ) -> bool:
        """
        Forward an email to the upstream SMTP server.

        Args:
            mail_from: Sender address.
            rcpt_tos: List of recipient addresses.
            data: Raw email content bytes.

        Returns:
            True if successfully sent.
        """
        try:
            # Run blocking SMTP operations in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_sync,
                mail_from,
                rcpt_tos,
                data,
            )
            logger.info(
                "smtp_upstream.sent",
                host=self.host,
                mail_from=mail_from,
                recipients=len(rcpt_tos),
            )
            return True
        except Exception as e:
            logger.error(
                "smtp_upstream.send_failed",
                host=self.host,
                error=str(e),
            )
            return False

    def _send_sync(
        self,
        mail_from: str,
        rcpt_tos: List[str],
        data: bytes,
    ) -> None:
        """Synchronous SMTP send (run in executor)."""
        if self.port == 465:
            # Direct SSL
            server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            server = smtplib.SMTP(self.host, self.port)
            if self.use_tls:
                server.starttls()

        try:
            if self.username and self.password:
                server.login(self.username, self.password)
            server.sendmail(mail_from, rcpt_tos, data)
        finally:
            server.quit()
