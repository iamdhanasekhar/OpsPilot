
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.schemas.service_dependency import (
    ServiceDependencyCreate,
    ServiceDependencyUpdate,
    ServiceDependencyResponse,
)

from app.services.service_dependency_service import ServiceDependencyService


router = APIRouter(
    prefix="/services/{service_id}/dependencies",
    tags=["Service Dependencies"],
)


@router.post(
    "",
    response_model=ServiceDependencyResponse,
    status_code=201,
)
async def create_dependency(
    service_id: int,
    data: ServiceDependencyCreate,
    session: AsyncSession = Depends(get_db),
):
    service = ServiceDependencyService(session)
    return await service.create_dependency(service_id, data)


@router.get(
    "",
    response_model=list[ServiceDependencyResponse],
)
async def get_outgoing_dependencies(
    service_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = ServiceDependencyService(session)
    return await service.get_outgoing_dependencies(service_id)


@router.get(
    "/incoming",
    response_model=list[ServiceDependencyResponse],
)
async def get_incoming_dependencies(
    service_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = ServiceDependencyService(session)
    return await service.get_incoming_dependencies(service_id)


@router.patch(
    "/{dependency_id}",
    response_model=ServiceDependencyResponse,
)
async def update_dependency(
    service_id: int,
    dependency_id: int,
    data: ServiceDependencyUpdate,
    session: AsyncSession = Depends(get_db),
):
    service = ServiceDependencyService(session)

    return await service.update_dependency(
        service_id,
        dependency_id,
        data,
    )


@router.delete("/{dependency_id}")
async def delete_dependency(
    service_id: int,
    dependency_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = ServiceDependencyService(session)

    return await service.delete_dependency(
        service_id,
        dependency_id,
    )
