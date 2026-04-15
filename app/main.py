import json
from contextlib import asynccontextmanager

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.core.config import LOG_RETENTION_DAYS
from app.core.database import Base, SessionLocal, engine
from app.core.event_manager import EventManager
from app.controllers.events_controller import router as events_router
from app.controllers.rules_controller import router as rules_router
from app.controllers.channels_controller import router as channels_router
from app.controllers.logs_controller import router as logs_router
from app.models.orm import Channel, Rule
from app.models.repositories.channel_repository import ChannelRepository
from app.models.repositories.log_repository import LogRepository
from app.models.repositories.rule_repository import RuleRepository
from app.models.services.dispatcher_service import DispatcherService
from app.models.services.log_listener import LogListener
from app.views.templates.spa import render_spa

scheduler = AsyncIOScheduler()


def _purge_logs_job() -> None:
    db = SessionLocal()
    try:
        deleted = LogRepository.purge_old(db, LOG_RETENTION_DAYS)
        print(f"[purge] removed {deleted} dispatch logs older than {LOG_RETENTION_DAYS} days")
    finally:
        db.close()


def _seed_demo_data() -> None:
    """Insert demo channels + rules on first startup (when DB has 0 channels)."""
    db = SessionLocal()
    try:
        if ChannelRepository.list_all(db):
            return  # already seeded

        webhook_ch = ChannelRepository.create(
            db,
            Channel(
                name="httpbin-webhook",
                type="webhook",
                config=json.dumps({"url": "https://httpbin.org/post", "method": "POST", "headers": {}}),
            ),
        )
        slack_ch = ChannelRepository.create(
            db,
            Channel(
                name="slack-demo",
                type="slack",
                config=json.dumps({"webhook_url": "https://hooks.slack.com/services/DEMO/FAKE/URL"}),
            ),
        )

        RuleRepository.create(
            db,
            Rule(
                name="critical-alerts → webhook",
                source_filter="*",
                event_type_filter="alert",
                condition_key="severity",
                condition_value="critical",
                channel_id=webhook_ch.id,
                priority=10,
                enabled=True,
            ),
        )
        RuleRepository.create(
            db,
            Rule(
                name="all-alerts → slack",
                source_filter="*",
                event_type_filter="alert",
                condition_key=None,
                condition_value=None,
                channel_id=slack_ch.id,
                priority=5,
                enabled=True,
            ),
        )
        print("[seed] demo channels and rules created")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed_demo_data()

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
def spa():
    return HTMLResponse(content=render_spa())
