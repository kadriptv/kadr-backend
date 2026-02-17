import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


_engine: Engine | None = None


def _get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    # Render Postgres URL may be 'postgres://', SQLAlchemy prefers 'postgresql://'
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://"):]

    _engine = create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )
    return _engine


def init_db() -> None:
    """
    Idempotent DB schema init.
    IMPORTANT: no manual commit/rollback here; engine.begin() handles it.
    """
    engine = _get_engine()

    statements = [
        # USERS
        """
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        );
        """,
        # PACKAGES
        """
        CREATE TABLE IF NOT EXISTS packages(
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price_cents INTEGER NOT NULL,
            currency TEXT NOT NULL,
            stripe_price_id TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        );
        """,
        # SUBSCRIPTIONS
        """
        CREATE TABLE IF NOT EXISTS subscriptions(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            package_id TEXT NOT NULL,
            status TEXT NOT NULL,
            stripe_subscription_id TEXT,
            created_at TIMESTAMPTZ NOT NULL
        );
        """,
        # PLAYLISTS
        """
        CREATE TABLE IF NOT EXISTS playlists(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            url TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        );
        """,
        # EPG (ВАЖНО: description вместо desc)
        """
        CREATE TABLE IF NOT EXISTS epg_programmes(
            playlist_id TEXT NOT NULL,
            tvg_id TEXT NOT NULL,
            start_utc TIMESTAMPTZ NOT NULL,
            stop_utc TIMESTAMPTZ NOT NULL,
            title TEXT,
            description TEXT,
            PRIMARY KEY (playlist_id, tvg_id, start_utc, stop_utc)
        );
        """,
    ]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


@contextmanager
def db():
    """
    Safe connection context. Always ensures schema exists.
    Uses engine.begin() to avoid 'transaction is inactive' issues.
    """
    init_db()
    engine = _get_engine()
    with engine.begin() as conn:
        yield conn
