import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest
from openai import AsyncOpenAI, NotFoundError

from sluice_router.main import create_app


@asynccontextmanager
async def _client(stub_app):
    router = create_app(httpx.ASGITransport(app=stub_app))
    async with router.router.lifespan_context(router):
        http = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=router), base_url="http://router"
        )
        client = AsyncOpenAI(
            base_url="http://router/v1", api_key="test", http_client=http
        )
        try:
            yield client
        finally:
            await client.close()


def run(coro):
    return asyncio.run(coro)


def test_models_list(stub_app):
    async def _test():
        async with _client(stub_app) as client:
            models = await client.models.list()
            assert [m.id for m in models.data] == ["qwen2.5-0.5b-instruct"]

    run(_test())


def test_non_streaming_completion(stub_app):
    async def _test():
        async with _client(stub_app) as client:
            resp = await client.chat.completions.create(
                model="qwen2.5-0.5b-instruct",
                messages=[{"role": "user", "content": "hi"}],
            )
            assert resp.choices[0].message.content == "Hello!"
            assert resp.usage.total_tokens == 5

    run(_test())


def test_streaming_deltas(stub_app):
    async def _test():
        async with _client(stub_app) as client:
            stream = await client.chat.completions.create(
                model="qwen2.5-0.5b-instruct",
                messages=[{"role": "user", "content": "hi"}],
                stream=True,
            )
            text = ""
            async for chunk in stream:
                text += chunk.choices[0].delta.content or ""
            assert text == "Hello!"

    run(_test())


def test_unknown_model_is_404(stub_app):
    async def _test():
        async with _client(stub_app) as client:
            with pytest.raises(NotFoundError) as exc:
                await client.chat.completions.create(
                    model="nope", messages=[{"role": "user", "content": "hi"}]
                )
            assert exc.value.status_code == 404
            assert exc.value.body["code"] == "model_not_found"

    run(_test())


def test_malformed_body_is_openai_400(stub_app):
    async def _test():
        router = create_app(httpx.ASGITransport(app=stub_app))
        async with (
            router.router.lifespan_context(router),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=router), base_url="http://router"
            ) as http,
        ):
            resp = await http.post(
                "/v1/chat/completions",
                content=b"{not json",
                headers={"content-type": "application/json"},
            )
        assert resp.status_code == 400
        assert set(resp.json()["error"]) == {"message", "type", "param", "code"}

    run(_test())


def test_unknown_route_uses_openai_envelope(stub_app):
    async def _test():
        router = create_app(httpx.ASGITransport(app=stub_app))
        async with (
            router.router.lifespan_context(router),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=router), base_url="http://router"
            ) as http,
        ):
            resp = await http.get("/nope")
        assert resp.status_code == 404
        assert "error" in resp.json()

    run(_test())
