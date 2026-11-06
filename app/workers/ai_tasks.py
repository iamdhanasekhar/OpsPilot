import asyncio

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.workers.celery_app import celery_app

from app.services.ai_incident_analysis_service import (
    AIIncidentAnalysisService,
)


logger = get_logger(__name__)


async def _analyze_incident(incident_id: int):
    async with AsyncSessionLocal() as session:
        service = AIIncidentAnalysisService(session)

        analysis = await service.analyze_incident(incident_id)

        return {
            "incident_id": incident_id,
            "analysis_id": analysis.id,
            "status": "COMPLETED",
        }


@celery_app.task(
    bind=True,
    name="ai.analyze_incident",
    autoretry_for=(RuntimeError,),
    retry_backoff=30,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def analyze_incident_task(self, incident_id: int):
    logger.info(
        "Starting AI analysis task for incident_id=%s",
        incident_id,
    )

    try:
        result = asyncio.run(_analyze_incident(incident_id))

        logger.info(
            "AI analysis task completed for incident_id=%s",
            incident_id,
        )

        return result

    except Exception:
        logger.exception(
            "AI analysis task failed for incident_id=%s",
            incident_id,
        )
        raise