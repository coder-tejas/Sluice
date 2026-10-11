from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Lifespan scope: single event loop for all requests in the test.
    # Pooled asyncpg connections are loop-bound, so a bare TestClient
    # (fresh loop per request) breaks DB-backed endpoints flakily.
    with TestClient(app) as client:
        yield client
