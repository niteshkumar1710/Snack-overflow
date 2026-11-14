from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.snack import Snack
from app.models.vote import Vote
from app.schemas.snack import SnackResponse
from app.schemas.summary import PantrySummaryResponse


class SummaryService:
    """Service calculating pantry inventory metrics and Snack of the Week."""

    @staticmethod
    def get_pantry_summary(db: Session) -> PantrySummaryResponse:
        """Calculate inventory counts across derived statuses and determine Snack of the Week.
        
        Tie-breaking rule for Snack of the Week:
        1. Highest number of votes (COUNT(votes.id) DESC).
        2. Higher available stock (Snack.quantity DESC) so employees can enjoy the popular snack.
        3. Alphabetical order by snack name (Snack.name ASC).
        """
        # Status counts based on rules:
        # - stocked: quantity > low_stock_threshold
        # - running_low: quantity > 0 and quantity <= low_stock_threshold
        # - gone: quantity == 0
        stocked_count = db.query(Snack).filter(Snack.quantity > Snack.low_stock_threshold).count()
        running_low_count = (
            db.query(Snack)
            .filter(Snack.quantity > 0, Snack.quantity <= Snack.low_stock_threshold)
            .count()
        )
        gone_count = db.query(Snack).filter(Snack.quantity == 0).count()
        total_snacks = stocked_count + running_low_count + gone_count

        # Subquery counting votes per snack
        vote_counts_sub = (
            db.query(
                Snack.id.label("snack_id"),
                func.count(Vote.id).label("vote_count"),
            )
            .outerjoin(Vote, Vote.snack_id == Snack.id)
            .group_by(Snack.id)
            .subquery()
        )

        # Retrieve top voted snack with deterministic tie-breaking
        top_row = (
            db.query(Snack, vote_counts_sub.c.vote_count)
            .join(vote_counts_sub, Snack.id == vote_counts_sub.c.snack_id)
            .order_by(
                vote_counts_sub.c.vote_count.desc(),
                Snack.quantity.desc(),  # Tie-breaker 1: greater stock
                Snack.name.asc(),       # Tie-breaker 2: alphabetical
            )
            .first()
        )

        snack_of_the_week: Optional[SnackResponse] = None
        if top_row:
            snack, vote_count = top_row
            snack_of_the_week = SnackResponse(
                id=snack.id,
                name=snack.name,
                category=snack.category,
                quantity=snack.quantity,
                low_stock_threshold=snack.low_stock_threshold,
                status=snack.status,
                votes_count=vote_count,
                created_at=snack.created_at,
                updated_at=snack.updated_at,
            )

        return PantrySummaryResponse(
            stocked_count=stocked_count,
            running_low_count=running_low_count,
            gone_count=gone_count,
            total_snacks=total_snacks,
            snack_of_the_week=snack_of_the_week,
        )


summary_service = SummaryService()
