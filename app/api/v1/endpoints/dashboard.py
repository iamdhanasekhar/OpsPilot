from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.schemas.dashboard import DashboardSummaryResponse

from app.services.dashboard_service import DashboardService


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
async def get_dashboard_summary(
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
):

    service = DashboardService(session)

    try:
        return await service.get_dashboard_summary(
            start_time=start_time,
            end_time=end_time,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )