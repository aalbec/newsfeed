"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test the root health endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    expected = {"message": "Hello, Docker! This is a FastAPI application."}
    assert response.json() == expected


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
