from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.activity import PersonalConsumptionHistoryResponse
from app.services.user_history_service import user_history_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me/consumption-history",
    response_model=PersonalConsumptionHistoryResponse,
    summary="Get authenticated user's consumption history",
    description="Retrieve only the authenticated employee's successfully completed snack consumption records.",
)
def get_personal_consumption_history(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(default=10, ge=1, le=100, description="Items per page"),
    start_date: Optional[str] = Query(default=None, description="Filter records starting from this ISO datetime"),
    end_date: Optional[str] = Query(default=None, description="Filter records up to this ISO datetime"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonalConsumptionHistoryResponse:
    """Return consumption records strictly belonging to the calling user."""
    parsed_start = None
    parsed_end = None
    if start_date:
        try:
            cleaned = start_date.replace("Z", "+00:00").replace(" ", "+")
            parsed_start = datetime.fromisoformat(cleaned)
        except ValueError:
            pass
    if end_date:
        try:
            cleaned = end_date.replace("Z", "+00:00").replace(" ", "+")
            parsed_end = datetime.fromisoformat(cleaned)
        except ValueError:
            pass

    return user_history_service.get_personal_consumption_history(
        db=db,
        user=current_user,
        page=page,
        limit=limit,
        start_date=parsed_start,
        end_date=parsed_end,
    )
