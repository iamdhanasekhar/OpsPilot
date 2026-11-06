
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.schemas.incident_analysis import (
    IncidentAnalysisCreate,
    IncidentAnalysisResponse,
)

from app.services.incident_analysis_service import IncidentAnalysisService
from app.services.ai_incident_analysis_service import AIIncidentAnalysisService


router = APIRouter(
    prefix="/incidents/{incident_id}/analyses",
    tags=["Incident Analyses"],
)


@router.post(
    "",
    response_model=IncidentAnalysisResponse,
    status_code=201,
)
async def create_analysis(
    incident_id: int,
    data: IncidentAnalysisCreate,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentAnalysisService(session)
    return await service.create_analysis(incident_id, data)


@router.get(
    "",
    response_model=list[IncidentAnalysisResponse],
)
async def get_incident_analyses(
    incident_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    service = IncidentAnalysisService(session)

    return await service.get_incident_analyses(
        incident_id,
        offset,
        limit,
    )


@router.get(
    "/latest",
    response_model=IncidentAnalysisResponse,
)
async def get_latest_analysis(
    incident_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentAnalysisService(session)
    return await service.get_latest_analysis(incident_id)


@router.post(
    "/analyze",
    response_model=IncidentAnalysisResponse,
    status_code=201,
)
async def analyze_incident(
    incident_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = AIIncidentAnalysisService(session)

    return await service.analyze_incident(incident_id)