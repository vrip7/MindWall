"""
MindWall — Proxy Configuration
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Configuration for the IMAP/SMTP proxy service.
"""

import os
from dataclasses import dataclass


@dataclass
class ProxyConfig:
    """Configuration for the MindWall IMAP/SMTP proxy."""

    # MindWall API
    api_base_url: str = "http://api:8000"
    api_secret_key: str = ""

    # IMAP proxy
    imap_listen_host: str = "0.0.0.0"
    imap_listen_port: int = 1143

    # SMTP proxy
    smtp_listen_host: str = "0.0.0.0"
    smtp_listen_port: int = 1025

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "ProxyConfig":
        """Load configuration from environment variables."""
        return cls(
            api_base_url=os.environ.get("API_BASE_URL", "http://api:8000"),
            api_secret_key=os.environ.get("API_SECRET_KEY", ""),
            imap_listen_host=os.environ.get("IMAP_LISTEN_HOST", "0.0.0.0"),
            imap_listen_port=int(os.environ.get("IMAP_LISTEN_PORT", "1143")),
            smtp_listen_host=os.environ.get("SMTP_LISTEN_HOST", "0.0.0.0"),
            smtp_listen_port=int(os.environ.get("SMTP_LISTEN_PORT", "1025")),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )
