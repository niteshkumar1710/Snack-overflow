import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.snack import Snack
from app.models.vote import Vote


@pytest.fixture
def auth_headers(db_session: Session) -> dict:
    user = User(
        name="Summary Viewer",
        email="summary_viewer@example.com",
        password_hash=hash_password("password123"),
        role="member",
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(db_session: Session) -> dict:
    admin = User(
        name="Admin Summary",
        email="admin_summary@example.com",
        password_hash=hash_password("password123"),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()
    token = create_access_token({"sub": str(admin.id), "email": admin.email, "role": admin.role})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /snacks/summary Tests
# ---------------------------------------------------------------------------

def test_summary_empty_pantry(auth_client: TestClient, auth_headers: dict):
    """Test summary endpoint on an empty pantry returns 0 counts and null Snack of the Week."""
    response = auth_client.get("/snacks/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["stocked_count"] == 0
    assert data["running_low_count"] == 0
    assert data["gone_count"] == 0
    assert data["total_snacks"] == 0
    assert data["snack_of_the_week"] is None


def test_summary_status_counts(auth_client: TestClient, auth_headers: dict, db_session: Session):
    """Test summary accurately partitions counts into stocked, running_low, and gone."""
    # Stocked: quantity > threshold (15 > 5)
    s1 = Snack(name="Trail Mix", category="healthy-ish", quantity=15, low_stock_threshold=5)
    # Running low: quantity <= threshold and quantity > 0
    s2 = Snack(name="Dark Chocolate", category="sweet", quantity=5, low_stock_threshold=5)
    s3 = Snack(name="Sparkling Water", category="drink", quantity=1, low_stock_threshold=5)
    # Gone: quantity == 0
    s4 = Snack(name="Potato Chips", category="savoury", quantity=0, low_stock_threshold=5)

    db_session.add_all([s1, s2, s3, s4])
    db_session.commit()

    response = auth_client.get("/snacks/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["stocked_count"] == 1
    assert data["running_low_count"] == 2
    assert data["gone_count"] == 1
    assert data["total_snacks"] == 4


def test_snack_of_the_week_highest_votes(
    auth_client: TestClient,
    auth_headers: dict,
    db_session: Session,
):
    """Test snack with the most votes is chosen as Snack of the Week."""
    snack_a = Snack(name="Pretzels", category="savoury", quantity=10, low_stock_threshold=5)
    snack_b = Snack(name="Energy Bars", category="healthy-ish", quantity=10, low_stock_threshold=5)
    db_session.add_all([snack_a, snack_b])
    db_session.commit()

    # Create 3 users and cast votes: 1 for snack_a, 2 for snack_b
    users = [
        User(name=f"User {i}", email=f"user_{i}@example.com", password_hash=hash_password("pw"), role="member")
        for i in range(3)
    ]
    db_session.add_all(users)
    db_session.commit()

    # User 0 votes for A
    db_session.add(Vote(user_id=users[0].id, snack_id=snack_a.id))
    # User 1 and User 2 vote for B
    db_session.add(Vote(user_id=users[1].id, snack_id=snack_b.id))
    db_session.add(Vote(user_id=users[2].id, snack_id=snack_b.id))
    db_session.commit()

    response = auth_client.get("/snacks/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["snack_of_the_week"] is not None
    assert data["snack_of_the_week"]["id"] == snack_b.id
    assert data["snack_of_the_week"]["name"] == "Energy Bars"
    assert data["snack_of_the_week"]["votes_count"] == 2


def test_snack_of_the_week_tie_breaker_stock(
    auth_client: TestClient,
    auth_headers: dict,
    db_session: Session,
):
    """Test tie-breaking: when votes are equal, the snack with higher available stock wins."""
    # Both have 1 vote, but Snack B has higher quantity (30 vs 10)
    snack_a = Snack(name="Orange Juice", category="drink", quantity=10, low_stock_threshold=5)
    snack_b = Snack(name="Apple Juice", category="drink", quantity=30, low_stock_threshold=5)
    db_session.add_all([snack_a, snack_b])
    db_session.commit()

    users = [
        User(name=f"Voter {i}", email=f"voter_{i}@example.com", password_hash=hash_password("pw"), role="member")
        for i in range(2)
    ]
    db_session.add_all(users)
    db_session.commit()

    db_session.add(Vote(user_id=users[0].id, snack_id=snack_a.id))
    db_session.add(Vote(user_id=users[1].id, snack_id=snack_b.id))
    db_session.commit()

    response = auth_client.get("/snacks/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["snack_of_the_week"] is not None
    # Higher stock wins
    assert data["snack_of_the_week"]["id"] == snack_b.id
    assert data["snack_of_the_week"]["name"] == "Apple Juice"


def test_snack_of_the_week_tie_breaker_alphabetical(
    auth_client: TestClient,
    auth_headers: dict,
    db_session: Session,
):
    """Test tie-breaking: when votes and quantities are equal, alphabetical order wins."""
    snack_z = Snack(name="Zesty Tortillas", category="savoury", quantity=15, low_stock_threshold=5)
    snack_a = Snack(name="Baked Pita Chips", category="savoury", quantity=15, low_stock_threshold=5)
    db_session.add_all([snack_z, snack_a])
    db_session.commit()

    users = [
        User(name=f"Alpha Voter {i}", email=f"alpha_{i}@example.com", password_hash=hash_password("pw"), role="member")
        for i in range(2)
    ]
    db_session.add_all(users)
    db_session.commit()

    # Equal votes: 1 each
    db_session.add(Vote(user_id=users[0].id, snack_id=snack_z.id))
    db_session.add(Vote(user_id=users[1].id, snack_id=snack_a.id))
    db_session.commit()

    response = auth_client.get("/snacks/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["snack_of_the_week"] is not None
    # Alphabetical order: "Baked Pita Chips" before "Zesty Tortillas"
    assert data["snack_of_the_week"]["id"] == snack_a.id
    assert data["snack_of_the_week"]["name"] == "Baked Pita Chips"


def test_summary_unauthenticated_returns_401(auth_client: TestClient):
    """Test unauthenticated summary request is rejected with HTTP 401."""
    response = auth_client.get("/snacks/summary")
    assert response.status_code == 401


def test_summary_accessible_by_admin(auth_client: TestClient, admin_headers: dict):
    """Test admin role can also access summary metrics."""
    response = auth_client.get("/snacks/summary", headers=admin_headers)
    assert response.status_code == 200
