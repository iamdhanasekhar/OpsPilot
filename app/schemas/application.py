from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApplicationCreate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=150
    )

    slug: str = Field(
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )

    description: str | None = None

    environment: str = Field(
        default="production",
        min_length=2,
        max_length=50
    )


class ApplicationUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    description: str | None = None

    environment: str | None = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    is_active: bool | None = None


class ApplicationResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    slug: str
    description: str | None
    environment: str
    is_active: bool
    created_at: datetime
    updated_at: datetime