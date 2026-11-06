
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.log_entry_repository import LogEntryRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.log_entry import LogEntryCreate
from app.core.exceptions import (
    ResourceNotFoundException,
    BusinessRuleException,
)
from sqlalchemy import select

from app.models.service import Service
from app.schemas.log_entry import LogEntryBulkCreate

logger = logging.getLogger(__name__)


class LogEntryService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = LogEntryRepository(session)
        self.service_repository = ServiceRepository(session)

    async def create_log(self, data: LogEntryCreate):

        service = await self.service_repository.get_by_id(
            data.service_id
        )

        if not service:
            raise ResourceNotFoundException("Service not found")

        try:
            log_entry = await self.repository.create(
                data.model_dump()
            )

            await self.session.commit()
            await self.session.refresh(log_entry)

            return log_entry

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to create log entry")
            raise

    async def get_log(self, log_id: int):

        log_entry = await self.repository.get_by_id(log_id)

        if not log_entry:
            raise ResourceNotFoundException(
                "Log entry not found"
            )

        return log_entry

    async def get_service_logs(
            self,
            service_id: int,
            level: str | None = None,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            offset: int = 0,
            limit: int = 100,
    ):

        service = await self.service_repository.get_by_id(
            service_id
        )

        if not service:
            raise ResourceNotFoundException("Service not found")

        if start_time and end_time and start_time > end_time:
            raise BusinessRuleException(
                "Start time cannot be greater than end time"
            )

        if offset < 0:
            raise BusinessRuleException(
                "Offset cannot be negative"
            )

        if limit < 1 or limit > 500:
            raise BusinessRuleException(
                "Limit must be between 1 and 500"
            )

        return await self.repository.get_by_filters(
            service_id=service_id,
            level=level,
            start_time=start_time,
            end_time=end_time,
            skip=offset,
            limit=limit,
        )

    async def get_trace_logs(self, trace_id: str):

        return await self.repository.get_by_trace_id(trace_id)

    async def create_bulk_logs(
            self,
            data: LogEntryBulkCreate,
    ):

        try:
            # Collect unique service IDs.
            service_ids = {
                log.service_id for log in data.logs
            }

            # Validate all services using one database query.
            result = await self.session.execute(
                select(Service.id).where(
                    Service.id.in_(service_ids)
                )
            )

            existing_service_ids = set(result.scalars().all())

            missing_service_ids = service_ids - existing_service_ids

            if missing_service_ids:
                raise ResourceNotFoundException(
                    f"Services not found: {sorted(missing_service_ids)}"
                )

            # Convert schemas into dictionaries.
            entries = [
                log.model_dump()
                for log in data.logs
            ]

            # Bulk insert.
            log_entries = await self.repository.create_many(
                entries
            )

            await self.session.commit()

            logger.info(
                "Successfully ingested %s log entries",
                len(log_entries),
            )

            return log_entries

        except Exception:
            await self.session.rollback()

            logger.exception(
                "Failed to bulk ingest log entries"
            )

            raise
