
import asyncio

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.model import Model
from app.models.model_version import ModelVersion
from tests.integration.conftest import make_session_factory


def run(coro):
    return asyncio.run(coro)


def _model(slug: str, name: str = "Fraud Detector") -> Model:
    return Model(
        name=name,
        slug=slug,
        description="Detects fraudulent transactions",
        model_type="traditional_ml",
    )


def _version(model_id: int, version: str = "1.0.0") -> ModelVersion:
    return ModelVersion(
        model_id=model_id,
        version=version,
        runtime="sklearn",
        artifact_uri=f"s3://models/fraud/{version}/",
        runtime_config={"n_estimators": 100},
    )


def test_model_and_version_roundtrip(container_db_url):
    async def _test():
        engine, factory = make_session_factory(container_db_url)
        try:
            async with factory() as s:
                model = _model("roundtrip-fraud")
                s.add(model)
                await s.flush()
                s.add(_version(model.id))
                await s.commit()
                assert model.id is not None
                assert model.created_at is not None

            async with factory() as s:
                loaded = (
                    await s.execute(
                        select(Model)
                        .options(selectinload(Model.versions))
                        .where(Model.slug == "roundtrip-fraud")
                    )
                ).scalar_one()
                assert loaded.name == "Fraud Detector"
                assert loaded.model_type == "traditional_ml"
                assert len(loaded.versions) == 1
                version = loaded.versions[0]
                assert version.version == "1.0.0"
                assert version.runtime == "sklearn"
                assert version.runtime_config == {"n_estimators": 100}
                assert version.created_at is not None
        finally:
            await engine.dispose()

    run(_test())


def test_duplicate_slug_rejected(container_db_url):
    async def _test():
        engine, factory = make_session_factory(container_db_url)
        try:
            async with factory() as s:
                s.add(_model("dup-slug", name="First"))
                await s.commit()

                s.add(_model("dup-slug", name="Second"))
                with pytest.raises(IntegrityError):
                    await s.commit()
                await s.rollback()
        finally:
            await engine.dispose()

    run(_test())


def test_duplicate_version_per_model_rejected(container_db_url):
    async def _test():
        engine, factory = make_session_factory(container_db_url)
        try:
            async with factory() as s:
                first = _model("versioned-fraud", name="First")
                second = _model("other-fraud", name="Second")
                s.add_all([first, second])
                await s.flush()

                s.add_all([_version(first.id), _version(second.id)])
                await s.commit()

                s.add(_version(first.id))
                with pytest.raises(IntegrityError):
                    await s.commit()
                await s.rollback()
        finally:
            await engine.dispose()

    run(_test())


def test_version_requires_existing_model(container_db_url):
    async def _test():
        engine, factory = make_session_factory(container_db_url)
        try:
            async with factory() as s:
                s.add(_version(999_999))
                with pytest.raises(IntegrityError):
                    await s.commit()
                await s.rollback()
        finally:
            await engine.dispose()

    run(_test())


def test_deleting_model_cascades_versions(container_db_url):
    async def _test():
        engine, factory = make_session_factory(container_db_url)
        try:
            async with factory() as s:
                model = _model("cascade-fraud")
                s.add(model)
                await s.flush()
                s.add(_version(model.id))
                await s.commit()
                model_id = model.id

            async with factory() as s:
                await s.execute(
                    text("DELETE FROM models WHERE id = :id"), {"id": model_id}
                )
                await s.commit()

                remaining = (
                    await s.execute(
                        text(
                            "SELECT count(*) FROM model_versions WHERE model_id = :id"
                        ),
                        {"id": model_id},
                    )
                ).scalar_one()
                assert remaining == 0
        finally:
            await engine.dispose()

    run(_test())
