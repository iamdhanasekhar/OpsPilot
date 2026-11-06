
from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from app.core.enums import IncidentServiceImpact


class IncidentService(Base):
    __tablename__ = "incident_services"

    incident_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        primary_key=True,
    )

    service_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("services.id", ondelete="RESTRICT"),
        primary_key=True,
    )

    impact_type: Mapped[IncidentServiceImpact] = mapped_column(
        Enum(IncidentServiceImpact),
        default=IncidentServiceImpact.AFFECTED,
        nullable=False,
    )

    incident = relationship(
        "Incident",
        back_populates="affected_services",
    )

    service = relationship(
        "Service",
        back_populates="incident_services",
    )
