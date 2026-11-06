from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class MTTRTrendPoint(BaseModel):
    timestamp: datetime
    average_mttr_seconds: float


class MTTRTrendResponse(BaseModel):
    interval: Literal["hour", "day"]
    data: list[MTTRTrendPoint]