from datetime import datetime, timezone
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class LogEntryCreate(BaseModel):

    service_id: int
    level: str = Field(min_length=1, max_length=20)
    message: str = Field(min_length=1)
    source: str | None = Field(default=None, max_length=150)
    trace_id: str | None = Field(default=None, max_length=100)
    request_id: str | None = Field(default=None, max_length=100)
    timestamp: datetime
    attributes_json: dict[str, Any] | None = None


    @field_validator("level")
    @classmethod
    def normalize_level(cls, value: str) -> str:

        value = value.strip().upper()

        if value == "WARN":
            value = "WARNING"

        allowed_levels = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        if value not in allowed_levels:
            raise ValueError(
                f"Invalid log level. Allowed levels: {sorted(allowed_levels)}"
            )

        return value

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:

        if value.tzinfo is not None:
            value = value.astimezone(
                timezone.utc
            ).replace(tzinfo=None)

        return value


class LogEntryResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    level: str
    message: str
    source: str | None
    trace_id: str | None
    request_id: str | None
    timestamp: datetime
    ingested_at: datetime
    attributes_json: dict[str, Any] | None


class LogEntryBulkCreate(BaseModel):

    logs: list[LogEntryCreate] = Field(
        min_length=1,
        max_length=500,
    )

