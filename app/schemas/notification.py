from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import (
    NotificationChannel,
    NotificationStatus,
)


class NotificationResponse(BaseModel):

    id: int
    incident_id: int
    incident_event_id: int

    channel: NotificationChannel
    recipient: str

    payload: dict | None

    status: NotificationStatus
    attempt_count: int
    last_error: str | None

    next_attempt_at: datetime
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):

    total: int
    limit: int
    offset: int

    items: list[NotificationResponse]