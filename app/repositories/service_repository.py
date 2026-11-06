from sqlalchemy import select
from app.models.service import Service
from app.repositories.base import BaseRepository
from sqlalchemy import select, func, case


class ServiceRepository(BaseRepository[Service]):

    def __init__(self, session):
        super().__init__(session, Service)

    async def get_by_slug(
        self,
        application_id: int,
        slug: str,
    ):
        result = await self.session.execute(
            select(Service).where(
                Service.application_id == application_id,
                Service.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_application(
        self,
        application_id: int,
        offset: int = 0,
        limit: int = 100,
    ):
        result = await self.session.execute(
            select(Service)
            .where(Service.application_id == application_id)
            .order_by(Service.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_dashboard_counts(self):
        result = await self.session.execute(
            select(
                func.count(Service.id),
                func.sum(
                    case((Service.is_active.is_(True), 1), else_=0)
                ),
                func.sum(
                    case((Service.is_active.is_(False), 1), else_=0)
                ),
            )
        )

        total, active, inactive = result.one()

        return {
            "total": total or 0,
            "active": active or 0,
            "inactive": inactive or 0,
        }

    async def get_by_ids(self, service_ids: list[int]):
        if not service_ids:
            return []

        result = await self.session.execute(
            select(Service).where(Service.id.in_(service_ids))
        )

        return result.scalars().all()
