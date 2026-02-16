from fastapi import APIRouter
from app.services.storage import list_packages

router = APIRouter()

@router.get("/packages")
def packages():
    items = list_packages()
    # do not expose stripe_price_id to the app if you don't want (but app needs it only for checkout via backend)
    return {"items": [{"id": p["id"], "name": p["name"], "price_cents": p["price_cents"], "currency": p["currency"]} for p in items]}
