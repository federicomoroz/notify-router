import os

DATABASE_URL       = os.getenv("DATABASE_URL", "sqlite:///./notify_router.db")
SENDGRID_API_KEY   = os.getenv("SENDGRID_API_KEY", "")
SENDER_EMAIL       = os.getenv("SENDER_EMAIL", "")
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "30"))

# Optional reliability features. Left unset, notify-router behaves exactly as before:
# POST /events is open and a failed dispatch is logged and not tried again.
# Read them as `config.NAME` at the point of use, so they can be changed at runtime.

# When set, POST /events requires the same value in the X-API-Key header.
INGEST_API_KEY         = os.getenv("INGEST_API_KEY", "")

# Total attempts per dispatch, the first one included. 1 means no retries.
DISPATCH_MAX_ATTEMPTS  = int(os.getenv("DISPATCH_MAX_ATTEMPTS", "1"))
RETRY_INTERVAL_SECONDS = int(os.getenv("RETRY_INTERVAL_SECONDS", "15"))
