
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.enums import IncidentEventType


class IncidentEventCreate(BaseModel):

    event_type: IncidentEventType
    message: str | None = None
    event_metadata: dict[str, Any] | None = None


class IncidentEventResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    event_type: IncidentEventType
    message: str | None
    event_metadata: dict[str, Any] | None
    created_at: datetime
