from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException

from app.core.database_async import get_async_db

router = APIRouter(
    prefix="/db",
    tags=["Database"],
)


@router.get(
    "/ping",
    summary="Database session check",
)
async def db_ping(db: AsyncSession = Depends(get_async_db)):
    try:
        one = (await db.execute(text("SELECT 1"))).scalar()
    except Exception:
        raise HTTPException(status_code=503, detail="database not reachable")
    return {
        "db": "ok",
        "one": one,
    }
