from typing import Optional
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.connection import get_db
from app.models.user import User
from app.utils.errors import AppException


def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract Bearer token from the Authorization header.
    
    Raises:
        AppException: If header is missing or improperly formatted.
    """
    if not authorization:
        raise AppException(
            status_code=401,
            code="AUTHENTICATION_REQUIRED",
            message="Authorization header is required.",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AppException(
            status_code=401,
            code="INVALID_AUTHORIZATION_HEADER",
            message="Authorization header must follow format: Bearer <token>",
        )

    return parts[1]


def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT token and return the currently authenticated User.
    
    Raises:
        AppException: If token is invalid/expired or user does not exist in the database.
    """
    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AppException(
            status_code=401,
            code="INVALID_TOKEN",
            message="Token payload is missing subject.",
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise AppException(
            status_code=401,
            code="INVALID_TOKEN",
            message="Invalid subject in token payload.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppException(
            status_code=401,
            code="USER_NOT_FOUND",
            message="User associated with token no longer exists.",
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Authorize only users with the 'admin' role.
    
    Raises:
        AppException: If current user does not have administrator privileges.
    """
    if current_user.role != "admin":
        raise AppException(
            status_code=403,
            code="FORBIDDEN",
            message="Administrator privileges required for this operation.",
        )
    return current_user
