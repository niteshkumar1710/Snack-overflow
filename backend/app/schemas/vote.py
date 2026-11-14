from pydantic import BaseModel


class VoteResponse(BaseModel):
    """Schema returned after a vote is created or removed."""
    message: str
    snack_id: int
    votes_count: int
    has_voted: bool
