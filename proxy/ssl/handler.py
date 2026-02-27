"""
MindWall — TLS Termination & Upstream TLS Handler
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Handles TLS termination for client connections and TLS upgrade
for upstream IMAP/SMTP server connections.
"""

import ssl
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class TLSHandler:
    """
    TLS configuration manager for the proxy.
    Handles both client-facing TLS termination and upstream TLS connections.
    """

    def create_upstream_context(
        self,
        verify_certs: bool = True,
        ca_file: Optional[str] = None,
    ) -> ssl.SSLContext:
        """
        Create an SSL context for upstream server connections.
        Validates certificates against the system trust store.

        Args:
            verify_certs: Whether to verify server certificates.
            ca_file: Optional path to CA certificate file.

        Returns:
            Configured SSL context for upstream connections.
        """
        context = ssl.create_default_context()

        if ca_file:
            context.load_verify_locations(ca_file)

        if not verify_certs:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            logger.warning("tls.cert_verification_disabled")
        else:
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

        # Enforce minimum TLS 1.2
        context.minimum_version = ssl.TLSVersion.TLSv1_2

        logger.debug(
            "tls.upstream_context_created",
            verify_certs=verify_certs,
            min_version="TLSv1.2",
        )

        return context

    def create_client_context(
        self,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
    ) -> Optional[ssl.SSLContext]:
        """
        Create an SSL context for client-facing connections.
        Only used if the proxy itself terminates TLS (optional).

        Args:
            cert_file: Path to the server certificate file.
            key_file: Path to the private key file.

        Returns:
            Configured SSL context, or None if no cert configured.
        """
        if not cert_file or not key_file:
            return None

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(certfile=cert_file, keyfile=key_file)

        logger.info("tls.client_context_created", cert_file=cert_file)

        return context
