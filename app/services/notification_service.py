from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException, BusinessRuleException
from app.core.logger import get_logger
from app.core.time import utc_now
from app.repositories.notification_repository import NotificationRepository
from app.core.enums import NotificationChannel, NotificationStatus

logger = get_logger(__name__)


class NotificationService:

    MAX_ATTEMPTS = 5
    INITIAL_RETRY_DELAY_SECONDS = 30
    MAX_RETRY_DELAY_SECONDS = 3600

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = NotificationRepository(session)

    async def create_notification(
        self,
        incident_id: int,
        incident_event_id: int,
        recipient: str,
        payload: dict,
    ):
        """
        Create a pending notification.

        Does not commit: the caller must commit this together
        with the corresponding incident event.
        """

        notification = await self.repository.create({
            "incident_id": incident_id,
            "incident_event_id": incident_event_id,
            "channel": NotificationChannel.EMAIL,
            "recipient": recipient,
            "payload": payload,
            "status": NotificationStatus.PENDING,
        })

        logger.info(
            "Notification created for incident %s",
            incident_id,
        )

        return notification

    async def mark_as_sent(self, notification_id: int):
        notification = await self.repository.get_by_id(notification_id)

        if not notification:
            logger.warning(
                "Notification %s not found",
                notification_id,
            )
            return None

        await self.repository.mark_sent(notification)

        logger.info(
            "Notification %s marked as sent",
            notification_id,
        )

        return notification

    async def handle_failure(
        self,
        notification_id: int,
        error: str,
    ):
        notification = await self.repository.get_by_id(notification_id)

        if not notification:
            logger.warning(
                "Notification %s not found",
                notification_id,
            )
            return None

        next_attempt_count = notification.attempt_count + 1

        terminal = next_attempt_count >= self.MAX_ATTEMPTS

        if terminal:
            next_attempt_at = utc_now()
        else:
            delay = min(
                self.INITIAL_RETRY_DELAY_SECONDS
                * (2 ** (next_attempt_count - 1)),
                self.MAX_RETRY_DELAY_SECONDS,
            )

            next_attempt_at = utc_now() + timedelta(seconds=delay)

        await self.repository.schedule_retry(
            notification=notification,
            error=error,
            next_attempt_at=next_attempt_at,
            terminal=terminal,
        )

        if terminal:
            logger.error(
                "Notification %s permanently failed after %s attempts",
                notification_id,
                next_attempt_count,
            )
        else:
            logger.warning(
                "Notification %s failed. Retry scheduled in %s seconds",
                notification_id,
                delay,
            )

        return notification

    async def get_notification(self, notification_id: int):
        notification = await self.repository.get_by_id(notification_id)

        if not notification:
            raise ResourceNotFoundException(
                f"Notification {notification_id} not found"
            )

        return notification

    async def list_notifications(
            self,
            incident_id: int | None = None,
            status: NotificationStatus | None = None,
            limit: int = 50,
            offset: int = 0,
    ):
        if limit < 1 or limit > 100:
            raise BusinessRuleException("Limit must be between 1 and 100")

        if offset < 0:
            raise BusinessRuleException("Offset cannot be negative")

        items = await self.repository.get_by_filters(
            incident_id=incident_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        total = await self.repository.count_by_filters(
            incident_id=incident_id,
            status=status,
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": items,
        }

    async def retry_notification(self, notification_id: int):
        notification = await self.repository.get_by_id_for_update(
            notification_id
        )

        if not notification:
            raise ResourceNotFoundException(
                f"Notification {notification_id} not found"
            )

        if notification.status != NotificationStatus.FAILED:
            raise BusinessRuleException(
                "Only failed notifications can be manually retried"
            )

        await self.repository.retry_failed(notification)

        await self.session.commit()
        await self.session.refresh(notification)

        return notification