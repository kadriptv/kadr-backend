import os, asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import api_router
from app.services.scheduler import start_scheduler
from app.services.bootstrap import ensure_default_packages
from app.db import init_db

load_dotenv()

def create_app() -> FastAPI:
    app = FastAPI(title="IPTV Backend v3 (Stripe Subscriptions)", version="3.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.on_event("startup")
    async def _startup():
        init_db()
        ensure_default_packages()
        asyncio.create_task(start_scheduler())

    return app

app = create_app()
