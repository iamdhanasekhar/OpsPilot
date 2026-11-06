
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.services.monitor_service import MonitorService

from app.schemas.monitor import (
    MonitorCreate,
    MonitorUpdate,
    MonitorResponse,
)


router = APIRouter(
    prefix="/monitors",
    tags=["Monitors"],
)


@router.post("/", response_model=MonitorResponse, status_code=201)
async def create_monitor(
    data: MonitorCreate,
    session: AsyncSession = Depends(get_db),
):
    return await MonitorService(session).create_monitor(data)


@router.get("/", response_model=list[MonitorResponse])
async def list_monitors(
    service_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_db),
):
    return await MonitorService(session).list_monitors(
        service_id, offset, limit, is_active
    )


@router.get("/{monitor_id}", response_model=MonitorResponse)
async def get_monitor(
    monitor_id: int,
    session: AsyncSession = Depends(get_db),
):
    return await MonitorService(session).get_monitor(monitor_id)


@router.patch("/{monitor_id}", response_model=MonitorResponse)
async def update_monitor(
    monitor_id: int,
    data: MonitorUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await MonitorService(session).update_monitor(
        monitor_id, data
    )


@router.delete("/{monitor_id}", response_model=MonitorResponse)
async def deactivate_monitor(
    monitor_id: int,
    session: AsyncSession = Depends(get_db),
):
    return await MonitorService(session).deactivate_monitor(monitor_id)
