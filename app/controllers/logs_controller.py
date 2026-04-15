from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.repositories.log_repository import LogRepository
from app.views.schemas.log_schema import LogOut

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[LogOut])
def list_logs(
    event_id: int | None = None,
    status: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return LogRepository.list_all(db, event_id=event_id, status=status, limit=limit)
