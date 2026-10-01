"""
Retries dispatches that failed, waiting longer each time.

Off unless DISPATCH_MAX_ATTEMPTS is above 1. A channel that fails because its
network is down (no internet at the site, the provider is down) gets the
notification later instead of losing it.
"""

import json
from datetime import datetime, timedelta, timezone

from app.core import config
from app.core.event_manager import EventManager
from app.core.events import DispatchFailed, DispatchSucceeded
from app.models.orm import DispatchRetry, EventRecord
from app.models.repositories.channel_repository import ChannelRepository
from app.models.repositories.retry_repository import RetryRepository
from app.models.services.dispatcher_service import DispatcherService

_FIRST_DELAY_SECONDS = 30
_MAX_DELAY_SECONDS   = 900


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def delay_after(attempts: int) -> timedelta:
    """30 s after the first failure, doubling up to 15 min."""
    return timedelta(seconds=min(_FIRST_DELAY_SECONDS * 2 ** (attempts - 1), _MAX_DELAY_SECONDS))


class RetryScheduler:
    """Turns the first failure of a dispatch into a pending retry."""

    def __init__(self, db_factory, events: EventManager) -> None:
        self._db_factory = db_factory
        events.subscribe(DispatchFailed, self._on_failed)

    def _on_failed(self, event: DispatchFailed) -> None:
        # Retries report their own failures; only a first attempt starts a retry.
        if config.DISPATCH_MAX_ATTEMPTS <= 1 or event.attempt != 1 or event.channel_type == "unknown":
            return
        db = self._db_factory()
        try:
            now = _utcnow()
            RetryRepository.create(db, DispatchRetry(
                event_id=event.event_id,
                rule_id=event.rule_id,
                channel_id=event.channel_id,
                attempts=1,
                status="pending",
                last_error=event.error[:500],
                next_attempt_at=now + delay_after(1),
                updated_at=now,
            ))
        finally:
            db.close()


class RetryWorker:
    """Runs on a timer and tries every pending retry that is due."""

    def __init__(self, db_factory, events: EventManager) -> None:
        self._db_factory = db_factory
        self._events = events

    async def run_due(self, dispatcher: DispatcherService, now: datetime | None = None) -> int:
        now = now or _utcnow()
        db = self._db_factory()
        tried = 0
        try:
            for retry in RetryRepository.list_due(db, now):
                await self._attempt(db, dispatcher, retry, now)
                tried += 1
        finally:
            db.close()
        return tried

    async def _attempt(self, db, dispatcher: DispatcherService, retry: DispatchRetry, now: datetime) -> None:
        event = db.get(EventRecord, retry.event_id)
        channel = ChannelRepository.get(db, retry.channel_id)
        if event is None or channel is None:
            RetryRepository.finish(db, retry, "gave_up", "event or channel no longer exists", now)
            return

        success, info = await dispatcher.send(channel, event, json.loads(event.payload or "{}"))
        attempt = retry.attempts + 1

        if success:
            self._events.emit(DispatchSucceeded(
                event_id=event.id, rule_id=retry.rule_id, channel_id=channel.id,
                channel_type=channel.type, info=f"retry {attempt}: {info}",
            ))
            RetryRepository.finish(db, retry, "delivered", None, now, attempts=attempt)
            return

        self._events.emit(DispatchFailed(
            event_id=event.id, rule_id=retry.rule_id, channel_id=channel.id,
            channel_type=channel.type, error=f"retry {attempt}: {info}", attempt=attempt,
        ))
        if attempt >= config.DISPATCH_MAX_ATTEMPTS:
            RetryRepository.finish(db, retry, "gave_up", info, now, attempts=attempt)
        else:
            RetryRepository.reschedule(db, retry, attempt, info, now + delay_after(attempt), now)
