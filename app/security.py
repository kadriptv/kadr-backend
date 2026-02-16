import os, base64, hmac, hashlib, json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

def _secret() -> bytes:
    return os.getenv("TOKEN_SECRET", "change-me-too").encode("utf-8")

def _ttl_hours() -> int:
    return int(os.getenv("TOKEN_TTL_HOURS", "168"))

def create_token(user_id: str) -> str:
    payload = {"uid": user_id, "exp": (datetime.now(timezone.utc) + timedelta(hours=_ttl_hours())).isoformat().replace("+00:00","Z")}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(_secret(), raw, hashlib.sha256).digest()
    def b64(b): return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")
    return b64(raw) + "." + b64(sig)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        raw_b64, sig_b64 = token.split(".", 1)
        def unb64(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
        raw = unb64(raw_b64)
        sig = unb64(sig_b64)
        expected = hmac.new(_secret(), raw, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(raw.decode("utf-8"))
        exp = datetime.fromisoformat(payload["exp"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) >= exp:
            return None
        return payload
    except Exception:
        return None
