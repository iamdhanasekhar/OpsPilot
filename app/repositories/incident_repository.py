from app.core.enums import IncidentStatus
from app.models.incident import Incident
from app.repositories.base import BaseRepository
from sqlalchemy import select, func, union
from sqlalchemy import literal_column
from app.models.incident_service import IncidentService
from datetime import datetime


class IncidentRepository(BaseRepository[Incident]):

    def __init__(self, session):
        super().__init__(session, Incident)

    async def get_by_service(
        self,
        service_id: int,
        offset: int = 0,
        limit: int = 100,
    ):
        result = await self.session.execute(
            select(Incident)
            .where(Incident.service_id == service_id)
            .order_by(Incident.started_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_filtered(
        self,
        service_id: int | None = None,
        status=None,
        severity=None,
        offset: int = 0,
        limit: int = 100,
    ):
        query = select(Incident)

        if service_id is not None:
            query = query.where(
                Incident.service_id == service_id
            )

        if status is not None:
            query = query.where(Incident.status == status)

        if severity is not None:
            query = query.where(Incident.severity == severity)

        result = await self.session.execute(
            query
            .order_by(Incident.started_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_by_service(self, service_id: int):
        result = await self.session.execute(
            select(Incident)
            .where(
                Incident.service_id == service_id,
                Incident.status.in_([
                    IncidentStatus.OPEN,
                    IncidentStatus.ACKNOWLEDGED,
                ]),
            )
            .order_by(Incident.started_at.desc())
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def count_by_severity(
            self,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
    ):
        filters = self._get_analytics_filters(start_time, end_time)

        result = await self.session.execute(
            select(
                Incident.severity,
                func.count(Incident.id).label("count"),
            )
            .where(*filters)
            .group_by(Incident.severity)
        )

        return result.all()

    async def count_by_status(
            self,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
    ):
        filters = self._get_analytics_filters(start_time, end_time)

        result = await self.session.execute(
            select(
                Incident.status,
                func.count(Incident.id).label("count"),
            )
            .where(*filters)
            .group_by(Incident.status)
        )

        return result.all()

    async def count_by_service(
            self,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
    ):
        filters = self._get_analytics_filters(start_time, end_time)

        filtered_incidents = (
            select(
                Incident.id.label("incident_id"),
                Incident.service_id.label("service_id"),
            )
            .where(*filters)
            .subquery()
        )

        # Primary service associations
        primary_services = select(
            filtered_incidents.c.incident_id,
            filtered_incidents.c.service_id,
        )

        # Affected service associations
        affected_services = (
            select(
                filtered_incidents.c.incident_id,
                IncidentService.service_id,
            )
            .join(
                IncidentService,
                IncidentService.incident_id
                == filtered_incidents.c.incident_id,
            )
        )

        # Remove duplicate incident-service associations
        all_services = union(
            primary_services,
            affected_services,
        ).subquery()

        result = await self.session.execute(
            select(
                all_services.c.service_id,
                func.count(all_services.c.incident_id).label("count"),
            )
            .group_by(all_services.c.service_id)
            .order_by(all_services.c.service_id)
        )

        return result.all()

    async def get_average_mttr(
            self,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
    ):
        filters = self._get_analytics_filters(start_time, end_time)

        filters.append(Incident.resolved_at.is_not(None))

        result = await self.session.execute(
            select(
                func.avg(
                    func.timestampdiff(
                        literal_column("SECOND"),
                        Incident.started_at,
                        Incident.resolved_at,
                    )
                )
            )
            .where(*filters)
        )

        return result.scalar_one()

    def _get_analytics_filters(
            self,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
    ):
        filters = []

        if start_time is not None:
            filters.append(Incident.started_at >= start_time)

        if end_time is not None:
            filters.append(Incident.started_at < end_time)

        return filters

    async def get_incident_trends(
            self,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            interval: str = "day",
    ):
        # Map supported intervals to MySQL date formats
        interval_formats = {
            "hour": "%Y-%m-%d %H:00:00",
            "day": "%Y-%m-%d 00:00:00",
        }

        if interval not in interval_formats:
            raise ValueError("Unsupported trend interval")

        date_format = interval_formats[interval]

        filters = self._get_analytics_filters(
            start_time,
            end_time,
        )

        # Group incidents into hourly or daily buckets
        time_bucket = func.date_format(
            Incident.started_at,
            date_format,
        ).label("timestamp")

        result = await self.session.execute(
            select(
                time_bucket,
                func.count(Incident.id).label("count"),
            )
            .where(*filters)
            .group_by(time_bucket)
            .order_by(time_bucket)
        )

        return result.all()

    async def get_mttr_trends(
            self,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            interval: str = "day",
    ):
        interval_formats = {
            "hour": "%Y-%m-%d %H:00:00",
            "day": "%Y-%m-%d 00:00:00",
        }

        if interval not in interval_formats:
            raise ValueError("Unsupported trend interval")

        date_format = interval_formats[interval]

        filters = [
            Incident.resolved_at.is_not(None)
        ]

        # Filter by resolution timestamp
        if start_time is not None:
            filters.append(
                Incident.resolved_at >= start_time
            )

        if end_time is not None:
            filters.append(
                Incident.resolved_at < end_time
            )

        time_bucket = func.date_format(
            Incident.resolved_at,
            date_format,
        ).label("timestamp")

        result = await self.session.execute(
            select(
                time_bucket,
                func.avg(
                    func.timestampdiff(
                        literal_column("SECOND"),
                        Incident.started_at,
                        Incident.resolved_at,
                    )
                ).label("average_mttr_seconds"),
            )
            .where(*filters)
            .group_by(time_bucket)
            .order_by(time_bucket)
        )

        return result.all()

