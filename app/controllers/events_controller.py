import json

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

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


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def receive_event(
    body: EventIn,
    request: Request,
    db: Session = Depends(get_db),
    dispatcher: DispatcherService = Depends(_get_dispatcher),
):
    record = EventRecord(
        source=body.source,
        event_type=body.event_type,
        payload=json.dumps(body.payload),
    )
    record = EventRepository.create(db, record)

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
        },
    )


@router.get("", response_model=list[EventOut])
def list_events(
    limit: int = Query(default=50, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return EventRepository.list_recent(db, limit=limit)
