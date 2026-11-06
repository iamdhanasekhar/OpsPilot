
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResourceNotFoundException,
    ResourceConflictException,
    BusinessRuleException,
)
from app.core.logger import get_logger

from app.models.monitor import Monitor

from app.repositories.monitor_repository import MonitorRepository
from app.repositories.service_repository import ServiceRepository

from app.schemas.monitor import MonitorCreate, MonitorUpdate


logger = get_logger(__name__)


class MonitorService:

    def __init__(self, session: AsyncSession):

        self.session = session

        self.repository = MonitorRepository(session)

        self.service_repository = ServiceRepository(session)

    async def create_monitor(
        self,
        data: MonitorCreate,
    ) -> Monitor:

        service = await self.service_repository.get_by_id(
            data.service_id
        )

        if not service:
            raise ResourceNotFoundException("Service not found")

        if not service.is_active:
            raise BusinessRuleException(
                "Cannot create monitor for an inactive service"
            )

        existing = await self.repository.get_by_name(
            data.service_id,
            data.name,
        )

        if existing:
            raise ResourceConflictException(
                "Monitor name already exists for this service"
            )

        monitor = Monitor(**data.model_dump())

        try:

            await self.repository.create(monitor)

            await self.session.commit()

            await self.session.refresh(monitor)

            logger.info(
                "Monitor created | id=%s | service_id=%s",
                monitor.id,
                monitor.service_id,
            )

            return monitor

        except Exception:

            await self.session.rollback()
            raise

    async def get_monitor(self, monitor_id: int) -> Monitor:

        monitor = await self.repository.get_by_id(monitor_id)

        if not monitor:
            raise ResourceNotFoundException("Monitor not found")

        return monitor

    async def list_monitors(
        self,
        service_id: int,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ):

        service = await self.service_repository.get_by_id(
            service_id
        )

        if not service:
            raise ResourceNotFoundException("Service not found")

        return await self.repository.get_by_service(
            service_id,
            offset,
            limit,
            is_active,
        )

    async def update_monitor(
        self,
        monitor_id: int,
        data: MonitorUpdate,
    ) -> Monitor:

        monitor = await self.get_monitor(monitor_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            raise BusinessRuleException(
                "At least one field must be provided"
            )

        for field, value in update_data.items():

            if value is None and field != "target_url":
                raise BusinessRuleException(
                    f"{field} cannot be null"
                )

        try:

            for field, value in update_data.items():
                setattr(monitor, field, value)

            await self.session.commit()

            await self.session.refresh(monitor)

            logger.info("Monitor updated | id=%s", monitor.id)

            return monitor

        except Exception:

            await self.session.rollback()
            raise

    async def deactivate_monitor(
        self,
        monitor_id: int,
    ) -> Monitor:

        monitor = await self.get_monitor(monitor_id)

        if not monitor.is_active:
            raise BusinessRuleException(
                "Monitor is already inactive"
            )

        try:

            monitor.is_active = False

            await self.session.commit()

            await self.session.refresh(monitor)

            logger.info("Monitor deactivated | id=%s", monitor.id)

            return monitor

        except Exception:

            await self.session.rollback()
            raise
