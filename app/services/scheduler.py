import os, asyncio
from sqlalchemy import text
from app.db import db, init_db
from app.services.epg_service import refresh_epg_for_playlist

async def start_scheduler():
    init_db()
    hours = int(os.getenv("EPG_REFRESH_HOURS", "6"))
    await asyncio.sleep(2)

    while True:
        try:
            with db() as conn:
                rows = conn.execute(
                    text("SELECT id, epg_url FROM playlists WHERE epg_url IS NOT NULL AND epg_url<>''")
                ).mappings().all()

            for r in rows:
                try:
                    await refresh_epg_for_playlist(r["id"], r["epg_url"])
                except Exception:
                    pass
        except Exception:
            pass

        await asyncio.sleep(hours * 3600)
