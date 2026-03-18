"""
MindWall — IMAP Proxy Server
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Transparent IMAP proxy that intercepts FETCH responses containing email bodies,
sends them to the MindWall API for analysis, and injects risk scores into
subject lines before returning to the email client.
"""

import asyncio
import base64
import re
import uuid
from typing import Optional

import httpx
import structlog

from .upstream import UpstreamIMAPConnection
from .interceptor import FetchInterceptor
from .injector import RiskScoreInjector
from config import ProxyConfig

logger = structlog.get_logger(__name__)

# Regex to parse quoted or unquoted tokens from IMAP LOGIN arguments
_TOKEN_RE = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"|(\S+)')

# Regex to detect IMAP literal markers  {N}  or  {N+}  at end of raw line bytes
_LITERAL_RE = re.compile(rb'\{(\d+)\+?\}\r?\n$')

# Regex to identify FETCH responses that contain BODY/RFC822 data
_FETCH_BODY_RE = re.compile(
    rb'^\*\s+\d+\s+FETCH\b.*(?:BODY\[|RFC822)',
    re.IGNORECASE,
)


def _parse_login_args(args: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse username and password from IMAP LOGIN arguments.
    Handles both quoted and unquoted forms per RFC 3501.
    Returns (username, password) or (None, None) on failure.
    """
    tokens = _TOKEN_RE.findall(args)
    parts = [quoted or unquoted for quoted, unquoted in tokens]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None


def _decode_authenticate_plain(data_b64: str) -> Optional[str]:
    """
    Decode AUTHENTICATE PLAIN base64 data to extract the username.
    SASL PLAIN format: ``authzid\\x00authcid\\x00password``
    Returns authcid (username) or None on failure.
    """
    try:
        decoded = base64.b64decode(data_b64).decode("utf-8", errors="replace")
        parts = decoded.split("\x00")
        if len(parts) >= 2:
            # authcid is the second field; authzid (first) may be empty
            return parts[1] if parts[1] else parts[0]
    except Exception:
        pass
    return None


class MindWallIMAPServer:
    """
    Transparent IMAP proxy that:
    1. Accepts connections from email clients on localhost:1143
    2. Auto-resolves the upstream IMAP server from MindWall API by login username
    3. Opens authenticated connection to upstream IMAP server
    4. Intercepts FETCH responses containing email bodies
    5. Sends body to MindWall API for analysis
    6. Injects risk score into subject line before returning to client
    """

    def __init__(self, config: ProxyConfig):
        self.config = config
        self.interceptor = FetchInterceptor(config.api_base_url, config.api_secret_key)
        self.injector = RiskScoreInjector()
        self._http_client = httpx.AsyncClient(
            base_url=config.api_base_url,
            headers={"X-MindWall-Key": config.api_secret_key},
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
        self._server = None

    async def _resolve_upstream(self, username: str) -> Optional[dict]:
        """
        Query MindWall API to resolve the upstream IMAP server for a login username.
        Returns dict with imap_host, imap_port, use_tls or None if not found.
        """
        try:
            resp = await self._http_client.get(
                f"/api/email-accounts/lookup/{username}",
            )
            if resp.status_code == 200:
                return resp.json()
            logger.debug("imap.account_not_found", username=username, status=resp.status_code)
        except Exception as e:
            logger.error("imap.resolve_upstream_failed", username=username, error=str(e))
        return None

    async def handle_client(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ):
        """Handle a single client connection by proxying to upstream IMAP."""
        peer = client_writer.get_extra_info("peername")
        logger.info("imap.client_connected", peer=str(peer))

        upstream = None
        got_command = False

        try:
            # Send IMAP greeting to client
            client_writer.write(b"* OK [CAPABILITY IMAP4rev1] MindWall IMAP Proxy Ready\r\n")
            await client_writer.drain()

            upstream_host = None
            upstream_port = None

            while True:
                raw = await asyncio.wait_for(client_reader.readline(), timeout=300)
                if not raw:
                    if not got_command:
                        # Client disconnected without sending any command.
                        # This almost always means the email client is configured
                        # with SSL/TLS or STARTTLS encryption.  The proxy only
                        # accepts plaintext — set "None" / "No encryption".
                        logger.warning(
                            "imap.tls_mismatch_suspected",
                            peer=str(peer),
                            hint="Client disconnected immediately without sending any "
                                 "command. This usually means the email client is "
                                 "configured with SSL/TLS or STARTTLS encryption. "
                                 "Set connection security to 'None' for localhost.",
                        )
                    break

                got_command = True

                # Detect TLS ClientHello (byte 0x16) — client tried direct TLS
                if raw[0:1] == b"\x16":
                    logger.warning(
                        "imap.tls_handshake_rejected",
                        peer=str(peer),
                        hint="Client sent a TLS ClientHello. The MindWall IMAP proxy "
                             "runs plaintext on localhost. Set connection security to "
                             "'None' in your email client.",
                    )
                    break

                decoded = raw.decode("utf-8", errors="replace").strip()
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
                    # Do NOT advertise STARTTLS — email clients connecting
                    # to the local proxy must use plaintext.  Upstream TLS
                    # is handled transparently by the proxy itself.
                    client_writer.write(
                        b"* CAPABILITY IMAP4rev1 AUTH=PLAIN LOGIN ID\r\n"
                    )
                    client_writer.write(f"{tag} OK CAPABILITY completed\r\n".encode())
                    await client_writer.drain()

                elif command == "ID":
                    # RFC 2971 — many clients (Thunderbird, Apple Mail) send
                    # ID before authentication.  Return minimal server ID.
                    client_writer.write(
                        b'* ID ("name" "MindWall" "vendor" "VRIP7")\r\n'
                    )
                    client_writer.write(f"{tag} OK ID completed\r\n".encode())
                    await client_writer.drain()

                elif command == "NOOP":
                    client_writer.write(f"{tag} OK NOOP completed\r\n".encode())
                    await client_writer.drain()

                elif command == "XMINDWALL" and len(parts) > 2:
                    # Custom command: XMINDWALL <host> <port>
                    # Optional manual override for upstream server
                    server_parts = parts[2].split()
                    if len(server_parts) >= 2:
                        upstream_host = server_parts[0]
                        upstream_port = int(server_parts[1])
                        client_writer.write(f"{tag} OK Upstream set\r\n".encode())
                    else:
                        client_writer.write(f"{tag} BAD Usage: XMINDWALL host port\r\n".encode())
                    await client_writer.drain()

                elif command == "LOGIN":
                    args = parts[2] if len(parts) > 2 else ""
                    login_username, _ = _parse_login_args(args)
                    logger.info("imap.login_attempt", username=login_username, peer=str(peer))

                    # Auto-resolve upstream if not explicitly set via XMINDWALL
                    if not upstream_host and login_username:
                        account = await self._resolve_upstream(login_username)
                        if account:
                            upstream_host = account["imap_host"]
                            upstream_port = account["imap_port"]
                            logger.info(
                                "imap.upstream_resolved",
                                username=login_username,
                                host=upstream_host,
                                port=upstream_port,
                            )
                        else:
                            logger.warning("imap.account_not_found", username=login_username)

                    if not upstream_host:
                        client_writer.write(
                            f"{tag} NO [ALERT] Account not configured in MindWall. "
                            f"Register this email in the MindWall dashboard first.\r\n".encode()
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
                        logger.info("imap.authenticated", username=login_username, peer=str(peer))
                        await self._pipe(client_reader, client_writer, upstream)
                        break
                    else:
                        logger.warning("imap.auth_failed", username=login_username, peer=str(peer))
                        # Close failed upstream so a retry can reconnect
                        upstream.close()
                        upstream = None

                elif command == "AUTHENTICATE":
                    # AUTHENTICATE PLAIN — extract credentials from base64,
                    # resolve upstream, replay auth to the real IMAP server.
                    auth_args = parts[2] if len(parts) > 2 else ""
                    auth_parts = auth_args.split(None, 1)
                    mechanism = auth_parts[0].upper() if auth_parts else ""
                    inline_data = auth_parts[1].strip() if len(auth_parts) > 1 else ""

                    if mechanism != "PLAIN":
                        client_writer.write(
                            f"{tag} NO Unsupported authentication mechanism\r\n".encode()
                        )
                        await client_writer.drain()
                        continue

                    # Collect base64 credentials (inline or via continuation)
                    if not inline_data:
                        client_writer.write(b"+ \r\n")
                        await client_writer.drain()
                        cont_line = await asyncio.wait_for(client_reader.readline(), timeout=60)
                        inline_data = cont_line.decode("utf-8", errors="replace").strip()

                    auth_username = _decode_authenticate_plain(inline_data)
                    logger.info("imap.authenticate_attempt", mechanism=mechanism, username=auth_username, peer=str(peer))

                    # Auto-resolve upstream from MindWall API
                    if not upstream_host and auth_username:
                        account = await self._resolve_upstream(auth_username)
                        if account:
                            upstream_host = account["imap_host"]
                            upstream_port = account["imap_port"]
                            logger.info("imap.upstream_resolved", username=auth_username, host=upstream_host, port=upstream_port)
                        else:
                            logger.warning("imap.account_not_found", username=auth_username)

                    if not upstream_host:
                        client_writer.write(
                            f"{tag} NO [ALERT] Account not configured in MindWall. "
                            f"Register this email in the MindWall dashboard first.\r\n".encode()
                        )
                        await client_writer.drain()
                        continue

                    # Connect to upstream and replay AUTHENTICATE PLAIN
                    upstream = UpstreamIMAPConnection(
                        host=upstream_host,
                        port=upstream_port,
                        use_ssl=True,
                    )
                    await upstream.connect()

                    # Send AUTHENTICATE PLAIN (without inline data) to upstream
                    await upstream.send_line(f"{tag} AUTHENTICATE PLAIN")
                    # Read the continuation prompt '+' from upstream
                    cont_resp = await asyncio.wait_for(upstream._reader.readline(), timeout=10)
                    cont_decoded = cont_resp.decode("utf-8", errors="replace").strip()

                    if cont_decoded.startswith("+"):
                        # Send the base64 credentials to upstream
                        await upstream.send_line(inline_data)
                        response = await upstream.read_response(tag)
                    elif cont_decoded.startswith(f"{tag} "):
                        # Server rejected immediately
                        response = [cont_decoded]
                    else:
                        response = [cont_decoded] + await upstream.read_response(tag)

                    for resp_line in response:
                        client_writer.write(resp_line.encode() + b"\r\n")
                    await client_writer.drain()

                    if any(f"{tag} OK" in r for r in response):
                        logger.info("imap.authenticated", username=auth_username, peer=str(peer))
                        await self._pipe(client_reader, client_writer, upstream)
                        break
                    else:
                        logger.warning("imap.auth_failed", username=auth_username, peer=str(peer))
                        upstream.close()
                        upstream = None

                elif command == "LOGOUT":
                    if upstream:
                        await upstream.send_line(decoded)
                    client_writer.write(f"* BYE MindWall IMAP Proxy logging out\r\n".encode())
                    client_writer.write(f"{tag} OK LOGOUT completed\r\n".encode())
                    await client_writer.drain()
                    break

                elif command == "STARTTLS":
                    # Not advertised in CAPABILITY but some clients try anyway.
                    # Local proxy runs plaintext; upstream TLS is handled internally.
                    client_writer.write(
                        f"{tag} BAD STARTTLS is not supported. "
                        f"Configure your email client with 'No encryption' or 'None' "
                        f"for this server (localhost:{self.config.imap_listen_port}).\r\n".encode()
                    )
                    await client_writer.drain()

                else:
                    if upstream:
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
        Bidirectional raw-byte pipe between email client and upstream IMAP.

        Both directions use raw ``read()`` to avoid any data corruption.
        A decoupled analysis worker receives teed bytes via an asyncio Queue
        and scans for FETCH body literals to submit for manipulation analysis.
        """
        analysis_queue = asyncio.Queue(maxsize=512)

        c2u = asyncio.create_task(
            self._pipe_raw(
                client_reader, upstream._writer, "c2u",
            )
        )
        u2c = asyncio.create_task(
            self._pipe_raw(
                upstream._reader, client_writer, "u2c",
                analysis_queue=analysis_queue,
            )
        )
        analyzer = asyncio.create_task(
            self._analysis_worker(analysis_queue)
        )

        try:
            done, pending = await asyncio.wait(
                [c2u, u2c], return_when=asyncio.FIRST_COMPLETED,
            )
            # Log reason for pipe exit
            for task in done:
                exc = task.exception() if not task.cancelled() else None
                if exc:
                    logger.warning("imap.pipe_task_error", error=str(exc))
        finally:
            c2u.cancel()
            u2c.cancel()
            # Signal analyzer to stop
            try:
                analysis_queue.put_nowait(None)
            except asyncio.QueueFull:
                pass
            analyzer.cancel()

    async def _pipe_raw(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        direction: str,
        analysis_queue: asyncio.Queue | None = None,
    ):
        """
        Forward raw bytes between two asyncio streams.

        This is the core data-forwarding loop. It reads whatever bytes
        are available (up to 65 536) and writes them immediately to the
        other side.  No decoding, no line parsing, no modification.
        The optional *analysis_queue* receives a copy of every chunk
        for background FETCH-body scanning.
        """
        total_bytes = 0
        chunks = 0
        try:
            while True:
                data = await asyncio.wait_for(reader.read(65536), timeout=600)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
                total_bytes += len(data)
                chunks += 1

                # Log first few chunks so we can verify data is flowing
                if chunks <= 3:
                    preview = data[:200].decode("utf-8", errors="replace").replace("\r\n", "\\r\\n")[:150]
                    logger.info(
                        "imap.pipe_data",
                        direction=direction,
                        chunk=chunks,
                        size=len(data),
                        preview=preview,
                    )

                # Tee bytes for analysis (upstream→client only)
                if analysis_queue is not None:
                    try:
                        analysis_queue.put_nowait(data)
                    except asyncio.QueueFull:
                        pass  # Drop — never slow down mail delivery
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            logger.info("imap.pipe_timeout", direction=direction, total_bytes=total_bytes)
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        except Exception as e:
            logger.error("imap.pipe_error", direction=direction, error=str(e))
        finally:
            logger.info(
                "imap.pipe_closed",
                direction=direction,
                total_bytes=total_bytes,
                chunks=chunks,
            )

    # ------------------------------------------------------------------
    #  Analysis worker — processes teed upstream bytes to find FETCH
    #  body literals and submit them for manipulation scoring.
    # ------------------------------------------------------------------

    async def _analysis_worker(self, queue: asyncio.Queue):
        """
        Consume raw upstream bytes from *queue*, reassemble IMAP lines,
        detect ``{N}`` literals inside FETCH responses, and submit
        the extracted email bodies for analysis.
        """
        line_buf = bytearray()
        in_literal = False
        lit_remaining = 0
        lit_data = bytearray()
        fetch_line = b""

        try:
            while True:
                chunk = await queue.get()
                if chunk is None:
                    break

                pos = 0
                while pos < len(chunk):
                    # --- Inside a literal: accumulate body bytes ---
                    if in_literal:
                        take = min(len(chunk) - pos, lit_remaining)
                        lit_data.extend(chunk[pos : pos + take])
                        pos += take
                        lit_remaining -= take
                        if lit_remaining <= 0:
                            asyncio.create_task(
                                self._analyze_fetched_body(
                                    fetch_line, bytes(lit_data),
                                )
                            )
                            in_literal = False
                            lit_data.clear()
                        continue

                    # --- Line accumulation mode ---
                    nl_idx = chunk.find(b"\n", pos)
                    if nl_idx == -1:
                        # No newline in remainder — buffer and wait
                        line_buf.extend(chunk[pos:])
                        break

                    line_buf.extend(chunk[pos : nl_idx + 1])
                    line = bytes(line_buf)
                    line_buf.clear()
                    pos = nl_idx + 1

                    # Check for FETCH literal marker
                    lit_match = _LITERAL_RE.search(line)
                    if lit_match and _FETCH_BODY_RE.search(line):
                        lit_size = int(lit_match.group(1))
                        if lit_size > 50:
                            fetch_line = line
                            in_literal = True
                            lit_remaining = lit_size
                            lit_data.clear()

                # Prevent unbounded buffer growth
                if len(line_buf) > 500_000:
                    line_buf.clear()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug("imap.analysis_worker_error", error=str(e))

    async def _analyze_fetched_body(self, fetch_line: bytes, body_data: bytes):
        """Parse and submit an intercepted FETCH body for manipulation analysis."""
        try:
            body_text = body_data.decode("utf-8", errors="replace")

            # Parse MIME to extract clean text content
            parsed = self.interceptor.mime_parser.parse(body_text)
            clean_text = self.interceptor.sanitizer.sanitize(
                parsed.text_content or parsed.html_content or ""
            )
            if not clean_text or len(clean_text.strip()) <= 20:
                return

            # Extract metadata from FETCH line + RFC822 headers
            headers_data = self.interceptor.parser.parse_headers(body_text)
            uid_match = re.search(rb'UID\s+(\d+)', fetch_line, re.IGNORECASE)
            uid = uid_match.group(1).decode() if uid_match else str(uuid.uuid4())

            received_at = None
            if headers_data.received_date:
                try:
                    from dateutil.parser import parse as parse_date
                    received_at = parse_date(headers_data.received_date).isoformat()
                except Exception:
                    pass

            payload = {
                "message_uid": uid,
                "recipient_email": headers_data.to_address or "unknown@unknown",
                "sender_email": headers_data.from_address or "unknown@unknown",
                "sender_display_name": headers_data.from_display or "",
                "subject": headers_data.subject or "",
                "body": clean_text[:8000],
                "channel": "imap",
                "received_at": received_at,
            }

            response = await self.interceptor._http_client.post(
                "/api/analyze",
                json=payload,
                headers={"X-MindWall-Key": self.interceptor.api_secret_key},
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    "imap.analysis_complete",
                    uid=uid,
                    score=result.get("manipulation_score"),
                    severity=result.get("severity"),
                )
            else:
                logger.warning(
                    "imap.analysis_failed",
                    uid=uid,
                    status=response.status_code,
                )
        except Exception as e:
            logger.debug("imap.analysis_error", error=str(e))

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
