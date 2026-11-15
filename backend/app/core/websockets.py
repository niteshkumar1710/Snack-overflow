import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active authenticated WebSocket connections for real-time stock broadcasts."""

    def __init__(self):
        # Maps user_id -> set of active WebSockets (supports multiple tabs per user)
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """Accept WebSocket connection and register it under user_id."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user_id={user_id}. Active users: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """Remove WebSocket connection on client disconnect or connection loss."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user_id={user_id}. Remaining active users: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message payload to all connected authenticated users.

        Safely handles dead connections by pruning them if sending fails.
        """
        payload = json.dumps(message)
        dead_connections = []

        for user_id, sockets in list(self.active_connections.items()):
            for ws in list(sockets):
                try:
                    await ws.send_text(payload)
                except Exception as exc:
                    logger.warning(f"Failed to send to user_id={user_id}: {exc}")
                    dead_connections.append((user_id, ws))

        # Clean up any dead connections encountered during broadcast
        for user_id, ws in dead_connections:
            self.disconnect(ws, user_id)


# Global singleton instance
ws_manager = ConnectionManager()
