from app.core.event_manager import EventManager
from app.core.events import DispatchFailed, DispatchSucceeded
from app.models.orm import DispatchLog
from app.models.repositories.log_repository import LogRepository


class LogListener:
    def __init__(self, db_factory, events: EventManager) -> None:
        self._db_factory = db_factory
        events.subscribe(DispatchSucceeded, self._on_success)
        events.subscribe(DispatchFailed,    self._on_failed)

    def _on_success(self, event: DispatchSucceeded) -> None:
        db = self._db_factory()
        try:
            LogRepository.create(
                db,
                DispatchLog(
                    event_id=event.event_id,
                    rule_id=event.rule_id,
                    channel_id=event.channel_id,
                    channel_type=event.channel_type,
                    status="success",
                ),
            )
        finally:
            db.close()

    def _on_failed(self, event: DispatchFailed) -> None:
        db = self._db_factory()
        try:
            LogRepository.create(
                db,
                DispatchLog(
                    event_id=event.event_id,
                    rule_id=event.rule_id,
                    channel_id=event.channel_id,
                    channel_type=event.channel_type,
                    status="failed",
                    response_info=event.error[:500],
                ),
            )
        finally:
            db.close()
