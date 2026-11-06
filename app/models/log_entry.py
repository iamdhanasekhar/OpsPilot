from datetime import datetime

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    DateTime,
    String,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class LogEntry(Base):

    __tablename__ = "log_entries"

    __table_args__ = (
        Index(
            "ix_log_entries_service_timestamp",
            "service_id",
            "timestamp"
        ),
        Index(
            "ix_log_entries_level_timestamp",
            "level",
            "timestamp"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    service_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False
    )

    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    source: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    trace_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    attributes_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )