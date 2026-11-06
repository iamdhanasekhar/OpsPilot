
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException, BusinessRuleException

from app.repositories.incident_repository import IncidentRepository
from app.repositories.incident_analysis_repository import IncidentAnalysisRepository

from app.schemas.incident_analysis import IncidentAnalysisCreate
from app.core.enums import IncidentEventType
from app.repositories.incident_event_repository import (
    IncidentEventRepository,
)


logger = logging.getLogger(__name__)


class IncidentAnalysisService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = IncidentAnalysisRepository(session)
        self.incident_repository = IncidentRepository(session)
        self.event_repository = IncidentEventRepository(session)

    async def create_analysis(
        self,
        incident_id: int,
        data: IncidentAnalysisCreate,
    ):

        incident = await self.incident_repository.get_by_id(
            incident_id
        )

        if not incident:
            raise ResourceNotFoundException("Incident not found")

        try:
            analysis_data = data.model_dump()
            analysis_data["incident_id"] = incident_id

            analysis = await self.repository.create(analysis_data)

            await self.event_repository.create({
                "incident_id": incident_id,
                "event_type": IncidentEventType.AI_ANALYZED,
                "message": "AI analysis completed for this incident.",
                "event_metadata": {
                    "analysis_id": analysis.id,
                    "model_name": analysis.model_name,
                },
            })

            await self.session.commit()
            await self.session.refresh(analysis)

            return analysis

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to create incident analysis")
            raise

    async def get_analysis(self, analysis_id: int):

        analysis = await self.repository.get_by_id(analysis_id)

        if not analysis:
            raise ResourceNotFoundException(
                "Incident analysis not found"
            )

        return analysis

    async def get_incident_analyses(
        self,
        incident_id: int,
        offset: int = 0,
        limit: int = 100,
    ):
        if offset < 0:
            raise BusinessRuleException("Offset cannot be negative")

        if limit < 1 or limit > 500:
            raise BusinessRuleException("Limit must be between 1 and 500")

        incident = await self.incident_repository.get_by_id(
            incident_id
        )

        if not incident:
            raise ResourceNotFoundException("Incident not found")

        return await self.repository.get_by_incident(
            incident_id,
            offset,
            limit,
        )

    async def get_latest_analysis(self, incident_id: int):

        incident = await self.incident_repository.get_by_id(
            incident_id
        )

        if not incident:
            raise ResourceNotFoundException("Incident not found")

        analysis = await self.repository.get_latest_by_incident(
            incident_id
        )

        if not analysis:
            raise ResourceNotFoundException(
                "No analysis found for this incident"
            )

        return analysis
