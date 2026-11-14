from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user with email and password, returning JWT and safe user details."""
    user, token = auth_service.authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password,
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.get("/admin-check")
def admin_verification_check(
    admin_user: User = Depends(require_admin),
):
    """Test endpoint verifying administrator authorization."""
    return {
        "status": "success",
        "message": f"Welcome, Admin {admin_user.name}!",
        "role": admin_user.role,
    }
