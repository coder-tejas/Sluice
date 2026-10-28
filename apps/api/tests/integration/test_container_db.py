"""Repository + service against a real containerized PostgreSQL."""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.system_metadata import SystemMetadata
from app.repositories.system_metadata import SystemMetadataRepository
from app.schemas.system_metadata import SystemMetadataCreate
from app.services.system_metadata import DuplicateKeyError, SystemMetadataService
from tests.integration.conftest import make_session_factory


def run(coro):
    return asyncio.run(coro)


def test_crud_on_real_postgres(container_db_url):
    async def _test():
        engine, factory = make_session_factory(container_db_url)
        try:
            async with factory() as s:
                repo = SystemMetadataRepository(s)
                created = await repo.create("c1", "v1")
                assert (await repo.get(created.id)).value == "v1"
                assert (await repo.get_by_key("c1")).id == created.id
                assert [e.key for e in await repo.list()] == ["c1"]
                await repo.update(created, "v2")
                assert (await repo.get(created.id)).value == "v2"
                await repo.delete(created)
                assert await repo.get(created.id) is None
        finally:
            await engine.dispose()

    run(_test())


def test_unique_constraint_enforced(container_db_url):
    async def _test():
        engine, factory = make_session_factory(container_db_url)
        try:
            async with factory() as s:
                repo = SystemMetadataRepository(s)
                await repo.create("uniq", "1")
                with pytest.raises(IntegrityError):
                    await repo.create("uniq", "2")
                await s.rollback()
                assert (await repo.get_by_key("uniq")).value == "1"
        finally:
            await engine.dispose()

    run(_test())


def test_rollback_discards_write(container_db_url):
    async def _test():
        engine, factory = make_session_factory(container_db_url)
        try:
            async with factory() as s:
                # uncommitted write, then rollback
                s.add(SystemMetadata(key="tmp", value="x"))
                await s.flush()
                await s.rollback()

            async with factory() as s:
                assert await SystemMetadataRepository(s).get_by_key("tmp") is None
        finally:
            await engine.dispose()

    run(_test())


def test_service_duplicate_maps_to_domain_error(container_db_url):
    async def _test():
        engine, factory = make_session_factory(container_db_url)
        try:
            async with factory() as s:
                service = SystemMetadataService(s)
                await service.create_entry(SystemMetadataCreate(key="svc"))
                with pytest.raises(DuplicateKeyError):
                    await service.create_entry(SystemMetadataCreate(key="svc"))
                assert (await service.get_entry("svc")).value is None
        finally:
            await engine.dispose()

    run(_test())


def test_connection_failure_surfaces():
    async def _test():
        engine, _ = make_session_factory("postgresql://u:p@127.0.0.1:1/db")
        try:
            with pytest.raises(Exception):
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
        finally:
            await engine.dispose()

    run(_test())
