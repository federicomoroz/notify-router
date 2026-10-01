import json
import os
import tempfile
from dataclasses import dataclass, field

import httpx
import pytest

# The app reads its settings when imported, so the test database is chosen first.
_db_dir = tempfile.mkdtemp(prefix="notify-router-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_db_dir, 'test.db')}"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.orm import Channel, DispatchLog, DispatchRetry, EventRecord, Rule  # noqa: E402
from app.models.services.dispatcher_service import DispatcherService  # noqa: E402


@dataclass
class Outbound:
    """Records every HTTP call the channels make and answers with the configured status."""

    status: int = 200
    requests: list[httpx.Request] = field(default_factory=list)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if "api.telegram.org" in str(request.url):
            return httpx.Response(self.status, json={"ok": True, "result": {"message_id": 7}})
        return httpx.Response(self.status, text="ok")

    def bodies(self) -> list[dict]:
        return [json.loads(r.content) for r in self.requests]


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        # What the first boot created, captured before any test cleans the tables.
        db = SessionLocal()
        try:
            c.seeded = {
                "channels": [(ch.name, ch.type) for ch in db.query(Channel).all()],
                "rules": [r.name for r in db.query(Rule).all()],
            }
        finally:
            db.close()
        yield c


@pytest.fixture
def outbound(client):
    """Routes the channels' HTTP calls to a fake, so no test reaches the internet."""
    fake = Outbound()
    client.app.state.dispatcher = DispatcherService(httpx.AsyncClient(transport=httpx.MockTransport(fake.handler)))
    return fake


@pytest.fixture
def clean(client):
    db = SessionLocal()
    try:
        for model in (DispatchRetry, DispatchLog, Rule, Channel, EventRecord):
            db.query(model).delete()
        db.commit()
    finally:
        db.close()
    return client


def make_channel(client, name: str, type_: str, config: dict) -> int:
    response = client.post("/channels", json={"name": name, "type": type_, "config": config})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def make_rule(client, channel_id: int, **fields) -> int:
    body = {"name": fields.pop("name", "rule"), "channel_id": channel_id, **fields}
    response = client.post("/rules", json=body)
    assert response.status_code == 201, response.text
    return response.json()["id"]
