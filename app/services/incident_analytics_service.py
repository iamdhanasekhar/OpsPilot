from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident_trend import (
    IncidentTrendResponse,
    IncidentTrendPoint,
)

from app.schemas.incident_analytics import (
    IncidentAnalyticsResponse,
    IncidentCountBySeverity,
    IncidentCountByStatus,
    IncidentCountByService,
)
from app.schemas.mttr_trend import (
    MTTRTrendResponse,
    MTTRTrendPoint,
)


class IncidentAnalyticsService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.incident_repository = IncidentRepository(session)

    async def get_incident_analytics(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> IncidentAnalyticsResponse:

        # 1. Validate date range
        if (
            start_time is not None
            and end_time is not None
            and start_time >= end_time
        ):
            raise ValueError(
                "start_time must be earlier than end_time"
            )

        # 2. Get incident counts grouped by severity
        severity_counts = (
            await self.incident_repository.count_by_severity(
                start_time, end_time
            )
        )

        # 3. Get incident counts grouped by status
        status_counts = (
            await self.incident_repository.count_by_status(
                start_time, end_time
            )
        )

        # 4. Get incident counts grouped by service
        service_counts = (
            await self.incident_repository.count_by_service(
                start_time, end_time
            )
        )

        # 5. Calculate average MTTR
        average_mttr = (
            await self.incident_repository.get_average_mttr(
                start_time, end_time
            )
        )

        # 6. Calculate total incidents
        total_incidents = sum(
            count for _, count in status_counts
        )

        # 7. Construct severity response
        by_severity = [
            IncidentCountBySeverity(
                severity=severity,
                count=count,
            )
            for severity, count in severity_counts
        ]

        # 8. Construct status response
        by_status = [
            IncidentCountByStatus(
                status=status,
                count=count,
            )
            for status, count in status_counts
        ]

        # 9. Construct service response
        by_service = [
            IncidentCountByService(
                service_id=service_id,
                count=count,
            )
            for service_id, count in service_counts
        ]

        # 10. Assemble final analytics response
        return IncidentAnalyticsResponse(
            total_incidents=total_incidents,
            by_severity=by_severity,
            by_status=by_status,
            by_service=by_service,
            average_mttr_seconds=(
                float(average_mttr)
                if average_mttr is not None
                else None
            ),
        )

    async def get_incident_trends(
            self,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            interval: str = "day",
    ) -> IncidentTrendResponse:

        # 1. Validate date range
        if (
                start_time is not None
                and end_time is not None
                and start_time >= end_time
        ):
            raise ValueError(
                "start_time must be earlier than end_time"
            )

        # 2. Fetch aggregated trend data
        trend_counts = await self.incident_repository.get_incident_trends(
            start_time=start_time,
            end_time=end_time,
            interval=interval,
        )

        # 3. Construct response data
        data = [
            IncidentTrendPoint(
                timestamp=timestamp,
                count=count,
            )
            for timestamp, count in trend_counts
        ]

        # 4. Return response
        return IncidentTrendResponse(
            interval=interval,
            data=data,
        )

    async def get_mttr_trends(
            self,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            interval: str = "day",
    ) -> MTTRTrendResponse:

        # 1. Validate date range
        if (
                start_time is not None
                and end_time is not None
                and start_time >= end_time
        ):
            raise ValueError(
                "start_time must be earlier than end_time"
            )

        # 2. Fetch MTTR aggregation
        mttr_counts = await self.incident_repository.get_mttr_trends(
            start_time=start_time,
            end_time=end_time,
            interval=interval,
        )

        # 3. Construct response
        data = [
            MTTRTrendPoint(
                timestamp=timestamp,
                average_mttr_seconds=float(average_mttr),
            )
            for timestamp, average_mttr in mttr_counts
        ]

        return MTTRTrendResponse(
            interval=interval,
            data=data,
        )
