
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MonitorCheckCreate(BaseModel):

    is_success: bool

    status_code: int | None = Field(
        default=None,
        ge=100,
        le=599
    )

    response_time_ms: int | None = Field(
        default=None,
        ge=0
    )

    error_message: str | None = None


class MonitorCheckResponse(BaseModel):

    id: int
    monitor_id: int
    is_success: bool
    status_code: int | None
    response_time_ms: int | None
    error_message: str | None
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)
