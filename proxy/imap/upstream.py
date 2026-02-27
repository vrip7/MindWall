"""
MindWall — Upstream IMAP Connection
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Manages asyncio connections to upstream IMAP servers (Gmail, Outlook, etc.)
with TLS support.
"""

import asyncio
import ssl
from typing import AsyncIterator, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class UpstreamIMAPConnection:
    """
    Manages an asyncio connection to an upstream IMAP server.
    Handles TLS negotiation and command/response communication.
    """

    def __init__(self, host: str, port: int, use_ssl: bool = True):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    async def connect(self) -> None:
        """Establish connection to the upstream IMAP server."""
        ssl_context = None
        if self.use_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED

        try:
            self._reader, self._writer = await asyncio.open_connection(
                host=self.host,
                port=self.port,
                ssl=ssl_context,
            )
            # Read server greeting
            greeting = await asyncio.wait_for(self._reader.readline(), timeout=10)
            logger.info(
                "upstream.connected",
                host=self.host,
                port=self.port,
                greeting=greeting.decode("utf-8", errors="replace").strip()[:100],
            )
        except Exception as e:
            logger.error("upstream.connection_failed", host=self.host, port=self.port, error=str(e))
            raise

    async def send_line(self, line: str) -> None:
        """Send a command line to the upstream server."""
        if self._writer:
            self._writer.write((line + "\r\n").encode("utf-8"))
            await self._writer.drain()

    async def read_response(self, tag: str, timeout: float = 30.0) -> List[str]:
        """
        Read a complete IMAP response for a given command tag.
        Returns all response lines including the tagged completion.
        """
        lines = []
        try:
            while True:
                line = await asyncio.wait_for(self._reader.readline(), timeout=timeout)
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").strip()
                lines.append(decoded)
                # Check if this is the tagged response (completion)
                if decoded.startswith(tag + " "):
                    break
        except asyncio.TimeoutError:
            logger.warning("upstream.read_timeout", tag=tag)
        return lines

    async def read_lines(self) -> AsyncIterator[str]:
        """Yield lines from the upstream IMAP server."""
        try:
            while True:
                line = await asyncio.wait_for(self._reader.readline(), timeout=600)
                if not line:
                    break
                yield line.decode("utf-8", errors="replace")
        except (asyncio.TimeoutError, asyncio.CancelledError, ConnectionResetError):
            pass

    def close(self) -> None:
        """Close the upstream connection."""
        if self._writer:
            try:
                self._writer.close()
            except Exception:
                pass
        logger.debug("upstream.closed", host=self.host, port=self.port)
