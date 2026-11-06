from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.enums import NotificationStatus
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_notification_service(
    session: AsyncSession = Depends(get_db),
):
    return NotificationService(session)


@router.get(
    "",
    response_model=NotificationListResponse,
)
async def list_notifications(
    incident_id: int | None = None,
    status: NotificationStatus | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: NotificationService = Depends(get_notification_service),
):
    return await service.list_notifications(
        incident_id=incident_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
async def get_notification(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.get_notification(notification_id)


@router.post(
    "/{notification_id}/retry",
    response_model=NotificationResponse,
)
async def retry_notification(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service),
):
    return await service.retry_notification(notification_id)