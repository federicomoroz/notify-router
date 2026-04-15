from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from sqlalchemy import func

from app.core.config import LOG_RETENTION_DAYS
from app.core.database import Base, SessionLocal, engine
from app.core.event_manager import EventManager
from app.controllers.events_controller import router as events_router
from app.controllers.rules_controller import router as rules_router
from app.controllers.channels_controller import router as channels_router
from app.controllers.logs_controller import router as logs_router
from app.models.orm import EventRecord
from app.models.repositories.log_repository import LogRepository
from app.models.services.dispatcher_service import DispatcherService
from app.models.services.log_listener import LogListener
from app.views.templates.dashboard import render_dashboard

scheduler = AsyncIOScheduler()


def _purge_logs_job() -> None:
    db = SessionLocal()
    try:
        deleted = LogRepository.purge_old(db, LOG_RETENTION_DAYS)
        print(f"[purge] removed {deleted} dispatch logs older than {LOG_RETENTION_DAYS} days")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    http_client = httpx.AsyncClient(timeout=15.0)
    events      = EventManager()

    dispatcher = DispatcherService(http_client=http_client)
    LogListener(db_factory=SessionLocal, events=events)

    app.state.events     = events
    app.state.dispatcher = dispatcher

    scheduler.add_job(_purge_logs_job, "interval", hours=24, id="purge_logs", replace_existing=True)
    scheduler.start()

    yield

    await http_client.aclose()
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="notify-router",
    description="Multi-channel notification routing engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(events_router)
app.include_router(rules_router)
app.include_router(channels_router)
app.include_router(logs_router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    db = SessionLocal()
    try:
        total_events     = db.query(func.count(EventRecord.id)).scalar() or 0
        counts           = LogRepository.count_by_status(db)
        success_count   = counts.get("success", 0)
        failed_count    = counts.get("failed", 0)
        total_dispatches = success_count + failed_count

        recent = LogRepository.list_all(db, limit=20)
        recent_dicts = [
            {
                "id":            log.id,
                "event_id":      log.event_id,
                "channel_type":  log.channel_type,
                "status":        log.status,
                "response_info": log.response_info,
                "dispatched_at": log.dispatched_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for log in recent
        ]

        html = render_dashboard(
            total_events=total_events,
            total_dispatches=total_dispatches,
            success_count=success_count,
            failed_count=failed_count,
            recent_logs=recent_dicts,
        )
        return HTMLResponse(content=html)
    finally:
        db.close()
