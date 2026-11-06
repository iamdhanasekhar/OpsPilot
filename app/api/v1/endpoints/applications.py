from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.application_service import ApplicationService
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=201,
)
async def create_application(
    data: ApplicationCreate,
    session: AsyncSession = Depends(get_db),
):

    service = ApplicationService(session)

    return await service.create_application(data)


@router.get(
    "/",
    response_model=list[ApplicationResponse],
)
async def list_applications(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_db),
):

    service = ApplicationService(session)

    return await service.list_applications(
        offset=offset,
        limit=limit,
        is_active=is_active,
    )


@router.get(
    "/slug/{slug}",
    response_model=ApplicationResponse,
)
async def get_application_by_slug(
    slug: str,
    session: AsyncSession = Depends(get_db),
):

    service = ApplicationService(session)

    return await service.get_application_by_slug(slug)


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
async def get_application(
    application_id: int,
    session: AsyncSession = Depends(get_db),
):

    service = ApplicationService(session)

    return await service.get_application(application_id)


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
)
async def update_application(
    application_id: int,
    data: ApplicationUpdate,
    session: AsyncSession = Depends(get_db),
):

    service = ApplicationService(session)

    return await service.update_application(
        application_id,
        data,
    )


@router.delete(
    "/{application_id}",
    response_model=ApplicationResponse,
)
async def deactivate_application(
    application_id: int,
    session: AsyncSession = Depends(get_db),
):

    service = ApplicationService(session)

    return await service.deactivate_application(
        application_id
    )