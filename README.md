# notify-router

Multi-channel notification routing engine. Any system POSTs an event; configurable rules evaluate the payload and matched channels (email, Telegram, Slack, generic webhook) receive a formatted notification. All dispatches are audited.

## Architecture

```
POST /events
  └── EventsController
        └── RouterPipeline
              ├── RuleMatchStep   — filter rules by source / event_type / condition
              └── DispatchStep    — call DispatcherService per rule → emit domain events

EventManager (pub/sub)
  └── LogListener → writes DispatchLog to SQLite

DispatcherService
  ├── EmailChannel    (SendGrid)
  ├── TelegramChannel (Bot API)
  ├── SlackChannel    (Incoming Webhook)
  └── WebhookChannel  (generic HTTP)
```

Patterns: Pipeline · EventManager · Strategy · Repository · SOLID throughout.

## Quick start

```bash
pip install -r requirements.txt
uvicorn app.main:app --port 8003 --reload
```

Open `http://localhost:8003/` for the dashboard or `http://localhost:8003/docs` for the API.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./notify_router.db` | SQLAlchemy DB URL |
| `SENDGRID_API_KEY` | `` | Required for email channels |
| `SENDER_EMAIL` | `` | From address for emails |
| `LOG_RETENTION_DAYS` | `30` | Days before dispatch logs are purged |

## Example usage

### 1. Create a Slack channel
```bash
curl -X POST http://localhost:8003/channels \
  -H "Content-Type: application/json" \
  -d '{"name":"ops-slack","type":"slack","config":{"webhook_url":"https://hooks.slack.com/..."}}'
```

### 2. Create a rule
```bash
curl -X POST http://localhost:8003/rules \
  -H "Content-Type: application/json" \
  -d '{"name":"critical alerts","source_filter":"*","event_type_filter":"alert","condition_key":"severity","condition_value":"critical","channel_id":1}'
```

### 3. Send an event
```bash
curl -X POST http://localhost:8003/events \
  -H "Content-Type: application/json" \
  -d '{"source":"monitor","event_type":"alert","payload":{"severity":"critical","message":"disk 95%"}}'
```

### 4. Check logs
```bash
curl http://localhost:8003/logs
```
