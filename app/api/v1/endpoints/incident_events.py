
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.enums import IncidentEventType

from app.schemas.incident_event import (
    IncidentEventCreate,
    IncidentEventResponse,
)

from app.services.incident_event_service import IncidentEventService


router = APIRouter(
    prefix="/incidents/{incident_id}/events",
    tags=["Incident Events"],
)


@router.post(
    "",
    response_model=IncidentEventResponse,
    status_code=201,
)
async def create_event(
    incident_id: int,
    data: IncidentEventCreate,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentEventService(session)
    return await service.create_event(incident_id, data)


@router.get(
    "",
    response_model=list[IncidentEventResponse],
)
async def get_incident_events(
    incident_id: int,
    event_type: IncidentEventType | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    service = IncidentEventService(session)

    return await service.get_incident_events(
        incident_id=incident_id,
        event_type=event_type,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{event_id}",
    response_model=IncidentEventResponse,
)
async def get_event(
    incident_id: int,
    event_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentEventService(session)

    return await service.get_event(
        incident_id=incident_id,
        event_id=event_id,
    )
