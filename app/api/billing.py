import os
import json
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import text

from app.db import db
from app.services.storage import (
    get_package,
    create_or_get_user_for_email,
    set_user_stripe,
    update_subscription_state,
    set_user_current_package,
    assign_package_to_user,
    get_user_by_stripe_customer,
    get_user_by_stripe_subscription,
)

router = APIRouter()

def _stripe():
    key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY is not set")
    stripe.api_key = key
    return stripe

def _base_url() -> str:
    return os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")

def _success_url() -> str:
    # You can point this to your website; for app flow user can just go back.
    return os.getenv("STRIPE_SUCCESS_URL", (_base_url() + "/paid") if _base_url() else "https://example.com/paid")

def _cancel_url() -> str:
    return os.getenv("STRIPE_CANCEL_URL", (_base_url() + "/cancel") if _base_url() else "https://example.com/cancel")

class CheckoutReq(BaseModel):
    email: EmailStr
    package_id: str

@router.post("/billing/checkout")
def create_checkout(req: CheckoutReq):
    pkg = get_package(req.package_id)
    if not pkg:
        raise HTTPException(status_code=400, detail="Invalid package_id")
    if not pkg.get("stripe_price_id"):
        raise HTTPException(status_code=500, detail="Package stripe_price_id not configured")

    user = create_or_get_user_for_email(req.email)
    st = _stripe()

    # Create or reuse Stripe customer
    customer_id = user.get("stripe_customer_id")
    if not customer_id:
        customer = st.Customer.create(email=user["email"], metadata={"user_id": user["id"]})
        customer_id = customer["id"]

    # Create Stripe Checkout Session for subscription
    session = st.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": pkg["stripe_price_id"], "quantity": 1}],
        success_url=_success_url(),
        cancel_url=_cancel_url(),
        allow_promotion_codes=True,
        metadata={"user_id": user["id"], "package_id": pkg["id"]},
        subscription_data={
            "metadata": {"user_id": user["id"], "package_id": pkg["id"]},
        },
    )

    # save customer id now (subscription id will come in webhook)
    with db() as conn:
        conn.execute(text("UPDATE users SET stripe_customer_id=:c, next_package_id=NULL WHERE id=:id"), {"c": customer_id, "id": user["id"]})

    return {"checkout_url": session["url"], "session_id": session["id"]}


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    wh_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not wh_secret:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET is not set")

    st = _stripe()

    try:
        event = st.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=wh_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {e}")

    etype = event["type"]
    obj = event["data"]["object"]

    # Helper to persist payment event
    def _save_payment(user_id: str | None):
        try:
            with db() as conn:
                conn.execute(text("""
                    INSERT INTO payments(
                        id, user_id, provider, event_type, stripe_event_id,
                        stripe_customer_id, stripe_subscription_id,
                        amount_cents, currency, status, raw_json, created_at
                    ) VALUES(
                        :id, :uid, 'stripe', :etype, :eid,
                        :cust, :sub,
                        :amt, :cur, :st, :raw, :ca
                    )
                    ON CONFLICT (id) DO NOTHING
                """), {
                    "id": f"pay_{event['id'][:24]}",
                    "uid": user_id or "",
                    "etype": etype,
                    "eid": event["id"],
                    "cust": obj.get("customer"),
                    "sub": obj.get("subscription") if isinstance(obj, dict) else None,
                    "amt": obj.get("amount_paid") if isinstance(obj, dict) else None,
                    "cur": (obj.get("currency") or "").upper() if isinstance(obj, dict) else None,
                    "st": obj.get("status") if isinstance(obj, dict) else None,
                    "raw": payload.decode("utf-8", errors="ignore"),
                    "ca": datetime.now(timezone.utc),
                })
        except Exception:
            pass

    # Extract user
    user = None
    user_id = None

    if etype == "checkout.session.completed":
        # session object
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        meta = obj.get("metadata") or {}
        user_id = meta.get("user_id")
        package_id = meta.get("package_id")

        if customer_id and subscription_id:
            set_user_stripe(customer_id, subscription_id, user_id=user_id)
        # fetch subscription to get period end
        try:
            sub = st.Subscription.retrieve(subscription_id)
            paid_until = datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc)
            if user_id:
                update_subscription_state(user_id, "active", paid_until)
                if package_id:
                    set_user_current_package(user_id, package_id)
                    assign_package_to_user(user_id, package_id, active_until=paid_until)
        except Exception:
            pass

    elif etype in ("invoice.paid", "invoice.payment_succeeded"):
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        if subscription_id:
            user = get_user_by_stripe_subscription(subscription_id)
        if not user and customer_id:
            user = get_user_by_stripe_customer(customer_id)
        if user:
            user_id = user["id"]
            try:
                sub = st.Subscription.retrieve(subscription_id) if subscription_id else None
                if sub:
                    paid_until = datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc)
                    update_subscription_state(user_id, "active", paid_until)
                    pkg = (sub.get("metadata") or {}).get("package_id") or user.get("current_package_id")
                    if pkg:
                        set_user_current_package(user_id, pkg)
                        assign_package_to_user(user_id, pkg, active_until=paid_until)
            except Exception:
                pass

    elif etype == "invoice.payment_failed":
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        if subscription_id:
            user = get_user_by_stripe_subscription(subscription_id)
        if not user and customer_id:
            user = get_user_by_stripe_customer(customer_id)
        if user:
            user_id = user["id"]
            # keep paid_until as-is; mark past_due
            update_subscription_state(user_id, "past_due", user.get("paid_until"))

    elif etype == "customer.subscription.deleted":
        subscription_id = obj.get("id")
        user = get_user_by_stripe_subscription(subscription_id)
        if user:
            user_id = user["id"]
            # ended now
            update_subscription_state(user_id, "expired", datetime.now(timezone.utc))

    elif etype == "customer.subscription.updated":
        subscription_id = obj.get("id")
        user = get_user_by_stripe_subscription(subscription_id)
        if user:
            user_id = user["id"]
            paid_until = datetime.fromtimestamp(obj.get("current_period_end", int(datetime.now(timezone.utc).timestamp())), tz=timezone.utc)
            status = obj.get("status") or "active"
            mapped = "active" if status in ("active", "trialing") else ("past_due" if status in ("past_due", "unpaid") else "expired")
            update_subscription_state(user_id, mapped, paid_until)

    _save_payment(user_id)

    return {"ok": True}
