from fastapi import APIRouter
from starlette.exceptions import HTTPException

from app.core.database_async import check_async_connection


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "",
    summary="Health check",
)
async def health():
    return {
        "status": "ok",
    }


@router.get(
    "/ready",
    summary="Readiness check",
)
async def ready():
    try:
        assert await check_async_connection() == 1
    except Exception:
        raise HTTPException(status_code=503, detail="database not ready")
    return {
        "status": "ready",
    }