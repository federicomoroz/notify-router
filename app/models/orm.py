from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Channel(Base):
    __tablename__ = "channels"

    id:     Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:   Mapped[str] = mapped_column(String(100), nullable=False)
    type:   Mapped[str] = mapped_column(String(20), nullable=False)   # email|telegram|slack|webhook
    config: Mapped[str] = mapped_column(String(2000), nullable=False, default="{}")  # JSON

    rules: Mapped[list["Rule"]] = relationship(
        "Rule", back_populates="channel", cascade="all, delete-orphan"
    )


class Rule(Base):
    __tablename__ = "rules"

    id:                Mapped[int]        = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:              Mapped[str]        = mapped_column(String(100), nullable=False)
    source_filter:     Mapped[str]        = mapped_column(String(100), nullable=False, default="*")
    event_type_filter: Mapped[str]        = mapped_column(String(100), nullable=False, default="*")
    condition_key:     Mapped[str | None] = mapped_column(String(100), nullable=True)
    condition_value:   Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel_id:        Mapped[int]        = mapped_column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    enabled:           Mapped[bool]       = mapped_column(Boolean, default=True)
    priority:          Mapped[int]        = mapped_column(Integer, default=0)
    created_at:        Mapped[datetime]   = mapped_column(DateTime, default=_utcnow)

    channel: Mapped["Channel"] = relationship("Channel", back_populates="rules")


class EventRecord(Base):
    __tablename__ = "events"
    # Each sender's key is unique, so an event sent twice is stored and dispatched once.
    # NULL keys never collide, so senders that do not send one behave as before.
    __table_args__ = (Index("ix_events_source_idempotency_key", "source", "idempotency_key", unique=True),)

    id:              Mapped[int]        = mapped_column(Integer, primary_key=True, autoincrement=True)
    source:          Mapped[str]        = mapped_column(String(100), nullable=False)
    event_type:      Mapped[str]        = mapped_column(String(100), nullable=False)
    payload:         Mapped[str]        = mapped_column(String(4000), nullable=False, default="{}")  # JSON
    received_at:     Mapped[datetime]   = mapped_column(DateTime, default=_utcnow)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True)


class DispatchLog(Base):
    __tablename__ = "dispatch_logs"

    id:            Mapped[int]        = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id:      Mapped[int]        = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    rule_id:       Mapped[int]        = mapped_column(Integer, nullable=False)
    channel_id:    Mapped[int]        = mapped_column(Integer, nullable=False)
    channel_type:  Mapped[str]        = mapped_column(String(20), nullable=False)
    status:        Mapped[str]        = mapped_column(String(20), nullable=False)  # success|failed
    response_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dispatched_at: Mapped[datetime]   = mapped_column(DateTime, default=_utcnow)


class DispatchRetry(Base):
    """A failed dispatch waiting for another attempt. Only used when retries are on."""

    __tablename__ = "dispatch_retries"

    id:              Mapped[int]        = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id:        Mapped[int]        = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    rule_id:         Mapped[int]        = mapped_column(Integer, nullable=False)
    channel_id:      Mapped[int]        = mapped_column(Integer, nullable=False)
    attempts:        Mapped[int]        = mapped_column(Integer, nullable=False)          # made so far
    status:          Mapped[str]        = mapped_column(String(20), nullable=False)       # pending|delivered|gave_up
    last_error:      Mapped[str | None] = mapped_column(String(500), nullable=True)
    next_attempt_at: Mapped[datetime]   = mapped_column(DateTime, nullable=False)
    created_at:      Mapped[datetime]   = mapped_column(DateTime, default=_utcnow)
    updated_at:      Mapped[datetime]   = mapped_column(DateTime, default=_utcnow)
