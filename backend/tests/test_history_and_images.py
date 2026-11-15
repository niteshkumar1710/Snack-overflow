import io
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.snack import Snack
from app.models.activity import Activity


@pytest.fixture
def member_user(db_session: Session) -> User:
    user = User(
        name="History Tester",
        email="history_tester@example.com",
        password_hash=hash_password("pw"),
        role="member",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session: Session) -> User:
    user = User(
        name="Other Tester",
        email="other_tester@example.com",
        password_hash=hash_password("pw"),
        role="member",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    admin = User(
        name="Admin Image Tester",
        email="admin_img@example.com",
        password_hash=hash_password("pw"),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def member_headers(member_user: User) -> dict:
    token = create_access_token({"sub": str(member_user.id), "email": member_user.email, "role": "member"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_headers(other_user: User) -> dict:
    token = create_access_token({"sub": str(other_user.id), "email": other_user.email, "role": "member"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    token = create_access_token({"sub": str(admin_user.id), "email": admin_user.email, "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_snack(db_session: Session) -> Snack:
    s = Snack(
        name="Chocolate Truffle",
        category="sweet",
        quantity=20,
        low_stock_threshold=5,
        image_url="https://example.com/truffle.jpg",
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


# ---------------------------------------------------------------------------
# Feature One: Personal Consumption History Tests
# ---------------------------------------------------------------------------

def test_unauthenticated_history_rejected(auth_client: TestClient):
    """Unauthenticated request to consumption history returns 401."""
    res = auth_client.get("/users/me/consumption-history")
    assert res.status_code == 401


def test_member_receives_only_own_consumption_history(
    auth_client: TestClient,
    member_headers: dict,
    other_headers: dict,
    member_user: User,
    other_user: User,
    sample_snack: Snack,
    db_session: Session,
):
    """Authenticated user receives only their own consumption records, excluding other users."""
    now = datetime.now(timezone.utc)

    # Member consumes 2 packets
    act1 = Activity(user_id=member_user.id, snack_id=sample_snack.id, action="consumed", amount=2, created_at=now)
    # Other user consumes 5 packets
    act2 = Activity(user_id=other_user.id, snack_id=sample_snack.id, action="consumed", amount=5, created_at=now)
    # Member restocks (should be excluded)
    act3 = Activity(user_id=member_user.id, snack_id=sample_snack.id, action="restocked", amount=10, created_at=now)

    db_session.add_all([act1, act2, act3])
    db_session.commit()

    # Query member history
    res = auth_client.get("/users/me/consumption-history", headers=member_headers)
    assert res.status_code == 200
    data = res.json()

    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["snack_name"] == "Chocolate Truffle"
    assert item["snack_image_url"] == "https://example.com/truffle.jpg"
    assert item["amount"] == 2
    assert data["summary"]["total_consumed_packets"] == 2
    assert data["summary"]["unique_snacks_tried"] == 1


def test_history_pagination_and_date_filtering(
    auth_client: TestClient,
    member_headers: dict,
    member_user: User,
    sample_snack: Snack,
    db_session: Session,
):
    """Test pagination bounds and ISO datetime filtering on personal consumption records."""
    now = datetime.now(timezone.utc)

    for i in range(1, 16):
        act = Activity(
            user_id=member_user.id,
            snack_id=sample_snack.id,
            action="consumed",
            amount=1,
            created_at=now + timedelta(days=i),
        )
        db_session.add(act)
    db_session.commit()

    # Page 1, limit 10
    res_p1 = auth_client.get("/users/me/consumption-history?page=1&limit=10", headers=member_headers)
    assert res_p1.status_code == 200
    p1 = res_p1.json()
    assert len(p1["items"]) == 10
    assert p1["pagination"]["total"] == 15
    assert p1["pagination"]["total_pages"] == 2

    # Date filter: filter items within days 5 to 7 (giving 1-second margin on ends)
    start = (now + timedelta(days=5) - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S")
    end = (now + timedelta(days=7) + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S")
    res_filtered = auth_client.get(
        f"/users/me/consumption-history?start_date={start}&end_date={end}",
        headers=member_headers,
    )
    assert res_filtered.status_code == 200
    filtered_data = res_filtered.json()
    assert len(filtered_data["items"]) == 3


def test_deleted_snack_handled_safely_in_history(
    auth_client: TestClient,
    member_headers: dict,
    member_user: User,
    db_session: Session,
):
    """Archived / deleted snack record does not crash the history endpoint."""
    temp_snack = Snack(name="Doomed Snack", category="drink", quantity=5, low_stock_threshold=2)
    db_session.add(temp_snack)
    db_session.commit()
    db_session.refresh(temp_snack)

    act = Activity(
        user_id=member_user.id,
        snack_id=temp_snack.id,
        action="consumed",
        amount=3,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(act)
    db_session.commit()

    # Query before deletion
    res_before = auth_client.get("/users/me/consumption-history", headers=member_headers)
    assert res_before.status_code == 200
    assert len(res_before.json()["items"]) == 1
    assert res_before.json()["items"][0]["snack_name"] == "Doomed Snack"

    # Delete snack with foreign key cascade
    db_session.delete(temp_snack)
    db_session.commit()

    # Query after deletion: endpoint handles clean state
    res_after = auth_client.get("/users/me/consumption-history", headers=member_headers)
    assert res_after.status_code == 200
    assert res_after.json()["items"] == []


# ---------------------------------------------------------------------------
# Feature Two: Optional Snack Images Tests
# ---------------------------------------------------------------------------

def test_admin_can_create_snack_without_image(auth_client: TestClient, admin_headers: dict):
    """Image upload MUST be optional: snack creation without image succeeds."""
    payload = {
        "name": "Snack No Image",
        "category": "sweet",
        "quantity": 12,
        "low_stock_threshold": 3,
    }
    res = auth_client.post("/snacks", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Snack No Image"
    assert data["image_url"] is None


def test_admin_can_create_snack_with_image(auth_client: TestClient, admin_headers: dict):
    """Snack created with image_url correctly stores and returns it."""
    payload = {
        "name": "Snack With Image",
        "category": "savoury",
        "quantity": 10,
        "low_stock_threshold": 2,
        "image_url": "https://example.com/snack.png",
    }
    res = auth_client.post("/snacks", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["image_url"] == "https://example.com/snack.png"


def test_admin_image_upload_endpoint(auth_client: TestClient, admin_headers: dict):
    """Admin can upload valid JPEG/PNG image file to storage endpoint."""
    # Fake PNG content
    fake_png = io.BytesIO(b"\x89PNG\r\n\x1a\nfakecontent")
    files = {"file": ("test.png", fake_png, "image/png")}

    res = auth_client.post("/snacks/upload-image", files=files, headers=admin_headers)
    assert res.status_code == 200
    assert "image_url" in res.json()
    assert ".png" in res.json()["image_url"]


def test_member_cannot_upload_image(auth_client: TestClient, member_headers: dict):
    """Members are forbidden from accessing admin image upload endpoint."""
    fake_png = io.BytesIO(b"\x89PNG\r\n\x1a\nfakecontent")
    files = {"file": ("test.png", fake_png, "image/png")}

    res = auth_client.post("/snacks/upload-image", files=files, headers=member_headers)
    assert res.status_code == 403


def test_invalid_image_type_rejected(auth_client: TestClient, admin_headers: dict):
    """Unsupported image types (e.g. PDF/TXT) are rejected with 400 Bad Request."""
    fake_txt = io.BytesIO(b"Not an image")
    files = {"file": ("document.pdf", fake_txt, "application/pdf")}

    res = auth_client.post("/snacks/upload-image", files=files, headers=admin_headers)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_admin_can_edit_replace_and_clear_image(
    auth_client: TestClient,
    admin_headers: dict,
    sample_snack: Snack,
):
    """Admin can update an existing snack to replace or clear its image."""
    # Replace image
    res1 = auth_client.patch(
        f"/snacks/{sample_snack.id}",
        json={"image_url": "https://example.com/new_image.jpg"},
        headers=admin_headers,
    )
    assert res1.status_code == 200
    assert res1.json()["image_url"] == "https://example.com/new_image.jpg"

    # Clear image by setting empty string
    res2 = auth_client.patch(
        f"/snacks/{sample_snack.id}",
        json={"image_url": ""},
        headers=admin_headers,
    )
    assert res2.status_code == 200
    assert res2.json()["image_url"] is None
