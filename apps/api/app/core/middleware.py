import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger("sluice.http")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request:Request,
        call_next,
    ):
        request_id = request.headers.get(
            "X-Request-ID"
        )
        
        if not request_id: 
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(
            request_id = request_id
        )
        start = time.perf_counter()
        
        try:
            response = await call_next(request)
            
            duration_ms = (
                time.perf_counter() - start,
            ) * 1000
            
            logger.info(
                "http_request",
                method = request.method,
                path = request.url.path,
                status_code = response.status_code,
                duration_ms = round(duration_ms,2),
            )
            response.headers["X-Request-ID"] = request_id
            
            return response
        except Exception:
            duration_ms = (
                time.perf_counter() - start
            ) * 1000
            
            logger.exception(
                "http_request_failed",
                method = request.method,
                path = request.url.path,
                status_code = 500,
                duration_ms = round(duration_ms,2),
            )
            raise
        finally:
            structlog.contextvars.clear_contextvars()