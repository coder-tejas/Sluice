"""Migrations own the schema: upgrade/downgrade on a blank database."""

import os

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from testcontainers.community.postgres import PostgresContainer

from app.core.config import get_settings
from tests.integration.conftest import CONTAINER_IMAGE, _base_url


def _sync_url(raw: str) -> str:
    return _base_url(raw).replace("postgresql://", "postgresql+psycopg://", 1)


def test_migration_cycle_from_scratch():
    with PostgresContainer(
        CONTAINER_IMAGE, username="sluice", password="sluice", dbname="sluice"
    ) as pg:
        url = _sync_url(pg.get_connection_url())
        cfg = Config("alembic.ini")
        engine = create_engine(url)
        # env.py resolves the URL from settings at run time, so point the
        # process env at the container for the duration of this test.
        prev = os.environ.get("SLUICE_DATABASE_URL")
        os.environ["SLUICE_DATABASE_URL"] = _base_url(pg.get_connection_url())
        get_settings.cache_clear()
        try:
            command.upgrade(cfg, "head")
            tables = inspect(engine).get_table_names()
            assert "system_metadata" in tables
            assert "models" in tables
            assert "model_versions" in tables
            with engine.connect() as conn:
                assert conn.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one() is not None

            command.downgrade(cfg, "base")
            tables = inspect(engine).get_table_names()
            assert "system_metadata" not in tables
            assert "models" not in tables
            assert "model_versions" not in tables

            command.upgrade(cfg, "head")
            assert "models" in inspect(engine).get_table_names()
        finally:
            if prev is None:
                os.environ.pop("SLUICE_DATABASE_URL", None)
            else:
                os.environ["SLUICE_DATABASE_URL"] = prev
            get_settings.cache_clear()
            engine.dispose()
