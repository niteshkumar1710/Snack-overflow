import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.snack import Snack


@pytest.fixture
def admin_headers(db_session: Session) -> dict:
    """Provides authorization headers for an administrator."""
    admin = User(name="Admin User", email="admin_test@example.com", password_hash=hash_password("pw"), role="admin")
    db_session.add(admin)
    db_session.commit()
    token = create_access_token({"sub": str(admin.id), "email": admin.email, "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_headers(db_session: Session) -> dict:
    """Provides authorization headers for a standard member."""
    member = User(name="Member User", email="member_test@example.com", password_hash=hash_password("pw"), role="member")
    db_session.add(member)
    db_session.commit()
    token = create_access_token({"sub": str(member.id), "email": member.email, "role": "member"})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Snack Creation Tests & Admin Authorization
# ---------------------------------------------------------------------------

def test_admin_create_snack_success(auth_client: TestClient, admin_headers: dict):
    """Test admin can successfully create a new snack with 201 status."""
    payload = {
        "name": "Gluten-Free Granola",
        "category": "healthy-ish",
        "quantity": 15,
        "low_stock_threshold": 5,
    }
    response = auth_client.post("/snacks", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Gluten-Free Granola"
    assert data["category"] == "healthy-ish"
    assert data["quantity"] == 15
    assert data["status"] == "stocked"


def test_member_cannot_create_snack(auth_client: TestClient, member_headers: dict):
    """Test standard member is forbidden (403) from creating snacks."""
    payload = {"name": "Chewy Cookies", "category": "sweet", "quantity": 10}
    response = auth_client.post("/snacks", json=payload, headers=member_headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_unauthenticated_cannot_create_snack(auth_client: TestClient):
    """Test unauthenticated request is rejected (401) from creating snacks."""
    payload = {"name": "Chewy Cookies", "category": "sweet", "quantity": 10}
    response = auth_client.post("/snacks", json=payload)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_create_snack_duplicate_name_rejected(auth_client: TestClient, admin_headers: dict, db_session: Session):
    """Test duplicate snack names are rejected with 409 Conflict."""
    db_session.add(Snack(name="Existing Chips", category="savoury", quantity=10))
    db_session.commit()

    payload = {"name": "existing chips", "category": "savoury", "quantity": 5}
    response = auth_client.post("/snacks", json=payload, headers=admin_headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_SNACK_NAME"


def test_create_snack_invalid_category(auth_client: TestClient, admin_headers: dict):
    """Test invalid category is rejected with 422 validation error."""
    payload = {"name": "Burger", "category": "junk-food", "quantity": 5}
    response = auth_client.post("/snacks", json=payload, headers=admin_headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_snack_negative_quantity(auth_client: TestClient, admin_headers: dict):
    """Test negative quantity is rejected with 422 validation error."""
    payload = {"name": "Negative Snack", "category": "sweet", "quantity": -5}
    response = auth_client.post("/snacks", json=payload, headers=admin_headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Snack Listing, Filtering, Search & Pagination Tests
# ---------------------------------------------------------------------------

def test_get_snacks_pagination(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test server-side pagination metadata and slice limits."""
    for i in range(15):
        db_session.add(Snack(name=f"Snack {i:02d}", category="sweet", quantity=10))
    db_session.commit()

    # Request page 1 with page_size 5
    response = auth_client.get("/snacks?page=1&page_size=5", headers=member_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert data["total_pages"] == 3
    assert len(data["items"]) == 5

    # Request page 3
    response_p3 = auth_client.get("/snacks?page=3&page_size=5", headers=member_headers)
    assert response_p3.status_code == 200
    assert len(response_p3.json()["items"]) == 5


def test_get_snacks_search(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test server-side case-insensitive substring search."""
    db_session.add(Snack(name="Sparkling Peach Water", category="drink", quantity=10))
    db_session.add(Snack(name="Peach Gummy Rings", category="sweet", quantity=10))
    db_session.add(Snack(name="Salted Cashews", category="healthy-ish", quantity=10))
    db_session.commit()

    response = auth_client.get("/snacks?search=peach", headers=member_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    names = [s["name"] for s in data["items"]]
    assert "Sparkling Peach Water" in names
    assert "Peach Gummy Rings" in names
    assert "Salted Cashews" not in names


def test_get_snacks_category_filter(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test server-side category filtering."""
    db_session.add(Snack(name="Iced Tea", category="drink", quantity=10))
    db_session.add(Snack(name="Almonds", category="healthy-ish", quantity=10))
    db_session.commit()

    response = auth_client.get("/snacks?category=drink", headers=member_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Iced Tea"


def test_get_snacks_status_filter(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test server-side status filtering: stocked, running_low, gone."""
    db_session.add(Snack(name="Item Stocked", category="sweet", quantity=20, low_stock_threshold=5))
    db_session.add(Snack(name="Item Running Low", category="sweet", quantity=3, low_stock_threshold=5))
    db_session.add(Snack(name="Item Gone", category="sweet", quantity=0, low_stock_threshold=5))
    db_session.commit()

    # Test 'stocked'
    r_stocked = auth_client.get("/snacks?status=stocked", headers=member_headers)
    assert r_stocked.status_code == 200
    assert r_stocked.json()["total"] == 1
    assert r_stocked.json()["items"][0]["status"] == "stocked"

    # Test 'running_low'
    r_low = auth_client.get("/snacks?status=running_low", headers=member_headers)
    assert r_low.status_code == 200
    assert r_low.json()["total"] == 1
    assert r_low.json()["items"][0]["status"] == "running_low"

    # Test 'gone'
    r_gone = auth_client.get("/snacks?status=gone", headers=member_headers)
    assert r_gone.status_code == 200
    assert r_gone.json()["total"] == 1
    assert r_gone.json()["items"][0]["status"] == "gone"


def test_get_snack_by_id(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test fetching single snack by ID."""
    snack = Snack(name="Trail Mix", category="healthy-ish", quantity=10)
    db_session.add(snack)
    db_session.commit()

    response = auth_client.get(f"/snacks/{snack.id}", headers=member_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Trail Mix"


def test_get_snack_not_found(auth_client: TestClient, member_headers: dict):
    """Test fetching non-existent snack returns 404."""
    response = auth_client.get("/snacks/99999", headers=member_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SNACK_NOT_FOUND"


# ---------------------------------------------------------------------------
# Snack Update & Delete Tests
# ---------------------------------------------------------------------------

def test_admin_update_snack(auth_client: TestClient, admin_headers: dict, db_session: Session):
    """Test administrator updating snack attributes."""
    snack = Snack(name="Original Name", category="sweet", quantity=10, low_stock_threshold=5)
    db_session.add(snack)
    db_session.commit()

    update_payload = {"name": "Updated Name", "quantity": 25}
    response = auth_client.patch(f"/snacks/{snack.id}", json=update_payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["quantity"] == 25
    assert data["status"] == "stocked"


def test_member_cannot_update_snack(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test member role cannot update snack (403)."""
    snack = Snack(name="Static Snack", category="sweet", quantity=10)
    db_session.add(snack)
    db_session.commit()

    response = auth_client.patch(f"/snacks/{snack.id}", json={"quantity": 100}, headers=member_headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_delete_snack(auth_client: TestClient, admin_headers: dict, db_session: Session):
    """Test administrator deleting a snack."""
    snack = Snack(name="To Delete", category="drink", quantity=5)
    db_session.add(snack)
    db_session.commit()

    response = auth_client.delete(f"/snacks/{snack.id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == snack.id

    # Verify deleted from DB
    check = db_session.query(Snack).filter_by(id=snack.id).first()
    assert check is None


def test_member_cannot_delete_snack(auth_client: TestClient, member_headers: dict, db_session: Session):
    """Test member role cannot delete snack (403)."""
    snack = Snack(name="Protected Snack", category="savoury", quantity=10)
    db_session.add(snack)
    db_session.commit()

    response = auth_client.delete(f"/snacks/{snack.id}", headers=member_headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
