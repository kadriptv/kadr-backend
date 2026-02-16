import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

def _db_url() -> str:
    # Example: postgresql+psycopg2://user:pass@host:5432/dbname
    return os.getenv("DB_URL", "")

_engine = None

def engine():
    global _engine
    if _engine is None:
        url = _db_url()
        if not url:
            raise RuntimeError("DB_URL is not set (Postgres required for production)")
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine

def init_db() -> None:
    """
    Create tables if not exist. Designed for Postgres.
    """
    eng = engine()
    ddl = [
        # users (legacy code kept for backward compatibility)
        """
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE,
            email TEXT UNIQUE,
            note TEXT,
            device_limit INTEGER NOT NULL DEFAULT 2,
            is_disabled BOOLEAN NOT NULL DEFAULT FALSE,

            status TEXT NOT NULL DEFAULT 'pending_payment', -- pending_payment|active|past_due|expired|blocked
            paid_until TIMESTAMPTZ,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            current_package_id TEXT,
            next_package_id TEXT,
            created_at TIMESTAMPTZ NOT NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users(stripe_customer_id);",
        "CREATE INDEX IF NOT EXISTS idx_users_stripe_sub ON users(stripe_subscription_id);",

        """
        CREATE TABLE IF NOT EXISTS user_devices(
            user_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            first_seen_at TIMESTAMPTZ NOT NULL,
            PRIMARY KEY(user_id, device_id)
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS packages(
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price_cents INTEGER NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'EUR',
            stripe_price_id TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_packages_price ON packages(price_cents);",

        """
        CREATE TABLE IF NOT EXISTS user_packages(
            user_id TEXT NOT NULL,
            package_id TEXT NOT NULL,
            active_until TIMESTAMPTZ,
            PRIMARY KEY(user_id, package_id)
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS playlists(
            id TEXT PRIMARY KEY,
            package_id TEXT NOT NULL,
            source_type TEXT NOT NULL,      -- file|url
            source_value TEXT NOT NULL,     -- filename|url
            m3u_text TEXT,                  -- stored copy (optional)
            epg_url TEXT,
            created_at TIMESTAMPTZ NOT NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_playlists_pkg ON playlists(package_id);",

        """
        CREATE TABLE IF NOT EXISTS channels(
            playlist_id TEXT NOT NULL,
            tvg_id TEXT NOT NULL,
            name TEXT NOT NULL,
            tvg_name TEXT,
            logo TEXT,
            grp TEXT,
            stream_url TEXT NOT NULL,
            raw_extinf TEXT,
            PRIMARY KEY(playlist_id, tvg_id)
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_channels_grp ON channels(playlist_id, grp);",
        "CREATE INDEX IF NOT EXISTS idx_channels_name ON channels(playlist_id, name);",

        """
        CREATE TABLE IF NOT EXISTS epg_programmes(
            playlist_id TEXT NOT NULL,
            tvg_id TEXT NOT NULL,
            start_utc TIMESTAMPTZ NOT NULL,
            stop_utc TIMESTAMPTZ NOT NULL,
            title TEXT,
            desc TEXT,
            PRIMARY KEY(playlist_id, tvg_id, start_utc, stop_utc)
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_epg_now ON epg_programmes(playlist_id, tvg_id, start_utc, stop_utc);",

        """
        CREATE TABLE IF NOT EXISTS login_codes(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            code TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            used BOOLEAN NOT NULL DEFAULT FALSE
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_login_codes_user ON login_codes(user_id, created_at);",

        """
        CREATE TABLE IF NOT EXISTS payments(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            provider TEXT NOT NULL, -- stripe
            event_type TEXT,
            stripe_event_id TEXT,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            amount_cents INTEGER,
            currency TEXT,
            status TEXT,
            raw_json TEXT,
            created_at TIMESTAMPTZ NOT NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id, created_at);",
    ]
    with eng.begin() as conn:
        for stmt in ddl:
            conn.execute(text(stmt))

@contextmanager
def db() -> Connection:
    init_db()
    conn = engine().connect()
    trans = conn.begin()
    try:
        yield conn
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
