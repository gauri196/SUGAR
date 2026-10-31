"""
SUGAR — Database Engine, Session Factory, and Declarative Base.

Connection URL is read from the environment variable SUGAR_DATABASE_URL.
Falls back to a local SQLite file at instance/sugar.db for development.

To use PostgreSQL in staging or production, set the environment variable:
    SUGAR_DATABASE_URL=postgresql+psycopg2://user:password@host:5432/sugar

Never hardcode credentials here.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# ---------------------------------------------------------------------------
# Connection URL
# ---------------------------------------------------------------------------

_DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent.parent / "instance" / "sugar.db"
_DEFAULT_URL = f"sqlite:///{_DEFAULT_SQLITE_PATH}"

DATABASE_URL: str = os.environ.get("SUGAR_DATABASE_URL", _DEFAULT_URL)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    echo=False,  # Set to True to log all SQL statements during debugging.
)

# Enable WAL mode and foreign-key enforcement for SQLite connections.
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all SUGAR ORM models."""


# ---------------------------------------------------------------------------
# FastAPI dependency helper
# ---------------------------------------------------------------------------

def get_db():
    """
    Yield a database session and guarantee it is closed after the request.

    Usage in a route::

        from backend.database import get_db
        from sqlalchemy.orm import Session

        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
