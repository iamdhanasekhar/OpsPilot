from typing import Any, Generic, TypeVar

from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.database import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
    ):
        self.session = session
        self.model = model
        self.logger = get_logger(
            f"opspilot.repository.{model.__name__.lower()}"
        )

    def _get_identity(self, instance: ModelType) -> Any:
        """Safely extract identity for logging (works with single or composite keys)."""
        if hasattr(instance, "id"):
            return instance.id
        try:
            insp = inspect(instance)
            if insp.identity:
                return insp.identity
        except Exception:
            pass
        return str(instance)

    async def get_by_id(
        self,
        record_id: int,
    ) -> ModelType | None:

        self.logger.debug(
            "Fetching %s with id=%s",
            self.model.__name__,
            record_id,
        )

        result = await self.session.execute(
            select(self.model).where(
                self.model.id == record_id
            )
        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:

        result = await self.session.execute(
            select(self.model)
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def create(
        self,
        data: dict[str, Any] | ModelType | Any,
    ) -> ModelType:

        if isinstance(data, self.model):
            instance = data
        elif isinstance(data, dict):
            instance = self.model(**data)
        else:
            # If it's a Pydantic schema
            instance = self.model(**data.model_dump())

        self.session.add(instance)

        await self.session.flush()
        await self.session.refresh(instance)

        self.logger.info(
            "Created %s with id=%s",
            self.model.__name__,
            self._get_identity(instance),
        )

        return instance

    async def update(
        self,
        instance: ModelType,
        data: dict[str, Any],
    ) -> ModelType:

        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)

        self.logger.info(
            "Updated %s with id=%s",
            self.model.__name__,
            self._get_identity(instance),
        )

        return instance

    async def delete(
        self,
        instance: ModelType,
    ) -> None:

        record_id = self._get_identity(instance)

        await self.session.delete(instance)
        await self.session.flush()

        self.logger.info(
            "Deleted %s with id=%s",
            self.model.__name__,
            record_id,
        )