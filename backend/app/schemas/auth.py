from pydantic import BaseModel, EmailStr
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Schema for login credentials."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for successful authentication response returning safe user details and JWT."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
