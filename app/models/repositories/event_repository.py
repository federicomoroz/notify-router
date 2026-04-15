from sqlalchemy.orm import Session

from app.models.orm import EventRecord


class EventRepository:
    @staticmethod
    def create(db: Session, record: EventRecord) -> EventRecord:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def list_recent(db: Session, limit: int = 50) -> list[EventRecord]:
        return (
            db.query(EventRecord)
            .order_by(EventRecord.received_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get(db: Session, event_id: int) -> EventRecord | None:
        return db.query(EventRecord).filter(EventRecord.id == event_id).first()
