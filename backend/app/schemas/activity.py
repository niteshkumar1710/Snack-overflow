from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.snack import SnackResponse


class ConsumeRequest(BaseModel):
    """Schema for snack consumption request."""
    amount: int = Field(default=1, ge=1, description="Amount to consume, must be a positive integer >= 1")


class RestockRequest(BaseModel):
    """Schema for snack restocking request."""
    amount: int = Field(..., ge=1, description="Amount to restock, must be a positive integer >= 1")


class ActivityResponse(BaseModel):
    """Schema for activity logging records."""
    id: int
    user_id: int
    snack_id: int
    action: str
    amount: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsumptionResponse(BaseModel):
    """Response returned upon successful snack consumption."""
    message: str
    snack: SnackResponse
    activity: ActivityResponse


class RestockResponse(BaseModel):
    """Response returned upon successful snack restocking."""
    message: str
    snack: SnackResponse
    activity: ActivityResponse


class ActivityUserResponse(BaseModel):
    """Minimal user information embedded in an activity record."""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActivitySnackResponse(BaseModel):
    """Minimal snack information embedded in an activity record."""
    id: int
    name: str
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ActivityItemResponse(BaseModel):
    """Detailed activity entry with associated user and snack."""
    id: int
    user: ActivityUserResponse
    snack: ActivitySnackResponse
    action: str
    amount: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityPaginationMeta(BaseModel):
    """Pagination metadata for activity queries."""
    page: int
    limit: int
    total: int
    total_pages: int


class PaginatedActivitiesResponse(BaseModel):
    """Response model for paginated activity log."""
    items: List[ActivityItemResponse]
    pagination: ActivityPaginationMeta


class PersonalConsumptionItem(BaseModel):
    """Personal consumption record for an employee."""
    activity_id: int
    snack_id: int
    snack_name: str
    snack_image_url: Optional[str] = None
    amount: int
    consumed_at: datetime


class PersonalConsumptionSummary(BaseModel):
    """Summary metrics of an employee's personal consumption."""
    total_consumed_packets: int
    unique_snacks_tried: int


class PersonalConsumptionHistoryResponse(BaseModel):
    """Response model for employee's personal consumption history."""
    items: List[PersonalConsumptionItem]
    summary: PersonalConsumptionSummary
    pagination: ActivityPaginationMeta
