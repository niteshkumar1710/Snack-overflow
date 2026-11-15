import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.core.websockets import ws_manager
from app.database.connection import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])


def authenticate_websocket(token: Optional[str], db: Session) -> Optional[User]:
    """Validate Bearer JWT token from WebSocket query param or headers and return User."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_id = int(user_id_str)
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception as exc:
        logger.warning(f"WebSocket authentication failed: {exc}")
        return None


@router.websocket("/ws/pantry")
async def websocket_pantry_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """Authenticated WebSocket endpoint for real-time pantry inventory events.

    Clients must supply their valid JWT access token as a query parameter (?token=<jwt>).
    Unauthenticated connections are rejected with close code 1008 (Policy Violation).
    """
    db = SessionLocal()
    user = None
    try:
        user = authenticate_websocket(token=token, db=db)
    finally:
        db.close()

    if not user:
        # Reject unauthenticated connection
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        return

    await ws_manager.connect(websocket, user.id)

    try:
        # Keep connection open and listen for client pings/messages
        while True:
            # We don't require client payloads, but listening keeps the socket alive
            # and handles client-side disconnects cleanly.
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user.id)
    except Exception as exc:
        logger.warning(f"WebSocket error for user_id={user.id}: {exc}")
        ws_manager.disconnect(websocket, user.id)
