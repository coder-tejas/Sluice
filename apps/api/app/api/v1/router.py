from fastapi import APIRouter
from app.api.v1.db import router as db_router
from app.api.v1.health import router as health_router

router = APIRouter(prefix="/v1")
router.include_router(health_router)
router.include_router(db_router)

#future
#router.include_router(models.router)
#router.include_router(inference.router)
#router.include_router(deployements.router)