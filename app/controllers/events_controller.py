import json
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import config
from app.core.database import get_db
from app.controllers.pipeline import DispatchStep, RouterContext, RouterPipeline, RuleMatchStep
from app.models.orm import EventRecord
from app.models.repositories.event_repository import EventRepository
from app.models.services.dispatcher_service import DispatcherService
from app.views.schemas.event_schema import EventIn, EventOut

router = APIRouter(prefix="/events", tags=["events"])

_pipeline = RouterPipeline(steps=[RuleMatchStep(), DispatchStep()])


def _get_dispatcher(request: Request) -> DispatcherService:
    return request.app.state.dispatcher


def _get_events(request: Request):
    return request.app.state.events


def _require_ingest_key(x_api_key: str | None = Header(default=None)) -> None:
    """Only when INGEST_API_KEY is set; otherwise /events stays open, as it always was."""
    expected = config.INGEST_API_KEY
    if expected and not secrets.compare_digest((x_api_key or "").encode(), expected.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or wrong X-API-Key")


def _duplicate(record: EventRecord) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"event_id": record.id, "matched_rules": 0, "dispatches": [], "duplicate": True},
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(_require_ingest_key)])
async def receive_event(
    body: EventIn,
    request: Request,
    db: Session = Depends(get_db),
    dispatcher: DispatcherService = Depends(_get_dispatcher),
):
    if body.idempotency_key and (seen := EventRepository.find_by_key(db, body.source, body.idempotency_key)):
        return _duplicate(seen)

    record = EventRecord(
        source=body.source,
        event_type=body.event_type,
        payload=json.dumps(body.payload),
        idempotency_key=body.idempotency_key,
    )
    try:
        record = EventRepository.create(db, record)
    except IntegrityError:
        # The same key arrived twice at the same moment: the other request dispatches it.
        db.rollback()
        return _duplicate(EventRepository.find_by_key(db, body.source, body.idempotency_key))

    events_bus = _get_events(request)
    ctx = RouterContext(
        event=record,
        payload=body.payload,
        db=db,
        dispatcher=dispatcher,
        events=events_bus,
    )
    results = await _pipeline.run(ctx)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "event_id":      record.id,
            "matched_rules": len(ctx.matched_rules),
            "dispatches":    results,
            "duplicate":     False,
        },
    )


@router.get("", response_model=list[EventOut])
def list_events(
    limit: int = Query(default=50, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return EventRepository.list_recent(db, limit=limit)
