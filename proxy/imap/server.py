"""
MindWall — IMAP Proxy Server
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Transparent IMAP proxy that intercepts FETCH responses containing email bodies,
sends them to the MindWall API for analysis, and injects risk scores into
subject lines before returning to the email client.
"""

import asyncio

import structlog

from .upstream import UpstreamIMAPConnection
from .interceptor import FetchInterceptor
from .injector import RiskScoreInjector
from ..config import ProxyConfig

logger = structlog.get_logger(__name__)


class MindWallIMAPServer:
    """
    Transparent IMAP proxy that:
    1. Accepts connections from email clients on localhost:1143
    2. Opens authenticated connection to upstream IMAP server
    3. Intercepts FETCH responses containing email bodies
    4. Sends body to MindWall API for analysis
    5. Injects risk score into subject line before returning to client
    """

    def __init__(self, config: ProxyConfig):
        self.config = config
        self.interceptor = FetchInterceptor(config.api_base_url, config.api_secret_key)
        self.injector = RiskScoreInjector()
        self._server = None

    async def handle_client(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ):
        """Handle a single client connection by proxying to upstream IMAP."""
        peer = client_writer.get_extra_info("peername")
        logger.info("imap.client_connected", peer=str(peer))

        # Read the initial client greeting to extract upstream server info
        # The client needs to configure upstream server in account settings
        # We read the LOGIN/AUTHENTICATE command to get credentials
        upstream = None

        try:
            # Send IMAP greeting to client
            client_writer.write(b"* OK [CAPABILITY IMAP4rev1] MindWall IMAP Proxy Ready\r\n")
            await client_writer.drain()

            upstream_host = None
            upstream_port = None
            authenticated = False

            while True:
                line = await asyncio.wait_for(client_reader.readline(), timeout=300)
                if not line:
                    break

                decoded = line.decode("utf-8", errors="replace").strip()
                logger.debug("imap.client_command", command=decoded[:100])

                # Parse the command
                parts = decoded.split(" ", 2)
                if len(parts) < 2:
                    client_writer.write(b"* BAD Invalid command\r\n")
                    await client_writer.drain()
                    continue

                tag = parts[0]
                command = parts[1].upper()

                if command == "CAPABILITY":
                    client_writer.write(
                        b"* CAPABILITY IMAP4rev1 AUTH=PLAIN LOGIN STARTTLS\r\n"
                    )
                    client_writer.write(f"{tag} OK CAPABILITY completed\r\n".encode())
                    await client_writer.drain()

                elif command == "XMINDWALL" and len(parts) > 2:
                    # Custom command: XMINDWALL <host> <port>
                    # Allows client to specify upstream server
                    server_parts = parts[2].split()
                    if len(server_parts) >= 2:
                        upstream_host = server_parts[0]
                        upstream_port = int(server_parts[1])
                        client_writer.write(f"{tag} OK Upstream set\r\n".encode())
                    else:
                        client_writer.write(f"{tag} BAD Usage: XMINDWALL host port\r\n".encode())
                    await client_writer.drain()

                elif command in ("LOGIN", "AUTHENTICATE"):
                    if not upstream_host:
                        # Default to reading from initial connection or env
                        # In production, upstream is configured per-account
                        client_writer.write(
                            f"{tag} NO Upstream server not configured. "
                            f"Use XMINDWALL <host> <port> first.\r\n".encode()
                        )
                        await client_writer.drain()
                        continue

                    # Connect to upstream IMAP server
                    upstream = UpstreamIMAPConnection(
                        host=upstream_host,
                        port=upstream_port,
                        use_ssl=True,
                    )
                    await upstream.connect()

                    # Forward LOGIN command to upstream
                    await upstream.send_line(decoded)
                    response = await upstream.read_response(tag)

                    # Forward response back to client
                    for resp_line in response:
                        client_writer.write(resp_line.encode() + b"\r\n")
                    await client_writer.drain()

                    if any(f"{tag} OK" in r for r in response):
                        authenticated = True
                        # Switch to bidirectional proxy mode
                        await self._pipe(client_reader, client_writer, upstream)
                        break

                elif command == "LOGOUT":
                    if upstream:
                        await upstream.send_line(decoded)
                    client_writer.write(f"* BYE MindWall IMAP Proxy logging out\r\n".encode())
                    client_writer.write(f"{tag} OK LOGOUT completed\r\n".encode())
                    await client_writer.drain()
                    break

                elif command == "STARTTLS":
                    # TLS is handled at the upstream level
                    client_writer.write(f"{tag} NO STARTTLS not supported on proxy (use SSL upstream)\r\n".encode())
                    await client_writer.drain()

                else:
                    if upstream and authenticated:
                        await upstream.send_line(decoded)
                        response = await upstream.read_response(tag)
                        for resp_line in response:
                            client_writer.write(resp_line.encode() + b"\r\n")
                        await client_writer.drain()
                    else:
                        client_writer.write(f"{tag} BAD Not authenticated\r\n".encode())
                        await client_writer.drain()

        except asyncio.TimeoutError:
            logger.warning("imap.timeout", peer=str(peer))
        except ConnectionResetError:
            logger.info("imap.connection_reset", peer=str(peer))
        except Exception as e:
            logger.error("imap.error", error=str(e), peer=str(peer))
        finally:
            if upstream:
                upstream.close()
            client_writer.close()
            try:
                await client_writer.wait_closed()
            except Exception:
                pass
            logger.info("imap.client_disconnected", peer=str(peer))

    async def _pipe(self, client_reader, client_writer, upstream):
        """
        Bidirectional pipe between client and upstream.
        Intercepts FETCH responses at the data level.
        """
        client_to_upstream = asyncio.create_task(
            self._forward_client_commands(client_reader, upstream)
        )
        upstream_to_client = asyncio.create_task(
            self._forward_upstream_responses(upstream, client_writer)
        )
        done, pending = await asyncio.wait(
            [client_to_upstream, upstream_to_client],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    async def _forward_client_commands(self, client_reader, upstream):
        """Forward commands from client to upstream IMAP server."""
        try:
            while True:
                line = await asyncio.wait_for(client_reader.readline(), timeout=600)
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").strip()
                logger.debug("imap.forward_to_upstream", command=decoded[:80])
                await upstream.send_line(decoded)
        except (asyncio.CancelledError, asyncio.TimeoutError, ConnectionResetError):
            pass

    async def _forward_upstream_responses(self, upstream, client_writer):
        """
        Reads responses from upstream IMAP.
        Detects FETCH responses containing RFC822/BODY content.
        Passes through interceptor before writing to client.
        """
        try:
            async for line in upstream.read_lines():
                processed = await self.interceptor.process_line(line)
                if processed:
                    if isinstance(processed, str):
                        processed = processed.encode("utf-8", errors="replace")
                    client_writer.write(processed)
                    await client_writer.drain()
        except (asyncio.CancelledError, ConnectionResetError):
            pass

    async def start(self):
        """Start the IMAP proxy server."""
        self._server = await asyncio.start_server(
            self.handle_client,
            host=self.config.imap_listen_host,
            port=self.config.imap_listen_port,
        )
        logger.info(
            "imap.server_started",
            host=self.config.imap_listen_host,
            port=self.config.imap_listen_port,
        )
        async with self._server:
            await self._server.serve_forever()
