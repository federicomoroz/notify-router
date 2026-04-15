from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.orm import Rule
from app.models.repositories.channel_repository import ChannelRepository
from app.models.repositories.rule_repository import RuleRepository
from app.views.schemas.rule_schema import RuleIn, RuleOut, RuleUpdate

router = APIRouter(prefix="/rules", tags=["rules"])


def _assert_channel_exists(db: Session, channel_id: int) -> None:
    if not ChannelRepository.get(db, channel_id):
        raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")


@router.get("", response_model=list[RuleOut])
def list_rules(db: Session = Depends(get_db)):
    return RuleRepository.list_all(db)


@router.post("", response_model=RuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(body: RuleIn, db: Session = Depends(get_db)):
    _assert_channel_exists(db, body.channel_id)
    rule = Rule(**body.model_dump())
    try:
        return RuleRepository.create(db, rule)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Rule could not be created (integrity error)")


@router.put("/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: int, body: RuleUpdate, db: Session = Depends(get_db)):
    rule = RuleRepository.get(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    data = body.model_dump(exclude_unset=True)
    if "channel_id" in data:
        _assert_channel_exists(db, data["channel_id"])
    try:
        return RuleRepository.update(db, rule, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Rule could not be updated (integrity error)")


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = RuleRepository.get(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    RuleRepository.delete(db, rule)
