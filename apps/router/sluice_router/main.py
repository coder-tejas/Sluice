from contextlib import asynccontextmanager
from time import time

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import StreamingResponse
from starlette.exceptions import HTTPException

from sluice_router.config import get_settings
from sluice_router.errors import (
    OpenAIError,
    http_error_handler,
    openai_error_handler,
    upstream_response,
    validation_error_handler,
)


def create_app(upstream_transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.http = httpx.AsyncClient(
            base_url=settings.worker_url.rstrip("/"),
            timeout=httpx.Timeout(settings.upstream_timeout, connect=10.0),
            transport=upstream_transport,
        )
        app.state.model_created = int(time())
        yield
        await app.state.http.aclose()

    app = FastAPI(title="Sluice Router", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(OpenAIError, openai_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/v1/models")
    async def list_models():
        return {
            "object": "list",
            "data": [
                {
                    "id": settings.model_id,
                    "object": "model",
                    "created": app.state.model_created,
                    "owned_by": "sluice",
                }
            ],
        }

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        try:
            body = await request.json()
        except ValueError:
            raise OpenAIError(
                400, "Request body must be valid JSON", code="invalid_json"
            )
        if not isinstance(body, dict):
            raise OpenAIError(
                400, "Request body must be a JSON object", code="invalid_body"
            )
        if body.get("model") != settings.model_id:
            raise OpenAIError(
                404,
                f"The model '{body.get('model')}' does not exist",
                param="model",
                code="model_not_found",
            )
        if not isinstance(body.get("messages"), list) or not body["messages"]:
            raise OpenAIError(
                400,
                "You must provide a non-empty 'messages' array",
                param="messages",
                code="missing_messages",
            )

        client: httpx.AsyncClient = request.app.state.http

        if not body.get("stream"):
            try:
                upstream = await client.post("/v1/chat/completions", json=body)
            except httpx.HTTPError as exc:
                raise OpenAIError(
                    502,
                    f"Upstream model server unavailable: {exc}",
                    type_="server_error",
                    code="upstream_unavailable",
                )
            return upstream_response(upstream.status_code, upstream.content)

        req = client.build_request(
            "POST",
            "/v1/chat/completions",
            json=body,
            headers={"accept": "text/event-stream"},
        )
        try:
            upstream = await client.send(req, stream=True)
        except httpx.HTTPError as exc:
            raise OpenAIError(
                502,
                f"Upstream model server unavailable: {exc}",
                type_="server_error",
                code="upstream_unavailable",
            )

        if upstream.status_code != 200:
            try:
                raw = await upstream.aread()
            finally:
                await upstream.aclose()
            return upstream_response(upstream.status_code, raw)

        async def relay():
            try:
                async for chunk in upstream.aiter_raw():
                    yield chunk
            finally:
                await upstream.aclose()

        return StreamingResponse(
            relay(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


app = create_app()
