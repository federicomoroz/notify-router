import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.orm import Channel
from app.models.repositories.channel_repository import ChannelRepository
from app.views.schemas.channel_schema import ChannelIn, ChannelOut, ChannelUpdate

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=list[ChannelOut])
def list_channels(db: Session = Depends(get_db)):
    return ChannelRepository.list_all(db)


@router.post("", response_model=ChannelOut, status_code=status.HTTP_201_CREATED)
def create_channel(body: ChannelIn, db: Session = Depends(get_db)):
    channel = Channel(
        name=body.name,
        type=body.type,
        config=json.dumps(body.config),
    )
    return ChannelRepository.create(db, channel)


@router.put("/{channel_id}", response_model=ChannelOut)
def update_channel(channel_id: int, body: ChannelUpdate, db: Session = Depends(get_db)):
    channel = ChannelRepository.get(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    data = body.model_dump(exclude_unset=True)
    if "config" in data:
        # Guard: null or non-dict config must never reach the DB as "null"
        data["config"] = json.dumps(data["config"] if isinstance(data["config"], dict) else {})
    try:
        return ChannelRepository.update(db, channel, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Channel could not be updated (integrity error)")


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    channel = ChannelRepository.get(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    try:
        ChannelRepository.delete(db, channel)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Channel is referenced by existing rules or logs")
