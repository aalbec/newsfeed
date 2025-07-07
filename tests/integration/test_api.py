"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    expected = {
        "message": "IT Newsfeed API",
        "docs": "/docs",
        "health": "/health"
    }
    # Check that all expected fields/values are present in the response
    assert expected.items() <= data.items()
    # Optionally check for required keys
    for key in ["description", "version", "endpoints"]:
        assert key in data
    # Optionally check endpoints structure
    assert set(["health", "ingest", "retrieve"]).issubset(data["endpoints"].keys())


def test_health_endpoint(client: TestClient):
    """Test the health endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "dependencies" in data
    assert isinstance(data["dependencies"], dict)
    assert "storage" in data["dependencies"]
    assert "filters" in data["dependencies"]
    assert "sources" in data["dependencies"]


def test_api_docs_available(client: TestClient):
    """Test that OpenAPI docs are accessible."""
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_alternative_docs_available(client: TestClient):
    """Test that alternative OpenAPI docs are accessible."""
    response = client.get("/redoc")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
