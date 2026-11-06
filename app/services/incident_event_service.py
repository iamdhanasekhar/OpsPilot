
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException

from app.repositories.incident_repository import IncidentRepository
from app.repositories.incident_event_repository import IncidentEventRepository

from app.schemas.incident_event import IncidentEventCreate


logger = logging.getLogger(__name__)


class IncidentEventService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = IncidentEventRepository(session)
        self.incident_repository = IncidentRepository(session)

    async def create_event(
        self,
        incident_id: int,
        data: IncidentEventCreate,
    ):

        incident = await self.incident_repository.get_by_id(
            incident_id
        )

        if not incident:
            raise ResourceNotFoundException("Incident not found")

        try:
            event_data = data.model_dump()
            event_data["incident_id"] = incident_id

            event = await self.repository.create(event_data)

            await self.session.commit()
            await self.session.refresh(event)

            return event

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to create incident event")
            raise

    async def get_event(
            self,
            incident_id: int,
            event_id: int,
    ):

        incident = await self.incident_repository.get_by_id(
            incident_id
        )

        if not incident:
            raise ResourceNotFoundException("Incident not found")

        event = await self.repository.get_by_id(event_id)

        if not event or event.incident_id != incident_id:
            raise ResourceNotFoundException(
                "Incident event not found"
            )

        return event

    async def get_incident_events(
        self,
        incident_id: int,
        event_type=None,
        offset: int = 0,
        limit: int = 100,
    ):

        incident = await self.incident_repository.get_by_id(
            incident_id
        )

        if not incident:
            raise ResourceNotFoundException("Incident not found")

        if event_type is not None:
            return await self.repository.get_by_event_type(
                incident_id,
                event_type,
                offset,
                limit,
            )

        return await self.repository.get_by_incident(
            incident_id,
            offset,
            limit,
        )
