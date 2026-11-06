from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.application import Application
from app.repositories.application_repository import (
    ApplicationRepository,
)
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
)
from app.core.exceptions import (
    ResourceNotFoundException,
    ResourceConflictException,
    BusinessRuleException,
)
from app.core.logger import get_logger


logger = get_logger(__name__)


class ApplicationService:

    def __init__(self, session: AsyncSession):

        self.session = session

        self.repository = ApplicationRepository(
            session
        )

    async def create_application(
        self,
        data: ApplicationCreate,
    ) -> Application:

        existing = await self.repository.get_by_slug(
            data.slug
        )

        if existing:
            raise ResourceConflictException(
                f"Application with slug '{data.slug}' already exists"
            )

        application = Application(
            name=data.name,
            slug=data.slug,
            description=data.description,
            environment=data.environment,
        )

        try:

            await self.repository.create(application)

            await self.session.commit()

            await self.session.refresh(application)

            logger.info(
                "Application created | id=%s | slug=%s",
                application.id,
                application.slug,
            )

            return application

        except IntegrityError:

            await self.session.rollback()

            # Protect against concurrent duplicate creation.
            existing = await self.repository.get_by_slug(
                data.slug
            )

            if existing:
                raise ResourceConflictException(
                    f"Application with slug '{data.slug}' already exists"
                )

            raise

        except Exception:

            await self.session.rollback()
            raise

    async def get_application(
        self,
        application_id: int,
    ) -> Application:

        application = await self.repository.get_by_id(
            application_id
        )

        if not application:
            raise ResourceNotFoundException(
                f"Application with ID {application_id} not found"
            )

        return application

    async def get_application_by_slug(
        self,
        slug: str,
    ) -> Application:

        application = await self.repository.get_by_slug(
            slug
        )

        if not application:
            raise ResourceNotFoundException(
                f"Application with slug '{slug}' not found"
            )

        return application

    async def list_applications(
        self,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[Application]:

        return await self.repository.get_paginated(
            offset=offset,
            limit=limit,
            is_active=is_active,
        )

    async def update_application(
        self,
        application_id: int,
        data: ApplicationUpdate,
    ) -> Application:

        application = await self.get_application(
            application_id
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field in ("name", "environment"):
            if field in update_data and update_data[field] is None:
                raise BusinessRuleException(
                    f"{field} cannot be null"
                )

        if not update_data:
            raise BusinessRuleException(
                "At least one field must be provided for update"
            )

        if (
            "is_active" in update_data
            and update_data["is_active"] is None
        ):
            raise BusinessRuleException(
                "is_active cannot be null"
            )

        try:

            await self.repository.update(
                application,
                update_data,
            )

            await self.session.commit()

            await self.session.refresh(application)

            logger.info(
                "Application updated | id=%s",
                application.id,
            )

            return application

        except Exception:

            await self.session.rollback()
            raise

    async def deactivate_application(
        self,
        application_id: int,
    ) -> Application:

        application = await self.get_application(
            application_id
        )

        if not application.is_active:
            raise BusinessRuleException(
                "Application is already inactive"
            )

        try:

            application.is_active = False

            await self.session.commit()

            await self.session.refresh(application)

            logger.info(
                "Application deactivated | id=%s",
                application.id,
            )

            return application

        except Exception:

            await self.session.rollback()
            raise