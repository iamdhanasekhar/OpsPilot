
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    IncidentSeverity,
    IncidentStatus,
)


class IncidentCreate(BaseModel):

    service_id: int
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    severity: IncidentSeverity


class IncidentResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    title: str
    description: str | None
    severity: IncidentSeverity
    status: IncidentStatus
    started_at: datetime
    resolved_at: datetime | None
