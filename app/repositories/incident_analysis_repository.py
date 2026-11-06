
from sqlalchemy import select

from app.models.incident_analysis import IncidentAnalysis
from app.repositories.base import BaseRepository


class IncidentAnalysisRepository(BaseRepository[IncidentAnalysis]):

    def __init__(self, session):
        super().__init__(session, IncidentAnalysis)

    async def get_by_incident(
        self,
        incident_id: int,
        offset: int = 0,
        limit: int = 100,
    ):
        result = await self.session.execute(
            select(IncidentAnalysis)
            .where(IncidentAnalysis.incident_id == incident_id)
            .order_by(
                IncidentAnalysis.created_at.desc(),
                IncidentAnalysis.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_latest_by_incident(self, incident_id: int):
        result = await self.session.execute(
            select(IncidentAnalysis)
            .where(IncidentAnalysis.incident_id == incident_id)
            .order_by(
                IncidentAnalysis.created_at.desc(),
                IncidentAnalysis.id.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
