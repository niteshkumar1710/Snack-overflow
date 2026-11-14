from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.snack import Snack


class Vote(Base):
    """Vote entity representing employee preferences for pantry snacks."""

    __tablename__ = "votes"
    __table_args__ = (
        # Mandatory database-level unique constraint to guarantee one vote per user per snack
        UniqueConstraint("user_id", "snack_id", name="uq_user_snack_vote"),
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="votes")
    snack: Mapped["Snack"] = relationship("Snack", back_populates="votes")

    def __repr__(self) -> str:
        return f"<Vote id={self.id} user_id={self.user_id} snack_id={self.snack_id}>"
