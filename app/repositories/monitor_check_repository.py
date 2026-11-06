from datetime import datetime

from sqlalchemy import select, func, case, and_

from app.models.monitor_check import MonitorCheck
from app.repositories.base import BaseRepository

from app.models.monitor import Monitor
from app.models.service import Service


class MonitorCheckRepository(BaseRepository[MonitorCheck]):

    def __init__(self, session):
        super().__init__(session, MonitorCheck)

    async def get_by_monitor(
        self,
        monitor_id: int,
        offset: int = 0,
        limit: int = 100,
    ):
        result = await self.session.execute(
            select(MonitorCheck)
            .where(MonitorCheck.monitor_id == monitor_id)
            .order_by(MonitorCheck.checked_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_filtered(
        self,
        monitor_id: int,
        is_success: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ):
        query = select(MonitorCheck).where(
            MonitorCheck.monitor_id == monitor_id
        )

        if is_success is not None:
            query = query.where(
                MonitorCheck.is_success == is_success
            )

        result = await self.session.execute(
            query
            .order_by(MonitorCheck.checked_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_latest_checks(
            self,
            monitor_id: int,
            limit: int = 100,
    ):
        result = await self.session.execute(
            select(MonitorCheck)
            .where(
                MonitorCheck.monitor_id == monitor_id
            )
            .order_by(
                MonitorCheck.checked_at.desc(),
                MonitorCheck.id.desc(),
            )
            .limit(limit)
        )

        return result.scalars().all()

    async def get_consecutive_failures(
            self,
            monitor_id: int,
    ):
        checks = await self.get_latest_checks(
            monitor_id=monitor_id,
        )

        failures = 0

        for check in checks:
            if check.is_success:
                break

            failures += 1

        return failures

    async def get_dashboard_counts(
        self,
        start_time=None,
        end_time=None,
    ):
        query = select(
            func.count(MonitorCheck.id),
            func.sum(
                case((MonitorCheck.is_success.is_(True), 1), else_=0)
            ),
            func.sum(
                case((MonitorCheck.is_success.is_(False), 1), else_=0)
            ),
        )

        if start_time is not None:
            query = query.where(
                MonitorCheck.checked_at >= start_time
            )

        if end_time is not None:
            query = query.where(
                MonitorCheck.checked_at < end_time
            )

        result = await self.session.execute(query)

        total, successful, failed = result.one()

        return {
            "total": total or 0,
            "successful": successful or 0,
            "failed": failed or 0,
        }

    async def get_latest_checks_by_service(self):
        latest_checks = (
            select(
                MonitorCheck.monitor_id.label("monitor_id"),
                MonitorCheck.is_success.label("is_success"),
                func.row_number().over(
                    partition_by=MonitorCheck.monitor_id,
                    order_by=(
                        MonitorCheck.checked_at.desc(),
                        MonitorCheck.id.desc(),
                    ),
                ).label("row_num"),
            )
            .subquery()
        )

        query = (
            select(
                Service.id.label("service_id"),
                Service.name.label("service_name"),
                Service.is_active.label("service_is_active"),
                Monitor.id.label("monitor_id"),
                latest_checks.c.is_success.label("is_success"),
            )
            .select_from(Service)
            .outerjoin(
                Monitor,
                and_(
                    Monitor.service_id == Service.id,
                    Monitor.is_active.is_(True),
                ),
            )
            .outerjoin(
                latest_checks,
                and_(
                    latest_checks.c.monitor_id == Monitor.id,
                    latest_checks.c.row_num == 1,
                ),
            )
            .order_by(Service.id)
        )

        result = await self.session.execute(query)

        return result.all()

    async def get_monitor_health_stats(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        # Latest check for each monitor (all-time).
        latest_checks = (
            select(
                MonitorCheck.monitor_id.label("monitor_id"),
                MonitorCheck.is_success.label("is_success"),
                MonitorCheck.checked_at.label("checked_at"),
                func.row_number().over(
                    partition_by=MonitorCheck.monitor_id,
                    order_by=(
                        MonitorCheck.checked_at.desc(),
                        MonitorCheck.id.desc(),
                    ),
                ).label("row_num"),
            )
            .subquery()
        )

        # Check counts within the requested time range.
        check_stats_query = select(
            MonitorCheck.monitor_id.label("monitor_id"),
            func.count(MonitorCheck.id).label("total_checks"),
            func.sum(
                case(
                    (MonitorCheck.is_success.is_(True), 1),
                    else_=0,
                )
            ).label("successful_checks"),
            func.sum(
                case(
                    (MonitorCheck.is_success.is_(False), 1),
                    else_=0,
                )
            ).label("failed_checks"),
        )

        if start_time is not None:
            check_stats_query = check_stats_query.where(
                MonitorCheck.checked_at >= start_time
            )

        if end_time is not None:
            check_stats_query = check_stats_query.where(
                MonitorCheck.checked_at < end_time
            )

        check_stats = (
            check_stats_query
            .group_by(MonitorCheck.monitor_id)
            .subquery()
        )

        query = (
            select(
                Monitor.id.label("monitor_id"),
                Monitor.name.label("monitor_name"),
                Monitor.target_url.label("target_url"),
                Monitor.is_active.label("monitor_is_active"),
                Service.id.label("service_id"),
                Service.name.label("service_name"),
                Service.is_active.label("service_is_active"),
                latest_checks.c.is_success.label("latest_check_success"),
                latest_checks.c.checked_at.label("latest_checked_at"),
                check_stats.c.total_checks.label("total_checks"),
                check_stats.c.successful_checks.label("successful_checks"),
                check_stats.c.failed_checks.label("failed_checks"),
            )
            .select_from(Monitor)
            .join(Service, Service.id == Monitor.service_id)
            .outerjoin(
                latest_checks,
                and_(
                    latest_checks.c.monitor_id == Monitor.id,
                    latest_checks.c.row_num == 1,
                ),
            )
            .outerjoin(
                check_stats,
                check_stats.c.monitor_id == Monitor.id,
            )
            .order_by(Monitor.id)
        )

        result = await self.session.execute(query)
        return result.all()
