from fastapi import APIRouter
from app.db import init_db
router = APIRouter()
@router.get("/health")
def health():
    init_db()
    return {"status":"ok"}
