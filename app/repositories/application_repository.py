from sqlalchemy import select

from app.models.application import Application
from app.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):

    def __init__(self, session):
        super().__init__(session, Application)

    async def get_by_slug(self, slug: str):
        result = await self.session.execute(
            select(Application).where(
                Application.slug == slug
            )
        )

        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ):

        query = select(Application)

        if is_active is not None:
            query = query.where(
                Application.is_active == is_active
            )

        query = (
            query
            .order_by(Application.id.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.scalars().all()

    async def update(
        self,
        application: Application,
        update_data: dict,
    ):

        for field, value in update_data.items():
            setattr(application, field, value)

        await self.session.flush()

        return application