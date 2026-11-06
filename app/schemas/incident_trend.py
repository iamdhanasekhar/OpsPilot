from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class IncidentTrendPoint(BaseModel):
    timestamp: datetime
    count: int


class IncidentTrendResponse(BaseModel):
    interval: Literal["hour", "day"]
    data: list[IncidentTrendPoint]