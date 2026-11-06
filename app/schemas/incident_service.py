
from pydantic import BaseModel, ConfigDict

from app.core.enums import IncidentServiceImpact


class IncidentServiceCreate(BaseModel):

    service_id: int
    impact_type: IncidentServiceImpact = IncidentServiceImpact.AFFECTED


class IncidentServiceUpdate(BaseModel):

    impact_type: IncidentServiceImpact


class IncidentServiceResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    incident_id: int
    service_id: int
    impact_type: IncidentServiceImpact
