from app.main import app


def test_health(client):
    response = client.get(
        "/v1/health"
    )
    
    assert response.status_code == 200
    
    assert response.json() == {
        "status" : "ok"
    }
    
def test_readiness(client):
    response = client.get(
        "/v1/health/ready"
    )
    assert response.status_code == 200
    
    assert response.json() == {
        "status" : "ready",
    }
    
def test_openapi(client):
    response  = client.get(
        "/openapi.json"
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["info"]["title"] == "Sluice"
    assert data["info"]["version"] == "0.1.0"
    
    assert "/v1/health" in data["paths"]
    assert "/v1/health/ready" in data["paths"]