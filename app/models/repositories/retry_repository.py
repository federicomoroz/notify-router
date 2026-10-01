from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.orm import DispatchRetry


class RetryRepository:
    @staticmethod
    def create(db: Session, retry: DispatchRetry) -> DispatchRetry:
        db.add(retry)
        db.commit()
        db.refresh(retry)
        return retry

    @staticmethod
    def list_due(db: Session, now: datetime) -> list[DispatchRetry]:
        return (
            db.query(DispatchRetry)
            .filter(DispatchRetry.status == "pending", DispatchRetry.next_attempt_at <= now)
            .order_by(DispatchRetry.id)
            .all()
        )

    @staticmethod
    def list_all(db: Session, status: str | None = None, limit: int = 100) -> list[DispatchRetry]:
        q = db.query(DispatchRetry)
        if status is not None:
            q = q.filter(DispatchRetry.status == status)
        return q.order_by(DispatchRetry.id.desc()).limit(limit).all()

    @staticmethod
    def reschedule(db: Session, retry: DispatchRetry, attempts: int, error: str, next_at: datetime, now: datetime) -> None:
        retry.attempts = attempts
        retry.last_error = error[:500]
        retry.next_attempt_at = next_at
        retry.updated_at = now
        db.commit()

    @staticmethod
    def finish(db: Session, retry: DispatchRetry, status: str, error: str | None, now: datetime, attempts: int | None = None) -> None:
        retry.status = status
        if attempts is not None:
            retry.attempts = attempts
        if error is not None:
            retry.last_error = error[:500]
        retry.updated_at = now
        db.commit()

    @staticmethod
    def purge_finished(db: Session, retention_days: int, now: datetime) -> int:
        cutoff = now - timedelta(days=retention_days)
        deleted = (
            db.query(DispatchRetry)
            .filter(DispatchRetry.status != "pending", DispatchRetry.updated_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted
