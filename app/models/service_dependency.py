from datetime import datetime

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    DateTime,
    Boolean,
    String,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class ServiceDependency(Base):

    __tablename__ = "service_dependencies"

    __table_args__ = (
        UniqueConstraint(
            "source_service_id",
            "target_service_id",
            name="uq_service_dependency"
        ),
        CheckConstraint(
            "source_service_id != target_service_id",
            name="ck_service_dependency_not_self"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    source_service_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    target_service_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    dependency_type: Mapped[str] = mapped_column(
        String(50),
        default="synchronous",
        nullable=False
    )

    is_critical: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )