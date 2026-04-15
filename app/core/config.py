import os

DATABASE_URL       = os.getenv("DATABASE_URL", "sqlite:///./notify_router.db")
SENDGRID_API_KEY   = os.getenv("SENDGRID_API_KEY", "")
SENDER_EMAIL       = os.getenv("SENDER_EMAIL", "")
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "30"))
