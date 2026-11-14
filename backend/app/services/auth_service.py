from typing import Tuple
from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.utils.errors import AppException


class AuthService:
    """Service handling user authentication and token issuance."""

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
