from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.deps import require_user
from app.db import db
from app.services.storage import get_active_playlists_for_user, list_groups_for_playlists, list_channels_for_playlists
from app.services.epg_service import now_next_for_playlists

router = APIRouter()

@router.get("/me")
def me(user=Depends(require_user)):
    with db() as conn:
        u = conn.execute(text("SELECT id, email, status, paid_until, current_package_id FROM users WHERE id=:id"), {"id": user["user_id"]}).mappings().first()
        pkg = None
        if u and u.get("current_package_id"):
            pkg = conn.execute(text("SELECT id, name, price_cents, currency FROM packages WHERE id=:id"), {"id": u["current_package_id"]}).mappings().first()
    return {
        "user_id": user["user_id"],
        "email": u.get("email") if u else None,
        "status": u.get("status") if u else None,
        "paid_until": u.get("paid_until").isoformat() if (u and u.get("paid_until")) else None,
        "package": dict(pkg) if pkg else None,
    }

@router.get("/groups")
def groups(user=Depends(require_user)):
    pls = get_active_playlists_for_user(user["user_id"])
    ids = [p["id"] for p in pls]
    return {"groups": list_groups_for_playlists(ids)}

@router.get("/channels")
def channels(group: str | None = None, search: str | None = None, limit: int = 5000, user=Depends(require_user)):
    pls = get_active_playlists_for_user(user["user_id"])
    ids = [p["id"] for p in pls]
    return {"group": group, "search": search, "items": list_channels_for_playlists(ids, group=group, search=search, limit=limit)}

@router.get("/epg/now_next/{tvg_id}")
def epg_now_next(tvg_id: str, user=Depends(require_user)):
    pls = get_active_playlists_for_user(user["user_id"])
    ids = [p["id"] for p in pls]
    if not ids:
        raise HTTPException(status_code=403, detail="No active playlists for this user")
    return now_next_for_playlists(ids, tvg_id)
