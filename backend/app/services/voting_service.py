from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.snack import Snack
from app.models.vote import Vote
from app.models.user import User
from app.utils.errors import AppException


class VotingService:
    """Service handling snack voting and unvoting operations."""

    @staticmethod
    def cast_vote(db: Session, user: User, snack_id: int) -> int:
        """Cast a vote for a snack.
        
        Enforces the database-level unique constraint (user_id, snack_id)
        to prevent duplicate voting even under high concurrency.
        """
        snack = db.query(Snack).filter(Snack.id == snack_id).first()
        if not snack:
            raise AppException(
                status_code=404,
                code="SNACK_NOT_FOUND",
                message=f"Snack with ID {snack_id} was not found.",
            )

        vote = Vote(user_id=user.id, snack_id=snack_id)
        db.add(vote)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise AppException(
                status_code=409,
                code="ALREADY_VOTED",
                message="You have already voted for this snack.",
            )

        vote_count = db.query(func.count(Vote.id)).filter(Vote.snack_id == snack_id).scalar() or 0
        return vote_count

    @staticmethod
    def remove_vote(db: Session, user: User, snack_id: int) -> int:
        """Remove the authenticated user's vote for a snack."""
        snack = db.query(Snack).filter(Snack.id == snack_id).first()
        if not snack:
            raise AppException(
                status_code=404,
                code="SNACK_NOT_FOUND",
                message=f"Snack with ID {snack_id} was not found.",
            )

        vote = db.query(Vote).filter(Vote.user_id == user.id, Vote.snack_id == snack_id).first()
        if not vote:
            raise AppException(
                status_code=404,
                code="VOTE_NOT_FOUND",
                message="You have not voted for this snack.",
            )

        db.delete(vote)
        db.commit()

        vote_count = db.query(func.count(Vote.id)).filter(Vote.snack_id == snack_id).scalar() or 0
        return vote_count


voting_service = VotingService()
