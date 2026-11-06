
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResourceConflictException,
    ResourceNotFoundException,
    BusinessRuleException,
)
from app.core.logger import get_logger
from app.models.service import Service
from app.repositories.service_repository import ServiceRepository
from app.repositories.application_repository import ApplicationRepository
from app.schemas.service import ServiceCreate, ServiceUpdate


logger = get_logger(__name__)


class ServiceService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ServiceRepository(session)
        self.application_repository = ApplicationRepository(session)

    async def create_service(self, data: ServiceCreate) -> Service:

        application = await self.application_repository.get_by_id(
            data.application_id
        )

        if not application:
            raise ResourceNotFoundException(
                "Application not found"
            )

        if not application.is_active:
            raise BusinessRuleException(
                "Cannot create service under an inactive application"
            )

        existing = await self.repository.get_by_slug(
            data.application_id,
            data.slug,
        )

        if existing:
            raise ResourceConflictException(
                "Service slug already exists in this application"
            )

        service = Service(**data.model_dump())

        try:
            await self.repository.create(service)
            await self.session.commit()
            await self.session.refresh(service)

            logger.info("Service created | id=%s", service.id)

            return service

        except Exception:
            await self.session.rollback()
            raise

    async def get_service(self, service_id: int) -> Service:

        service = await self.repository.get_by_id(service_id)

        if not service:
            raise ResourceNotFoundException("Service not found")

        return service

    async def list_services(
        self,
        application_id: int,
        offset: int = 0,
        limit: int = 100,
    ):

        application = await self.application_repository.get_by_id(
            application_id
        )

        if not application:
            raise ResourceNotFoundException("Application not found")

        return await self.repository.get_by_application(
            application_id,
            offset,
            limit,
        )

    async def update_service(
        self,
        service_id: int,
        data: ServiceUpdate,
    ) -> Service:

        service = await self.get_service(service_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            raise BusinessRuleException(
                "At least one field must be provided"
            )

        for field in ("name", "is_active"):
            if field in update_data and update_data[field] is None:
                raise BusinessRuleException(
                    f"{field} cannot be null"
                )

        try:
            for field, value in update_data.items():
                setattr(service, field, value)

            await self.session.commit()
            await self.session.refresh(service)

            return service

        except Exception:
            await self.session.rollback()
            raise

    async def deactivate_service(self, service_id: int) -> Service:

        service = await self.get_service(service_id)

        if not service.is_active:
            raise BusinessRuleException(
                "Service is already inactive"
            )

        try:
            service.is_active = False

            await self.session.commit()
            await self.session.refresh(service)

            return service

        except Exception:
            await self.session.rollback()
            raise
