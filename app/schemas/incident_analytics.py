from pydantic import BaseModel
from app.core.enums import IncidentSeverity, IncidentStatus


class IncidentCountBySeverity(BaseModel):
    severity: IncidentSeverity
    count: int


class IncidentCountByStatus(BaseModel):
    status: IncidentStatus
    count: int


class IncidentCountByService(BaseModel):
    service_id: int
    count: int


class IncidentAnalyticsResponse(BaseModel):
    total_incidents: int
    by_severity: list[IncidentCountBySeverity]
    by_status: list[IncidentCountByStatus]
    by_service: list[IncidentCountByService]
    average_mttr_seconds: float | None