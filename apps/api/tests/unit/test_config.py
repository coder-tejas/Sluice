import pytest
from pydantic import ValidationError

from app.core.config import get_settings

VALID_URL = "postgresql://Sluice:Sluice@localhost:5432/Sluice"


def _fresh_settings(monkeypatch, env: dict):
    get_settings.cache_clear()
    for key in (
        "SLUICE_DATABASE_URL",
        "SLUICE_APP_NAME",
        "SLUICE_ENVIRONMENT",
        "SLUICE_LOG_LEVEL",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    try:
        return get_settings()
    finally:
        get_settings.cache_clear()


def test_database_url_loads(monkeypatch):
    settings = _fresh_settings(
        monkeypatch, {"SLUICE_DATABASE_URL": VALID_URL}
    )
    assert str(settings.database_url) == VALID_URL


def test_missing_database_url_raises(monkeypatch):
    with pytest.raises(ValidationError):
        _fresh_settings(monkeypatch, {})


def test_invalid_database_url_raises(monkeypatch):
    with pytest.raises(ValidationError):
        _fresh_settings(monkeypatch, {"SLUICE_DATABASE_URL": "http://not-postgres"})
