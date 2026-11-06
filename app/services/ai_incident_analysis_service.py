import json

from pydantic import ValidationError

from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.incident_analysis import IncidentAnalysisCreate
from app.services.incident_context_service import IncidentContextService
from app.services.incident_analysis_service import IncidentAnalysisService
from app.services.ollama_service import OllamaService


logger = get_logger(__name__)


SYSTEM_PROMPT = """
You are an experienced Site Reliability Engineer (SRE).

Analyze the supplied production incident context.

Your objectives:
1. Identify the most likely root cause.
2. Explain the evidence supporting your findings.
3. Identify potential contributing factors.
4. Recommend actionable remediation steps.

Important rules:
- Use only the supplied evidence.
- Never invent logs, events, services, or dependencies.
- Distinguish confirmed facts from hypotheses.
- If evidence is insufficient, explicitly state that.
- Do not claim certainty without sufficient evidence.
- Consider timestamps and event ordering.
- Consider recovery logs as well as failure logs.

Return ONLY valid JSON with this exact structure:

{
    "findings": "Detailed incident analysis",
    "confidence": 0.0,
    "evidence": {
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "limitations": []
    },
    "remediation_suggestions": {
        "immediate_actions": [],
        "long_term_actions": []
    }
}

Confidence must be a number between 0 and 1.
"""


class AIIncidentAnalysisService:

    def __init__(self, session):
        self.context_service = IncidentContextService(session)
        self.ollama_service = OllamaService()
        self.analysis_service = IncidentAnalysisService(session)

    async def analyze_incident(self, incident_id: int):

        logger.info(
            "Starting AI analysis for incident_id=%s",
            incident_id,
        )

        # 1. Collect incident context
        context = await self.context_service.build_context(incident_id)

        # Release the read transaction before the potentially long LLM call.
        await self.context_service.incident_repository.session.rollback()

        # 2. Construct user prompt
        user_prompt = (
            "Analyze the following incident context:\n\n"
            + json.dumps(context, indent=2, default=str)
        )

        # 3. Generate analysis using Ollama
        result = await self.ollama_service.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # 4. Validate model output
        try:
            analysis_data = IncidentAnalysisCreate(
                model_name=settings.OLLAMA_MODEL,
                findings=result["findings"],
                confidence=result.get("confidence"),
                evidence=result.get("evidence"),
                remediation_suggestions=result.get(
                    "remediation_suggestions"
                ),
            )

        except (KeyError, ValidationError) as exc:
            logger.exception(
                "Invalid AI analysis for incident_id=%s",
                incident_id,
            )
            raise ValueError(
                "AI generated an invalid incident analysis"
            ) from exc

        # 5. Persist analysis and AI_ANALYZED event
        analysis = await self.analysis_service.create_analysis(
            incident_id,
            analysis_data,
        )

        logger.info(
            "AI analysis completed for incident_id=%s, analysis_id=%s",
            incident_id,
            analysis.id,
        )

        return analysis
