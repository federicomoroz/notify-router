from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.repositories.retry_repository import RetryRepository

router = APIRouter(prefix="/retries", tags=["retries"])


class RetryOut(BaseModel):
    id:              int
    event_id:        int
    rule_id:         int
    channel_id:      int
    attempts:        int
    status:          str
    last_error:      str | None
    next_attempt_at: datetime
    updated_at:      datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[RetryOut])
def list_retries(
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Dispatches waiting for another attempt, delivered late or given up. Empty when retries are off."""
    return RetryRepository.list_all(db, status=status, limit=limit)
