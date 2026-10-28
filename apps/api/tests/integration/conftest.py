import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from app.core.config import get_settings
from app.main import app

CONTAINER_IMAGE = "postgres:16"


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Lifespan scope: single event loop for all requests in the test.
    # Pooled asyncpg connections are loop-bound, so a bare TestClient
    # (fresh loop per request) breaks DB-backed endpoints flakily.
    with TestClient(app) as client:
        yield client


def _base_url(raw: str) -> str:
    # testcontainers returns postgresql+psycopg2://...; strip to bare scheme
    # so each layer can add the driver it needs.
    return "postgresql://" + raw.split("://", 1)[1]


@pytest.fixture(scope="module")
def container_db_url():
    """Fresh real PostgreSQL, migrated to head. One container per module."""
    prev = os.environ.get("SLUICE_DATABASE_URL")
    with PostgresContainer(
        CONTAINER_IMAGE, username="sluice", password="sluice", dbname="sluice"
    ) as pg:
        url = _base_url(pg.get_connection_url())
        os.environ["SLUICE_DATABASE_URL"] = url
        get_settings.cache_clear()
        try:
            command.upgrade(Config("alembic.ini"), "head")
            yield url
        finally:
            if prev is None:
                os.environ.pop("SLUICE_DATABASE_URL", None)
            else:
                os.environ["SLUICE_DATABASE_URL"] = prev
            get_settings.cache_clear()


def make_session_factory(sync_url):
    """Async engine + sessions for one event loop. Dispose when done."""
    engine = create_async_engine(
        sync_url.replace("postgresql://", "postgresql+asyncpg://", 1),
        pool_pre_ping=True,
    )
    return engine, async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
