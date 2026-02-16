import os
from datetime import datetime, timezone
from sqlalchemy import text
from app.db import db


def bootstrap():
    with db() as conn:
        # --- USERS ---
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        """))

        # --- PACKAGES ---
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS packages(
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price_cents INTEGER NOT NULL,
            currency TEXT NOT NULL,
            stripe_price_id TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        """))

        # --- SUBSCRIPTIONS ---
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS subscriptions(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            package_id TEXT NOT NULL,
            status TEXT NOT NULL,
            stripe_subscription_id TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        """))

        # --- PLAYLISTS ---
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS playlists(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            url TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        """))

        # --- EPG (ВАЖНО: исправлено desc → description) ---
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS epg_programmes(
            playlist_id TEXT NOT NULL,
            tvg_id TEXT NOT NULL,
            start_utc TIMESTAMP WITH TIME ZONE NOT NULL,
            stop_utc TIMESTAMP WITH TIME ZONE NOT NULL,
            title TEXT,
            description TEXT,
            PRIMARY KEY (playlist_id, tvg_id, start_utc, stop_utc)
        );
        """))

        conn.commit()

    # Заполняем тарифы
    ensure_default_packages()


def ensure_default_packages():
    basic_price_id = os.getenv("STRIPE_BASIC_PRICE_ID", "").strip()
    prem_price_id = os.getenv("STRIPE_PREMIUM_PRICE_ID", "").strip()

    if not basic_price_id or not prem_price_id:
        return

    now = datetime.now(timezone.utc)

    with db() as conn:
        cnt = conn.execute(text("SELECT COUNT(*) AS c FROM packages")).mappings().first()["c"]
        if cnt and int(cnt) > 0:
            return

        conn.execute(text("""
            INSERT INTO packages(id, name, price_cents, currency, stripe_price_id, created_at)
            VALUES(:id, :name, :price_cents, :currency, :stripe_price_id, :created_at)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": "pkg_basic",
            "name": "Basic",
            "price_cents": 500,
            "currency": "EUR",
            "stripe_price_id": basic_price_id,
            "created_at": now,
        })

        conn.execute(text("""
            INSERT INTO packages(id, name, price_cents, currency, stripe_price_id, created_at)
            VALUES(:id, :name, :price_cents, :currency, :stripe_price_id, :created_at)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": "pkg_premium",
            "name": "Premium",
            "price_cents": 950,
            "currency": "EUR",
            "stripe_price_id": prem_price_id,
            "created_at": now,
        })

        conn.commit()
