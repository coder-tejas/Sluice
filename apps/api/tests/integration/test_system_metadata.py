import asyncio

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.core.database_async import AsyncSessionLocal, async_engine
from app.models.system_metadata import SystemMetadata


def run(coro):
    return asyncio.run(coro)


async def _reset():
    await async_engine.dispose()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def _drop():
    async with AsyncSessionLocal() as s:
        await s.execute(text("DROP TABLE IF EXISTS system_metadata"))
        await s.commit()
    await async_engine.dispose()


def test_insert_and_select():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                s.add(SystemMetadata(key="m26", value="hi"))
                await s.commit()

            async with AsyncSessionLocal() as s:
                row = (
                    await s.execute(
                        select(SystemMetadata).where(SystemMetadata.key == "m26")
                    )
                ).scalar_one()
                assert row.value == "hi"
                assert row.created_at is not None
                assert row.updated_at is not None
        finally:
            await _drop()

    run(_test())


def test_nullable_value():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                s.add(SystemMetadata(key="null-val"))
                await s.commit()

            async with AsyncSessionLocal() as s:
                row = (
                    await s.execute(
                        select(SystemMetadata).where(SystemMetadata.key == "null-val")
                    )
                ).scalar_one()
                assert row.value is None
        finally:
            await _drop()

    run(_test())


def test_unique_key_violation():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                s.add(SystemMetadata(key="dup", value="1"))
                await s.commit()

            async with AsyncSessionLocal() as s:
                s.add(SystemMetadata(key="dup", value="2"))
                with pytest.raises(IntegrityError):
                    await s.commit()
        finally:
            await _drop()

    run(_test())
