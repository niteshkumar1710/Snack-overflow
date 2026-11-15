from typing import Optional
from fastapi import APIRouter, Depends, Query, Header, status
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
from app.schemas.activity import (
    ConsumeRequest,
    RestockRequest,
    ConsumptionResponse,
    RestockResponse,
)
from app.schemas.vote import VoteResponse
from app.schemas.summary import PantrySummaryResponse
from app.services.snack_service import snack_service
from app.services.consumption_service import consumption_service
from app.services.voting_service import voting_service
from app.services.summary_service import summary_service
from app.services.idempotency_service import IdempotencyService

router = APIRouter(prefix="/snacks", tags=["Snacks"])


@router.get("/summary", response_model=PantrySummaryResponse)
def get_pantry_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PantrySummaryResponse:
    """Retrieve pantry dashboard metrics: stock status counts and Snack of the Week."""
    return summary_service.get_pantry_summary(db=db)


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
        current_user=current_user,
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
    return snack_service.get_snack_by_id(db=db, snack_id=snack_id, current_user=current_user)


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


@router.post("/{snack_id}/consume", response_model=ConsumptionResponse)
def consume_snack(
    snack_id: int,
    payload: ConsumeRequest = ConsumeRequest(amount=1),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConsumptionResponse:
    """Atomically consume one or more packets of a snack using database-level conditional updates.

    Supports optional Idempotency-Key header to prevent duplicate execution across retries.
    """
    idemp_record = None
    if idempotency_key:
        fingerprint = IdempotencyService.generate_fingerprint(
            method="POST",
            path=f"/snacks/{snack_id}/consume",
            payload={"amount": payload.amount},
        )
        idemp_record, cached_response = IdempotencyService.start_operation(
            db=db,
            user_id=current_user.id,
            key=idempotency_key,
            fingerprint=fingerprint,
        )
        if cached_response is not None:
            return ConsumptionResponse(**cached_response)

    try:
        snack_resp, activity_resp = consumption_service.consume_snack(
            db=db,
            snack_id=snack_id,
            user=current_user,
            amount=payload.amount,
        )
        response_obj = ConsumptionResponse(
            message=f"Successfully consumed {payload.amount} packet(s) of '{snack_resp.name}'.",
            snack=snack_resp,
            activity=activity_resp,
        )

        if idemp_record:
            IdempotencyService.complete_operation(
                db=db,
                record_id=idemp_record.id,
                status_code=200,
                response_data=response_obj.model_dump(mode="json"),
            )

        return response_obj
    except Exception:
        if idemp_record:
            IdempotencyService.fail_operation(db=db, record_id=idemp_record.id)
        raise


@router.post("/{snack_id}/restock", response_model=RestockResponse)
def restock_snack(
    snack_id: int,
    payload: RestockRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RestockResponse:
    """Restock snack quantity and log the restocked activity (Administrator only).

    Supports optional Idempotency-Key header to prevent duplicate execution across retries.
    """
    idemp_record = None
    if idempotency_key:
        fingerprint = IdempotencyService.generate_fingerprint(
            method="POST",
            path=f"/snacks/{snack_id}/restock",
            payload={"amount": payload.amount},
        )
        idemp_record, cached_response = IdempotencyService.start_operation(
            db=db,
            user_id=admin.id,
            key=idempotency_key,
            fingerprint=fingerprint,
        )
        if cached_response is not None:
            return RestockResponse(**cached_response)

    try:
        snack_resp, activity_resp = consumption_service.restock_snack(
            db=db,
            snack_id=snack_id,
            admin=admin,
            amount=payload.amount,
        )
        response_obj = RestockResponse(
            message=f"Successfully restocked {payload.amount} packet(s) of '{snack_resp.name}'.",
            snack=snack_resp,
            activity=activity_resp,
        )

        if idemp_record:
            IdempotencyService.complete_operation(
                db=db,
                record_id=idemp_record.id,
                status_code=200,
                response_data=response_obj.model_dump(mode="json"),
            )

        return response_obj
    except Exception:
        if idemp_record:
            IdempotencyService.fail_operation(db=db, record_id=idemp_record.id)
        raise


@router.post("/{snack_id}/vote", response_model=VoteResponse)
def vote_for_snack(
    snack_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VoteResponse:
    """Cast a vote for a pantry snack. Enforces one vote per user per snack."""
    new_count = voting_service.cast_vote(db=db, user=current_user, snack_id=snack_id)
    return VoteResponse(
        message="Vote recorded successfully.",
        snack_id=snack_id,
        votes_count=new_count,
        has_voted=True,
    )


@router.delete("/{snack_id}/vote", response_model=VoteResponse)
def remove_vote_for_snack(
    snack_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VoteResponse:
    """Remove the authenticated user's vote for a pantry snack."""
    new_count = voting_service.remove_vote(db=db, user=current_user, snack_id=snack_id)
    return VoteResponse(
        message="Vote removed successfully.",
        snack_id=snack_id,
        votes_count=new_count,
        has_voted=False,
    )
