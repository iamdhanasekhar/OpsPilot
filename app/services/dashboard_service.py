from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import IncidentSeverity, IncidentStatus

from app.schemas.dashboard import (
    DashboardSummaryResponse,
    ServiceSummary,
    MonitorSummary,
    MonitorCheckSummary, MonitorHealthStatus, MonitorHealthItem,
)

from app.services.incident_analytics_service import (
    IncidentAnalyticsService,
)

from app.repositories.service_repository import ServiceRepository
from app.repositories.monitor_repository import MonitorRepository
from app.repositories.monitor_check_repository import MonitorCheckRepository

from app.schemas.dashboard import (
    ServiceHealthItem,
    ServiceHealthStatus,
)


class DashboardService:

    def __init__(self, session: AsyncSession):
        self.session = session

        self.incident_analytics_service = IncidentAnalyticsService(session)

        self.service_repository = ServiceRepository(session)
        self.monitor_repository = MonitorRepository(session)
        self.monitor_check_repository = MonitorCheckRepository(session)

    async def get_dashboard_summary(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        # Incident analytics
        analytics = await self.incident_analytics_service.get_incident_analytics(
            start_time=start_time,
            end_time=end_time,
        )

        status_counts = {
            item.status: item.count
            for item in analytics.by_status
        }

        severity_counts = {
            item.severity: item.count
            for item in analytics.by_severity
        }

        # Service summary
        service_counts = await self.service_repository.get_dashboard_counts()

        # Monitor summary
        monitor_counts = await self.monitor_repository.get_dashboard_counts()

        # Monitor check summary
        check_counts = await self.monitor_check_repository.get_dashboard_counts(
            start_time=start_time,
            end_time=end_time,
        )

        services_health, health_summary = (
            await self.get_services_health()
        )

        monitors_health, overall_availability = (
            await self.get_monitors_health(
                start_time=start_time,
                end_time=end_time,
            )
        )

        return DashboardSummaryResponse(
            total_incidents=analytics.total_incidents,
            open_incidents=status_counts.get(IncidentStatus.OPEN, 0),
            critical_incidents=severity_counts.get(
                IncidentSeverity.CRITICAL, 0
            ),
            resolved_incidents=status_counts.get(
                IncidentStatus.RESOLVED, 0
            ),
            average_mttr_seconds=analytics.average_mttr_seconds,

            by_severity=analytics.by_severity,
            by_service=analytics.by_service,

            services=ServiceSummary(
                total_services=service_counts["total"],
                active_services=service_counts["active"],
                inactive_services=service_counts["inactive"],
            ),

            monitors=MonitorSummary(
                total_monitors=monitor_counts["total"],
                active_monitors=monitor_counts["active"],
                inactive_monitors=monitor_counts["inactive"],
            ),

            monitor_checks=MonitorCheckSummary(
                total_checks=check_counts["total"],
                successful_checks=check_counts["successful"],
                failed_checks=check_counts["failed"],
            ),

            services_health=services_health,
            health_summary=health_summary,
            monitors_health=monitors_health,
            overall_availability_percentage=overall_availability,
        )

    async def get_services_health(self):
        rows = await self.monitor_check_repository.get_latest_checks_by_service()

        services = {}

        for row in rows:
            service = services.setdefault(
                row.service_id,
                {
                    "service_id": row.service_id,
                    "service_name": row.service_name,
                    "service_is_active": row.service_is_active,
                    "active_monitors": 0,
                    "healthy_monitors": 0,
                    "failed_monitors": 0,
                    "unknown_monitors": 0,
                },
            )

            if row.monitor_id is None:
                continue

            service["active_monitors"] += 1

            if row.is_success is True:
                service["healthy_monitors"] += 1
            elif row.is_success is False:
                service["failed_monitors"] += 1
            else:
                service["unknown_monitors"] += 1

        health_items = []

        for service in services.values():
            if not service["service_is_active"]:
                status = ServiceHealthStatus.INACTIVE

            elif service["active_monitors"] == 0:
                status = ServiceHealthStatus.NO_MONITORS

            elif service["healthy_monitors"] == 0:
                if service["failed_monitors"] == 0:
                    status = ServiceHealthStatus.UNKNOWN
                else:
                    status = ServiceHealthStatus.DOWN

            elif (
                service["failed_monitors"] > 0
                or service["unknown_monitors"] > 0
            ):
                status = ServiceHealthStatus.DEGRADED

            else:
                status = ServiceHealthStatus.HEALTHY

            health_items.append(
                ServiceHealthItem(
                    service_id=service["service_id"],
                    service_name=service["service_name"],
                    health_status=status,
                    active_monitors=service["active_monitors"],
                    healthy_monitors=service["healthy_monitors"],
                    failed_monitors=service["failed_monitors"],
                    unknown_monitors=service["unknown_monitors"],
                )
            )

        health_summary = {
            status.value: 0
            for status in ServiceHealthStatus
        }

        for item in health_items:
            health_summary[item.health_status.value] += 1

        return health_items, health_summary

    async def get_monitors_health(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        rows = await self.monitor_check_repository.get_monitor_health_stats(
            start_time=start_time,
            end_time=end_time,
        )

        monitor_items = []

        overall_successful = 0
        overall_total = 0

        for row in rows:
            total = row.total_checks or 0
            successful = row.successful_checks or 0
            failed = row.failed_checks or 0

            if not row.monitor_is_active or not row.service_is_active:
                status = MonitorHealthStatus.INACTIVE
            elif row.latest_check_success is None:
                status = MonitorHealthStatus.UNKNOWN
            elif row.latest_check_success:
                status = MonitorHealthStatus.HEALTHY
            else:
                status = MonitorHealthStatus.DOWN

            availability = (
                round((successful / total) * 100, 2)
                if total > 0
                else None
            )

            # Overall availability considers only active monitors
            # belonging to active services.
            if status != MonitorHealthStatus.INACTIVE:
                overall_successful += successful
                overall_total += total

            monitor_items.append(
                MonitorHealthItem(
                    monitor_id=row.monitor_id,
                    monitor_name=row.monitor_name,
                    service_id=row.service_id,
                    service_name=row.service_name,
                    target_url=row.target_url,
                    health_status=status,
                    latest_check_success=row.latest_check_success,
                    latest_checked_at=row.latest_checked_at,
                    total_checks=total,
                    successful_checks=successful,
                    failed_checks=failed,
                    availability_percentage=availability,
                )
            )

        overall_availability = (
            round((overall_successful / overall_total) * 100, 2)
            if overall_total > 0
            else None
        )

        return monitor_items, overall_availability
