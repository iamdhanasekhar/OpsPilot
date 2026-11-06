
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MonitorCreate(BaseModel):

    service_id: int

    name: str = Field(min_length=2, max_length=150)

    monitor_type: Literal["http"] = "http"

    target_url: str = Field(min_length=1, max_length=1000)

    method: Literal["GET", "POST", "PUT", "HEAD"] = "GET"

    expected_status_code: int = Field(default=200, ge=100, le=599)

    interval_seconds: int = Field(default=30, ge=10)

    timeout_seconds: int = Field(default=5, ge=1, le=60)

    failure_threshold: int = Field(default=3, ge=1)


class MonitorUpdate(BaseModel):

    name: str | None = Field(default=None, min_length=2, max_length=150)

    target_url: str | None = Field(default=None, min_length=1, max_length=1000)

    method: Literal["GET", "POST", "PUT", "HEAD"] | None = None

    expected_status_code: int | None = Field(default=None, ge=100, le=599)

    interval_seconds: int | None = Field(default=None, ge=10)

    timeout_seconds: int | None = Field(default=None, ge=1, le=60)

    failure_threshold: int | None = Field(default=None, ge=1)

    is_active: bool | None = None


class MonitorResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    name: str
    monitor_type: str
    target_url: str
    method: str
    expected_status_code: int
    interval_seconds: int
    timeout_seconds: int
    failure_threshold: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
