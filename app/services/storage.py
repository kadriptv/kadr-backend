import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import text

from app.db import db
from app.parsers.m3u import parse_m3u, extract_epg_url


# ---------- Packages ----------
def create_package(name: str, price_cents: int, currency: str, stripe_price_id: str) -> Dict[str, Any]:
    package_id = f"pkg_{uuid.uuid4().hex[:10]}"
    created_at = datetime.now(timezone.utc)
    with db() as conn:
        conn.execute(
            text("INSERT INTO packages(id, name, price_cents, currency, stripe_price_id, created_at) "
                 "VALUES(:id,:name,:price,:cur,:spi,:ca)"),
            {"id": package_id, "name": name, "price": int(price_cents), "cur": currency.upper(), "spi": stripe_price_id, "ca": created_at},
        )
    return {"package_id": package_id, "name": name, "price_cents": int(price_cents), "currency": currency.upper(), "stripe_price_id": stripe_price_id}

def list_packages() -> List[dict]:
    with db() as conn:
        rows = conn.execute(text("SELECT id, name, price_cents, currency, stripe_price_id, created_at FROM packages ORDER BY price_cents ASC")).mappings().all()
        return [dict(r) for r in rows]

def get_package(package_id: str) -> Optional[dict]:
    with db() as conn:
        r = conn.execute(text("SELECT * FROM packages WHERE id=:id"), {"id": package_id}).mappings().first()
        return dict(r) if r else None


# ---------- Users / Subscription ----------
def get_user_by_code(code: str) -> Optional[dict]:
    with db() as conn:
        row = conn.execute(text("SELECT id, code, device_limit, is_disabled, status, paid_until FROM users WHERE code=:c"), {"c": code}).mappings().first()
        return dict(row) if row else None

def get_user_by_email(email: str) -> Optional[dict]:
    e = (email or "").strip().lower()
    if not e:
        return None
    with db() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE email=:e"), {"e": e}).mappings().first()
        return dict(row) if row else None

def get_user_by_stripe_customer(customer_id: str) -> Optional[dict]:
    with db() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE stripe_customer_id=:c"), {"c": customer_id}).mappings().first()
        return dict(row) if row else None

def get_user_by_stripe_subscription(sub_id: str) -> Optional[dict]:
    with db() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE stripe_subscription_id=:s"), {"s": sub_id}).mappings().first()
        return dict(row) if row else None

def create_or_get_user_for_email(email: str, device_limit: int = 2) -> dict:
    e = email.strip().lower()
    now = datetime.now(timezone.utc)
    with db() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE email=:e"), {"e": e}).mappings().first()
        if row:
            return dict(row)
        user_id = f"usr_{uuid.uuid4().hex[:10]}"
        # legacy activation code (optional)
        code = f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
        conn.execute(
            text("INSERT INTO users(id, code, email, note, device_limit, is_disabled, status, created_at) "
                 "VALUES(:id,:code,:email,'',:dl,FALSE,'pending_payment',:ca)"),
            {"id": user_id, "code": code, "email": e, "dl": int(device_limit), "ca": now},
        )
        row2 = conn.execute(text("SELECT * FROM users WHERE id=:id"), {"id": user_id}).mappings().first()
        return dict(row2)

def set_user_stripe(customer_id: str, subscription_id: str, email: Optional[str] = None, user_id: Optional[str] = None) -> None:
    with db() as conn:
        if user_id:
            conn.execute(
                text("UPDATE users SET stripe_customer_id=:c, stripe_subscription_id=:s WHERE id=:id"),
                {"c": customer_id, "s": subscription_id, "id": user_id},
            )
        elif email:
            conn.execute(
                text("UPDATE users SET stripe_customer_id=:c, stripe_subscription_id=:s WHERE email=:e"),
                {"c": customer_id, "s": subscription_id, "e": email.strip().lower()},
            )
        else:
            conn.execute(
                text("UPDATE users SET stripe_subscription_id=:s WHERE stripe_customer_id=:c"),
                {"c": customer_id, "s": subscription_id},
            )


def set_user_current_package(user_id: str, package_id: str) -> None:
    with db() as conn:
        conn.execute(text("UPDATE users SET current_package_id=:p WHERE id=:id"), {"p": package_id, "id": user_id})


def update_subscription_state(user_id: str, status: str, paid_until: Optional[datetime]) -> None:
    with db() as conn:
        conn.execute(
            text("UPDATE users SET status=:st, paid_until=:pu WHERE id=:id"),
            {"st": status, "pu": paid_until, "id": user_id},
        )

def is_subscription_active(user: dict) -> bool:
    if not user:
        return False
    if bool(user.get("is_disabled")):
        return False
    status = (user.get("status") or "").lower()
    if status not in ("active",):
        return False
    pu = user.get("paid_until")
    if not pu:
        return False
    if isinstance(pu, str):
        try:
            pu = datetime.fromisoformat(pu.replace("Z","+00:00"))
        except Exception:
            return False
    return datetime.now(timezone.utc) < pu


# ---------- Login codes (email OTP) ----------
def create_login_code(user_id: str, ttl_minutes: int = 10) -> str:
    code = f"{uuid.uuid4().int % 1000000:06d}"
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ttl_minutes)
    lc_id = f"lc_{uuid.uuid4().hex[:10]}"
    with db() as conn:
        # mark old unused as used
        conn.execute(text("UPDATE login_codes SET used=TRUE WHERE user_id=:uid AND used=FALSE"), {"uid": user_id})
        conn.execute(
            text("INSERT INTO login_codes(id, user_id, code, created_at, expires_at, used) VALUES(:id,:uid,:code,:ca,:ea,FALSE)"),
            {"id": lc_id, "uid": user_id, "code": code, "ca": now, "ea": expires},
        )
    return code

def verify_login_code(user_id: str, code: str) -> bool:
    now = datetime.now(timezone.utc)
    with db() as conn:
        row = conn.execute(
            text("SELECT id, code, expires_at, used FROM login_codes WHERE user_id=:uid ORDER BY created_at DESC LIMIT 1"),
            {"uid": user_id},
        ).mappings().first()
        if not row:
            return False
        if bool(row["used"]):
            return False
        if row["code"] != code:
            return False
        if row["expires_at"] <= now:
            return False
        # consume
        conn.execute(text("UPDATE login_codes SET used=TRUE WHERE id=:id"), {"id": row["id"]})
        return True


# ---------- Devices ----------
def register_device(user_id: str, device_id: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    with db() as conn:
        lim = conn.execute(text("SELECT device_limit FROM users WHERE id=:id"), {"id": user_id}).mappings().first()
        if not lim:
            raise ValueError("user not found")
        limit = int(lim["device_limit"])
        exists = conn.execute(text("SELECT 1 FROM user_devices WHERE user_id=:u AND device_id=:d"), {"u": user_id, "d": device_id}).first()
        if exists:
            return {"ok": True, "already": True, "limit": limit}
        cnt = conn.execute(text("SELECT COUNT(*) AS c FROM user_devices WHERE user_id=:u"), {"u": user_id}).mappings().first()["c"]
        if int(cnt) >= limit:
            return {"ok": False, "error": "device_limit_reached", "limit": limit}
        conn.execute(
            text("INSERT INTO user_devices(user_id, device_id, first_seen_at) VALUES(:u,:d,:t)"),
            {"u": user_id, "d": device_id, "t": now},
        )
    return {"ok": True, "already": False, "limit": limit}


# ---------- Playlists / Channels ----------
def save_playlist_for_package(m3u_text: str, package_id: str, source_type: str, source_value: str) -> Dict[str, Any]:
    playlist_id = f"pl_{uuid.uuid4().hex[:10]}"
    created_at = datetime.now(timezone.utc)
    epg_url = extract_epg_url(m3u_text)
    channels = parse_m3u(m3u_text)

    with db() as conn:
        conn.execute(
            text("INSERT INTO playlists(id, package_id, source_type, source_value, m3u_text, epg_url, created_at) "
                 "VALUES(:id,:pkg,:st,:sv,:m3u,:epg,:ca)"),
            {"id": playlist_id, "pkg": package_id, "st": source_type, "sv": source_value, "m3u": m3u_text, "epg": epg_url, "ca": created_at},
        )
        for ch in channels:
            conn.execute(
                text("INSERT INTO channels(playlist_id, tvg_id, name, tvg_name, logo, grp, stream_url, raw_extinf) "
                     "VALUES(:pid,:tvg,:name,:tvg_name,:logo,:grp,:url,:raw) "
                     "ON CONFLICT (playlist_id, tvg_id) DO UPDATE SET "
                     "name=EXCLUDED.name, tvg_name=EXCLUDED.tvg_name, logo=EXCLUDED.logo, grp=EXCLUDED.grp, stream_url=EXCLUDED.stream_url, raw_extinf=EXCLUDED.raw_extinf"),
                {"pid": playlist_id, "tvg": ch.tvg_id, "name": ch.name, "tvg_name": ch.tvg_name, "logo": ch.logo, "grp": ch.grp, "url": ch.stream_url, "raw": ch.raw_extinf},
            )

    return {"playlist_id": playlist_id, "package_id": package_id, "epg_url": epg_url, "channels_count": len(channels)}

def get_latest_playlist_for_package(package_id: str) -> Optional[dict]:
    with db() as conn:
        row = conn.execute(
            text("SELECT * FROM playlists WHERE package_id=:pkg ORDER BY created_at DESC LIMIT 1"),
            {"pkg": package_id},
        ).mappings().first()
        return dict(row) if row else None

def get_active_playlists_for_user(user_id: str) -> List[dict]:
    now = datetime.now(timezone.utc)
    with db() as conn:
        pkgs = conn.execute(
            text("SELECT package_id, active_until FROM user_packages WHERE user_id=:u AND (active_until IS NULL OR active_until > :now)"),
            {"u": user_id, "now": now},
        ).mappings().all()

        playlists = []
        for r in pkgs:
            pl = conn.execute(
                text("SELECT * FROM playlists WHERE package_id=:pkg ORDER BY created_at DESC LIMIT 1"),
                {"pkg": r["package_id"]},
            ).mappings().first()
            if pl:
                playlists.append(dict(pl))
        return playlists

def list_groups_for_playlists(playlist_ids: List[str]) -> List[str]:
    if not playlist_ids:
        return []
    with db() as conn:
        rows = conn.execute(
            text("SELECT DISTINCT grp FROM channels WHERE playlist_id = ANY(:ids) AND grp IS NOT NULL AND grp<>'' ORDER BY grp"),
            {"ids": playlist_ids},
        ).mappings().all()
        return [r["grp"] for r in rows]

def list_channels_for_playlists(playlist_ids: List[str], group: Optional[str]=None, search: Optional[str]=None, limit: int=5000) -> List[dict]:
    if not playlist_ids:
        return []
    params = {"ids": playlist_ids, "limit": limit}
    sql = "SELECT playlist_id, tvg_id, name, tvg_name, logo, grp, stream_url FROM channels WHERE playlist_id = ANY(:ids)"
    if group:
        sql += " AND grp=:grp"
        params["grp"] = group
    if search:
        sql += " AND (name ILIKE :s OR tvg_id ILIKE :s OR COALESCE(tvg_name,'') ILIKE :s)"
        params["s"] = f"%{search}%"
    sql += " ORDER BY grp, name LIMIT :limit"

    with db() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
        return [dict(r) for r in rows]


# ---------- User packages assignment (used by admin & also for active playlists) ----------
def assign_package_to_user(user_id: str, package_id: str, active_until: Optional[datetime] = None) -> Dict[str, Any]:
    with db() as conn:
        conn.execute(
            text("INSERT INTO user_packages(user_id, package_id, active_until) VALUES(:u,:p,:au) "
                 "ON CONFLICT (user_id, package_id) DO UPDATE SET active_until=EXCLUDED.active_until"),
            {"u": user_id, "p": package_id, "au": active_until},
        )
    return {"user_id": user_id, "package_id": package_id, "active_until": active_until.isoformat() if active_until else None}

def create_user(note: str = "", device_limit: int = 2) -> Dict[str, Any]:
    # legacy admin-created user without email
    user_id = f"usr_{uuid.uuid4().hex[:10]}"
    code = f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
    created_at = datetime.now(timezone.utc)
    with db() as conn:
        conn.execute(
            text("INSERT INTO users(id, code, note, device_limit, is_disabled, status, created_at) "
                 "VALUES(:id,:code,:note,:dl,FALSE,'pending_payment',:ca)"),
            {"id": user_id, "code": code, "note": note, "dl": int(device_limit), "ca": created_at},
        )
    return {"user_id": user_id, "code": code, "note": note, "device_limit": int(device_limit)}

def list_users() -> List[dict]:
    with db() as conn:
        rows = conn.execute(
            text("SELECT id, code, email, note, device_limit, is_disabled, status, paid_until, stripe_customer_id, stripe_subscription_id, created_at "
                 "FROM users ORDER BY created_at DESC")
        ).mappings().all()
        return [dict(r) for r in rows]
