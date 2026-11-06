
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResourceNotFoundException,
    BusinessRuleException,
)

from app.repositories.service_repository import ServiceRepository
from app.repositories.service_dependency_repository import ServiceDependencyRepository

from app.schemas.service_dependency import (
    ServiceDependencyCreate,
    ServiceDependencyUpdate,
)


logger = logging.getLogger(__name__)


class ServiceDependencyService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ServiceDependencyRepository(session)
        self.service_repository = ServiceRepository(session)

    async def create_dependency(
        self,
        source_service_id: int,
        data: ServiceDependencyCreate,
    ):

        if source_service_id == data.target_service_id:
            raise BusinessRuleException(
                "A service cannot depend on itself"
            )

        source = await self.service_repository.get_by_id(
            source_service_id
        )

        if not source:
            raise ResourceNotFoundException(
                "Source service not found"
            )

        target = await self.service_repository.get_by_id(
            data.target_service_id
        )

        if not target:
            raise ResourceNotFoundException(
                "Target service not found"
            )

        existing = await self.repository.get_dependency(
            source_service_id,
            data.target_service_id,
        )

        if existing:
            raise BusinessRuleException(
                "Dependency already exists"
            )

        try:
            dependency_data = data.model_dump()
            dependency_data["source_service_id"] = source_service_id

            dependency = await self.repository.create(
                dependency_data
            )

            await self.session.commit()
            await self.session.refresh(dependency)

            return dependency

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to create service dependency")
            raise

    async def get_outgoing_dependencies(
        self,
        service_id: int,
    ):

        service = await self.service_repository.get_by_id(service_id)

        if not service:
            raise ResourceNotFoundException("Service not found")

        return await self.repository.get_by_source(service_id)

    async def get_incoming_dependencies(
        self,
        service_id: int,
    ):

        service = await self.service_repository.get_by_id(service_id)

        if not service:
            raise ResourceNotFoundException("Service not found")

        return await self.repository.get_by_target(service_id)

    async def update_dependency(
        self,
        source_service_id: int,
        dependency_id: int,
        data: ServiceDependencyUpdate,
    ):

        dependency = await self.repository.get_by_id(dependency_id)

        if not dependency or dependency.source_service_id != source_service_id:
            raise ResourceNotFoundException(
                "Service dependency not found"
            )

        updates = data.model_dump(exclude_unset=True)

        if not updates:
            raise BusinessRuleException(
                "No fields provided for update"
            )

        try:
            for field, value in updates.items():
                setattr(dependency, field, value)

            await self.session.commit()
            await self.session.refresh(dependency)

            return dependency

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to update service dependency")
            raise

    async def delete_dependency(
        self,
        source_service_id: int,
        dependency_id: int,
    ):

        dependency = await self.repository.get_by_id(dependency_id)

        if not dependency or dependency.source_service_id != source_service_id:
            raise ResourceNotFoundException(
                "Service dependency not found"
            )

        try:
            await self.session.delete(dependency)
            await self.session.commit()

            return {"message": "Service dependency removed"}

        except Exception:
            await self.session.rollback()
            logger.exception("Failed to delete service dependency")
            raise
