"""Fast integration tests for API contract compliance.

These tests focus on the core API contract without triggering background ingestion
or external services. They test the API structure and basic functionality.

NOTE: Even this minimal test is slow (30+ seconds) because the /retrieve endpoint
applies semantic filtering (loads AI models) to all items in storage, which may be
populated by background ingestion. For truly fast tests, the app would need a test mode
that disables background ingestion and filtering, or uses mocks/stubs for those parts.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


def test_api_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200


def test_docs(client):
    """Test that OpenAPI documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_ingest_exists(client):
    """Test that /ingest endpoint exists."""
    # Test with empty request to see if endpoint exists
    response = client.post("/api/v1/ingest", json={"items": []})
    # Should return 400 (no items) or 200 (empty accepted), not 404
    assert response.status_code in [200, 400, 422]


def test_retrieve_exists(client):
    """Test that /retrieve endpoint exists."""
    response = client.get("/api/v1/retrieve")
    # Should return 200, not 404
    assert response.status_code == 200


def test_ingest_endpoint_validation(client):
    """Test /ingest endpoint validation."""
    # Test with invalid request format
    response = client.post("/api/v1/ingest", json={"invalid": "format"})
    assert response.status_code == 422  # Validation error


def test_ingest_endpoint_missing_items(client):
    """Test /ingest endpoint with missing items field."""
    # Test with missing items field
    response = client.post("/api/v1/ingest", json={})
    assert response.status_code == 422  # Validation error
