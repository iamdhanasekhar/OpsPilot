
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.monitor_check import (
    MonitorCheckCreate,
    MonitorCheckResponse,
)
from app.services.monitor_check_service import MonitorCheckService


router = APIRouter(
    tags=["Monitor Checks"]
)


@router.post(
    "/monitors/{monitor_id}/checks",
    response_model=MonitorCheckResponse,
    status_code=201,
)
async def create_monitor_check(
    monitor_id: int,
    data: MonitorCheckCreate,
    session: AsyncSession = Depends(get_db),
):
    service = MonitorCheckService(session)

    return await service.create_check(monitor_id, data)


@router.get(
    "/monitors/{monitor_id}/checks",
    response_model=list[MonitorCheckResponse],
)
async def get_monitor_checks(
    monitor_id: int,
    is_success: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    service = MonitorCheckService(session)

    return await service.get_monitor_checks(
        monitor_id=monitor_id,
        is_success=is_success,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/monitor-checks/{check_id}",
    response_model=MonitorCheckResponse,
)
async def get_monitor_check(
    check_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = MonitorCheckService(session)

    return await service.get_check(check_id)
