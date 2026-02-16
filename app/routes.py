from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.me import router as me_router
from app.api.public import router as public_router
from app.api.billing import router as billing_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/api", tags=["health"])
api_router.include_router(public_router, prefix="/api", tags=["public"])
api_router.include_router(auth_router, prefix="/api", tags=["auth"])
api_router.include_router(billing_router, prefix="/api", tags=["billing"])
api_router.include_router(admin_router, prefix="/api/admin", tags=["admin"])
api_router.include_router(me_router, prefix="/api/me", tags=["me"])
