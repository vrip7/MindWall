"""
MindWall — WebSocket Connection Manager
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Manages active WebSocket connections for real-time alert broadcasting.
"""

import json
from typing import Any, Dict, List

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time alert delivery.
    Thread-safe connection tracking and broadcast.
    """

    def __init__(self):
        self._active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._active_connections.append(websocket)
        logger.info("ws_manager.connected", total_connections=len(self._active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
        logger.info("ws_manager.disconnected", total_connections=len(self._active_connections))

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected WebSocket clients.
        Silently removes disconnected clients.
        """
        if not self._active_connections:
            return

        payload = json.dumps(message, default=str)
        disconnected = []

        for connection in self._active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning("ws_manager.send_failed", error=str(e))
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

        if self._active_connections:
            logger.debug(
                "ws_manager.broadcast",
                event=message.get("event"),
                recipients=len(self._active_connections),
            )

    @property
    def connection_count(self) -> int:
        """Return the number of active connections."""
        return len(self._active_connections)
