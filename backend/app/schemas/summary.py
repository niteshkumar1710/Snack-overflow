from typing import Optional
from pydantic import BaseModel
from app.schemas.snack import SnackResponse


class PantrySummaryResponse(BaseModel):
    """Pantry dashboard inventory counts and Snack of the Week."""
    stocked_count: int
    running_low_count: int
    gone_count: int
    total_snacks: int
    snack_of_the_week: Optional[SnackResponse] = None
