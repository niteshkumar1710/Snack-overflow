import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.snack import Snack
from app.core.websockets import ws_manager


@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(
        name="WS Tester",
        email="ws_tester@example.com",
        password_hash=hash_password("SuperSecret123"),
        role="member",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    admin = User(
        name="WS Admin",
        email="ws_admin@example.com",
        password_hash=hash_password("SuperSecret123"),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def user_token(test_user: User) -> str:
    return create_access_token({"sub": str(test_user.id), "email": test_user.email, "role": "member"})


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token({"sub": str(admin_user.id), "email": admin_user.email, "role": "admin"})


@pytest.fixture
def snack(db_session: Session) -> Snack:
    s = Snack(
        name="Realtime Cashews",
        category="healthy-ish",
        quantity=5,
        low_stock_threshold=2,
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


def test_unauthenticated_websocket_connection_rejected(auth_client: TestClient):
    """Connecting to WebSocket without a valid token must be rejected with 1008 Policy Violation."""
    with pytest.raises(Exception):
        with auth_client.websocket_connect("/ws/pantry"):
            pass


def test_authenticated_websocket_connection_and_ping(auth_client: TestClient, user_token: str):
    """Connecting with a valid JWT token succeeds, and responding to ping with pong works."""
    with auth_client.websocket_connect(f"/ws/pantry?token={user_token}") as ws:
        ws.send_text("ping")
        response = ws.receive_text()
        assert response == "pong"


def test_stock_update_broadcast_on_consumption(
    auth_client: TestClient,
    user_token: str,
    snack: Snack,
):
    """When a snack is consumed, all connected WebSocket clients receive a STOCK_UPDATED event."""
    with auth_client.websocket_connect(f"/ws/pantry?token={user_token}") as ws:
        # Perform consumption via REST API
        headers = {"Authorization": f"Bearer {user_token}"}
        res = auth_client.post(f"/snacks/{snack.id}/consume", json={"amount": 2}, headers=headers)
        assert res.status_code == 200

        # Receive real-time broadcast message
        event_str = ws.receive_text()
        event = json.loads(event_str)

        assert event["type"] == "STOCK_UPDATED"
        assert event["event"] == "consumed"
        assert event["snack_id"] == snack.id
        assert event["snack_name"] == "Realtime Cashews"
        assert event["quantity"] == 3
        assert event["status"] == "stocked"
        assert event["amount"] == 2


def test_stock_update_broadcast_on_restocking(
    auth_client: TestClient,
    admin_token: str,
    user_token: str,
    snack: Snack,
):
    """When an administrator restocks a snack, connected users receive a real-time restocked event."""
    with auth_client.websocket_connect(f"/ws/pantry?token={user_token}") as ws:
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = auth_client.post(f"/snacks/{snack.id}/restock", json={"amount": 10}, headers=headers)
        assert res.status_code == 200

        event_str = ws.receive_text()
        event = json.loads(event_str)

        assert event["type"] == "STOCK_UPDATED"
        assert event["event"] == "restocked"
        assert event["snack_id"] == snack.id
        assert event["quantity"] == 15
        assert event["amount"] == 10


def test_no_broadcast_on_failed_consumption(
    auth_client: TestClient,
    user_token: str,
    snack: Snack,
):
    """When consumption fails (e.g. insufficient stock), no success event is broadcast."""
    with auth_client.websocket_connect(f"/ws/pantry?token={user_token}") as ws:
        headers = {"Authorization": f"Bearer {user_token}"}
        # Attempt to consume more than available
        res = auth_client.post(f"/snacks/{snack.id}/consume", json={"amount": 999}, headers=headers)
        assert res.status_code == 409

        # Ping-pong to verify channel has no leaked event
        ws.send_text("ping")
        response = ws.receive_text()
        assert response == "pong"
