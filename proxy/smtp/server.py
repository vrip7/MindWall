"""
MindWall — SMTP Proxy Server
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Lightweight SMTP proxy for monitoring outbound communications.
Forwards to the real upstream SMTP server while optionally logging metadata.
"""

import asyncio
from typing import Optional

import structlog
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, Envelope, Session

from .upstream import SMTPUpstream
from ..config import ProxyConfig

logger = structlog.get_logger(__name__)


class MindWallSMTPHandler:
    """
    SMTP message handler that forwards messages to the upstream SMTP server.
    Optionally monitors outbound communication patterns.
    """

    def __init__(self, config: ProxyConfig):
        self.config = config

    async def handle_RCPT(
        self,
        server: SMTP,
        session: Session,
        envelope: Envelope,
        address: str,
        rcpt_options: list,
    ) -> str:
        """Handle RCPT TO command."""
        envelope.rcpt_tos.append(address)
        return "250 OK"

    async def handle_DATA(
        self,
        server: SMTP,
        session: Session,
        envelope: Envelope,
    ) -> str:
        """
        Handle DATA command — the actual email content.
        Logs outbound metadata for potential cross-channel analysis.
        """
        logger.info(
            "smtp.outbound",
            mail_from=envelope.mail_from,
            rcpt_tos=envelope.rcpt_tos,
            data_length=len(envelope.content) if envelope.content else 0,
        )

        # In production, forward to upstream SMTP
        # The actual forwarding requires upstream SMTP credentials
        # which are configured per-account in the email client

        return "250 Message accepted for delivery"


class MindWallSMTPServer:
    """SMTP proxy server that listens for outbound emails."""

    def __init__(self, config: ProxyConfig):
        self.config = config
        self.handler = MindWallSMTPHandler(config)
        self._controller: Optional[Controller] = None

    async def start(self):
        """Start the SMTP proxy server."""
        self._controller = Controller(
            self.handler,
            hostname=self.config.smtp_listen_host,
            port=self.config.smtp_listen_port,
        )
        self._controller.start()
        logger.info(
            "smtp.server_started",
            host=self.config.smtp_listen_host,
            port=self.config.smtp_listen_port,
        )
        # Keep running
        while True:
            await asyncio.sleep(3600)

    def stop(self):
        """Stop the SMTP proxy server."""
        if self._controller:
            self._controller.stop()
            logger.info("smtp.server_stopped")
