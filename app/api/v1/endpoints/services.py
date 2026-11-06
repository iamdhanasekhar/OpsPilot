
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.service_service import ServiceService
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
)


router = APIRouter(prefix="/services", tags=["Services"])


@router.post("/", response_model=ServiceResponse, status_code=201)
async def create_service(
    data: ServiceCreate,
    session: AsyncSession = Depends(get_db),
):
    return await ServiceService(session).create_service(data)


@router.get("/", response_model=list[ServiceResponse])
async def list_services(
    application_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    return await ServiceService(session).list_services(
        application_id, offset, limit
    )


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    session: AsyncSession = Depends(get_db),
):
    return await ServiceService(session).get_service(service_id)


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    data: ServiceUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await ServiceService(session).update_service(
        service_id, data
    )


@router.delete("/{service_id}", response_model=ServiceResponse)
async def deactivate_service(
    service_id: int,
    session: AsyncSession = Depends(get_db),
):
    return await ServiceService(session).deactivate_service(service_id)
