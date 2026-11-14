from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models.snack import ALLOWED_CATEGORIES


class SnackBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Unique name of the snack")
    category: str = Field(..., description="Category: sweet, savoury, drink, healthy-ish")
    quantity: int = Field(default=0, ge=0, description="Available stock quantity (must be >= 0)")
    low_stock_threshold: int = Field(default=5, ge=0, description="Low stock threshold (must be >= 0)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Snack name cannot be empty or whitespace only.")
        return trimmed

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in ALLOWED_CATEGORIES:
            allowed = ", ".join(ALLOWED_CATEGORIES)
            raise ValueError(f"Category '{v}' is invalid. Allowed categories are: {allowed}.")
        return normalized


class SnackCreate(SnackBase):
    """Schema for creating a new snack."""
    pass


class SnackUpdate(BaseModel):
    """Schema for updating an existing snack. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    category: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Snack name cannot be empty or whitespace only.")
            return trimmed
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            normalized = v.strip().lower()
            if normalized not in ALLOWED_CATEGORIES:
                allowed = ", ".join(ALLOWED_CATEGORIES)
                raise ValueError(f"Category '{v}' is invalid. Allowed categories are: {allowed}.")
            return normalized
        return v


class SnackResponse(BaseModel):
    """Schema for snack response with derived status and vote count."""
    id: int
    name: str
    category: str
    quantity: int
    low_stock_threshold: int
    status: str
    votes_count: int = 0
    user_has_voted: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedSnacksResponse(BaseModel):
    """Schema for paginated snack list with metadata."""
    items: List[SnackResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
