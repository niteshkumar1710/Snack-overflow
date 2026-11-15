from typing import Tuple
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserRegisterRequest
from app.utils.errors import AppException


class AuthService:
    """Service handling user authentication, registration, and token issuance."""

    @staticmethod
    def register_user(db: Session, payload: UserRegisterRequest) -> User:
        """Register a new user account.

        Security Requirements:
        - Email uniqueness checked at both Python level and DB unique constraint.
        - Passwords securely hashed with bcrypt.
        - Role is ALWAYS hardcoded to 'member' (never client-controlled).
        - Returns safe User entity without password hash.
        """
        normalized_email = payload.email.strip().lower()

        # Check existing user by email
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise AppException(
                status_code=409,
                code="EMAIL_ALREADY_EXISTS",
                message=f"An account with email '{normalized_email}' already exists.",
            )

        hashed_pw = hash_password(payload.password)

        new_user = User(
            name=payload.name.strip(),
            email=normalized_email,
            password_hash=hashed_pw,
            role="member",  # Strictly enforced server-side
        )

        db.add(new_user)
        try:
            db.commit()
            db.refresh(new_user)
        except IntegrityError:
            db.rollback()
            raise AppException(
                status_code=409,
                code="EMAIL_ALREADY_EXISTS",
                message=f"An account with email '{normalized_email}' already exists.",
            )

        return new_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Tuple[User, str]:
        """Authenticate a user by email and password, returning the user and a JWT access token.
        
        Raises:
            AppException: 401 if credentials do not match or user is not found.
        """
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user or not verify_password(password, user.password_hash):
            raise AppException(
                status_code=401,
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
        access_token = create_access_token(data=token_data)
        return user, access_token


auth_service = AuthService()
