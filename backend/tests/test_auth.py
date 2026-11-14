from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User
from seed import seed_database


def test_login_successful(auth_client: TestClient, db_session: Session):
    """Test successful authentication returns JWT token and safe user details."""
    user = User(
        name="John Doe",
        email="john@example.com",
        password_hash=hash_password("Password@123"),
        role="member",
    )
    db_session.add(user)
    db_session.commit()

    response = auth_client.post(
        "/auth/login",
        json={"email": "john@example.com", "password": "Password@123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "john@example.com"
    assert data["user"]["role"] == "member"
    # Crucial security requirement: password hash must NEVER be returned
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_login_incorrect_password(auth_client: TestClient, db_session: Session):
    """Test login failure with wrong password returns 401 and consistent error format."""
    user = User(
        name="Jane Doe",
        email="jane@example.com",
        password_hash=hash_password("CorrectPass123"),
        role="member",
    )
    db_session.add(user)
    db_session.commit()

    response = auth_client.post(
        "/auth/login",
        json={"email": "jane@example.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email(auth_client: TestClient):
    """Test login failure with non-existent email returns 401."""
    response = auth_client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "AnyPassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_missing_token_rejected(auth_client: TestClient):
    """Test protected endpoint rejects requests without Authorization header with 401."""
    response = auth_client.get("/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_invalid_token_rejected(auth_client: TestClient):
    """Test protected endpoint rejects malformed or fabricated JWT tokens with 401."""
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = auth_client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_expired_token_rejected(auth_client: TestClient, db_session: Session):
    """Test protected endpoint rejects expired JWT tokens with 401."""
    user = User(
        name="Tim Traveler",
        email="tim@example.com",
        password_hash=hash_password("Password123"),
        role="member",
    )
    db_session.add(user)
    db_session.commit()

    expired_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )

    headers = {"Authorization": f"Bearer {expired_token}"}
    response = auth_client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "TOKEN_EXPIRED"


def test_admin_access_allowed_for_admin(auth_client: TestClient, db_session: Session):
    """Test admin role can access admin-protected endpoints."""
    admin = User(
        name="Chief Admin",
        email="admin_chief@example.com",
        password_hash=hash_password("AdminPass123"),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()

    token = create_access_token(data={"sub": str(admin.id), "email": admin.email, "role": admin.role})
    headers = {"Authorization": f"Bearer {token}"}

    response = auth_client.get("/auth/admin-check", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["role"] == "admin"


def test_admin_access_rejected_for_member(auth_client: TestClient, db_session: Session):
    """Test member role is rejected with 403 Forbidden on admin-protected endpoints."""
    member = User(
        name="Regular Member",
        email="reg_member@example.com",
        password_hash=hash_password("MemberPass123"),
        role="member",
    )
    db_session.add(member)
    db_session.commit()

    token = create_access_token(data={"sub": str(member.id), "email": member.email, "role": member.role})
    headers = {"Authorization": f"Bearer {token}"}

    response = auth_client.get("/auth/admin-check", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "FORBIDDEN"
    assert "Administrator privileges required" in data["error"]["message"]


def test_seed_script_idempotency(db_session: Session):
    """Test seed script runs successfully and is safe to execute repeatedly without duplicating data."""
    # Run first time
    seed_database(db_session)
    users_count_1 = db_session.query(User).count()
    assert users_count_1 == 2  # demo admin and demo member

    admin_user = db_session.query(User).filter_by(email="admin@example.com").first()
    member_user = db_session.query(User).filter_by(email="member@example.com").first()
    assert admin_user is not None and admin_user.role == "admin"
    assert member_user is not None and member_user.role == "member"

    # Run second time to verify idempotency
    seed_database(db_session)
    users_count_2 = db_session.query(User).count()
    assert users_count_2 == 2  # still exactly 2 users
