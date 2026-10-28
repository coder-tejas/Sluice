import asyncio

import pytest
from sqlalchemy import text

from app.core.database import Base
from app.core.database_async import AsyncSessionLocal, async_engine
from app.schemas.system_metadata import SystemMetadataCreate, SystemMetadataRead
from app.services.system_metadata import (
    DuplicateKeyError,
    EntryNotFoundError,
    SystemMetadataService,
)


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


def test_create_and_read_dto():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                created = await SystemMetadataService(s).create_entry(
                    SystemMetadataCreate(key="s1", value="v")
                )
                assert isinstance(created, SystemMetadataRead)
                assert created.key == "s1"
                assert created.id is not None

                read = await SystemMetadataService(s).get_entry("s1")
                assert read == created
        finally:
            await _drop()

    run(_test())


def test_blank_or_oversize_rejected():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                service = SystemMetadataService(s)
                with pytest.raises(ValueError):
                    await service.create_entry(SystemMetadataCreate(key="   "))
                with pytest.raises(ValueError):
                    await service.create_entry(
                        SystemMetadataCreate(key="k" * 129)
                    )
                with pytest.raises(ValueError):
                    await service.create_entry(
                        SystemMetadataCreate(key="k", value="v" * 513)
                    )
        finally:
            await _drop()

    run(_test())


def test_duplicate_rolls_back_and_session_survives():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                service = SystemMetadataService(s)
                await service.create_entry(SystemMetadataCreate(key="dup"))
                with pytest.raises(DuplicateKeyError):
                    await service.create_entry(SystemMetadataCreate(key="dup"))
                # session usable after the handled conflict
                again = await service.create_entry(
                    SystemMetadataCreate(key="after-dup", value="ok")
                )
                assert again.key == "after-dup"
        finally:
            await _drop()

    run(_test())


def test_missing_raises_not_found():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                service = SystemMetadataService(s)
                with pytest.raises(EntryNotFoundError):
                    await service.get_entry("nope")
                with pytest.raises(EntryNotFoundError):
                    await service.update_entry("nope", "v")
                with pytest.raises(EntryNotFoundError):
                    await service.delete_entry("nope")
        finally:
            await _drop()

    run(_test())


def test_update_and_delete():
    async def _test():
        await _reset()
        try:
            async with AsyncSessionLocal() as s:
                service = SystemMetadataService(s)
                await service.create_entry(SystemMetadataCreate(key="u1", value="a"))
                updated = await service.update_entry("u1", "b")
                assert updated.value == "b"

                entries = await service.list_entries()
                assert [e.key for e in entries] == ["u1"]

                await service.delete_entry("u1")
                with pytest.raises(EntryNotFoundError):
                    await service.get_entry("u1")
        finally:
            await _drop()

    run(_test())
