
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResourceNotFoundException,
    BusinessRuleException,
)

from app.repositories.incident_repository import IncidentRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.incident_service_repository import IncidentServiceRepository

from app.schemas.incident_service import (
    IncidentServiceCreate,
    IncidentServiceUpdate,
)


logger = logging.getLogger(__name__)


class IncidentServiceService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = IncidentServiceRepository(session)
        self.incident_repository = IncidentRepository(session)
        self.service_repository = ServiceRepository(session)

    async def add_service(
        self,
        incident_id: int,
        data: IncidentServiceCreate,
    ):

        incident = await self.incident_repository.get_by_id(incident_id)

        if not incident:
            raise ResourceNotFoundException("Incident not found")

        service = await self.service_repository.get_by_id(data.service_id)

        if not service:
            raise ResourceNotFoundException("Service not found")

        existing = await self.repository.get_association(
            incident_id,
            data.service_id,
        )

        if existing:
            raise BusinessRuleException(
                "Service is already associated with this incident"
            )

        try:
            association_data = data.model_dump()
            association_data["incident_id"] = incident_id

            association = await self.repository.create(association_data)

            await self.session.commit()
            await self.session.refresh(association)

            return association

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to associate service with incident")
            raise

    async def get_affected_services(self, incident_id: int):

        incident = await self.incident_repository.get_by_id(incident_id)

        if not incident:
            raise ResourceNotFoundException("Incident not found")

        return await self.repository.get_by_incident(incident_id)

    async def update_impact(
        self,
        incident_id: int,
        service_id: int,
        data: IncidentServiceUpdate,
    ):

        association = await self.repository.get_association(
            incident_id,
            service_id,
        )

        if not association:
            raise ResourceNotFoundException(
                "Incident-service association not found"
            )

        try:
            association.impact_type = data.impact_type

            await self.session.commit()
            await self.session.refresh(association)

            return association

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to update service impact")
            raise

    async def remove_service(
        self,
        incident_id: int,
        service_id: int,
    ):

        association = await self.repository.get_association(
            incident_id,
            service_id,
        )

        if not association:
            raise ResourceNotFoundException(
                "Incident-service association not found"
            )

        try:
            await self.session.delete(association)
            await self.session.commit()

            return {"message": "Service removed from incident"}

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to remove service association")
            raise
