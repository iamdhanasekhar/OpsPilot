from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monitor import Monitor
from app.models.service import Service
from app.models.monitor_check import MonitorCheck
from app.models.incident import Incident
from app.models.incident_event import IncidentEvent

from app.core.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentEventType,
)
from app.core.time import utc_now

from app.repositories.monitor_check_repository import (
    MonitorCheckRepository,
)
from app.repositories.incident_repository import (
    IncidentRepository,
)

# 1. Import your custom get_logger helper
from app.core.logger import get_logger

# 2. Instantiate the logger with the current module name
logger = get_logger(__name__)


class MonitoringService:

    def __init__(self, session: AsyncSession):
        self.session = session

        self.check_repository = MonitorCheckRepository(session)
        self.incident_repository = IncidentRepository(session)

    async def process_check(
        self,
        monitor_id: int,
        is_success: bool,
        status_code: int | None,
        response_time_ms: int | None,
        error_message: str | None,
    ):

        try:
            # Fetch monitor.
            result = await self.session.execute(
                select(Monitor).where(
                    Monitor.id == monitor_id
                )
            )

            monitor = result.scalar_one_or_none()

            if monitor is None:
                logger.warning(
                    "Monitor %s no longer exists",
                    monitor_id,
                )
                return

            # Serialize incident processing at service level.
            await self.session.execute(
                select(Service.id)
                .where(Service.id == monitor.service_id)
                .with_for_update()
            )

            # Save check result.
            check = MonitorCheck(
                monitor_id=monitor_id,
                is_success=is_success,
                status_code=status_code,
                response_time_ms=response_time_ms,
                error_message=error_message,
                checked_at=utc_now(),
            )

            self.session.add(check)

            # Ensure the new check is visible to history queries.
            await self.session.flush()

            # Evaluate consecutive failures.
            failures = (
                await self.check_repository.get_consecutive_failures(
                    monitor_id
                )
            )

            logger.info(
                "Monitor %s consecutive failures: %s/%s",
                monitor_id,
                failures,
                monitor.failure_threshold,
            )

            # Create incident if threshold is reached.
            if (
                failures >= monitor.failure_threshold
                and monitor.failure_threshold > 0
            ):

                existing_incident = (
                    await self.incident_repository.get_active_by_service(
                        monitor.service_id
                    )
                )

                if existing_incident is None:

                    incident = Incident(
                        service_id=monitor.service_id,
                        title=f"Monitor failure: {monitor.name}",
                        description=(
                            f"Monitor '{monitor.name}' failed "
                            f"{failures} consecutive checks. "
                            f"Latest error: {error_message or 'Unexpected HTTP status'}"
                        ),
                        severity=IncidentSeverity.HIGH,
                        status=IncidentStatus.OPEN,
                        started_at=utc_now(),
                    )

                    self.session.add(incident)

                    await self.session.flush()

                    event = IncidentEvent(
                        incident_id=incident.id,
                        event_type=IncidentEventType.CREATED,
                        message=(
                            f"Incident automatically created after "
                            f"{failures} consecutive monitor failures."
                        ),
                        event_metadata={
                            "monitor_id": monitor_id,
                            "failure_count": failures,
                            "failure_threshold": monitor.failure_threshold,
                            "status_code": status_code,
                        },
                    )

                    self.session.add(event)

                    logger.warning(
                        "Incident created for service %s",
                        monitor.service_id,
                    )

            # Automatically resolve incident after recovery.
            elif is_success:

                existing_incident = (
                    await self.incident_repository.get_active_by_service(
                        monitor.service_id
                    )
                )

                if existing_incident is not None:

                    all_healthy = await self._are_all_monitors_healthy(
                        monitor.service_id
                    )

                    if all_healthy:

                        existing_incident.status = IncidentStatus.RESOLVED
                        existing_incident.resolved_at = utc_now()

                        event = IncidentEvent(
                            incident_id=existing_incident.id,
                            event_type=IncidentEventType.RESOLVED,
                            message=(
                                "Incident automatically resolved. "
                                "All active monitors have recovered."
                            ),
                            event_metadata={
                                "recovery_trigger_monitor_id": monitor_id,
                            },
                        )

                        self.session.add(event)

                        logger.info(
                            "Incident %s automatically resolved for service %s",
                            existing_incident.id,
                            monitor.service_id,
                        )


            await self.session.commit()

            return {
                "monitor_id": monitor_id,
                "is_success": is_success,
                "consecutive_failures": failures,
            }

        except Exception:
            await self.session.rollback()

            logger.exception(
                "Failed to process monitoring result for monitor %s",
                monitor_id,
            )

            raise

    async def _are_all_monitors_healthy(
            self,
            service_id: int,
    ) -> bool:

        result = await self.session.execute(
            select(Monitor.id).where(
                Monitor.service_id == service_id,
                Monitor.is_active.is_(True),
            )
        )

        monitor_ids = result.scalars().all()

        # Don't resolve an incident if the service has no active monitors.
        if not monitor_ids:
            return False

        for monitor_id in monitor_ids:

            latest_checks = await self.check_repository.get_latest_checks(
                monitor_id=monitor_id,
                limit=1,
            )

            # No check means health is unknown.
            if not latest_checks:
                return False

            if not latest_checks[0].is_success:
                return False

        return True
