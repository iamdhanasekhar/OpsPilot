from datetime import timedelta
from app.models.monitor import Monitor
from app.repositories.base import BaseRepository
from app.core.time import utc_now
from sqlalchemy import select, func, case


class MonitorRepository(BaseRepository[Monitor]):

    def __init__(self, session):
        super().__init__(session, Monitor)

    async def get_by_service(
        self,
        service_id: int,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ):
        query = select(Monitor).where(
            Monitor.service_id == service_id
        )

        if is_active is not None:
            query = query.where(
                Monitor.is_active == is_active
            )

        query = (
            query
            .order_by(Monitor.id.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def get_active_monitors(self):
        result = await self.session.execute(
            select(Monitor).where(
                Monitor.is_active.is_(True)
            )
        )

        return result.scalars().all()

    async def get_due_monitors(
        self,
        limit: int = 100,
    ):
        now = utc_now()

        query = (
            select(Monitor)
            .where(
                Monitor.is_active.is_(True),
                Monitor.next_check_at <= now,
            )
            .order_by(Monitor.next_check_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        result = await self.session.execute(query)

        monitors = result.scalars().all()

        # Claim each monitor by advancing its next check time.
        for monitor in monitors:
            monitor.next_check_at = (
                now + timedelta(
                    seconds=monitor.interval_seconds
                )
            )

        await self.session.flush()

        return monitors

    async def get_by_name(
        self,
        service_id: int,
        name: str,
    ):
        result = await self.session.execute(
            select(Monitor).where(
                Monitor.service_id == service_id,
                Monitor.name == name,
            )
        )

        return result.scalar_one_or_none()

    async def get_dashboard_counts(self):
        result = await self.session.execute(
            select(
                func.count(Monitor.id),
                func.sum(
                    case((Monitor.is_active.is_(True), 1), else_=0)
                ),
                func.sum(
                    case((Monitor.is_active.is_(False), 1), else_=0)
                ),
            )
        )

        total, active, inactive = result.one()

        return {
            "total": total or 0,
            "active": active or 0,
            "inactive": inactive or 0,
        }
