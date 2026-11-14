from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root welcome endpoint returns 200 and docs links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "Snack Overflow"
    assert "version" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


def test_health_check_endpoint(client: TestClient):
    """Test health check returns system status structure."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["app"] == "Snack Overflow"
    assert "database" in data
    assert "connected" in data["database"]
