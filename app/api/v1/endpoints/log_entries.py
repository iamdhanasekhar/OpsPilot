
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.log_entry_service import LogEntryService
from app.schemas.log_entry import (
    LogEntryCreate,
    LogEntryResponse,
    LogEntryBulkCreate,
)

router = APIRouter(
    prefix="/logs",
    tags=["Log Entries"],
)


@router.post(
    "",
    response_model=LogEntryResponse,
    status_code=201,
)
async def create_log(
    data: LogEntryCreate,
    session: AsyncSession = Depends(get_db),
):
    service = LogEntryService(session)
    return await service.create_log(data)


@router.get(
    "/trace/{trace_id}",
    response_model=list[LogEntryResponse],
)
async def get_trace_logs(
    trace_id: str,
    session: AsyncSession = Depends(get_db),
):
    service = LogEntryService(session)
    return await service.get_trace_logs(trace_id)


@router.get(
    "/{log_id}",
    response_model=LogEntryResponse,
)
async def get_log(
    log_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = LogEntryService(session)
    return await service.get_log(log_id)


@router.get(
    "/services/{service_id}/logs",
    response_model=list[LogEntryResponse],
)
async def get_service_logs(
    service_id: int,
    level: str | None = Query(default=None),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    service = LogEntryService(session)

    return await service.get_service_logs(
        service_id=service_id,
        level=level,
        start_time=start_time,
        end_time=end_time,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/bulk",
    response_model=list[LogEntryResponse],
    status_code=201,
)
async def create_bulk_logs(
    data: LogEntryBulkCreate,
    session: AsyncSession = Depends(get_db),
):

    service = LogEntryService(session)

    return await service.create_bulk_logs(data)
