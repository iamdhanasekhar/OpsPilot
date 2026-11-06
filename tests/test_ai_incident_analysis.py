import asyncio
from pprint import pprint

from app.core.database import AsyncSessionLocal
from app.services.ai_incident_analysis_service import (
    AIIncidentAnalysisService,
)


async def test_ai_incident_analysis():

    async with AsyncSessionLocal() as session:
        service = AIIncidentAnalysisService(session)

        analysis = await service.analyze_incident(3)

        pprint({
            "id": analysis.id,
            "incident_id": analysis.incident_id,
            "model_name": analysis.model_name,
            "findings": analysis.findings,
            "confidence": analysis.confidence,
            "evidence": analysis.evidence,
            "remediation_suggestions": analysis.remediation_suggestions,
        })


if __name__ == "__main__":
    asyncio.run(test_ai_incident_analysis())