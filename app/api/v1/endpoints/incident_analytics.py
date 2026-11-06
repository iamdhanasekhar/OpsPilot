from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.incident_analytics import IncidentAnalyticsResponse
from app.services.incident_analytics_service import IncidentAnalyticsService
from typing import Literal
from app.schemas.incident_trend import IncidentTrendResponse
from app.schemas.mttr_trend import MTTRTrendResponse


router = APIRouter(
    prefix="/incident-analytics",
    tags=["Incident Analytics"],
)


@router.get("/", response_model=IncidentAnalyticsResponse)
async def get_incident_analytics(
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    service = IncidentAnalyticsService(session)

    try:
        return await service.get_incident_analytics(
            start_time=start_time,
            end_time=end_time,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get(
    "/trends",
    response_model=IncidentTrendResponse,
)
async def get_incident_trends(
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    interval: Literal["hour", "day"] = Query(default="day"),
    session: AsyncSession = Depends(get_db),
):
    service = IncidentAnalyticsService(session)

    try:
        return await service.get_incident_trends(
            start_time=start_time,
            end_time=end_time,
            interval=interval,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get(
    "/mttr-trends",
    response_model=MTTRTrendResponse,
)
async def get_mttr_trends(
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    interval: Literal["hour", "day"] = Query(default="day"),
    session: AsyncSession = Depends(get_db),
):
    service = IncidentAnalyticsService(session)

    try:
        return await service.get_mttr_trends(
            start_time=start_time,
            end_time=end_time,
            interval=interval,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
