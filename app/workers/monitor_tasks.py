import asyncio
import time

import httpx

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.time import utc_now
from app.core import logger

from app.models.monitor import Monitor
from app.models.monitor_check import MonitorCheck

from app.workers.celery_app import celery_app

from app.services.monitoring_service import MonitoringService
from app.repositories.monitor_repository import MonitorRepository

logger = logger.get_logger(__name__)


async def _get_due_monitor_ids():
    async with AsyncSessionLocal() as session:

        repository = MonitorRepository(session)

        monitors = await repository.get_due_monitors()

        monitor_ids = [
            monitor.id for monitor in monitors
        ]

        # Persist next_check_at before dispatching tasks.
        await session.commit()

        return monitor_ids


@celery_app.task(name="monitoring.schedule_due_monitors")
def schedule_due_monitors():

    monitor_ids = asyncio.run(
        _get_due_monitor_ids()
    )

    for monitor_id in monitor_ids:
        execute_monitor.delay(monitor_id)

    logger.info(
        "Dispatched %s monitoring tasks",
        len(monitor_ids)
    )

    return {
        "dispatched": len(monitor_ids)
    }


async def _execute_monitor(monitor_id: int):

    # 1. Fetch monitor configuration.
    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Monitor).where(
                Monitor.id == monitor_id,
                Monitor.is_active.is_(True),
            )
        )

        monitor = result.scalar_one_or_none()

        if monitor is None:
            logger.warning(
                "Monitor %s not found or inactive",
                monitor_id
            )
            return

        # Copy configuration before closing session.
        config = {
            "target_url": monitor.target_url,
            "method": monitor.method,
            "expected_status_code": monitor.expected_status_code,
            "timeout_seconds": monitor.timeout_seconds,
        }

    # 2. Execute HTTP health check.
    status_code = None
    response_time_ms = None
    error_message = None
    is_success = False

    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(
            timeout=config["timeout_seconds"],
            follow_redirects=True,
        ) as client:

            response = await client.request(
                method=config["method"],
                url=config["target_url"],
            )

            status_code = response.status_code

            is_success = (
                status_code == config["expected_status_code"]
            )

            if not is_success:
                error_message = (
                    f"Expected HTTP "
                    f"{config['expected_status_code']}, "
                    f"received {status_code}"
                )

    except httpx.TimeoutException:
        error_message = "Request timed out"

    except httpx.RequestError as exc:
        error_message = f"HTTP request failed: {str(exc)}"

    except (httpx.HTTPError, ValueError) as exc:
        error_message = f"Invalid HTTP request: {str(exc)}"

    finally:
        response_time_ms = round(
            (time.perf_counter() - start_time) * 1000
        )

    # 3. Process and persist monitoring result.
    async with AsyncSessionLocal() as session:

        monitoring_service = MonitoringService(session)

        result = await monitoring_service.process_check(
            monitor_id=monitor_id,
            is_success=is_success,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_message=error_message,
        )

    logger.info(
        "Monitor %s completed | success=%s | status=%s | response_time=%sms",
        monitor_id,
        is_success,
        status_code,
        response_time_ms,
    )

    return result


@celery_app.task(name="monitoring.execute_monitor")
def execute_monitor(monitor_id: int):

    return asyncio.run(
        _execute_monitor(monitor_id)
    )