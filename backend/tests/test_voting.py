import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.snack import Snack
from app.models.vote import Vote


@pytest.fixture
def member_user(db_session: Session) -> User:
    member = User(
        name="Voter One",
        email="voter1@example.com",
        password_hash=hash_password("password123"),
        role="member",
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    return member


@pytest.fixture
def member_headers(member_user: User) -> dict:
    token = create_access_token({"sub": str(member_user.id), "email": member_user.email, "role": member_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_member_user(db_session: Session) -> User:
    member2 = User(
        name="Voter Two",
        email="voter2@example.com",
        password_hash=hash_password("password123"),
        role="member",
    )
    db_session.add(member2)
    db_session.commit()
    db_session.refresh(member2)
    return member2


@pytest.fixture
def second_member_headers(second_member_user: User) -> dict:
    token = create_access_token({"sub": str(second_member_user.id), "email": second_member_user.email, "role": second_member_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session: Session) -> User:
    admin = User(
        name="Admin Voter",
        email="admin_voter@example.com",
        password_hash=hash_password("password123"),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    token = create_access_token({"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_snack(db_session: Session) -> Snack:
    snack = Snack(
        name="Roasted Almonds",
        category="healthy-ish",
        quantity=20,
        low_stock_threshold=5,
    )
    db_session.add(snack)
    db_session.commit()
    db_session.refresh(snack)
    return snack


# ---------------------------------------------------------------------------
# POST /snacks/{snack_id}/vote Tests
# ---------------------------------------------------------------------------

def test_cast_vote_success(
    auth_client: TestClient,
    member_headers: dict,
    member_user: User,
    sample_snack: Snack,
    db_session: Session,
):
    """Test authenticated member casting a vote for an existing snack."""
    response = auth_client.post(f"/snacks/{sample_snack.id}/vote", headers=member_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Vote recorded successfully."
    assert data["snack_id"] == sample_snack.id
    assert data["votes_count"] == 1
    assert data["has_voted"] is True

    # Verify vote record is committed to database
    db_vote = (
        db_session.query(Vote)
        .filter_by(user_id=member_user.id, snack_id=sample_snack.id)
        .first()
    )
    assert db_vote is not None


def test_cast_vote_duplicate_returns_409(
    auth_client: TestClient,
    member_headers: dict,
    sample_snack: Snack,
):
    """Test duplicate voting attempts for the same snack trigger HTTP 409 ALREADY_VOTED."""
    # First vote succeeds
    first_res = auth_client.post(f"/snacks/{sample_snack.id}/vote", headers=member_headers)
    assert first_res.status_code == 200

    # Second vote must be rejected by database unique constraint
    second_res = auth_client.post(f"/snacks/{sample_snack.id}/vote", headers=member_headers)
    assert second_res.status_code == 409
    data = second_res.json()
    assert data["error"]["code"] == "ALREADY_VOTED"
    assert "already voted" in data["error"]["message"].lower()


def test_cast_vote_multiple_users(
    auth_client: TestClient,
    member_headers: dict,
    second_member_headers: dict,
    sample_snack: Snack,
    db_session: Session,
):
    """Test multiple users voting for the same snack increments vote tally properly."""
    res1 = auth_client.post(f"/snacks/{sample_snack.id}/vote", headers=member_headers)
    assert res1.status_code == 200
    assert res1.json()["votes_count"] == 1

    res2 = auth_client.post(f"/snacks/{sample_snack.id}/vote", headers=second_member_headers)
    assert res2.status_code == 200
    assert res2.json()["votes_count"] == 2

    # Database count must be 2
    count = db_session.query(Vote).filter_by(snack_id=sample_snack.id).count()
    assert count == 2


def test_cast_vote_nonexistent_snack_returns_404(
    auth_client: TestClient,
    member_headers: dict,
):
    """Test voting for a non-existent snack ID returns HTTP 404."""
    response = auth_client.post("/snacks/999999/vote", headers=member_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SNACK_NOT_FOUND"


def test_cast_vote_unauthenticated_returns_401(
    auth_client: TestClient,
    sample_snack: Snack,
):
    """Test voting without authentication token returns HTTP 401."""
    response = auth_client.post(f"/snacks/{sample_snack.id}/vote")
    assert response.status_code == 401


def test_admin_can_also_vote(
    auth_client: TestClient,
    admin_headers: dict,
    sample_snack: Snack,
):
    """Test administrator can participate in voting."""
    response = auth_client.post(f"/snacks/{sample_snack.id}/vote", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["has_voted"] is True
    assert response.json()["votes_count"] == 1


# ---------------------------------------------------------------------------
# DELETE /snacks/{snack_id}/vote Tests
# ---------------------------------------------------------------------------

def test_remove_vote_success(
    auth_client: TestClient,
    member_headers: dict,
    member_user: User,
    sample_snack: Snack,
    db_session: Session,
):
    """Test user successfully removing their previously cast vote."""
    # Cast vote first
    auth_client.post(f"/snacks/{sample_snack.id}/vote", headers=member_headers)

    # Remove vote
    response = auth_client.delete(f"/snacks/{sample_snack.id}/vote", headers=member_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Vote removed successfully."
    assert data["snack_id"] == sample_snack.id
    assert data["votes_count"] == 0
    assert data["has_voted"] is False

    # Verify vote record is deleted from DB
    db_vote = (
        db_session.query(Vote)
        .filter_by(user_id=member_user.id, snack_id=sample_snack.id)
        .first()
    )
    assert db_vote is None


def test_remove_vote_when_not_voted_returns_404(
    auth_client: TestClient,
    member_headers: dict,
    sample_snack: Snack,
):
    """Test removing a vote when the user never voted returns HTTP 404 VOTE_NOT_FOUND."""
    response = auth_client.delete(f"/snacks/{sample_snack.id}/vote", headers=member_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "VOTE_NOT_FOUND"


def test_remove_vote_nonexistent_snack_returns_404(
    auth_client: TestClient,
    member_headers: dict,
):
    """Test removing a vote for a non-existent snack returns HTTP 404."""
    response = auth_client.delete("/snacks/999999/vote", headers=member_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SNACK_NOT_FOUND"


def test_remove_vote_does_not_affect_other_user_vote(
    auth_client: TestClient,
    member_headers: dict,
    second_member_headers: dict,
    second_member_user: User,
    sample_snack: Snack,
    db_session: Session,
):
    """Test removing user 1's vote does not delete or affect user 2's vote."""
    auth_client.post(f"/snacks/{sample_snack.id}/vote", headers=member_headers)
    auth_client.post(f"/snacks/{sample_snack.id}/vote", headers=second_member_headers)

    # User 1 removes their vote
    response = auth_client.delete(f"/snacks/{sample_snack.id}/vote", headers=member_headers)
    assert response.status_code == 200
    assert response.json()["votes_count"] == 1

    # User 2's vote must still exist
    vote2 = (
        db_session.query(Vote)
        .filter_by(user_id=second_member_user.id, snack_id=sample_snack.id)
        .first()
    )
    assert vote2 is not None


def test_remove_vote_unauthenticated_returns_401(
    auth_client: TestClient,
    sample_snack: Snack,
):
    """Test unauthenticated DELETE vote request returns HTTP 401."""
    response = auth_client.delete(f"/snacks/{sample_snack.id}/vote")
    assert response.status_code == 401
