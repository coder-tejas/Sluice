from fastapi.testclient import TestClient

from app.main import app

client = TestClient()

def test_request_id_is_generated():
    response = client.get(
        "/v1/health"
    )
    
    assert  response.status_code == 200
    
    request_id = response.headers.get(
        "X-Request-ID"
    )
    
    assert request_id is not None
    assert len(request_id) > 0
    
def test_request_id_is_preserved():
    request_id = "test_req-123"
    response = client.get(
        "/v1/health",
        headers={
            "X-Request-ID" : request_id,
        },
    )
    
    
    assert response.status_code == 200
    
    assert response.headers[
        "X-Request-ID"
    ] == request_id


def test_request_id_is_present_on_404():
    request_id = "missing-route-123"
    
    response = client.get(
        "/v1/does-not-exist",
        headers={
            "X-Request-ID":request_id,
        },
    )
    
    assert response.status_code == 404
    
    assert response.headers[
        "X-Request-ID"
    ] == request_id
    
    
    data = response.json()
    
    assert data["error"]["code"] == "HTTP_ERROR"
    assert data["error"]["request_id"] == request_id