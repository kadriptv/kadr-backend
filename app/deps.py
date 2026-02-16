import os
from datetime import datetime, timezone
from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text

from app.security import verify_token
from app.db import db

bearer = HTTPBearer(auto_error=False)

def require_admin(x_admin_key: str = Header(default="", alias="X-Admin-Key")):
    if x_admin_key != os.getenv("ADMIN_KEY", "change-me"):
        raise HTTPException(status_code=401, detail="Admin key missing or invalid")
    return True

def require_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    payload = verify_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    with db() as conn:
        u = conn.execute(
            text("SELECT id, is_disabled, status, paid_until FROM users WHERE id=:id"),
            {"id": user_id},
        ).mappings().first()

        if not u:
            raise HTTPException(status_code=401, detail="User not found")
        if bool(u["is_disabled"]):
            raise HTTPException(status_code=403, detail="User is disabled")

        status = (u["status"] or "").lower()
        pu = u["paid_until"]
        if status != "active" or pu is None or datetime.now(timezone.utc) >= pu:
            # 402 is reasonable for "payment required"
            raise HTTPException(status_code=402, detail="Subscription inactive or expired. Please оплатите пакет.")

    return {"user_id": user_id}
