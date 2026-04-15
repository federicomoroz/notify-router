from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.orm import DispatchLog


class LogRepository:
    @staticmethod
    def create(db: Session, log: DispatchLog) -> DispatchLog:
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def list_all(
        db: Session,
        event_id: int | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[DispatchLog]:
        q = db.query(DispatchLog)
        if event_id is not None:
            q = q.filter(DispatchLog.event_id == event_id)
        if status is not None:
            q = q.filter(DispatchLog.status == status)
        return q.order_by(DispatchLog.dispatched_at.desc()).limit(limit).all()

    @staticmethod
    def purge_old(db: Session, retention_days: int) -> int:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=retention_days)
        deleted = (
            db.query(DispatchLog)
            .filter(DispatchLog.dispatched_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted

    @staticmethod
    def count_by_status(db: Session) -> dict[str, int]:
        rows = db.query(DispatchLog.status, func.count(DispatchLog.id)).group_by(DispatchLog.status).all()
        return {status: count for status, count in rows}
