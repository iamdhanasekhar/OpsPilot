
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceDependencyCreate(BaseModel):

    target_service_id: int
    dependency_type: str = Field(
        default="synchronous",
        min_length=1,
        max_length=50,
    )
    is_critical: bool = False


class ServiceDependencyUpdate(BaseModel):

    dependency_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    is_critical: bool | None = None


class ServiceDependencyResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_service_id: int
    target_service_id: int
    dependency_type: str
    is_critical: bool
    created_at: datetime
