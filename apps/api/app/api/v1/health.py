from fastapi import APIRouter


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
    return {
        "status": "ready",
    }