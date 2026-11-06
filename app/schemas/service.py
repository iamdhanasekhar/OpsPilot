
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    application_id: int

    name: str = Field(min_length=2, max_length=150)
    slug: str = Field(
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    base_url: str | None = Field(default=None, max_length=500)


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    base_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    name: str
    slug: str
    base_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
