
from sqlalchemy import select

from app.models.incident_event import IncidentEvent
from app.repositories.base import BaseRepository


class IncidentEventRepository(BaseRepository[IncidentEvent]):

    def __init__(self, session):
        super().__init__(session, IncidentEvent)

    async def get_by_incident(
        self,
        incident_id: int,
        offset: int = 0,
        limit: int = 100,
    ):
        result = await self.session.execute(
            select(IncidentEvent)
            .where(IncidentEvent.incident_id == incident_id)
            .order_by(IncidentEvent.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_event_type(
        self,
        incident_id: int,
        event_type,
        offset: int = 0,
        limit: int = 100,
    ):
        result = await self.session.execute(
            select(IncidentEvent)
            .where(
                IncidentEvent.incident_id == incident_id,
                IncidentEvent.event_type == event_type,
            )
            .order_by(IncidentEvent.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()
