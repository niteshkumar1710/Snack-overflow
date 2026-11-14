from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.database.connection import get_db
from app.models.user import User
from app.schemas.snack import (
    SnackCreate,
    SnackUpdate,
    SnackResponse,
    PaginatedSnacksResponse,
)
from app.services.snack_service import snack_service

router = APIRouter(prefix="/snacks", tags=["Snacks"])


@router.get("", response_model=PaginatedSnacksResponse)
def get_snacks(
    search: Optional[str] = Query(None, description="Search by snack name"),
    category: Optional[str] = Query(None, description="Filter by category (sweet, savoury, drink, healthy-ish)"),
    status: Optional[str] = Query(None, description="Filter by derived status (stocked, running_low, gone)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedSnacksResponse:
    """Retrieve a paginated list of snacks with server-side filtering, searching, and pagination."""
    items, total, total_pages = snack_service.get_snacks(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        status=status,
    )
    return PaginatedSnacksResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{snack_id}", response_model=SnackResponse)
def get_snack(
    snack_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SnackResponse:
    """Retrieve details of a single snack by its unique ID."""
    return snack_service.get_snack_by_id(db=db, snack_id=snack_id)


@router.post("", response_model=SnackResponse, status_code=status.HTTP_201_CREATED)
def create_snack(
    payload: SnackCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> SnackResponse:
    """Create a new pantry snack (Administrator only)."""
    return snack_service.create_snack(db=db, snack_in=payload)


@router.patch("/{snack_id}", response_model=SnackResponse)
def update_snack(
    snack_id: int,
    payload: SnackUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> SnackResponse:
    """Update an existing snack's details (Administrator only)."""
    return snack_service.update_snack(db=db, snack_id=snack_id, snack_in=payload)


@router.delete("/{snack_id}")
def delete_snack(
    snack_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a snack and its related activity/vote records (Administrator only)."""
    snack_name = snack_service.delete_snack(db=db, snack_id=snack_id)
    return {
        "message": f"Snack '{snack_name}' was deleted successfully.",
        "id": snack_id,
    }
