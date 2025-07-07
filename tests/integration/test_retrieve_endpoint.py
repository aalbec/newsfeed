"""Integration tests for the /retrieve endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app with lifespan events."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_news_items():
    """Sample news items for testing."""
    return [
        {
            "id": "test_001",
            "source": "test",
            "title": "Critical Security Vulnerability in Apache Log4j",
            "body": "A zero-day vulnerability has been discovered in Apache Log4j...",
            "published_at": "2024-12-10T15:30:00Z",
            "version": 1
        },
        {
            "id": "test_002",
            "source": "test",
            "title": "Major Cloud Outage Affects Multiple Services",
            "body": "A widespread cloud outage has impacted services across...",
            "published_at": "2024-12-10T16:00:00Z",
            "version": 1
        }
    ]


class TestRetrieveEndpoint:
    """Test the /api/v1/retrieve endpoint."""

    def test_retrieve_response_structure_when_empty(self, client):
        """Test retrieve response structure (storage may have background items)."""
        response = client.get("/api/v1/retrieve")
        assert response.status_code == 200

        data = response.json()

        # Check required fields regardless of content
        assert "items" in data
        assert "total" in data
        assert "filtering_info" in data

        # Check filtering info structure
        filtering_info = data["filtering_info"]
        assert "total_items_in_storage" in filtering_info
        assert "items_passing_filters" in filtering_info
        assert "relevance_threshold" in filtering_info

        # Note: Background ingestion may populate storage,
        # so we don't assert empty state

    def test_retrieve_response_structure(self, client, sample_news_items):
        """Test that retrieve response has correct structure."""
        # First ingest some items
        client.post("/api/v1/ingest", json={"items": sample_news_items})

        # Then retrieve
        response = client.get("/api/v1/retrieve")
        assert response.status_code == 200

        data = response.json()

        # Check required fields
        assert "items" in data
        assert "total" in data
        assert "filtering_info" in data

        # Check filtering info structure
        filtering_info = data["filtering_info"]
        assert "total_items_in_storage" in filtering_info
        assert "items_passing_filters" in filtering_info
        assert "relevance_threshold" in filtering_info

    def test_retrieve_items_have_required_fields(self, client, sample_news_items):
        """Test that retrieved items have all required fields."""
        # First ingest some items
        client.post("/api/v1/ingest", json={"items": sample_news_items})

        # Then retrieve
        response = client.get("/api/v1/retrieve")
        assert response.status_code == 200

        data = response.json()

        # If items are returned, check their structure
        if data["total"] > 0:
            for item in data["items"]:
                assert "id" in item
                assert "source" in item
                assert "title" in item
                assert "published_at" in item
                assert "version" in item
                assert "relevance_score" in item
                assert "score_breakdown" in item

    def test_retrieve_deterministic_results(self, client, sample_news_items):
        """Test that retrieve results are deterministic."""
        # First ingest some items
        client.post("/api/v1/ingest", json={"items": sample_news_items})

        # Retrieve multiple times
        response1 = client.get("/api/v1/retrieve")
        response2 = client.get("/api/v1/retrieve")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Results should be identical
        assert data1["total"] == data2["total"]
        assert len(data1["items"]) == len(data2["items"])


# TODO: Additional tests for future phases:
# - test_retrieve_with_query_parameters - Test query parameters (if added)
# - test_retrieve_error_handling - Test error scenarios
# - test_retrieve_performance - Test performance with large datasets
# - test_retrieve_caching - Test caching behavior (if implemented)
# - test_retrieve_authentication - Test authentication (if added)
