from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.database.connection import get_db
from app.models.user import User
from app.schemas.activity import PaginatedActivitiesResponse, ActivityPaginationMeta
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/activities", tags=["Activities"])


@router.get(
    "",
    response_model=PaginatedActivitiesResponse,
    summary="Get paginated activity log",
    description="Retrieve activity history ordered newest first. Restricted to administrators.",
)
def get_activities(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(default=10, ge=1, le=100, description="Items per page (max 100)"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retrieve paginated activity log.
    
    Protected by `require_admin`. Non-admin members receive 403 Forbidden.
    Unauthenticated callers receive 401 Unauthorized.
    """
    items, total, total_pages = ActivityService.get_activities(
        db=db,
        page=page,
        limit=limit,
    )

    return PaginatedActivitiesResponse(
        items=items,
        pagination=ActivityPaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
        ),
    )
