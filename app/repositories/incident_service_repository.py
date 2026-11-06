
from sqlalchemy import select

from app.models.incident_service import IncidentService
from app.repositories.base import BaseRepository


class IncidentServiceRepository(BaseRepository[IncidentService]):

    def __init__(self, session):
        super().__init__(session, IncidentService)

    async def get_by_incident(
        self,
        incident_id: int,
    ):
        result = await self.session.execute(
            select(IncidentService)
            .where(IncidentService.incident_id == incident_id)
        )
        return result.scalars().all()

    async def get_by_service(
        self,
        service_id: int,
    ):
        result = await self.session.execute(
            select(IncidentService)
            .where(IncidentService.service_id == service_id)
        )
        return result.scalars().all()

    async def get_association(
        self,
        incident_id: int,
        service_id: int,
    ):
        result = await self.session.execute(
            select(IncidentService).where(
                IncidentService.incident_id == incident_id,
                IncidentService.service_id == service_id,
            )
        )
        return result.scalar_one_or_none()
