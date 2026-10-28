import asyncio

from sqlalchemy import text

from app.core.database import Base
from app.core.database_async import AsyncSessionLocal, async_engine
from app.repositories.system_metadata import SystemMetadataRepository


def run(coro):
    return asyncio.run(coro)


async def _reset():
    await async_engine.dispose()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as s:
        await s.execute(text("DELETE FROM system_metadata"))
        await s.commit()


async def _drop():
    async with AsyncSessionLocal() as s:
        await s.execute(text("DELETE FROM system_metadata"))
        await s.commit()
    await async_engine.dispose()


def _repo(session):
    return SystemMetadataRepository(session)


def test_crud_roundtrip():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                repo = _repo(s)
                created = await repo.create("r1", "v1")
                assert created.id is not None

                assert (await repo.get(created.id)).value == "v1"
                assert (await repo.get_by_key("r1")).id == created.id

                updated = await repo.update(created, "v2")
                assert updated.value == "v2"

                await repo.delete(updated)
                assert await repo.get(created.id) is None
                assert (await repo.list()) == []
        finally:
            await _drop()

    run(_test())


def test_list_pagination():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                repo = _repo(s)
                for i in range(3):
                    await repo.create(f"k{i}", f"v{i}")

            async with AsyncSessionLocal() as s:
                repo = _repo(s)
                page = await repo.list(limit=2, offset=1)
                assert [e.key for e in page] == ["k1", "k2"]
                assert len(await repo.list()) == 3
        finally:
            await _drop()

    run(_test())


def test_get_missing_returns_none():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                repo = _repo(s)
                assert await repo.get(999999) is None
                assert await repo.get_by_key("nope") is None
        finally:
            await _drop()

    run(_test())
