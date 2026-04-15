# notify-router

A multi-channel notification routing engine built with FastAPI. Any system POSTs an event to it; configurable rules evaluate the payload; matched channels — email, Telegram, Slack, or any generic webhook — receive a formatted notification. Every dispatch is audited in full.

---

## What Problem It Solves

Modern services generate alerts, status changes, and business events from dozens of sources. Wiring each service directly to each notification channel creates a spaghetti of integrations: every new channel requires touching every producer, credentials scatter across codebases, and there is no central audit of what was sent to whom.

`notify-router` inverts this: producers post a generic event payload to a single endpoint. Routing rules — stored in a database and editable at runtime — decide which channels receive the notification and under what conditions. Adding a new channel or changing routing logic requires zero code changes.

```
                        ┌─────────────────────────────────────┐
  Any service           │           notify-router              │
  POST /events  ──────► │                                      │──► Email (SendGrid)
  {source,             │  Rules engine evaluates payload       │──► Telegram Bot
   event_type,          │  against all enabled rules           │──► Slack Webhook
   payload}             │                                      │──► Generic HTTP
                        │  Every dispatch written to audit log │
                        └─────────────────────────────────────┘
```

---

## Architecture

The project follows **MVC + Repository + Composition Root** with strict SOLID principles throughout. The core insight is that `POST /events` should not know anything about channels or logging — those concerns are injected and communicated via a synchronous pub/sub event bus.

```
notify-router/
├── app/
│   ├── core/
│   │   ├── config.py            # Flat env-var constants
│   │   ├── database.py          # SQLAlchemy engine, SessionLocal, FK enforcement
│   │   ├── event_manager.py     # Pub/sub event bus (subscribe / emit)
│   │   └── events.py            # Domain events: EventReceived, DispatchSucceeded, DispatchFailed
│   │
│   ├── controllers/
│   │   ├── pipeline.py          # RouterContext, PipelineStep protocol, RuleMatchStep, DispatchStep
│   │   ├── events_controller.py # POST /events — runs pipeline, returns dispatch summary
│   │   ├── rules_controller.py  # CRUD /rules
│   │   ├── channels_controller.py # CRUD /channels
│   │   └── logs_controller.py   # GET /logs with filters
│   │
│   ├── models/
│   │   ├── orm.py               # Channel, Rule, EventRecord, DispatchLog SQLAlchemy models
│   │   ├── repositories/
│   │   │   ├── event_repository.py
│   │   │   ├── rule_repository.py   # match_all() — filtered rule evaluation
│   │   │   ├── channel_repository.py
│   │   │   └── log_repository.py    # count_by_status(), purge_old()
│   │   └── services/
│   │       ├── interfaces.py        # ChannelBase ABC
│   │       ├── dispatcher_service.py # Registry: channel.type → ChannelBase impl
│   │       ├── log_listener.py      # Subscribes to events, writes DispatchLog
│   │       └── channels/
│   │           ├── email_channel.py    # SendGrid (non-blocking via executor)
│   │           ├── telegram_channel.py # Telegram Bot API
│   │           ├── slack_channel.py    # Slack Incoming Webhook
│   │           └── webhook_channel.py  # Generic HTTP (any method, custom headers)
│   │
│   ├── views/
│   │   ├── schemas/             # Pydantic v2 request/response models + validators
│   │   └── templates/
│   │       └── dashboard.py     # Pure-Python HTML renderer (80s terminal aesthetic)
│   │
│   └── main.py                  # Composition root — wires all dependencies, lifespan
│
└── requirements.txt
```

---

## Request Flow

```
POST /events  {source, event_type, payload}
  │
  ▼
EventsController.receive_event()
  │  persists EventRecord to SQLite
  │
  ▼
RouterPipeline.run(RouterContext)
  │
  ├─► RuleMatchStep.execute(ctx)
  │     RuleRepository.match_all(db, source, event_type, payload)
  │     → filters enabled rules by source, event_type, condition key/value
  │     → stores matched rules in ctx.matched_rules
  │
  └─► DispatchStep.execute(ctx)
        for each matched rule:
          ChannelRepository.get(db, rule.channel_id)
          DispatcherService.send(channel, event, payload)
          │
          ├── success → EventManager.emit(DispatchSucceeded)
          └── failure → EventManager.emit(DispatchFailed)
                              │
                        LogListener._on_success / _on_failed
                              │
                        LogRepository.create(db, DispatchLog)
                              │
                        SQLite dispatch_logs table

  Response: 202 {event_id, matched_rules, dispatches: [{rule_id, channel_id, status, info}]}
```

**Key property:** `EventsController` has zero knowledge of `LogListener` or `DispatchLog`. The controller only emits domain events; the listener subscribes at startup. Adding a new side-effect (e.g. a Prometheus counter) means adding one more subscriber — no existing code changes.

---

## Design Patterns

### Pipeline
`RouterPipeline` holds an ordered list of `PipelineStep` objects and calls `execute(ctx)` on each. Steps share state through `RouterContext` (a plain mutable dataclass). Adding a new processing step — say, a deduplication step or a rate-limit step per channel — means creating one new class and inserting it into the list at the composition root. No existing steps are modified.

```python
class RouterPipeline:
    def __init__(self, steps: list[PipelineStep]) -> None: ...
    async def run(self, ctx: RouterContext) -> list[dict]: ...
```

Unlike rate-guardian's pipeline (where a step can short-circuit by returning early), notify-router's pipeline **never short-circuits**: every matched rule is attempted independently. A Slack failure does not block the webhook.

### EventManager (Pub/Sub)
A minimal synchronous event bus. Components subscribe to typed events at startup; the emitter knows nothing about its subscribers.

```python
events.subscribe(DispatchSucceeded, log_listener._on_success)
events.subscribe(DispatchFailed,    log_listener._on_failed)

# later, in DispatchStep:
events.emit(DispatchSucceeded(event_id=..., rule_id=..., info="HTTP 200"))
```

This is the same `EventManager` used in rate-guardian — extracted as a reusable core component.

### Strategy (ChannelBase)
Each channel type is a stateless class implementing the `ChannelBase` ABC:

```python
class ChannelBase(ABC):
    @staticmethod
    @abstractmethod
    async def send(http, config, event, payload) -> tuple[bool, str]: ...
```

`DispatcherService` holds a registry mapping `channel.type` strings to implementations. Adding a new channel (e.g. PagerDuty) means writing one class and adding one entry to the registry — the dispatcher, pipeline, and controllers are untouched.

| Type | Implementation | Key config fields |
|------|---------------|-------------------|
| `email` | SendGrid API (via executor to avoid blocking) | `to`, `subject_template` |
| `telegram` | Telegram Bot API | `bot_token`, `chat_id` |
| `slack` | Incoming Webhook | `webhook_url` |
| `webhook` | Generic httpx request | `url`, `method`, `headers` |

### Repository
All database access is isolated behind static repository methods. Controllers and pipeline steps receive a `db: Session` and call `RuleRepository.match_all()`, `ChannelRepository.get()` etc. — never raw SQLAlchemy queries inline.

`RuleRepository.match_all()` is worth examining directly: it loads all enabled rules in priority order and filters them in Python, which keeps the logic readable and testable without mocking SQLAlchemy:

```python
def _matches(rule, source, event_type, payload) -> bool:
    if rule.source_filter != "*" and rule.source_filter != source:
        return False
    if rule.event_type_filter != "*" and rule.event_type_filter != event_type:
        return False
    if rule.condition_key:
        return str(payload.get(rule.condition_key, "")) == rule.condition_value
    return True
```

### Composition Root
`app/main.py` is the only place where concrete dependencies are created and wired together. Every other module depends on abstractions or receives dependencies via FastAPI's `Depends` / `request.app.state`. This means the entire dependency graph can be re-wired for testing without touching application code.

---

## SOLID Application

| Principle | Application |
|-----------|-------------|
| **S** — Single Responsibility | `RuleMatchStep` only matches; `DispatchStep` only dispatches; `LogListener` only writes logs. No class has two reasons to change. |
| **O** — Open/Closed | New channel types added by implementing `ChannelBase` + one registry entry. New pipeline steps added without modifying `RouterPipeline`. New event side-effects added without modifying `DispatchStep`. |
| **L** — Liskov Substitution | Any `ChannelBase` subclass can replace another in `DispatcherService._registry`. `PipelineStep` is a `@runtime_checkable` Protocol — violations caught at construction. |
| **I** — Interface Segregation | `ChannelBase` exposes a single method. Repositories expose only the queries their callers need. No god interfaces. |
| **D** — Dependency Inversion | `DispatchStep` depends on `DispatcherService` (injected via `RouterContext`). Controllers depend on `Request.app.state` (injected at composition root). Nothing instantiates its own dependencies. |

---

## Rule Matching

Rules are evaluated in `priority DESC` order. The first three filters are applied in sequence; a rule only fires if all pass:

| Field | Value | Behaviour |
|-------|-------|-----------|
| `source_filter` | `"*"` | Match any source |
| `source_filter` | `"monitor"` | Exact match only — case-sensitive |
| `event_type_filter` | `"*"` | Match any event type |
| `event_type_filter` | `"alert"` | Exact match only |
| `condition_key` | `null` | No payload condition — rule always fires |
| `condition_key` + `condition_value` | `"severity"` / `"critical"` | `str(payload["severity"]) == "critical"` |

Rules with `condition_key` set but `condition_value` omitted are rejected at the API layer (Pydantic `model_validator`). Both fields must be set together or both must be null.

**Multiple matches:** all matched rules fire independently. A Telegram failure does not prevent the webhook from firing.

---

## Data Model

```
channels
  id | name | type (email|telegram|slack|webhook) | config (JSON)

rules
  id | name | source_filter | event_type_filter
     | condition_key | condition_value
     | channel_id → channels.id (CASCADE DELETE)
     | enabled | priority | created_at

events
  id | source | event_type | payload (JSON) | received_at

dispatch_logs
  id | event_id → events.id | rule_id | channel_id
     | channel_type | status (success|failed)
     | response_info | dispatched_at
```

Deleting a channel cascade-deletes all its rules (enforced at ORM level and by `PRAGMA foreign_keys = ON` at the SQLite connection level).

---

## Quick Start

```bash
git clone https://github.com/federicomoroz/notify-router
cd notify-router
pip install -r requirements.txt
uvicorn app.main:app --port 8003 --reload
```

- **Dashboard:** `http://localhost:8003/`
- **Swagger UI:** `http://localhost:8003/docs`

---

## Usage Example

### 1 — Create a Slack channel

```bash
curl -X POST http://localhost:8003/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ops-slack",
    "type": "slack",
    "config": { "webhook_url": "https://hooks.slack.com/services/..." }
  }'
# → {"id": 1, "name": "ops-slack", "type": "slack", "config": {...}}
```

### 2 — Create a routing rule

```bash
curl -X POST http://localhost:8003/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "critical alerts → Slack",
    "source_filter": "*",
    "event_type_filter": "alert",
    "condition_key": "severity",
    "condition_value": "critical",
    "channel_id": 1,
    "priority": 10
  }'
```

### 3 — Post an event (matches the rule)

```bash
curl -X POST http://localhost:8003/events \
  -H "Content-Type: application/json" \
  -d '{
    "source": "monitor",
    "event_type": "alert",
    "payload": { "severity": "critical", "message": "disk at 95%" }
  }'
# → 202
# {
#   "event_id": 1,
#   "matched_rules": 1,
#   "dispatches": [
#     {"rule_id": 1, "channel_id": 1, "channel_type": "slack",
#      "status": "success", "info": "Slack OK"}
#   ]
# }
```

### 4 — Audit the dispatch

```bash
curl "http://localhost:8003/logs?event_id=1"
# → [{"id":1,"event_id":1,"channel_type":"slack","status":"success",
#      "response_info":"Slack OK","dispatched_at":"2026-..."}]
```

---

## API Reference

### Events

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/events` | Receive event, run pipeline, return dispatch summary (202) |
| `GET` | `/events?limit=N` | List recent events (default 50, max 1000) |

**POST /events body:**
```json
{
  "source":     "string (1–100 chars, required)",
  "event_type": "string (1–100 chars, required)",
  "payload":    "object (optional, max 4000 chars serialized)"
}
```

### Channels

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/channels` | List all channels |
| `POST` | `/channels` | Create channel |
| `PUT` | `/channels/{id}` | Partial update |
| `DELETE` | `/channels/{id}` | Delete (cascade-deletes rules) |

**Channel types and required config keys:**

| type | config keys |
|------|-------------|
| `email` | `to` (address), `subject_template` (optional, supports `{source}` and `{event_type}`) |
| `telegram` | `bot_token`, `chat_id` |
| `slack` | `webhook_url` |
| `webhook` | `url`, `method` (default `POST`), `headers` (optional dict) |

### Rules

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/rules` | List all rules (priority DESC) |
| `POST` | `/rules` | Create rule |
| `PUT` | `/rules/{id}` | Partial update |
| `DELETE` | `/rules/{id}` | Delete rule |

### Logs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/logs` | Dispatch audit log |

Query params: `event_id`, `status` (`success`\|`failed`), `limit` (1–10000, default 100).

### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | HTML dashboard — totals, success rate, recent dispatch log |

---

## Configuration

All settings via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./notify_router.db` | SQLAlchemy database URL |
| `SENDGRID_API_KEY` | _(empty)_ | Required for `email` channels |
| `SENDER_EMAIL` | _(empty)_ | From address for outgoing emails |
| `LOG_RETENTION_DAYS` | `30` | Dispatch logs older than this are purged daily |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (mapped columns) |
| Database | SQLite (swappable via `DATABASE_URL`) |
| HTTP client | httpx (async, shared `AsyncClient`) |
| Scheduler | APScheduler 3.10 (daily log purge) |
| Email | SendGrid Python SDK |
| Validation | Pydantic v2 |
| Python | 3.11+ |
