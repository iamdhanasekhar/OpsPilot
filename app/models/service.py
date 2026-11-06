from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    BigInteger,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utc_now


class Service(Base):

    __tablename__ = "services"

    __table_args__ = (
        UniqueConstraint(
            "application_id",
            "slug",
            name="uq_services_application_slug"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    application_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "applications.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    base_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Many services can belong to one application.
    application: Mapped["Application"] = relationship(
        "Application",
        back_populates="services"
    )

    # One service can have multiple monitors.
    monitors: Mapped[list["Monitor"]] = relationship(
        "Monitor",
        back_populates="service",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    primary_incidents = relationship(
        "Incident",
        back_populates="primary_service",
    )

    incident_services = relationship(
        "IncidentService",
        back_populates="service",
    )