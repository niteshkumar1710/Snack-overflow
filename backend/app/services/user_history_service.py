import math
from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.activity import Activity
from app.models.snack import Snack
from app.models.user import User
from app.schemas.activity import (
    PersonalConsumptionItem,
    PersonalConsumptionSummary,
    ActivityPaginationMeta,
    PersonalConsumptionHistoryResponse,
)


class UserHistoryService:
    """Service handling personal consumption history queries with pagination and date filtering."""

    @staticmethod
    def get_personal_consumption_history(
        db: Session,
        user: User,
        page: int = 1,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PersonalConsumptionHistoryResponse:
        """Fetch strictly authenticated user's consumption records ordered newest first.
        
        Handles deleted snacks safely without crashing using outer joins.
        """
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10

        base_filter = [
            Activity.user_id == user.id,
            Activity.action == "consumed",
        ]

        if start_date:
            base_filter.append(Activity.created_at >= start_date)
        if end_date:
            base_filter.append(Activity.created_at <= end_date)

        # 1. Total summary metrics for this user
        total_packets = (
            db.query(func.coalesce(func.sum(Activity.amount), 0))
            .filter(*base_filter)
            .scalar()
            or 0
        )
        unique_snacks = (
            db.query(func.count(func.distinct(Activity.snack_id)))
            .filter(*base_filter)
            .scalar()
            or 0
        )

        total_records = db.query(func.count(Activity.id)).filter(*base_filter).scalar() or 0
        total_pages = math.ceil(total_records / limit) if total_records > 0 else 0

        # 2. Paginated rows ordered newest first
        offset = (page - 1) * limit
        activities = (
            db.query(Activity)
            .outerjoin(Snack, Activity.snack_id == Snack.id)
            .options(joinedload(Activity.snack))
            .filter(*base_filter)
            .order_by(Activity.created_at.desc(), Activity.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items: List[PersonalConsumptionItem] = []
        for act in activities:
            snack_name = act.snack.name if act.snack else f"Snack #{act.snack_id} (Archived)"
            snack_image = act.snack.image_url if act.snack else None

            items.append(
                PersonalConsumptionItem(
                    activity_id=act.id,
                    snack_id=act.snack_id,
                    snack_name=snack_name,
                    snack_image_url=snack_image,
                    amount=act.amount,
                    consumed_at=act.created_at,
                )
            )

        return PersonalConsumptionHistoryResponse(
            items=items,
            summary=PersonalConsumptionSummary(
                total_consumed_packets=int(total_packets),
                unique_snacks_tried=int(unique_snacks),
            ),
            pagination=ActivityPaginationMeta(
                page=page,
                limit=limit,
                total=total_records,
                total_pages=total_pages,
            ),
        )


user_history_service = UserHistoryService()
