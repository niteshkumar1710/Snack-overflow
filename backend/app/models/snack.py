from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.vote import Vote
    from app.models.activity import Activity

ALLOWED_CATEGORIES = ("sweet", "savoury", "drink", "healthy-ish")


class Snack(Base):
    """Snack entity representing pantry inventory items."""

    __tablename__ = "snacks"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_snacks_quantity_non_negative"),
        CheckConstraint("low_stock_threshold >= 0", name="ck_snacks_threshold_non_negative"),
        CheckConstraint(
            "category IN ('sweet', 'savoury', 'drink', 'healthy-ish')",
            name="ck_snacks_category",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    # Cascade delete votes and activity records when a snack is permanently deleted
    votes: Mapped[List["Vote"]] = relationship(
        "Vote",
        back_populates="snack",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        back_populates="snack",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def status(self) -> str:
        """Derived snack status calculated dynamically from quantity and low_stock_threshold.
        
        Rules:
        - stocked: quantity > low_stock_threshold
        - running_low: quantity > 0 and quantity <= low_stock_threshold
        - gone: quantity == 0
        """
        if self.quantity == 0:
            return "gone"
        if self.quantity <= self.low_stock_threshold:
            return "running_low"
        return "stocked"

    def __repr__(self) -> str:
        return f"<Snack id={self.id} name={self.name} qty={self.quantity} status={self.status}>"
