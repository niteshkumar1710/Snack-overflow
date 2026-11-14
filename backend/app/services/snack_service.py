import math
from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.snack import Snack, ALLOWED_CATEGORIES
from app.models.vote import Vote
from app.schemas.snack import SnackCreate, SnackUpdate, SnackResponse
from app.utils.errors import AppException


class SnackService:
    """Service handling all business logic for pantry snack management."""

    @staticmethod
    def get_snacks(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[SnackResponse], int, int]:
        """Fetch paginated, filtered, and searched snacks from the database.
        
        Filtering and pagination are executed server-side at the SQL query level.
        Returns:
            (items, total, total_pages)
        """
        query = db.query(Snack)

        # 1. Server-side search by snack name (case-insensitive)
        if search and search.strip():
            query = query.filter(Snack.name.ilike(f"%{search.strip()}%"))

        # 2. Server-side category filtering
        if category and category.strip():
            cat = category.strip().lower()
            if cat not in ALLOWED_CATEGORIES:
                raise AppException(
                    status_code=400,
                    code="INVALID_CATEGORY",
                    message=f"Category '{category}' is invalid. Allowed: {', '.join(ALLOWED_CATEGORIES)}",
                )
            query = query.filter(Snack.category == cat)

        # 3. Server-side derived status filtering
        if status and status.strip():
            st = status.strip().lower()
            if st == "stocked":
                query = query.filter(Snack.quantity > Snack.low_stock_threshold)
            elif st == "running_low":
                query = query.filter(Snack.quantity > 0, Snack.quantity <= Snack.low_stock_threshold)
            elif st == "gone":
                query = query.filter(Snack.quantity == 0)
            else:
                raise AppException(
                    status_code=400,
                    code="INVALID_STATUS",
                    message="Status filter must be one of: 'stocked', 'running_low', 'gone'.",
                )

        # Total count before pagination
        total = query.count()

        # Calculate total pages
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        # Pagination & ordering
        offset = (page - 1) * page_size
        snacks = query.order_by(Snack.name.asc()).offset(offset).limit(page_size).all()

        # Convert to response schemas with vote counts
        items: List[SnackResponse] = []
        for snack in snacks:
            vote_count = db.query(func.count(Vote.id)).filter(Vote.snack_id == snack.id).scalar() or 0
            items.append(
                SnackResponse(
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
            )

        return items, total, total_pages

    @staticmethod
    def get_snack_by_id(db: Session, snack_id: int) -> SnackResponse:
        """Fetch details of a specific snack by ID."""
        snack = db.query(Snack).filter(Snack.id == snack_id).first()
        if not snack:
            raise AppException(
                status_code=404,
                code="SNACK_NOT_FOUND",
                message=f"Snack with ID {snack_id} was not found.",
            )

        vote_count = db.query(func.count(Vote.id)).filter(Vote.snack_id == snack.id).scalar() or 0
        return SnackResponse(
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

    @staticmethod
    def create_snack(db: Session, snack_in: SnackCreate) -> SnackResponse:
        """Create a new snack in the pantry (Admin only)."""
        # Check for duplicate snack name (case-insensitive)
        existing = db.query(Snack).filter(func.lower(Snack.name) == snack_in.name.lower()).first()
        if existing:
            raise AppException(
                status_code=409,
                code="DUPLICATE_SNACK_NAME",
                message=f"A snack with the name '{snack_in.name}' already exists.",
            )

        snack = Snack(
            name=snack_in.name,
            category=snack_in.category,
            quantity=snack_in.quantity,
            low_stock_threshold=snack_in.low_stock_threshold,
        )
        db.add(snack)
        db.commit()
        db.refresh(snack)

        return SnackResponse(
            id=snack.id,
            name=snack.name,
            category=snack.category,
            quantity=snack.quantity,
            low_stock_threshold=snack.low_stock_threshold,
            status=snack.status,
            votes_count=0,
            created_at=snack.created_at,
            updated_at=snack.updated_at,
        )

    @staticmethod
    def update_snack(db: Session, snack_id: int, snack_in: SnackUpdate) -> SnackResponse:
        """Update an existing snack's attributes (Admin only)."""
        snack = db.query(Snack).filter(Snack.id == snack_id).first()
        if not snack:
            raise AppException(
                status_code=404,
                code="SNACK_NOT_FOUND",
                message=f"Snack with ID {snack_id} was not found.",
            )

        # Check duplicate name if name is being changed
        if snack_in.name is not None and snack_in.name.lower() != snack.name.lower():
            existing = (
                db.query(Snack)
                .filter(func.lower(Snack.name) == snack_in.name.lower(), Snack.id != snack_id)
                .first()
            )
            if existing:
                raise AppException(
                    status_code=409,
                    code="DUPLICATE_SNACK_NAME",
                    message=f"A snack with the name '{snack_in.name}' already exists.",
                )
            snack.name = snack_in.name

        if snack_in.category is not None:
            snack.category = snack_in.category

        if snack_in.quantity is not None:
            snack.quantity = snack_in.quantity

        if snack_in.low_stock_threshold is not None:
            snack.low_stock_threshold = snack_in.low_stock_threshold

        db.commit()
        db.refresh(snack)

        vote_count = db.query(func.count(Vote.id)).filter(Vote.snack_id == snack.id).scalar() or 0
        return SnackResponse(
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

    @staticmethod
    def delete_snack(db: Session, snack_id: int) -> str:
        """Delete a snack and cascade-delete its votes and activities (Admin only)."""
        snack = db.query(Snack).filter(Snack.id == snack_id).first()
        if not snack:
            raise AppException(
                status_code=404,
                code="SNACK_NOT_FOUND",
                message=f"Snack with ID {snack_id} was not found.",
            )

        snack_name = snack.name
        db.delete(snack)
        db.commit()
        return snack_name


snack_service = SnackService()
