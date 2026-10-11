from app.core.database_async import AsyncSessionLocal, get_async_db
from app.main import app


def test_db_ping(client):
    response = client.get("/v1/db/ping")

    assert response.status_code == 200
    assert response.json() == {"db": "ok", "one": 1}


def test_session_lifecycle_per_request(client):
    seen = []
    close_calls = []

    async def tracking_dep():
        async with AsyncSessionLocal() as session:
            seen.append(session)
            orig_close = session.close

            async def spy_close():
                close_calls.append(session)
                await orig_close()

            session.close = spy_close
            yield session

    app.dependency_overrides[get_async_db] = tracking_dep
    try:
        assert client.get("/v1/db/ping").status_code == 200
        assert client.get("/v1/db/ping").status_code == 200
    finally:
        app.dependency_overrides.pop(get_async_db, None)

    assert len(seen) == 2
    assert seen[0] is not seen[1]
    assert sorted(id(s) for s in close_calls) == sorted(id(s) for s in seen)
