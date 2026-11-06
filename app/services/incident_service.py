from datetime import timedelta

from app.core.config import settings
from app.services.notification_service import NotificationService

from app.repositories.log_entry_repository import LogEntryRepository
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logger import get_logger
from app.core.time import utc_now
from app.core.enums import IncidentStatus, IncidentEventType
from app.core.exceptions import (
    ResourceNotFoundException,
    BusinessRuleException,
)

from app.repositories.incident_repository import IncidentRepository
from app.repositories.incident_event_repository import IncidentEventRepository
from app.repositories.service_repository import ServiceRepository

from app.schemas.incident import IncidentCreate
from app.repositories.incident_service_repository import (
    IncidentServiceRepository,
)


logger = get_logger(__name__)


class IncidentService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = IncidentRepository(session)
        self.event_repository = IncidentEventRepository(session)
        self.service_repository = ServiceRepository(session)
        self.log_repository = LogEntryRepository(session)
        self.incident_service_repository = IncidentServiceRepository(session)
        self.notification_service = NotificationService(session)

    async def _record_event(
        self,
        incident_id: int,
        event_type: IncidentEventType,
        message: str | None = None,
        event_metadata: dict | None = None,
    ):

        return await self.event_repository.create(
            {
                "incident_id": incident_id,
                "event_type": event_type,
                "message": message,
                "event_metadata": event_metadata,
            }
        )

    async def create_incident(self, data: IncidentCreate):

        service = await self.service_repository.get_by_id(
            data.service_id
        )

        if not service:
            raise ResourceNotFoundException("Service not found")

        try:
            incident = await self.repository.create(
                data.model_dump()
            )

            event = await self._record_event(
                incident_id=incident.id,
                event_type=IncidentEventType.CREATED,
                message="Incident created",
            )

            await self._queue_notification(
                incident=incident,
                event=event,
                event_type="CREATED",
            )

            await self.session.commit()
            await self.session.refresh(incident)

            # Dispatch AI analysis only after successful database commit.
            try:
                from app.workers.ai_tasks import analyze_incident_task

                analyze_incident_task.delay(incident.id)

                logger.info(
                    "AI analysis dispatched for incident_id=%s",
                    incident.id,
                )

            except Exception:
                # Incident creation must succeed even if Celery is unavailable.
                logger.exception(
                    "Failed to dispatch AI analysis for incident_id=%s",
                    incident.id,
                )

            return incident

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to create incident")
            raise

    async def get_incident(self, incident_id: int):

        incident = await self.repository.get_by_id(incident_id)

        if not incident:
            raise ResourceNotFoundException("Incident not found")

        return incident

    async def get_incidents(
        self,
        service_id: int | None = None,
        status=None,
        severity=None,
        offset: int = 0,
        limit: int = 100,
    ):

        if service_id is not None:
            service = await self.service_repository.get_by_id(
                service_id
            )

            if not service:
                raise ResourceNotFoundException("Service not found")

        return await self.repository.get_filtered(
            service_id=service_id,
            status=status,
            severity=severity,
            offset=offset,
            limit=limit,
        )

    async def acknowledge_incident(self, incident_id: int):

        incident = await self.get_incident(incident_id)

        if incident.status != IncidentStatus.OPEN:
            raise BusinessRuleException(
                "Only open incidents can be acknowledged"
            )

        try:
            incident.status = IncidentStatus.ACKNOWLEDGED

            await self._record_event(
                incident_id=incident.id,
                event_type=IncidentEventType.ACKNOWLEDGED,
                message="Incident acknowledged",
            )

            await self.session.commit()
            await self.session.refresh(incident)

            return incident

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to acknowledge incident")
            raise

    async def resolve_incident(self, incident_id: int):

        incident = await self.get_incident(incident_id)

        if incident.status == IncidentStatus.RESOLVED:
            raise BusinessRuleException(
                "Incident is already resolved"
            )

        try:
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = utc_now()

            event = await self._record_event(
                incident_id=incident.id,
                event_type=IncidentEventType.RESOLVED,
                message="Incident resolved",
            )

            await self._queue_notification(
                incident=incident,
                event=event,
                event_type="RESOLVED",
            )

            await self.session.commit()
            await self.session.refresh(incident)

            return incident

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to resolve incident")
            raise

    async def get_incident_logs(
            self,
            incident_id: int,
            level: str | None = None,
            offset: int = 0,
            limit: int = 100,
    ):
        incident = await self.get_incident(incident_id)

        if offset < 0:
            raise BusinessRuleException(
                "Offset cannot be negative"
            )

        if limit < 1 or limit > 500:
            raise BusinessRuleException(
                "Limit must be between 1 and 500"
            )

        # Primary service
        service_ids = {incident.service_id}

        # Affected services
        associations = await self.incident_service_repository.get_by_incident(
            incident_id
        )

        service_ids.update(
            association.service_id
            for association in associations
        )

        # Incident correlation window
        start_time = incident.started_at - timedelta(minutes=5)
        end_time = incident.resolved_at or utc_now()

        return await self.log_repository.get_by_filters(
            service_ids=list(service_ids),
            level=level,
            start_time=start_time,
            end_time=end_time,
            skip=offset,
            limit=limit,
        )

    async def _queue_notification(
            self,
            incident,
            event,
            event_type: str,
    ):
        recipient = settings.NOTIFICATION_EMAIL

        if not recipient:
            logger.warning(
                "NOTIFICATION_EMAIL not configured. "
                "Skipping notification for incident %s",
                incident.id,
            )
            return

        await self.notification_service.create_notification(
            incident_id=incident.id,
            incident_event_id=event.id,
            recipient=recipient,
            payload={
                "incident_id": incident.id,
                "event_type": event_type,
                "message": (
                    f"Incident #{incident.id} "
                    f"was {event_type.lower()}."
                ),
            },
        )
