from datetime import datetime

from pydantic import BaseModel
from enum import Enum

from app.schemas.incident_analytics import (
    IncidentCountBySeverity,
    IncidentCountByService,
)


class ServiceSummary(BaseModel):
    total_services: int
    active_services: int
    inactive_services: int


class MonitorSummary(BaseModel):
    total_monitors: int
    active_monitors: int
    inactive_monitors: int


class MonitorCheckSummary(BaseModel):
    total_checks: int
    successful_checks: int
    failed_checks: int


class ServiceHealthStatus(str, Enum):
    INACTIVE = "INACTIVE"
    NO_MONITORS = "NO_MONITORS"
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


class ServiceHealthItem(BaseModel):
    service_id: int
    service_name: str
    health_status: ServiceHealthStatus
    active_monitors: int
    healthy_monitors: int
    failed_monitors: int
    unknown_monitors: int


class MonitorHealthStatus(str, Enum):
    INACTIVE = "INACTIVE"
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DOWN = "DOWN"


class MonitorHealthItem(BaseModel):
    monitor_id: int
    monitor_name: str
    service_id: int
    service_name: str
    target_url: str
    health_status: MonitorHealthStatus
    latest_check_success: bool | None
    latest_checked_at: datetime | None
    total_checks: int
    successful_checks: int
    failed_checks: int
    availability_percentage: float | None


class DashboardSummaryResponse(BaseModel):
    total_incidents: int
    open_incidents: int
    critical_incidents: int
    resolved_incidents: int
    average_mttr_seconds: float | None
    overall_availability_percentage: float | None

    services_health: list[ServiceHealthItem]
    health_summary: dict[str, int]
    monitors_health: list[MonitorHealthItem]
    by_severity: list[IncidentCountBySeverity]
    by_service: list[IncidentCountByService]

    services: ServiceSummary
    monitors: MonitorSummary
    monitor_checks: MonitorCheckSummary
