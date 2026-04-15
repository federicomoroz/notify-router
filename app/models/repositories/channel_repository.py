from sqlalchemy.orm import Session

from app.models.orm import Channel


class ChannelRepository:
    @staticmethod
    def list_all(db: Session) -> list[Channel]:
        return db.query(Channel).all()

    @staticmethod
    def get(db: Session, channel_id: int) -> Channel | None:
        return db.query(Channel).filter(Channel.id == channel_id).first()

    @staticmethod
    def create(db: Session, channel: Channel) -> Channel:
        db.add(channel)
        db.commit()
        db.refresh(channel)
        return channel

    @staticmethod
    def update(db: Session, channel: Channel, data: dict) -> Channel:
        for key, value in data.items():
            setattr(channel, key, value)
        db.commit()
        db.refresh(channel)
        return channel

    @staticmethod
    def delete(db: Session, channel: Channel) -> None:
        db.delete(channel)
        db.commit()
