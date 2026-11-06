
import asyncio
from datetime import timedelta

from app.core.database import AsyncSessionLocal
from app.core.time import utc_now
from app.models.monitor_check import MonitorCheck
from app.repositories.monitor_check_repository import (
    MonitorCheckRepository,
)


async def test_consecutive_failures():

    monitor_id = 1  # Use an existing monitor ID

    async with AsyncSessionLocal() as session:

        try:
            now = utc_now()

            # Insert temporary check history.
            checks = [
                MonitorCheck(
                    monitor_id=monitor_id,
                    is_success=False,
                    checked_at=now - timedelta(seconds=3),
                ),
                MonitorCheck(
                    monitor_id=monitor_id,
                    is_success=False,
                    checked_at=now - timedelta(seconds=2),
                ),
                MonitorCheck(
                    monitor_id=monitor_id,
                    is_success=True,
                    checked_at=now - timedelta(seconds=1),
                ),
            ]

            session.add_all(checks)
            await session.flush()

            repository = MonitorCheckRepository(session)

            failures = await repository.get_consecutive_failures(
                monitor_id
            )

            print("Expected: 0")
            print("Actual:", failures)

            assert failures == 0

            print("Test passed!")

        finally:
            # Roll back all temporary records.
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(test_consecutive_failures())
