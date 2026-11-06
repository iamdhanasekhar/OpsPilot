from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "opspilot",
    broker=settings.CELERY_BROKER_URL,
    backend="rpc://",
    include=[
        "app.workers.monitor_tasks",
        "app.workers.notification_tasks",
        "app.workers.ai_tasks",
    ]
)


celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,

    # Results
    task_ignore_result=True,

    # Connection reliability
    broker_connection_retry_on_startup=True,

    # Periodic scheduling
    beat_schedule={
        "schedule-monitors-every-5-seconds": {
            "task": "monitoring.schedule_due_monitors",
            "schedule": 5.0,
        },
        "dispatch-notifications-every-5-seconds": {
            "task": "notifications.dispatch_pending_notifications",
            "schedule": 5.0,
        },
    },
)

# Force-import to guarantee task registration
from app.workers import monitor_tasks
from app.workers import notification_tasks
from app.workers import ai_tasks