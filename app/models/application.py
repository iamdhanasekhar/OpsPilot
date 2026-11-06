from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    BigInteger,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utc_now


class Application(Base):

    __tablename__ = "applications"

    __table_args__ = (
        UniqueConstraint(
            "slug",
            name="uq_applications_slug"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    environment: Mapped[str] = mapped_column(
        String(50),
        default="production",
        nullable=False
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

    # One application can have multiple services.
    services: Mapped[list["Service"]] = relationship(
        "Service",
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True
    )