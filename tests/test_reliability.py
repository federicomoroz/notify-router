"""The optional reliability features. Each one is off until configured."""

import inspect
from datetime import datetime, timedelta, timezone

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine, inspect as inspect_db, text

from app.core import config
from app.core.database import upgrade_schema
from app.main import schedule_retries
from conftest import make_channel, make_rule

LATER = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)


def _event(client, **extra):
    return client.post("/events", json={"source": "comanda", "event_type": "alert", "payload": {"x": 1}, **extra})


def _run_retries(client, now=LATER):
    return client.portal.call(client.app.state.retry_worker.run_due, client.app.state.dispatcher, now)


# API key

def test_with_an_ingest_key_events_need_it_and_reading_stays_open(clean, outbound, monkeypatch):
    monkeypatch.setattr(config, "INGEST_API_KEY", "secret")

    assert _event(clean).status_code == 401
    assert clean.post("/events", headers={"X-API-Key": "wrong"},
                      json={"source": "comanda", "event_type": "alert"}).status_code == 401
    assert clean.post("/events", headers={"X-API-Key": "secret"},
                      json={"source": "comanda", "event_type": "alert"}).status_code == 202
    assert clean.get("/events").status_code == 200


# Idempotency

def test_an_event_sent_twice_with_the_same_key_is_dispatched_once(clean, outbound):
    channel = make_channel(clean, "hook", "webhook", {"url": "https://x.example/hook"})
    make_rule(clean, channel)

    first = _event(clean, idempotency_key="outbox-1").json()
    second = _event(clean, idempotency_key="outbox-1").json()

    assert first["duplicate"] is False
    assert second == {"event_id": first["event_id"], "matched_rules": 0, "dispatches": [], "duplicate": True}
    assert len(outbound.requests) == 1
    assert len(clean.get("/events").json()) == 1


def test_keys_are_per_source_and_events_without_a_key_are_never_deduplicated(clean, outbound):
    channel = make_channel(clean, "hook", "webhook", {"url": "https://x.example/hook"})
    make_rule(clean, channel)

    clean.post("/events", json={"source": "a", "event_type": "alert", "idempotency_key": "k"})
    clean.post("/events", json={"source": "b", "event_type": "alert", "idempotency_key": "k"})
    _event(clean)
    _event(clean)

    assert len(outbound.requests) == 4


def test_an_old_database_gets_the_new_column_on_start(tmp_path):
    old = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with old.begin() as conn:
        conn.execute(text(
            "CREATE TABLE events (id INTEGER PRIMARY KEY, source VARCHAR(100), event_type VARCHAR(100), "
            "payload VARCHAR(4000), received_at DATETIME)"))
        conn.execute(text("INSERT INTO events (source, event_type, payload) VALUES ('shop', 'alert', '{}')"))

    upgrade_schema(old)
    upgrade_schema(old)  # Safe to run on every start.

    assert "idempotency_key" in {c["name"] for c in inspect_db(old).get_columns("events")}
    with old.begin() as conn:
        assert conn.execute(text("SELECT count(*) FROM events")).scalar() == 1
        conn.execute(text("INSERT INTO events (source, event_type, payload, idempotency_key) VALUES ('s', 't', '{}', 'k')"))
        with pytest.raises(Exception):
            conn.execute(text("INSERT INTO events (source, event_type, payload, idempotency_key) VALUES ('s', 't', '{}', 'k')"))


# Telegram

def test_telegram_escapes_markdown_so_names_with_underscores_get_through(clean, outbound):
    channel = make_channel(clean, "tg", "telegram", {"bot_token": "T", "chat_id": "1"})
    make_rule(clean, channel)

    clean.post("/events", json={"source": "shop", "event_type": "alert", "payload": {"insumo": "Ojo_de*bife [kg]"}})

    assert outbound.bodies()[0]["text"].endswith("• *insumo*: Ojo\\_de\\*bife \\[kg]")


# Retries

def test_retries_are_off_by_default(clean, outbound):
    outbound.status = 500
    channel = make_channel(clean, "hook", "webhook", {"url": "https://down.example/hook"})
    make_rule(clean, channel)

    _event(clean)

    assert config.DISPATCH_MAX_ATTEMPTS == 1
    assert clean.get("/retries").json() == []


def test_a_failed_dispatch_is_retried_later_and_delivered(clean, outbound, monkeypatch):
    monkeypatch.setattr(config, "DISPATCH_MAX_ATTEMPTS", 5)
    outbound.status = 500
    channel = make_channel(clean, "hook", "webhook", {"url": "https://down.example/hook"})
    make_rule(clean, channel)
    event_id = _event(clean).json()["event_id"]

    pending = clean.get("/retries").json()
    assert [(r["status"], r["attempts"]) for r in pending] == [("pending", 1)]
    assert _run_retries(clean, now=datetime.now(timezone.utc).replace(tzinfo=None)) == 0  # not due yet

    outbound.status = 200
    assert _run_retries(clean) == 1

    assert [(r["status"], r["attempts"]) for r in clean.get("/retries").json()] == [("delivered", 2)]
    logs = clean.get("/logs", params={"event_id": event_id}).json()
    assert sorted(log["status"] for log in logs) == ["failed", "success"]
    assert len(outbound.requests) == 2


def test_retries_give_up_after_the_maximum(clean, outbound, monkeypatch):
    monkeypatch.setattr(config, "DISPATCH_MAX_ATTEMPTS", 3)
    outbound.status = 500
    channel = make_channel(clean, "hook", "webhook", {"url": "https://down.example/hook"})
    make_rule(clean, channel)
    _event(clean)

    _run_retries(clean)
    _run_retries(clean, now=LATER + timedelta(days=1))
    _run_retries(clean, now=LATER + timedelta(days=2))

    retry = clean.get("/retries").json()[0]
    assert (retry["status"], retry["attempts"]) == ("gave_up", 3)
    assert len(outbound.requests) == 3


def test_the_retry_round_is_a_coroutine_the_scheduler_awaits():
    scheduler = AsyncIOScheduler()

    schedule_retries(scheduler, worker=None, application=None)

    assert inspect.iscoroutinefunction(scheduler.get_job("retry_dispatches").func)
