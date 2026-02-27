"""
MindWall — IMAP/SMTP Proxy Entrypoint
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Starts both the IMAP and SMTP proxy servers as concurrent asyncio tasks.
"""

import asyncio
import signal
import sys

import structlog

from imap.server import MindWallIMAPServer
from smtp.server import MindWallSMTPServer
from config import ProxyConfig

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def main():
    """Start both IMAP and SMTP proxy servers."""
    config = ProxyConfig.from_env()

    logger.info(
        "mindwall.proxy.starting",
        imap_listen=f"{config.imap_listen_host}:{config.imap_listen_port}",
        smtp_listen=f"{config.smtp_listen_host}:{config.smtp_listen_port}",
        api_url=config.api_base_url,
    )

    imap_server = MindWallIMAPServer(config)
    smtp_server = MindWallSMTPServer(config)

    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()

    def handle_signal():
        logger.info("mindwall.proxy.shutdown_signal")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    try:
        # Start both servers concurrently
        await asyncio.gather(
            imap_server.start(),
            smtp_server.start(),
        )
    except asyncio.CancelledError:
        logger.info("mindwall.proxy.cancelled")
    except Exception as e:
        logger.error("mindwall.proxy.error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
