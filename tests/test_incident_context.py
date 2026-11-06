import asyncio
from pprint import pprint

from app.core.database import AsyncSessionLocal
from app.services.incident_context_service import IncidentContextService


async def test_incident_context():
    async with AsyncSessionLocal() as session:
        service = IncidentContextService(session)

        context = await service.build_context(2)

        pprint(context)


if __name__ == "__main__":
    asyncio.run(test_incident_context())