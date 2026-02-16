from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.security import create_token
from app.services.storage import (
    get_user_by_code,
    register_device,
    create_or_get_user_for_email,
    create_login_code,
    verify_login_code,
    get_user_by_email,
    is_subscription_active,
)
from app.services.mailer import send_login_code

router = APIRouter()

# -------- Legacy activation by admin-issued code (kept for backward compatibility) --------
class ActivateReq(BaseModel):
    code: str
    device_id: str

@router.post("/auth/activate")
def activate(req: ActivateReq):
    code = req.code.strip().upper()
    device_id = req.device_id.strip()
    if not code or not device_id:
        raise HTTPException(status_code=400, detail="code and device_id are required")
    user = get_user_by_code(code)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid code")
    if bool(user.get("is_disabled")):
        raise HTTPException(status_code=403, detail="User is disabled")
    # Require active subscription
    if not is_subscription_active(user):
        raise HTTPException(status_code=402, detail="Subscription inactive. Please оплатите пакет.")
    reg = register_device(user["id"], device_id)
    if not reg.get("ok"):
        raise HTTPException(status_code=403, detail=f"Device limit reached (limit={reg.get('limit')})")
    return {"access_token": create_token(user["id"]), "token_type": "bearer"}


# -------- Email + one-time code login (Gmail) --------
class RegisterReq(BaseModel):
    email: EmailStr

@router.post("/auth/register")
def register(req: RegisterReq):
    u = create_or_get_user_for_email(req.email)
    return {"ok": True, "user_id": u["id"], "status": u.get("status", "pending_payment")}

class RequestCodeReq(BaseModel):
    email: EmailStr

@router.post("/auth/request_code")
def request_code(req: RequestCodeReq):
    user = get_user_by_email(req.email)
    if not user:
        # allow auto-create to reduce friction
        user = create_or_get_user_for_email(req.email)
    if bool(user.get("is_disabled")):
        raise HTTPException(status_code=403, detail="User is disabled")
    if not is_subscription_active(user):
        raise HTTPException(status_code=402, detail="Subscription inactive. Please оплатите пакет.")
    code = create_login_code(user["id"])
    try:
        send_login_code(user["email"], code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")
    return {"ok": True, "message": "Login code sent to email"}

class VerifyCodeReq(BaseModel):
    email: EmailStr
    code: str

@router.post("/auth/verify_code")
def verify_code(req: VerifyCodeReq):
    user = get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if bool(user.get("is_disabled")):
        raise HTTPException(status_code=403, detail="User is disabled")
    if not is_subscription_active(user):
        raise HTTPException(status_code=402, detail="Subscription inactive. Please оплатите пакет.")
    ok = verify_login_code(user["id"], req.code.strip())
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    return {"access_token": create_token(user["id"]), "token_type": "bearer"}
