"""
MindWall — SMTP Proxy Server
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

SMTP proxy that forwards outbound emails through the configured upstream SMTP server.
Resolves upstream credentials from the MindWall API by sender email.
"""

import asyncio
from typing import Optional

import httpx
import structlog
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, AuthResult, Envelope, LoginPassword, Session

from .upstream import SMTPUpstream
from config import ProxyConfig

logger = structlog.get_logger(__name__)


class MindWallSMTPHandler:
    """
    SMTP message handler that resolves the upstream SMTP server from the
    MindWall API and forwards outbound emails with the stored credentials.
    """

    def __init__(self, config: ProxyConfig):
        self.config = config
        self._http_client = httpx.AsyncClient(
            base_url=config.api_base_url,
            headers={"X-MindWall-Key": config.api_secret_key},
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

    async def _resolve_upstream(self, username: str) -> Optional[dict]:
        """Look up upstream SMTP config from MindWall API by login username."""
        try:
            resp = await self._http_client.get(
                f"/api/email-accounts/lookup/{username}",
            )
            if resp.status_code == 200:
                return resp.json()
            logger.debug("smtp.account_not_found", username=username, status=resp.status_code)
        except Exception as e:
            logger.error("smtp.resolve_upstream_failed", username=username, error=str(e))
        return None

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
        Handle DATA command — resolve upstream SMTP and forward the email.
        Uses the authenticated login name or MAIL FROM to look up the account.
        """
        sender = envelope.mail_from or ""
        login_name = getattr(session, "login_data", {}).get("username", sender)

        logger.info(
            "smtp.outbound",
            mail_from=sender,
            rcpt_tos=envelope.rcpt_tos,
            data_length=len(envelope.content) if envelope.content else 0,
        )

        # Resolve the upstream SMTP server from the API
        account = await self._resolve_upstream(login_name)
        if not account:
            # Try with MAIL FROM address if login name didn't match
            if login_name != sender and sender:
                account = await self._resolve_upstream(sender)

        if not account:
            logger.warning("smtp.no_upstream_account", sender=sender, login=login_name)
            return "451 Unable to forward — email account not configured in MindWall"

        # Forward through upstream SMTP
        upstream = SMTPUpstream(
            host=account["smtp_host"],
            port=account["smtp_port"],
            use_tls=account.get("use_tls", True),
            username=account["username"],
            password=account["password"],
        )

        content = envelope.content if isinstance(envelope.content, bytes) else envelope.content.encode()
        success = await upstream.send(
            mail_from=sender,
            rcpt_tos=envelope.rcpt_tos,
            data=content,
        )

        if success:
            logger.info("smtp.forwarded", sender=sender, recipients=len(envelope.rcpt_tos))
            return "250 Message accepted for delivery"
        else:
            logger.error("smtp.forward_failed", sender=sender)
            return "451 Upstream delivery failed — please retry"


def _smtp_authenticator(server, session, envelope, mechanism, auth_data):
    """
    Accept AUTH credentials and store the login username on the session.
    Real credential validation happens at the upstream SMTP server when forwarding.
    """
    username = ""
    if isinstance(auth_data, LoginPassword):
        username = auth_data.login.decode() if isinstance(auth_data.login, bytes) else str(auth_data.login)
    elif hasattr(auth_data, "login"):
        username = str(auth_data.login)

    session.login_data = {"username": username}
    logger.debug("smtp.auth_accepted", username=username, mechanism=mechanism)
    return AuthResult(success=True)


class MindWallSMTPServer:
    """SMTP proxy server that accepts outbound emails and forwards to upstream."""

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
            authenticator=_smtp_authenticator,
            auth_required=False,
            auth_require_tls=False,
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
