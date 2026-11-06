
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.enums import IncidentSeverity, IncidentStatus

from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
)

from app.services.incident_service import IncidentService
from app.schemas.log_entry import LogEntryResponse


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=201,
)
async def create_incident(
    data: IncidentCreate,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentService(session)
    return await service.create_incident(data)


@router.get(
    "",
    response_model=list[IncidentResponse],
)
async def get_incidents(
    service_id: int | None = None,
    status: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    service = IncidentService(session)

    return await service.get_incidents(
        service_id=service_id,
        status=status,
        severity=severity,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def get_incident(
    incident_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentService(session)
    return await service.get_incident(incident_id)


@router.post(
    "/{incident_id}/acknowledge",
    response_model=IncidentResponse,
)
async def acknowledge_incident(
    incident_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentService(session)
    return await service.acknowledge_incident(incident_id)


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
)
async def resolve_incident(
    incident_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentService(session)
    return await service.resolve_incident(incident_id)


@router.get(
    "/{incident_id}/logs",
    response_model=list[LogEntryResponse],
)
async def get_incident_logs(
    incident_id: int,
    level: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    service = IncidentService(session)

    return await service.get_incident_logs(
        incident_id=incident_id,
        level=level,
        offset=offset,
        limit=limit,
    )