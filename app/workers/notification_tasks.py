import asyncio

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.repositories.notification_repository import (
    NotificationRepository,
)
from app.workers.celery_app import celery_app
from app.core.enums import NotificationStatus
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService

logger = get_logger(__name__)


async def _dispatch_notifications():

    async with AsyncSessionLocal() as session:
        try:
            repository = NotificationRepository(session)

            notifications = await repository.claim_pending(
                limit=100
            )

            notification_ids = [
                notification.id
                for notification in notifications
            ]

            await session.commit()

        except Exception:
            await session.rollback()
            logger.exception(
                "Failed to claim pending notifications"
            )
            raise

    dispatched = 0

    for notification_id in notification_ids:
        try:
            celery_app.send_task(
                "notifications.send_email",
                args=[notification_id],
            )

            dispatched += 1

        except Exception:
            logger.exception(
                "Failed to dispatch notification %s",
                notification_id,
            )

    logger.info(
        "Notification dispatcher completed | dispatched=%s",
        dispatched,
    )

    return {"dispatched": dispatched}


async def _send_notification(notification_id: int):

    # 1. Fetch notification.
    async with AsyncSessionLocal() as session:

        repository = NotificationRepository(session)

        notification = await repository.get_by_id(
            notification_id
        )

        if notification is None:
            logger.warning(
                "Notification %s not found",
                notification_id,
            )
            return

        if notification.status == NotificationStatus.SENT:
            logger.info(
                "Notification %s already sent",
                notification_id,
            )
            return

        if notification.status != NotificationStatus.PROCESSING:
            logger.warning(
                "Notification %s is not PROCESSING",
                notification_id,
            )
            return

        recipient = notification.recipient
        payload = notification.payload or {}

    # 2. Prepare email.
    event_type = payload.get("event_type", "UPDATED")
    incident_id = payload.get("incident_id")

    subject = (
        f"OpsPilot Alert: Incident #{incident_id} "
        f"{event_type.lower()}"
    )

    body = (
        "OpsPilot Lite Incident Notification\n\n"
        f"Incident ID: {incident_id}\n"
        f"Event: {event_type}\n\n"
        f"{payload.get('message', 'Incident status updated.')}\n"
    )

    # 3. Send email.
    try:
        EmailService.send_email(
            recipient=recipient,
            subject=subject,
            body=body,
        )

    except Exception as exc:

        logger.exception(
            "Email delivery failed for notification %s",
            notification_id,
        )

        async with AsyncSessionLocal() as session:

            service = NotificationService(session)

            await service.handle_failure(
                notification_id=notification_id,
                error=str(exc),
            )

            await session.commit()

        return

    # 4. Mark notification as SENT.
    async with AsyncSessionLocal() as session:

        service = NotificationService(session)

        await service.mark_as_sent(notification_id)

        await session.commit()

    logger.info(
        "Notification %s successfully delivered to %s",
        notification_id,
        recipient,
    )


@celery_app.task(name="notifications.send_email")
def send_email_notification(notification_id: int):

    return asyncio.run(
        _send_notification(notification_id)
    )


@celery_app.task(
    name="notifications.dispatch_pending_notifications"
)
def dispatch_pending_notifications():

    return asyncio.run(
        _dispatch_notifications()
    )