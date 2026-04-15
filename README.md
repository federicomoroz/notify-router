# notify-router

A multi-channel notification routing engine built with FastAPI. Any system POSTs an event to it; configurable rules evaluate the payload; matched channels — email, Telegram, Slack, or any generic webhook — receive a formatted notification. Every dispatch is audited in full.

A **browser UI** lets you manage channels, rules, and events without touching the terminal. A seed dataset is loaded on first boot so the live demo is immediately explorable.

---

## Live Demo

```bash
git clone https://github.com/federicomoroz/notify-router
cd notify-router
pip install -r requirements.txt
uvicorn app.main:app --port 8003
```

Open **http://localhost:8003** in your browser.

On first startup with an empty database, two demo channels and two routing rules are created automatically:

| | Name | Type | Purpose |
|--|------|------|---------|
| Channel 1 | httpbin-webhook | webhook → `httpbin.org/post` | Always succeeds — shows a live dispatch |
| Channel 2 | slack-demo | slack → fake URL | Always fails — shows the failure path |
| Rule 1 | critical-alerts → webhook | `event_type=alert`, `severity=critical` | priority 10 |
| Rule 2 | all-alerts → slack | `event_type=alert`, any payload | priority 5 |

Go to the **Events** tab, hit **Send Event** with the pre-filled payload, and watch both rules fire in the dispatch result panel. Check the **Logs** tab to see the audit entries.

---

## What Problem It Solves

Modern services generate alerts, status changes, and business events from dozens of sources. Wiring each service directly to each notification channel creates a spaghetti of integrations: every new channel requires touching every producer, credentials scatter across codebases, and there is no central audit of what was sent to whom.

`notify-router` inverts this: producers post a generic event payload to a single endpoint. Routing rules — stored in a database and editable at runtime via the UI — decide which channels receive the notification and under what conditions. Adding a new channel or changing routing logic requires zero code changes.

```
                        ┌─────────────────────────────────────┐
  Any service           │           notify-router              │
  POST /events  ──────► │                                      │──► Email (SendGrid)
  {source,              │  Rules engine evaluates payload      │──► Telegram Bot
   event_type,          │  against all enabled rules           │──► Slack Webhook
   payload}             │                                      │──► Generic HTTP
                        │  Every dispatch written to audit log │
                        └─────────────────────────────────────┘
```

---

## Browser UI

`GET /` serves a single-page app with five tabs. No build step, no framework — vanilla JS talking to the REST API.

| Tab | What you can do |
|-----|----------------|
| **Dashboard** | Stats overview (events, dispatches, success/fail counts, success rate, channel and rule counts) + recent dispatch table |
| **Channels** | Create, edit, and delete channels. Config fields change dynamically based on channel type |
| **Rules** | Create and delete routing rules. Enable/disable individual rules with a toggle |
| **Events** | Send a test event and see the dispatch result inline — which rules matched, which channels succeeded or failed |
| **Logs** | Full dispatch audit log, filterable by status and event ID |

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
│   │       └── spa.py           # Pure-Python HTML renderer — full browser SPA
│   │
│   └── main.py                  # Composition root — wires all dependencies, lifespan, seed data
│
├── render.yaml                  # Render.com deploy config
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

`RuleRepository.match_all()` loads all enabled rules in priority order and filters them in Python, keeping the logic readable and testable without mocking SQLAlchemy:

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
`app/main.py` is the only place where concrete dependencies are created and wired together. Every other module depends on abstractions or receives dependencies via FastAPI's `Depends` / `request.app.state`. The entire dependency graph can be re-wired for testing without touching application code.

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

Rules are evaluated in `priority DESC` order. All three filters must pass for a rule to fire:

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
     | channel_id → channels.id
     | enabled | priority | created_at

events
  id | source | event_type | payload (JSON) | received_at

dispatch_logs
  id | event_id → events.id | rule_id | channel_id
     | channel_type | status (success|failed)
     | response_info | dispatched_at
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
| `DELETE` | `/channels/{id}` | Delete |

**Channel types and config keys:**

| type | config keys |
|------|-------------|
| `email` | `to`, `subject_template` (supports `{source}` and `{event_type}`) |
| `telegram` | `bot_token`, `chat_id` |
| `slack` | `webhook_url` |
| `webhook` | `url`, `method` (default `POST`), `headers` (optional dict) |

### Rules

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/rules` | List all rules (priority DESC) |
| `POST` | `/rules` | Create rule |
| `PUT` | `/rules/{id}` | Partial update (supports `enabled` toggle) |
| `DELETE` | `/rules/{id}` | Delete rule |

### Logs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/logs` | Dispatch audit log |

Query params: `event_id`, `status` (`success`\|`failed`), `limit` (1–10000, default 100).

### UI

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Browser SPA — full channel/rule/event management |
| `GET` | `/docs` | Swagger UI |

---

## Configuration

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
