from fastapi import APIRouter

from app.version import VERSION

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "CNIS Parser API", "version": VERSION}
