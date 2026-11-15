import math
from typing import Tuple, List
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.activity import Activity


class ActivityService:
    """Service handling activity log queries with database-level pagination."""

    @staticmethod
    def get_activities(
        db: Session,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[Activity], int, int]:
        """Fetch a paginated list of activity entries ordered newest first.

        Eagerly loads related User and Snack entities via joinedload to prevent
        N+1 SELECT queries.

        Args:
            db: Active database session.
            page: 1-indexed page number.
            limit: Maximum items per page.

        Returns:
            Tuple of (list_of_activities, total_count, total_pages)
        """
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10

        # Total count calculated efficiently on the database side
        total = db.query(func.count(Activity.id)).scalar() or 0
        total_pages = math.ceil(total / limit) if total > 0 else 0

        offset = (page - 1) * limit

        # Database-level pagination via offset & limit, ordered newest first (created_at DESC, id DESC)
        items = (
            db.query(Activity)
            .options(joinedload(Activity.user), joinedload(Activity.snack))
            .order_by(Activity.created_at.desc(), Activity.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return items, total, total_pages
