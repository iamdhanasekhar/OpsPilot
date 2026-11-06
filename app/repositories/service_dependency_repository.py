
from sqlalchemy import select, or_

from app.models.service_dependency import ServiceDependency
from app.repositories.base import BaseRepository


class ServiceDependencyRepository(BaseRepository[ServiceDependency]):

    def __init__(self, session):
        super().__init__(session, ServiceDependency)

    async def get_by_source(self, source_service_id: int):
        result = await self.session.execute(
            select(ServiceDependency)
            .where(
                ServiceDependency.source_service_id == source_service_id
            )
            .order_by(ServiceDependency.id.desc())
        )
        return result.scalars().all()

    async def get_by_target(self, target_service_id: int):
        result = await self.session.execute(
            select(ServiceDependency)
            .where(
                ServiceDependency.target_service_id == target_service_id
            )
            .order_by(ServiceDependency.id.desc())
        )
        return result.scalars().all()

    async def get_dependency(
        self,
        source_service_id: int,
        target_service_id: int,
    ):
        result = await self.session.execute(
            select(ServiceDependency).where(
                ServiceDependency.source_service_id == source_service_id,
                ServiceDependency.target_service_id == target_service_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_for_services(self, service_ids: list[int]):
        result = await self.session.execute(
            select(ServiceDependency).where(
                or_(
                    ServiceDependency.source_service_id.in_(service_ids),
                    ServiceDependency.target_service_id.in_(service_ids),
                )
            )
        )
        return result.scalars().all()
