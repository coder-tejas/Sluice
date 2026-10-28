from app.main import app  # noqa: F401  (ensures routes registered)


def _cleanup(client, *keys):
    for key in keys:
        client.delete(f"/v1/metadata/{key}")


def test_metadata_crud_via_api(client):
    key = "api-crud"
    try:
        created = client.post(
            "/v1/metadata", json={"key": key, "value": "v1"}
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["key"] == key
        assert body["value"] == "v1"
        assert body["id"] is not None

        read = client.get(f"/v1/metadata/{key}")
        assert read.status_code == 200
        assert read.json() == body

        deleted = client.delete(f"/v1/metadata/{key}")
        assert deleted.status_code == 204

        assert client.get(f"/v1/metadata/{key}").status_code == 404
    finally:
        _cleanup(client, key)


def test_metadata_duplicate_is_409(client):
    key = "api-dup"
    try:
        assert client.post("/v1/metadata", json={"key": key}).status_code == 201
        dup = client.post("/v1/metadata", json={"key": key})
        assert dup.status_code == 409
    finally:
        _cleanup(client, key)


def test_metadata_validation_is_422(client):
    assert client.post("/v1/metadata", json={"key": ""}).status_code == 422
    assert client.get("/v1/metadata/missing-key-xyz").status_code == 404
