
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.schemas.incident_service import (
    IncidentServiceCreate,
    IncidentServiceUpdate,
    IncidentServiceResponse,
)

from app.services.incident_service_service import IncidentServiceService


router = APIRouter(
    prefix="/incidents/{incident_id}/services",
    tags=["Incident Services"],
)


@router.post(
    "",
    response_model=IncidentServiceResponse,
    status_code=201,
)
async def add_service(
    incident_id: int,
    data: IncidentServiceCreate,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentServiceService(session)
    return await service.add_service(incident_id, data)


@router.get(
    "",
    response_model=list[IncidentServiceResponse],
)
async def get_affected_services(
    incident_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentServiceService(session)
    return await service.get_affected_services(incident_id)


@router.patch(
    "/{service_id}",
    response_model=IncidentServiceResponse,
)
async def update_service_impact(
    incident_id: int,
    service_id: int,
    data: IncidentServiceUpdate,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentServiceService(session)

    return await service.update_impact(
        incident_id,
        service_id,
        data,
    )


@router.delete("/{service_id}")
async def remove_service(
    incident_id: int,
    service_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = IncidentServiceService(session)

    return await service.remove_service(
        incident_id,
        service_id,
    )
