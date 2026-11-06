from datetime import timedelta
from app.core.exceptions import ResourceNotFoundException
from app.core.time import utc_now

from app.repositories.incident_repository import IncidentRepository
from app.repositories.incident_service_repository import IncidentServiceRepository
from app.repositories.log_entry_repository import LogEntryRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.service_dependency_repository import ServiceDependencyRepository


class IncidentContextService:

    def __init__(self, session):
        self.incident_repository = IncidentRepository(session)
        self.incident_service_repository = IncidentServiceRepository(session)
        self.log_repository = LogEntryRepository(session)
        self.service_repository = ServiceRepository(session)
        self.dependency_repository = ServiceDependencyRepository(session)

    @staticmethod
    def _enum_value(value):
        return value.value if hasattr(value, "value") else value

    @staticmethod
    def _timestamp(value):
        return value.isoformat() if value else None

    @staticmethod
    def _serialize_service(service):
        if not service:
            return None

        return {
            "id": service.id,
            "name": service.name,
            "slug": service.slug,
            "base_url": service.base_url,
            "is_active": service.is_active,
        }

    async def build_context(self, incident_id: int) -> dict:
        # 1. Retrieve incident
        incident = await self.incident_repository.get_by_id(incident_id)

        if not incident:
            raise ResourceNotFoundException("Incident not found")

        # 2. Retrieve primary service
        primary_service = await self.service_repository.get_by_id(
            incident.service_id
        )

        # 3. Retrieve affected service associations
        associations = await self.incident_service_repository.get_by_incident(
            incident_id
        )

        affected_services = []
        service_ids = {incident.service_id}

        for association in associations:
            service_ids.add(association.service_id)

            if association.service_id == incident.service_id:
                continue

            service = await self.service_repository.get_by_id(
                association.service_id
            )

            if service:
                affected_services.append({
                    **self._serialize_service(service),
                    "impact_type": self._enum_value(
                        association.impact_type
                    ),
                })

        # 4. Retrieve correlated logs
        start_time = incident.started_at - timedelta(minutes=5)

        end_time = incident.resolved_at or utc_now()

        logs = await self.log_repository.get_by_filters(
            service_ids=list(service_ids),
            start_time=start_time,
            end_time=end_time,
            skip=0,
            limit=100,
        )

        recent_logs = [
            {
                "id": log.id,
                "service_id": log.service_id,
                "level": log.level,
                "message": log.message,
                "source": log.source,
                "trace_id": log.trace_id,
                "request_id": log.request_id,
                "timestamp": self._timestamp(log.timestamp),
                "attributes": log.attributes_json,
            }
            for log in logs
        ]

        # 5. Retrieve related service dependencies
        dependencies = await self.dependency_repository.get_for_services(
            list(service_ids)
        )

        # Resolve dependency service names without lazy-loading relationships
        dependency_service_ids = {
            service_id
            for dependency in dependencies
            for service_id in (
                dependency.source_service_id,
                dependency.target_service_id,
            )
        }

        dependency_services = {}

        for service_id in dependency_service_ids:
            service = await self.service_repository.get_by_id(service_id)
            if service:
                dependency_services[service_id] = service.name

        service_dependencies = [
            {
                "source_service_id": dependency.source_service_id,
                "source_service_name": dependency_services.get(
                    dependency.source_service_id
                ),
                "target_service_id": dependency.target_service_id,
                "target_service_name": dependency_services.get(
                    dependency.target_service_id
                ),
                "dependency_type": dependency.dependency_type,
                "is_critical": dependency.is_critical,
            }
            for dependency in dependencies
        ]

        # 6. Return structured context
        return {
            "incident": {
                "id": incident.id,
                "title": incident.title,
                "description": incident.description,
                "severity": self._enum_value(incident.severity),
                "status": self._enum_value(incident.status),
                "started_at": self._timestamp(incident.started_at),
                "resolved_at": self._timestamp(incident.resolved_at),
            },
            "primary_service": self._serialize_service(primary_service),
            "affected_services": affected_services,
            "recent_logs": recent_logs,
            "service_dependencies": service_dependencies,
        }
