from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
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
    assert data["error"]["message"] == "Invalid email or password."


def test_login_unknown_email(auth_client: TestClient):
    """Test login with non-existent email returns 401 and generic error to prevent email enumeration."""
    response = auth_client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "SomePassword123"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_missing_token_rejected(auth_client: TestClient):
    """Test accessing protected endpoint without Authorization header returns 401."""
    response = auth_client.get("/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert "Authorization header is required" in data["error"]["message"]


def test_invalid_token_rejected(auth_client: TestClient):
    """Test accessing protected endpoint with forged/tampered JWT returns 401."""
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = auth_client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_expired_token_rejected(auth_client: TestClient, db_session: Session):
    """Test expired JWT token is rejected with 401 TOKEN_EXPIRED."""
    user = User(
        name="Expiring User",
        email="expire@example.com",
        password_hash=hash_password("Password123"),
        role="member",
    )
    db_session.add(user)
    db_session.commit()

    # Generate token that expired 1 hour ago
    expired_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=timedelta(hours=-1),
    )
    headers = {"Authorization": f"Bearer {expired_token}"}

    response = auth_client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "TOKEN_EXPIRED"
    assert "expired" in data["error"]["message"].lower()


def test_admin_access_allowed_for_admin(auth_client: TestClient, db_session: Session):
    """Test admin role can access admin-protected endpoints."""
    admin = User(
        name="Super Admin",
        email="superadmin@example.com",
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


# ---------------------------------------------------------------------------
# Bonus Stage 1: Registration Endpoint Tests
# ---------------------------------------------------------------------------

def test_register_successful(auth_client: TestClient, db_session: Session):
    """Test public registration creates new user with role='member' and returns 201 Created."""
    payload = {
        "name": "Alice Wonder",
        "email": "alice@example.com",
        "password": "StrongPassword123!",
    }
    response = auth_client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Alice Wonder"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "member"
    assert "id" in data
    # Security: Password and password hash must never be in response
    assert "password" not in data
    assert "password_hash" not in data

    # Verify database record and password hashing
    user_in_db = db_session.query(User).filter_by(email="alice@example.com").first()
    assert user_in_db is not None
    assert user_in_db.name == "Alice Wonder"
    assert user_in_db.role == "member"
    assert user_in_db.password_hash != "StrongPassword123!"
    assert verify_password("StrongPassword123!", user_in_db.password_hash) is True


def test_register_duplicate_email_rejected(auth_client: TestClient, db_session: Session):
    """Test registering with an existing email returns HTTP 409 Conflict."""
    existing_user = User(
        name="Existing User",
        email="existing@example.com",
        password_hash=hash_password("Pass123456"),
        role="member",
    )
    db_session.add(existing_user)
    db_session.commit()

    payload = {
        "name": "Imposter User",
        "email": "existing@example.com",
        "password": "NewPassword123!",
    }
    response = auth_client.post("/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "EMAIL_ALREADY_EXISTS"
    assert "already exists" in data["error"]["message"].lower()


def test_register_invalid_email_format(auth_client: TestClient):
    """Test registering with an invalid email returns HTTP 422 validation error."""
    payload = {
        "name": "Invalid Email",
        "email": "not-an-email",
        "password": "Password123!",
    }
    response = auth_client.post("/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_register_empty_name(auth_client: TestClient):
    """Test registering with empty or whitespace-only name returns HTTP 422 validation error."""
    payload = {
        "name": "   ",
        "email": "emptyname@example.com",
        "password": "Password123!",
    }
    response = auth_client.post("/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_register_weak_short_password(auth_client: TestClient):
    """Test registering with a password shorter than 8 characters returns HTTP 422."""
    payload = {
        "name": "Short Pass",
        "email": "shortpass@example.com",
        "password": "short",
    }
    response = auth_client.post("/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_register_cannot_self_assign_admin_role(auth_client: TestClient, db_session: Session):
    """Test client cannot escalate privileges by providing role='admin' in payload."""
    payload = {
        "name": "Hacker WannaBe",
        "email": "hacker@example.com",
        "password": "SecretPassword123!",
        "role": "admin",  # Attacker attempt
    }
    response = auth_client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    # Security: Server must ignore any client-sent role and assign 'member'
    assert data["role"] == "member"

    user_in_db = db_session.query(User).filter_by(email="hacker@example.com").first()
    assert user_in_db.role == "member"


def test_registered_user_can_login_immediately(auth_client: TestClient, db_session: Session):
    """Test end-to-end flow: register a new account, then immediately login with credentials."""
    # 1. Register
    reg_payload = {
        "name": "New Employee",
        "email": "newbie@example.com",
        "password": "NewEmployee@123",
    }
    reg_res = auth_client.post("/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    # 2. Login
    login_payload = {
        "email": "newbie@example.com",
        "password": "NewEmployee@123",
    }
    login_res = auth_client.post("/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == "newbie@example.com"
    assert login_data["user"]["role"] == "member"

    # 3. Access protected /auth/me
    token = login_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_res = auth_client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "New Employee"


def test_existing_admin_and_member_login_still_works(auth_client: TestClient, db_session: Session):
    """Test regression: existing seeded admin and member accounts continue to authenticate."""
    seed_database(db_session)

    # Admin login
    admin_login = auth_client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "Admin@123"},
    )
    assert admin_login.status_code == 200
    assert admin_login.json()["user"]["role"] == "admin"

    # Member login
    member_login = auth_client.post(
        "/auth/login",
        json={"email": "member@example.com", "password": "Member@123"},
    )
    assert member_login.status_code == 200
    assert member_login.json()["user"]["role"] == "member"
