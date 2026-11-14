from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.snack import Snack


class Activity(Base):
    """Activity entity logging snack consumption and restocking events."""

    __tablename__ = "activities"
    __table_args__ = (
        CheckConstraint("action IN ('consumed', 'restocked')", name="ck_activities_action"),
        CheckConstraint("amount > 0", name="ck_activities_amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snack_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("snacks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activities")
    snack: Mapped["Snack"] = relationship("Snack", back_populates="activities")

    def __repr__(self) -> str:
        return f"<Activity id={self.id} user_id={self.user_id} snack_id={self.snack_id} action={self.action} amount={self.amount}>"
