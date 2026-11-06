from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    BigInteger,
    ForeignKey,
    Integer,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utc_now


class Monitor(Base):

    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    service_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    monitor_type: Mapped[str] = mapped_column(
        String(30),
        default="http",
        nullable=False
    )

    target_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    method: Mapped[str] = mapped_column(
        String(10),
        default="GET",
        nullable=False
    )

    expected_status_code: Mapped[int] = mapped_column(
        Integer,
        default=200,
        nullable=False
    )

    interval_seconds: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False
    )

    next_check_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,

        index=True
    )

    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False
    )

    failure_threshold: Mapped[int] = mapped_column(
        Integer,
        default=3,
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

    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="monitors"
    )

    checks: Mapped[list["MonitorCheck"]] = relationship(
        "MonitorCheck",
        back_populates="monitor",
        cascade="all, delete-orphan",
        passive_deletes=True
    )