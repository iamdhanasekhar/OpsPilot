from datetime import datetime, timedelta

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.time import utc_now
from app.core.enums import NotificationStatus
from app.models.notification import Notification


class NotificationRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Notification:
        notification = Notification(**data)

        self.session.add(notification)
        await self.session.flush()

        return notification

    async def get_by_id(self, notification_id: int):
        result = await self.session.execute(
            select(Notification).where(
                Notification.id == notification_id
            )
        )

        return result.scalar_one_or_none()

    async def get_pending(self, limit: int = 100):
        result = await self.session.execute(
            select(Notification)
            .where(
                Notification.status == NotificationStatus.PENDING,
                Notification.next_attempt_at <= utc_now(),
            )
            .order_by(Notification.created_at.asc())
            .limit(limit)
        )

        return result.scalars().all()

    async def mark_sent(self, notification: Notification):
        notification.status = NotificationStatus.SENT
        notification.sent_at = utc_now()
        notification.locked_at = None
        notification.last_error = None

        await self.session.flush()

    async def schedule_retry(
        self,
        notification: Notification,
        error: str,
        next_attempt_at: datetime,
        terminal: bool = False,
    ):
        notification.status = (
            NotificationStatus.FAILED
            if terminal
            else NotificationStatus.PENDING
        )

        notification.attempt_count += 1
        notification.last_error = error
        notification.next_attempt_at = next_attempt_at
        notification.locked_at = None

        await self.session.flush()

    async def claim_pending(self, limit: int = 100):
        now = utc_now()
        stale_threshold = now - timedelta(minutes=5)

        result = await self.session.execute(
            select(Notification)
            .where(
                or_(
                    (
                            (Notification.status == NotificationStatus.PENDING)
                            & (Notification.next_attempt_at <= now)
                    ),
                    (
                            (Notification.status == NotificationStatus.PROCESSING)
                            & (
                                Notification.locked_at.is_not(None)
                            )
                            & (
                                    Notification.locked_at <= stale_threshold
                            )
                    ),
                )
            )
            .order_by(Notification.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        notifications = result.scalars().all()

        for notification in notifications:
            notification.status = NotificationStatus.PROCESSING
            notification.locked_at = now

        await self.session.flush()

        return notifications

    async def get_by_filters(
            self,
            incident_id: int | None = None,
            status: NotificationStatus | None = None,
            limit: int = 50,
            offset: int = 0,
    ):
        query = select(Notification)

        if incident_id is not None:
            query = query.where(
                Notification.incident_id == incident_id
            )

        if status is not None:
            query = query.where(
                Notification.status == status
            )

        query = (
            query
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def count_by_filters(
            self,
            incident_id: int | None = None,
            status: NotificationStatus | None = None,
    ):
        query = select(func.count(Notification.id))

        if incident_id is not None:
            query = query.where(
                Notification.incident_id == incident_id
            )

        if status is not None:
            query = query.where(
                Notification.status == status
            )

        result = await self.session.execute(query)

        return result.scalar_one()

    async def get_by_id_for_update(self, notification_id: int):
        result = await self.session.execute(
            select(Notification)
            .where(Notification.id == notification_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def retry_failed(self, notification: Notification):
        notification.status = NotificationStatus.PENDING
        notification.attempt_count = 0
        notification.next_attempt_at = utc_now()
        notification.last_error = None
        notification.locked_at = None
        notification.sent_at = None

        await self.session.flush()
