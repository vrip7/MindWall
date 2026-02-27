"""
MindWall — WebSocket Router
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

WS /ws/alerts — Real-time WebSocket feed for the dashboard.
"""

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert streaming.
    Dashboard clients connect here to receive immediate notifications
    when new threats are detected.
    """
    ws_manager = websocket.app.state.ws_manager

    await ws_manager.connect(websocket)
    logger.info("websocket.connected", client=str(websocket.client))

    try:
        while True:
            # Keep connection alive — listen for client messages (e.g. pings)
            data = await websocket.receive_text()
            # Client can send "ping" to keep alive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("websocket.disconnected", client=str(websocket.client))
    except Exception as e:
        ws_manager.disconnect(websocket)
        logger.error("websocket.error", error=str(e), client=str(websocket.client))
