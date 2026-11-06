
from sqlalchemy import select, case

from app.models.log_entry import LogEntry
from app.repositories.base import BaseRepository
from app.core.time import datetime


class LogEntryRepository(BaseRepository[LogEntry]):

    def __init__(self, session):
        super().__init__(session, LogEntry)

    async def get_by_service(
        self,
        service_id: int,
        offset: int = 0,
        limit: int = 100,
    ):
        result = await self.session.execute(
            select(LogEntry)
            .where(LogEntry.service_id == service_id)
            .order_by(LogEntry.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_level(
        self,
        service_id: int,
        level: str,
        offset: int = 0,
        limit: int = 100,
    ):
        result = await self.session.execute(
            select(LogEntry)
            .where(
                LogEntry.service_id == service_id,
                LogEntry.level == level,
            )
            .order_by(LogEntry.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_trace_id(self, trace_id: str):
        result = await self.session.execute(
            select(LogEntry)
            .where(LogEntry.trace_id == trace_id)
            .order_by(LogEntry.timestamp.asc())
        )
        return result.scalars().all()

    async def get_by_time_range(
        self,
        service_id: int,
        start_time,
        end_time,
        offset: int = 0,
        limit: int = 100,
    ):
        result = await self.session.execute(
            select(LogEntry)
            .where(
                LogEntry.service_id == service_id,
                LogEntry.timestamp >= start_time,
                LogEntry.timestamp <= end_time,
            )
            .order_by(LogEntry.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def create_many(
            self,
            entries: list[dict],
    ):
        log_entries = [
            LogEntry(**entry)
            for entry in entries
        ]

        self.session.add_all(log_entries)

        await self.session.flush()

        return log_entries

    async def get_by_filters(
            self,
            service_id: int | None = None,
            service_ids: list[int] | None = None,
            level: str | None = None,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            skip: int = 0,
            limit: int = 100,
    ):
        query = select(LogEntry)

        if service_ids is not None:
            query = query.where(
                LogEntry.service_id.in_(service_ids)
            )
        elif service_id is not None:
            query = query.where(
                LogEntry.service_id == service_id
            )
        else:
            raise ValueError("service_id or service_ids is required")

        if level:
            query = query.where(LogEntry.level == level)

        if start_time:
            query = query.where(
                LogEntry.timestamp >= start_time
            )

        if end_time:
            query = query.where(
                LogEntry.timestamp <= end_time
            )

        query = (
            query
            .order_by(LogEntry.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_for_incident_context(
            self,
            service_ids: list[int],
            start_time,
            end_time,
            limit: int = 100,
    ):
        priority = case(
            (LogEntry.level == "CRITICAL", 0),
            (LogEntry.level == "ERROR", 1),
            (LogEntry.level == "WARNING", 2),
            else_=3,
        )

        result = await self.session.execute(
            select(LogEntry)
            .where(
                LogEntry.service_id.in_(service_ids),
                LogEntry.timestamp >= start_time,
                LogEntry.timestamp <= end_time,
            )
            .order_by(priority, LogEntry.timestamp.desc())
            .limit(limit)
        )

        return result.scalars().all()
