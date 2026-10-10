from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.core.middleware import RequestIDMiddleware

settings = get_settings()

configure_logging(
    log_level = settings.log_level,
    environment = settings.environment,
)

logger = structlog.get_logger("sluice")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "application_starting",
        app_name = settings.app_name,
        version = settings.app_version,
        environment = settings.environment,
    )
    yield
    logger.info(
        "application_stopping"
    )
    
app = FastAPI(
    title = settings.app_name,
    version = settings.app_version,
    description = (
        "Sluice is a prod grade-oriented"
        "ML/LLM  inference platform"
    ),
    docs_url = "/docs",
    redoc_url = "/redoc",
    openapi_url = "/openapi.json",
    lifespan=lifespan
    )

app.add_middleware(
    RequestIDMiddleware,
)

app.add_exception_handler(
    HTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    unhandled_exception_handler,
)

app.include_router(
    v1_router
)