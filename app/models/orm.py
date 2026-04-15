from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id:     Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:   Mapped[str] = mapped_column(String(100), nullable=False)
    type:   Mapped[str] = mapped_column(String(20), nullable=False)   # email|telegram|slack|webhook
    config: Mapped[str] = mapped_column(String(2000), nullable=False, default="{}")  # JSON


class Rule(Base):
    __tablename__ = "rules"

    id:                Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:              Mapped[str]            = mapped_column(String(100), nullable=False)
    source_filter:     Mapped[str]            = mapped_column(String(100), nullable=False, default="*")
    event_type_filter: Mapped[str]            = mapped_column(String(100), nullable=False, default="*")
    condition_key:     Mapped[str | None]     = mapped_column(String(100), nullable=True)
    condition_value:   Mapped[str | None]     = mapped_column(String(255), nullable=True)
    channel_id:        Mapped[int]            = mapped_column(Integer, ForeignKey("channels.id"), nullable=False)
    enabled:           Mapped[bool]           = mapped_column(Boolean, default=True)
    priority:          Mapped[int]            = mapped_column(Integer, default=0)
    created_at:        Mapped[datetime]       = mapped_column(DateTime, default=datetime.utcnow)


class EventRecord(Base):
    __tablename__ = "events"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    source:      Mapped[str]      = mapped_column(String(100), nullable=False)
    event_type:  Mapped[str]      = mapped_column(String(100), nullable=False)
    payload:     Mapped[str]      = mapped_column(String(4000), nullable=False, default="{}")  # JSON
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DispatchLog(Base):
    __tablename__ = "dispatch_logs"

    id:            Mapped[int]        = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id:      Mapped[int]        = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    rule_id:       Mapped[int]        = mapped_column(Integer, nullable=False)
    channel_id:    Mapped[int]        = mapped_column(Integer, nullable=False)
    channel_type:  Mapped[str]        = mapped_column(String(20), nullable=False)
    status:        Mapped[str]        = mapped_column(String(20), nullable=False)  # success|failed
    response_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dispatched_at: Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)
