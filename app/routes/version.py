from fastapi import APIRouter

from app.version import get_version_info

router = APIRouter()


@router.get("/version")
async def version():
    return get_version_info()
