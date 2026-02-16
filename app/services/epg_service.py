from datetime import datetime, timezone
from typing import Dict, Any, List

from sqlalchemy import text

from app.db import db
from app.parsers.xmltv import iter_programmes_from_bytes
from app.services.downloader import download_bytes

def _maybe_decompress(data: bytes) -> bytes:
    # gzip magic header
    if data[:2] == b"\x1f\x8b":
        import gzip
        return gzip.decompress(data)
    return data

async def refresh_epg_for_playlist(playlist_id: str, epg_url: str) -> Dict[str, Any]:
    raw = await download_bytes(epg_url, timeout_total=120)
    xml_bytes = _maybe_decompress(raw)

    inserted = 0
    started_at = datetime.now(timezone.utc)

    with db() as conn:
        conn.execute(text("DELETE FROM epg_programmes WHERE playlist_id=:pid"), {"pid": playlist_id})
        for p in iter_programmes_from_bytes(xml_bytes):
            conn.execute(
                text("INSERT INTO epg_programmes(playlist_id, tvg_id, start_utc, stop_utc, title, desc) "
                     "VALUES(:pid,:tvg,:start,:stop,:title,:desc) "
                     "ON CONFLICT (playlist_id, tvg_id, start_utc, stop_utc) DO UPDATE SET title=EXCLUDED.title, desc=EXCLUDED.desc"),
                {
                    "pid": playlist_id,
                    "tvg": p.tvg_id,
                    "start": p.start_utc.replace("Z","+00:00"),
                    "stop": p.stop_utc.replace("Z","+00:00"),
                    "title": p.title,
                    "desc": p.desc,
                }
            )
            inserted += 1

    return {
        "playlist_id": playlist_id,
        "epg_url": epg_url,
        "programmes_inserted": inserted,
        "started_at": started_at.isoformat(),
    }

def now_next_for_playlists(playlist_ids: List[str], tvg_id: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    with db() as conn:
        for pid in playlist_ids:
            now_row = conn.execute(
                text("SELECT title, desc, start_utc, stop_utc FROM epg_programmes "
                     "WHERE playlist_id=:pid AND tvg_id=:tvg AND start_utc<=:now AND stop_utc>:now "
                     "ORDER BY start_utc DESC LIMIT 1"),
                {"pid": pid, "tvg": tvg_id, "now": now},
            ).mappings().first()

            next_row = conn.execute(
                text("SELECT title, desc, start_utc, stop_utc FROM epg_programmes "
                     "WHERE playlist_id=:pid AND tvg_id=:tvg AND start_utc>:now "
                     "ORDER BY start_utc ASC LIMIT 1"),
                {"pid": pid, "tvg": tvg_id, "now": now},
            ).mappings().first()

            if now_row or next_row:
                def obj(r):
                    if not r:
                        return None
                    return {
                        "title": r["title"],
                        "desc": r["desc"],
                        "start": r["start_utc"].isoformat(),
                        "stop": r["stop_utc"].isoformat(),
                    }

                return {"tvg_id": tvg_id, "playlist_id": pid, "now": obj(now_row), "next": obj(next_row)}

    return {"tvg_id": tvg_id, "playlist_id": None, "now": None, "next": None}
