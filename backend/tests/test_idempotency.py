import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.snack import Snack
from app.models.idempotency import IdempotencyRecord


@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(
        name="Idempotent Eater",
        email="idemp_eater@example.com",
        password_hash=hash_password("SuperSecret123"),
        role="member",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user(db_session: Session) -> User:
    user = User(
        name="Second Eater",
        email="second_eater@example.com",
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
        name="Idempotent Admin",
        email="idemp_admin@example.com",
        password_hash=hash_password("SuperSecret123"),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def user_headers(test_user: User) -> dict:
    token = create_access_token({"sub": str(test_user.id), "email": test_user.email, "role": "member"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_headers(second_user: User) -> dict:
    token = create_access_token({"sub": str(second_user.id), "email": second_user.email, "role": "member"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    token = create_access_token({"sub": str(admin_user.id), "email": admin_user.email, "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def snack(db_session: Session) -> Snack:
    s = Snack(
        name="Pecan Crunch",
        category="sweet",
        quantity=10,
        low_stock_threshold=3,
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


def test_first_request_succeeds_and_records_idempotency(
    auth_client: TestClient,
    user_headers: dict,
    snack: Snack,
    db_session: Session,
):
    """Initial request with Idempotency-Key consumes stock and completes record."""
    key = str(uuid.uuid4())
    headers = {**user_headers, "Idempotency-Key": key}

    response = auth_client.post(
        f"/snacks/{snack.id}/consume",
        json={"amount": 2},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["snack"]["quantity"] == 8

    # Verify database record
    record = db_session.query(IdempotencyRecord).filter_by(key=key).first()
    assert record is not None
    assert record.status == "completed"
    assert record.response_status_code == 200


def test_repeated_request_returns_cached_result_without_double_decrement(
    auth_client: TestClient,
    user_headers: dict,
    snack: Snack,
    db_session: Session,
):
    """Replaying request with the SAME key and SAME payload returns original result without decrementing stock again."""
    key = str(uuid.uuid4())
    headers = {**user_headers, "Idempotency-Key": key}

    # First request
    resp1 = auth_client.post(f"/snacks/{snack.id}/consume", json={"amount": 3}, headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["snack"]["quantity"] == 7

    # Second request with identical key
    resp2 = auth_client.post(f"/snacks/{snack.id}/consume", json={"amount": 3}, headers=headers)
    assert resp2.status_code == 200
    # Crucial: quantity remains 7, did NOT decrement to 4!
    assert resp2.json()["snack"]["quantity"] == 7

    # Verify in DB
    refreshed_snack = db_session.query(Snack).filter_by(id=snack.id).first()
    assert refreshed_snack.quantity == 7


def test_same_key_with_different_payload_returns_conflict(
    auth_client: TestClient,
    user_headers: dict,
    snack: Snack,
):
    """Reusing an existing key with a DIFFERENT payload must be rejected with 409 Conflict."""
    key = str(uuid.uuid4())
    headers = {**user_headers, "Idempotency-Key": key}

    # Original request: amount = 1
    resp1 = auth_client.post(f"/snacks/{snack.id}/consume", json={"amount": 1}, headers=headers)
    assert resp1.status_code == 200

    # Tampered / different request: amount = 5
    resp2 = auth_client.post(f"/snacks/{snack.id}/consume", json={"amount": 5}, headers=headers)
    assert resp2.status_code == 409
    err = resp2.json()["error"]
    assert err["code"] == "IDEMPOTENCY_KEY_PAYLOAD_MISMATCH"


def test_different_keys_execute_different_operations(
    auth_client: TestClient,
    user_headers: dict,
    snack: Snack,
):
    """Distinct keys represent distinct operations and mutate stock sequentially."""
    key1 = str(uuid.uuid4())
    key2 = str(uuid.uuid4())

    resp1 = auth_client.post(
        f"/snacks/{snack.id}/consume",
        json={"amount": 2},
        headers={**user_headers, "Idempotency-Key": key1},
    )
    assert resp1.status_code == 200
    assert resp1.json()["snack"]["quantity"] == 8

    resp2 = auth_client.post(
        f"/snacks/{snack.id}/consume",
        json={"amount": 2},
        headers={**user_headers, "Idempotency-Key": key2},
    )
    assert resp2.status_code == 200
    assert resp2.json()["snack"]["quantity"] == 6


def test_user_scoping_prevents_sharing_results_across_accounts(
    auth_client: TestClient,
    user_headers: dict,
    second_user_headers: dict,
    snack: Snack,
):
    """Two different users generating the same key string are scoped independently by user_id."""
    shared_key_string = "client-action-12345"

    # User 1 consumes 1
    resp1 = auth_client.post(
        f"/snacks/{snack.id}/consume",
        json={"amount": 1},
        headers={**user_headers, "Idempotency-Key": shared_key_string},
    )
    assert resp1.status_code == 200
    assert resp1.json()["snack"]["quantity"] == 9

    # User 2 uses the exact same key string: executes their own operation, NOT returning User 1's cached response!
    resp2 = auth_client.post(
        f"/snacks/{snack.id}/consume",
        json={"amount": 1},
        headers={**second_user_headers, "Idempotency-Key": shared_key_string},
    )
    assert resp2.status_code == 200
    # Stock decrements for User 2 as well
    assert resp2.json()["snack"]["quantity"] == 8


def test_failed_request_can_be_retried(
    auth_client: TestClient,
    user_headers: dict,
    snack: Snack,
    db_session: Session,
):
    """If an operation fails (e.g. insufficient stock), the key is marked failed and can be retried later once restocked."""
    key = str(uuid.uuid4())
    headers = {**user_headers, "Idempotency-Key": key}

    # Request more than available (snack has 10, request 15)
    resp1 = auth_client.post(f"/snacks/{snack.id}/consume", json={"amount": 15}, headers=headers)
    assert resp1.status_code == 409
    assert resp1.json()["error"]["code"] == "INSUFFICIENT_STOCK"

    # Verify idempotency record is marked failed or cleaned
    record = db_session.query(IdempotencyRecord).filter_by(key=key).first()
    assert record is None or record.status == "failed"

    # Restock the snack to 20
    snack.quantity = 20
    db_session.commit()

    # Retry the exact same request with the same key now that stock is available
    resp2 = auth_client.post(f"/snacks/{snack.id}/consume", json={"amount": 15}, headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["snack"]["quantity"] == 5


def test_restocking_idempotency_support(
    auth_client: TestClient,
    admin_headers: dict,
    snack: Snack,
    db_session: Session,
):
    """Administrator restock operations support Idempotency-Key to prevent double restocking on retries."""
    key = str(uuid.uuid4())
    headers = {**admin_headers, "Idempotency-Key": key}

    # First restock
    resp1 = auth_client.post(f"/snacks/{snack.id}/restock", json={"amount": 10}, headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["snack"]["quantity"] == 20

    # Replay restock
    resp2 = auth_client.post(f"/snacks/{snack.id}/restock", json={"amount": 10}, headers=headers)
    assert resp2.status_code == 200
    # Does NOT increase to 30!
    assert resp2.json()["snack"]["quantity"] == 20
