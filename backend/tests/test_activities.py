import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.snack import Snack
from app.models.activity import Activity


@pytest.fixture
def admin_user(db_session: Session) -> User:
    admin = User(
        name="Admin Boss",
        email="admin_boss@example.com",
        password_hash=hash_password("SuperSecret123"),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def member_user(db_session: Session) -> User:
    member = User(
        name="Regular Member",
        email="regular_member@example.com",
        password_hash=hash_password("SuperSecret123"),
        role="member",
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    return member


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    token = create_access_token({"sub": str(admin_user.id), "email": admin_user.email, "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_headers(member_user: User) -> dict:
    token = create_access_token({"sub": str(member_user.id), "email": member_user.email, "role": "member"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_snack(db_session: Session) -> Snack:
    snack = Snack(
        name="Tortilla Chips",
        category="savoury",
        quantity=20,
        low_stock_threshold=5,
    )
    db_session.add(snack)
    db_session.commit()
    db_session.refresh(snack)
    return snack


# ---------------------------------------------------------------------------
# Authorization Tests
# ---------------------------------------------------------------------------

def test_unauthenticated_request_rejected(auth_client: TestClient):
    """Unauthenticated users must receive HTTP 401 Unauthorized."""
    response = auth_client.get("/activities")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_member_request_forbidden(auth_client: TestClient, member_headers: dict):
    """Authenticated members without admin privileges must receive HTTP 403 Forbidden."""
    response = auth_client.get("/activities", headers=member_headers)
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FORBIDDEN"
    assert "Administrator privileges required" in data["error"]["message"]


def test_admin_access_granted(auth_client: TestClient, admin_headers: dict):
    """Authenticated administrators must receive HTTP 200 OK."""
    response = auth_client.get("/activities", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "pagination" in data
    assert isinstance(data["items"], list)


# ---------------------------------------------------------------------------
# Empty State & Pagination Tests
# ---------------------------------------------------------------------------

def test_empty_activity_history(auth_client: TestClient, admin_headers: dict):
    """When no activity records exist, return an empty list with total = 0."""
    response = auth_client.get("/activities", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["pagination"]["total"] == 0
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["limit"] == 10
    assert data["pagination"]["total_pages"] == 0


def test_pagination_and_ordering(
    auth_client: TestClient,
    admin_headers: dict,
    admin_user: User,
    sample_snack: Snack,
    db_session: Session,
):
    """Test pagination bounds, items per page, and descending chronological order."""
    now = datetime.now(timezone.utc)

    # Insert 15 activity entries with incremental timestamps
    for i in range(1, 16):
        activity = Activity(
            user_id=admin_user.id,
            snack_id=sample_snack.id,
            action="consumed" if i % 2 == 1 else "restocked",
            amount=i,
            created_at=now + timedelta(minutes=i),
        )
        db_session.add(activity)
    db_session.commit()

    # Page 1 with limit 10
    response_p1 = auth_client.get("/activities?page=1&limit=10", headers=admin_headers)
    assert response_p1.status_code == 200
    p1_data = response_p1.json()
    assert len(p1_data["items"]) == 10
    assert p1_data["pagination"]["total"] == 15
    assert p1_data["pagination"]["page"] == 1
    assert p1_data["pagination"]["limit"] == 10
    assert p1_data["pagination"]["total_pages"] == 2

    # Newest entry should have amount = 15 (most recent timestamp)
    assert p1_data["items"][0]["amount"] == 15
    assert p1_data["items"][9]["amount"] == 6

    # Page 2 with limit 10
    response_p2 = auth_client.get("/activities?page=2&limit=10", headers=admin_headers)
    assert response_p2.status_code == 200
    p2_data = response_p2.json()
    assert len(p2_data["items"]) == 5
    assert p2_data["pagination"]["total"] == 15
    assert p2_data["pagination"]["page"] == 2
    assert p2_data["items"][0]["amount"] == 5
    assert p2_data["items"][-1]["amount"] == 1


def test_activity_item_structure_and_relations(
    auth_client: TestClient,
    admin_headers: dict,
    admin_user: User,
    sample_snack: Snack,
    db_session: Session,
):
    """Verify that activity items include eager-loaded user and snack details without password hashes."""
    activity = Activity(
        user_id=admin_user.id,
        snack_id=sample_snack.id,
        action="restocked",
        amount=10,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(activity)
    db_session.commit()

    response = auth_client.get("/activities", headers=admin_headers)
    assert response.status_code == 200
    item = response.json()["items"][0]

    assert item["id"] == activity.id
    assert item["action"] == "restocked"
    assert item["amount"] == 10
    assert "created_at" in item

    # Verify nested user representation
    assert item["user"]["id"] == admin_user.id
    assert item["user"]["name"] == admin_user.name
    assert "password_hash" not in item["user"]

    # Verify nested snack representation
    assert item["snack"]["id"] == sample_snack.id
    assert item["snack"]["name"] == sample_snack.name


def test_consumption_and_restocking_record_activities(
    auth_client: TestClient,
    admin_headers: dict,
    member_headers: dict,
    sample_snack: Snack,
):
    """Ensure consuming and restocking snacks automatically creates activity log records."""
    # Member consumes 2 snacks
    res_consume = auth_client.post(
        f"/snacks/{sample_snack.id}/consume",
        json={"amount": 2},
        headers=member_headers,
    )
    assert res_consume.status_code == 200

    # Admin restocks 5 snacks
    res_restock = auth_client.post(
        f"/snacks/{sample_snack.id}/restock",
        json={"amount": 5},
        headers=admin_headers,
    )
    assert res_restock.status_code == 200

    # Verify admin activities endpoint reflects both actions
    res_activities = auth_client.get("/activities?limit=10", headers=admin_headers)
    assert res_activities.status_code == 200
    items = res_activities.json()["items"]
    assert len(items) >= 2

    # Newest first: restock first, then consume
    assert items[0]["action"] == "restocked"
    assert items[0]["amount"] == 5
    assert items[1]["action"] == "consumed"
    assert items[1]["amount"] == 2
