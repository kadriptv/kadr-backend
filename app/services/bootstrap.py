import os
from datetime import datetime, timezone

from sqlalchemy import text

from app.db import db


def bootstrap():
    # Таблицы создаются в init_db() внутри db()
    # Тут только сидинг тарифов
    ensure_default_packages()


def ensure_default_packages():
    """
    Seed Basic/Premium packages if packages table is empty.
    Requires STRIPE_BASIC_PRICE_ID and STRIPE_PREMIUM_PRICE_ID in environment.
    """
    basic_price_id = os.getenv("STRIPE_BASIC_PRICE_ID", "").strip()
    prem_price_id = os.getenv("STRIPE_PREMIUM_PRICE_ID", "").strip()

    # Не падаем, просто пропускаем (можно создать пакеты через админку)
    if not basic_price_id or not prem_price_id:
        return

    now = datetime.now(timezone.utc)

    with db() as conn:
        cnt = conn.execute(text("SELECT COUNT(*) AS c FROM packages")).mappings().first()["c"]
        if cnt and int(cnt) > 0:
            return

        conn.execute(
            text(
                """
                INSERT INTO packages(id, name, price_cents, currency, stripe_price_id, created_at)
                VALUES(:id, :name, :price_cents, :currency, :stripe_price_id, :created_at)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": "pkg_basic",
                "name": "Basic",
                "price_cents": 500,
                "currency": "EUR",
                "stripe_price_id": basic_price_id,
                "created_at": now,
            },
        )

        conn.execute(
            text(
                """
                INSERT INTO packages(id, name, price_cents, currency, stripe_price_id, created_at)
                VALUES(:id, :name, :price_cents, :currency, :stripe_price_id, :created_at)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": "pkg_premium",
                "name": "Premium",
                "price_cents": 950,
                "currency": "EUR",
                "stripe_price_id": prem_price_id,
                "created_at": now,
            },
        )
