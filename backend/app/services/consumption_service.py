from typing import Tuple
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.models.snack import Snack
from app.models.activity import Activity
from app.models.vote import Vote
from app.models.user import User
from app.schemas.snack import SnackResponse
from app.schemas.activity import ActivityResponse
from app.utils.errors import AppException


class ConsumptionService:
    """Service implementing atomic stock consumption and restocking transactions."""

    @staticmethod
    def consume_snack(
        db: Session,
        snack_id: int,
        user: User,
        amount: int = 1,
    ) -> Tuple[SnackResponse, ActivityResponse]:
        """Atomically consume snack quantity using a database-level conditional update.
        
        Guarantees that:
        1. Stock is decremented directly in SQL with 'quantity >= :amount'.
        2. Stock never drops below zero.
        3. Stock update and activity log record occur in the same transaction.
        4. If stock is insufficient, returns HTTP 409 Conflict.
        """
        if amount <= 0:
            raise AppException(
                status_code=422,
                code="INVALID_AMOUNT",
                message="Consumption amount must be a positive integer greater than or equal to 1.",
            )

        # Database-level atomic conditional update
        # This prevents the classic read-then-write race condition by relying on
        # database row-level locks during WHERE evaluation.
        update_stmt = text("""
            UPDATE snacks
            SET quantity = quantity - :amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :snack_id
              AND quantity >= :amount
            RETURNING id, name, category, quantity, low_stock_threshold, image_url, created_at, updated_at;
        """)

        result = db.execute(update_stmt, {"snack_id": snack_id, "amount": amount})
        row = result.fetchone()

        # If no row was updated, determine the exact root cause
        if not row:
            snack_exists = db.query(Snack.id).filter(Snack.id == snack_id).first()
            if not snack_exists:
                raise AppException(
                    status_code=404,
                    code="SNACK_NOT_FOUND",
                    message=f"Snack with ID {snack_id} was not found.",
                )
            # Snack exists but quantity was insufficient for the requested amount
            raise AppException(
                status_code=409,
                code="INSUFFICIENT_STOCK",
                message="Someone beat you to the last packet!",
            )

        # In the exact same transaction, record the activity
        activity = Activity(
            user_id=user.id,
            snack_id=snack_id,
            action="consumed",
            amount=amount,
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)

        # Derive status
        qty = row.quantity
        thresh = row.low_stock_threshold
        if qty == 0:
            derived_status = "gone"
        elif qty <= thresh:
            derived_status = "running_low"
        else:
            derived_status = "stocked"

        votes_count = db.query(func.count(Vote.id)).filter(Vote.snack_id == snack_id).scalar() or 0

        snack_resp = SnackResponse(
            id=row.id,
            name=row.name,
            category=row.category,
            quantity=row.quantity,
            low_stock_threshold=row.low_stock_threshold,
            status=derived_status,
            image_url=getattr(row, "image_url", None),
            votes_count=votes_count,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

        activity_resp = ActivityResponse.model_validate(activity)
        return snack_resp, activity_resp

    @staticmethod
    def restock_snack(
        db: Session,
        snack_id: int,
        admin: User,
        amount: int,
    ) -> Tuple[SnackResponse, ActivityResponse]:
        """Atomically restock snack quantity and log the restocked activity (Admin only)."""
        if amount <= 0:
            raise AppException(
                status_code=422,
                code="INVALID_AMOUNT",
                message="Restock amount must be a positive integer greater than or equal to 1.",
            )

        update_stmt = text("""
            UPDATE snacks
            SET quantity = quantity + :amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :snack_id
            RETURNING id, name, category, quantity, low_stock_threshold, image_url, created_at, updated_at;
        """)

        result = db.execute(update_stmt, {"snack_id": snack_id, "amount": amount})
        row = result.fetchone()

        if not row:
            raise AppException(
                status_code=404,
                code="SNACK_NOT_FOUND",
                message=f"Snack with ID {snack_id} was not found.",
            )

        # In the exact same transaction, record the activity
        activity = Activity(
            user_id=admin.id,
            snack_id=snack_id,
            action="restocked",
            amount=amount,
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)

        qty = row.quantity
        thresh = row.low_stock_threshold
        if qty == 0:
            derived_status = "gone"
        elif qty <= thresh:
            derived_status = "running_low"
        else:
            derived_status = "stocked"

        votes_count = db.query(func.count(Vote.id)).filter(Vote.snack_id == snack_id).scalar() or 0

        snack_resp = SnackResponse(
            id=row.id,
            name=row.name,
            category=row.category,
            quantity=row.quantity,
            low_stock_threshold=row.low_stock_threshold,
            status=derived_status,
            image_url=getattr(row, "image_url", None),
            votes_count=votes_count,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

        activity_resp = ActivityResponse.model_validate(activity)
        return snack_resp, activity_resp


consumption_service = ConsumptionService()
