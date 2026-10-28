"""Service logic with a mocked repository: no PostgreSQL, milliseconds."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.system_metadata import SystemMetadata
from app.schemas.system_metadata import SystemMetadataCreate
from app.services.system_metadata import (
    DuplicateKeyError,
    EntryNotFoundError,
    SystemMetadataService,
)


def run(coro):
    return asyncio.run(coro)


def _entry(**kwargs):
    now = datetime.now(timezone.utc)
    defaults = {
        "id": 1,
        "key": "k",
        "value": "v",
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    return SystemMetadata(**defaults)


def _service():
    session = AsyncMock()
    service = SystemMetadataService(session)
    service.repo = AsyncMock()
    return session, service


def test_create_delegates_and_returns_dto():
    session, service = _service()
    service.repo.create.return_value = _entry()

    result = run(service.create_entry(SystemMetadataCreate(key="k", value="v")))

    service.repo.create.assert_awaited_once_with("k", "v")
    assert result.key == "k"
    assert result.value == "v"
    assert not hasattr(result, "_sa_instance_state")


def test_blank_key_never_reaches_repo():
    _, service = _service()

    with pytest.raises(ValueError):
        run(service.create_entry(SystemMetadataCreate(key="   ")))

    service.repo.create.assert_not_called()


def test_duplicate_rolls_back_and_raises_domain_error():
    session, service = _service()
    service.repo.create.side_effect = IntegrityError("INSERT", {}, Exception("dup"))

    with pytest.raises(DuplicateKeyError):
        run(service.create_entry(SystemMetadataCreate(key="dup")))

    session.rollback.assert_awaited_once()


def test_missing_entry_raises_not_found():
    _, service = _service()
    service.repo.get_by_key.return_value = None

    with pytest.raises(EntryNotFoundError):
        run(service.get_entry("nope"))


def test_update_and_delete_flow():
    session, service = _service()
    service.repo.get_by_key.return_value = _entry(value="a")
    service.repo.update.return_value = _entry(value="b")

    updated = run(service.update_entry("k", "b"))
    assert updated.value == "b"

    run(service.delete_entry("k"))
    service.repo.delete.assert_awaited_once()
