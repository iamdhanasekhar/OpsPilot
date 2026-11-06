
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    BigInteger,
    ForeignKey,
    Integer,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utc_now


class MonitorCheck(Base):

    __tablename__ = "monitor_checks"

    __table_args__ = (
        Index(
            "ix_monitor_checks_monitor_checked_at",
            "monitor_id",
            "checked_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    monitor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False
    )

    is_success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )

    status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    response_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    monitor: Mapped["Monitor"] = relationship(
        "Monitor",
        back_populates="checks"
    )