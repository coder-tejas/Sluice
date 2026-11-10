import json

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse


def stub_upstream() -> FastAPI:
    stub = FastAPI()

    @stub.post("/v1/chat/completions")
    async def completions(request: Request):
        body = await request.json()
        if body.get("stream"):

            async def events():
                for token in ["Hel", "lo", "!"]:
                    chunk = {
                        "id": "chatcmpl-stub",
                        "object": "chat.completion.chunk",
                        "created": 0,
                        "model": body["model"],
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": token},
                                "finish_reason": None,
                            }
                        ],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(events(), media_type="text/event-stream")

        return {
            "id": "chatcmpl-stub",
            "object": "chat.completion",
            "created": 0,
            "model": body["model"],
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        }

    return stub


@pytest.fixture
def stub_app() -> FastAPI:
    return stub_upstream()
