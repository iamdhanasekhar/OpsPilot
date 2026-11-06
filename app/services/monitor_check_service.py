
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.monitor_check_repository import MonitorCheckRepository
from app.repositories.monitor_repository import MonitorRepository
from app.schemas.monitor_check import MonitorCheckCreate
from app.core.exceptions import ResourceNotFoundException, BusinessRuleException


logger = logging.getLogger(__name__)


class MonitorCheckService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = MonitorCheckRepository(session)
        self.monitor_repository = MonitorRepository(session)

    async def create_check(
        self,
        monitor_id: int,
        data: MonitorCheckCreate,
    ):

        monitor = await self.monitor_repository.get_by_id(monitor_id)

        if not monitor:
            raise ResourceNotFoundException(
                f"Monitor with id {monitor_id} not found"
            )

        if data.is_success and data.error_message:
            raise BusinessRuleException(
                "A successful monitor check cannot contain an error message"
            )

        if not data.is_success and data.status_code is None and not data.error_message:
            raise BusinessRuleException(
                "A failed monitor check must contain a status code or error message"
            )

        try:
            check = await self.repository.create(
                {
                    "monitor_id": monitor_id,
                    **data.model_dump(),
                }
            )

            await self.session.commit()
            await self.session.refresh(check)

            return check

        except Exception:
            await self.session.rollback()
            logger.exception(
                "Failed to create monitor check for monitor %s",
                monitor_id,
            )
            raise

    async def get_check(self, check_id: int):

        check = await self.repository.get_by_id(check_id)

        if not check:
            raise ResourceNotFoundException(
                f"Monitor check with id {check_id} not found"
            )

        return check

    async def get_monitor_checks(
        self,
        monitor_id: int,
        is_success: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ):

        monitor = await self.monitor_repository.get_by_id(monitor_id)

        if not monitor:
            raise ResourceNotFoundException(
                f"Monitor with id {monitor_id} not found"
            )

        return await self.repository.get_filtered(
            monitor_id=monitor_id,
            is_success=is_success,
            offset=offset,
            limit=limit,
        )
