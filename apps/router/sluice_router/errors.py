import json

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class OpenAIError(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        type_: str = "invalid_request_error",
        param: str | None = None,
        code: str | None = None,
    ):
        self.status_code = status_code
        self.message = message
        self.type = type_
        self.param = param
        self.code = code


def error_response(
    status_code: int,
    message: str,
    type_: str = "invalid_request_error",
    param: str | None = None,
    code: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": type_,
                "param": param,
                "code": code,
            }
        },
    )


async def openai_error_handler(_request, exc: OpenAIError) -> JSONResponse:
    return error_response(exc.status_code, exc.message, exc.type, exc.param, exc.code)


async def http_error_handler(_request, exc: HTTPException) -> JSONResponse:
    return error_response(exc.status_code, str(exc.detail))


async def validation_error_handler(
    _request, exc: RequestValidationError
) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    param = ".".join(str(p) for p in first.get("loc", ())[1:]) or None
    return error_response(
        400, first.get("msg", "Invalid request"), param=param, code="invalid_request"
    )


def upstream_response(status_code: int, content: bytes) -> JSONResponse:
    try:
        payload = json.loads(content)
    except ValueError:
        payload = None
    if not isinstance(payload, dict):
        payload = {
            "error": {
                "message": content.decode(errors="replace")[:500] or "Upstream error",
                "type": "server_error",
                "param": None,
                "code": "upstream_error",
            }
        }
    elif status_code >= 400 and "error" not in payload:
        payload = {
            "error": {
                "message": str(payload),
                "type": "server_error",
                "param": None,
                "code": "upstream_error",
            }
        }
    return JSONResponse(status_code=status_code, content=payload)
