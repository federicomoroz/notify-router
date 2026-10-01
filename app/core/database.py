from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def upgrade_schema(target=None) -> None:
    """
    create_all() makes missing tables but never changes existing ones, so a
    database from an older version gets its new columns here. Safe to run on
    every start: it only adds what is missing.
    """
    target = target or engine
    columns = {c["name"] for c in inspect(target).get_columns("events")}
    with target.begin() as conn:
        if "idempotency_key" not in columns:
            conn.execute(text("ALTER TABLE events ADD COLUMN idempotency_key VARCHAR(100)"))
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_events_source_idempotency_key "
            "ON events (source, idempotency_key)"
        ))
