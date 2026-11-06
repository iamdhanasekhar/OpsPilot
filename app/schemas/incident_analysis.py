
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IncidentAnalysisCreate(BaseModel):

    model_name: str = Field(min_length=1, max_length=100)
    findings: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence: dict[str, Any] | None = None
    remediation_suggestions: dict[str, Any] | None = None


class IncidentAnalysisResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    model_name: str
    findings: str
    confidence: float | None
    evidence: dict[str, Any] | None
    remediation_suggestions: dict[str, Any] | None
    created_at: datetime
