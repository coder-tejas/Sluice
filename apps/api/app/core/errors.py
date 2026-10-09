import structlog

from fastapi import Request
from fastapi.exception import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

logger = stuctlog.get_logger("sluice.errors")

async  def http_exception_handler(
    request:Request,
    exc:HTTPException,
):
    request_id = getattr(
        request.state,
        "request.id",
        None
    )
    
    return JSONResponse(
        status_code = exc.status_code,
        content = {
            "error" :{
                "code" : "HTTP_ERROR",
                "message" : str(exc.detail),
                "request_id" : request_id,
            }
        }
    )
    
async def validation_exception_handler(
    request:Request,
    exc:RequestValidationError,
):
    request_id  = getattr(
        request.state,
        "request_id",
        None
    )
    return JSONResponse(
        status_code = HTTP_422_UNPROCESSABLE_ENTITY,
        content = {
            "error" : {
                "code" : "VALIDATION_ERROR",
                "message" : "Request validation Error",
                "request_id" : request_id,
                "details" : exc.errors(),
            }
        },
    )
    
async def unhandled_exception_handled(
    request:Request,
    exc:Exception
):
    request_id = getattr(
        request.state,
        "request_id",
        None
    )
    logger.exception(
        "unhandled_exception",
        exception_type = type(exc).__name__,
    )
    return JSONResponse(
        status_code = HTTP_500_INTERNAL_SERVER_ERROR,
        content = {
            "error" : {
                "code" : "INTERNAL_SERVER_ERROR",
                "message" : "An unexcepted error occurred",
                "request_id" : request_id,
            }
        },
    )
