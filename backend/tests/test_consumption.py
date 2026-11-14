import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.snack import Snack
from app.models.activity import Activity


@pytest.fixture
def admin_headers(db_session: Session) -> dict:
    admin = User(name="Admin Eater", email="admin_eater@example.com", password_hash=hash_password("pw"), role="admin")
    db_session.add(admin)
    db_session.commit()
    token = create_access_token({"sub": str(admin.id), "email": admin.email, "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_headers(db_session: Session) -> dict:
    member = User(name="Member Eater", email="member_eater@example.com", password_hash=hash_password("pw"), role="member")
    db_session.add(member)
    db_session.commit()
    token = create_access_token({"sub": str(member.id), "email": member.email, "role": "member"})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Consumption Endpoint Tests
# ---------------------------------------------------------------------------

def test_successful_consumption(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test successful consumption decrements stock, updates status, and logs activity."""
    snack = Snack(name="Wasabi Peas", category="healthy-ish", quantity=5, low_stock_threshold=3)
    db_session.add(snack)
    db_session.commit()

    response = auth_client.post(
        f"/snacks/{snack.id}/consume",
        json={"amount": 2},
        headers=member_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["snack"]["quantity"] == 3
    assert data["snack"]["status"] == "running_low"
    assert data["activity"]["action"] == "consumed"
    assert data["activity"]["amount"] == 2

    # Verify activity was committed to the database
    activity = db_session.query(Activity).filter_by(snack_id=snack.id).first()
    assert activity is not None
    assert activity.amount == 2
    assert activity.action == "consumed"


def test_consumption_insufficient_stock_returns_409(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test consumption when requested amount exceeds available quantity returns HTTP 409."""
    snack = Snack(name="Last M&M Bag", category="sweet", quantity=1, low_stock_threshold=2)
    db_session.add(snack)
    db_session.commit()

    # Request 2 when only 1 is available
    response = auth_client.post(
        f"/snacks/{snack.id}/consume",
        json={"amount": 2},
        headers=member_headers,
    )
    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "INSUFFICIENT_STOCK"
    assert "Someone beat you to the last packet!" in data["error"]["message"]

    # Verify quantity did not change and no activity was created
    db_session.refresh(snack)
    assert snack.quantity == 1
    activities_count = db_session.query(Activity).filter_by(snack_id=snack.id).count()
    assert activities_count == 0


def test_consumption_to_exact_zero(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test consuming the last packet sets quantity to 0 and derived status to 'gone'."""
    snack = Snack(name="Final Soda", category="drink", quantity=1, low_stock_threshold=2)
    db_session.add(snack)
    db_session.commit()

    response = auth_client.post(
        f"/snacks/{snack.id}/consume",
        json={"amount": 1},
        headers=member_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["snack"]["quantity"] == 0
    assert data["snack"]["status"] == "gone"


def test_consumption_when_stock_is_already_zero(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test consuming an already depleted snack returns 409 Conflict."""
    snack = Snack(name="Depleted Chips", category="savoury", quantity=0, low_stock_threshold=2)
    db_session.add(snack)
    db_session.commit()

    response = auth_client.post(
        f"/snacks/{snack.id}/consume",
        json={"amount": 1},
        headers=member_headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_consumption_invalid_amount(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test invalid consumption amounts (0 or negative) are rejected with 422."""
    snack = Snack(name="Almond Bar", category="healthy-ish", quantity=10)
    db_session.add(snack)
    db_session.commit()

    # Zero amount
    r_zero = auth_client.post(f"/snacks/{snack.id}/consume", json={"amount": 0}, headers=member_headers)
    assert r_zero.status_code == 422

    # Negative amount
    r_neg = auth_client.post(f"/snacks/{snack.id}/consume", json={"amount": -3}, headers=member_headers)
    assert r_neg.status_code == 422


def test_consumption_snack_not_found(auth_client: TestClient, member_headers: dict):
    """Test consuming non-existent snack returns 404."""
    response = auth_client.post("/snacks/99999/consume", json={"amount": 1}, headers=member_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SNACK_NOT_FOUND"


# ---------------------------------------------------------------------------
# Restocking Endpoint Tests
# ---------------------------------------------------------------------------

def test_successful_restocking(auth_client: TestClient, admin_headers: dict, db_session: Session):
    """Test admin restocking increments quantity and logs restocked activity."""
    snack = Snack(name="Granola Bites", category="healthy-ish", quantity=2, low_stock_threshold=5)
    db_session.add(snack)
    db_session.commit()

    response = auth_client.post(
        f"/snacks/{snack.id}/restock",
        json={"amount": 15},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["snack"]["quantity"] == 17
    assert data["snack"]["status"] == "stocked"
    assert data["activity"]["action"] == "restocked"
    assert data["activity"]["amount"] == 15

    # Verify activity committed to DB
    act = db_session.query(Activity).filter_by(snack_id=snack.id, action="restocked").first()
    assert act is not None
    assert act.amount == 15


def test_member_cannot_restock(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test standard member is forbidden from restocking (403)."""
    snack = Snack(name="Water Bottles", category="drink", quantity=5)
    db_session.add(snack)
    db_session.commit()

    response = auth_client.post(
        f"/snacks/{snack.id}/restock",
        json={"amount": 20},
        headers=member_headers,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_restock_invalid_amount(auth_client: TestClient, admin_headers: dict, db_session: Session):
    """Test non-positive restock amounts are rejected with 422."""
    snack = Snack(name="Peanut Butter Cups", category="sweet", quantity=5)
    db_session.add(snack)
    db_session.commit()

    response = auth_client.post(
        f"/snacks/{snack.id}/restock",
        json={"amount": 0},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_restock_snack_not_found(auth_client: TestClient, admin_headers: dict):
    """Test restocking non-existent snack returns 404."""
    response = auth_client.post("/snacks/99999/restock", json={"amount": 10}, headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SNACK_NOT_FOUND"
