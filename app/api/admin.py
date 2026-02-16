import aiohttp
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.deps import require_admin
from app.services.storage import (
    create_package, list_packages, create_user, list_users,
    assign_package_to_user, save_playlist_for_package, get_latest_playlist_for_package
)
from app.services.epg_service import refresh_epg_for_playlist

router = APIRouter(dependencies=[Depends(require_admin)])

class PackageReq(BaseModel):
    name: str
    price_cents: int
    currency: str = "EUR"
    stripe_price_id: str

class UserReq(BaseModel):
    note: str = ""
    device_limit: int = 2

class FromUrlReq(BaseModel):
    url: str

@router.post("/packages")
def create_pkg(req: PackageReq):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if req.price_cents < 0:
        raise HTTPException(status_code=400, detail="price_cents must be >= 0")
    if not req.stripe_price_id.strip():
        raise HTTPException(status_code=400, detail="stripe_price_id is required")
    return create_package(name, req.price_cents, req.currency, req.stripe_price_id.strip())

@router.get("/packages")
def get_pkgs():
    return {"items": list_packages()}

@router.post("/users")
def create_usr(req: UserReq):
    return create_user(note=req.note or "", device_limit=req.device_limit or 2)

@router.get("/users")
def get_users():
    return {"items": list_users()}

@router.post("/users/{user_id}/packages/{package_id}")
def assign_pkg(user_id: str, package_id: str):
    return assign_package_to_user(user_id, package_id, active_until=None)

@router.post("/packages/{package_id}/playlist/upload")
async def upload_playlist(package_id: str, file: UploadFile = File(...), refresh_epg: bool = True):
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1251", errors="ignore")
    meta = save_playlist_for_package(text, package_id, "file", file.filename or "upload")
    if refresh_epg and meta.get("epg_url"):
        try:
            meta["epg"] = {"refreshed": True, **(await refresh_epg_for_playlist(meta["playlist_id"], meta["epg_url"]))}
        except Exception as e:
            meta["epg"] = {"refreshed": False, "error": str(e)}
    return meta

@router.post("/packages/{package_id}/playlist/from_url")
async def playlist_from_url(package_id: str, req: FromUrlReq, refresh_epg: bool = True):
    url = req.url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    timeout = aiohttp.ClientTimeout(total=60)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                raw = await resp.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot download M3U: {e}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1251", errors="ignore")
    meta = save_playlist_for_package(text, package_id, "url", url)
    if refresh_epg and meta.get("epg_url"):
        try:
            meta["epg"] = {"refreshed": True, **(await refresh_epg_for_playlist(meta["playlist_id"], meta["epg_url"]))}
        except Exception as e:
            meta["epg"] = {"refreshed": False, "error": str(e)}
    return meta

@router.get("/packages/{package_id}/playlist/latest")
def latest_playlist(package_id: str):
    return {"item": get_latest_playlist_for_package(package_id)}
