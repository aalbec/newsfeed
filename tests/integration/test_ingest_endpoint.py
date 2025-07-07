"""Integration tests for the /ingest endpoint."""

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
        },
        {
            "id": "test_003",
            "source": "test",
            "title": "New Software Update Available",
            "body": "A new software update has been released with bug fixes...",
            "published_at": "2024-12-10T16:30:00Z",
            "version": 1
        }
    ]


class TestIngestEndpoint:
    """Test the /api/v1/ingest endpoint."""

    def test_ingest_valid_items(self, client, sample_news_items):
        """Test ingesting valid news items."""
        response = client.post("/api/v1/ingest", json={"items": sample_news_items})
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "summary" in data

        summary = data["summary"]
        assert summary["total_received"] == 3
        assert summary["accepted"] == 3
        assert summary["rejected"] == 0
        assert summary["duplicates"] == 0
        assert summary["errors"] == 0

    def test_ingest_empty_items(self, client):
        """Test ingesting empty items list."""
        response = client.post("/api/v1/ingest", json={"items": []})
        assert response.status_code == 422

    def test_ingest_missing_items(self, client):
        """Test ingesting with missing items field."""
        response = client.post("/api/v1/ingest", json={})
        assert response.status_code == 422

    def test_ingest_invalid_item_fields(self, client):
        """Test ingesting items with invalid fields."""
        invalid_items = [
            {
                "id": "",  # Empty ID
                "source": "test",
                "title": "Test Title",
                "published_at": "2024-12-10T15:30:00Z",
                "version": 1
            }
        ]
        response = client.post("/api/v1/ingest", json={"items": invalid_items})
        assert response.status_code == 422

    def test_ingest_duplicate_items(self, client, sample_news_items):
        """Test ingesting duplicate items."""
        # First ingestion
        response1 = client.post("/api/v1/ingest", json={"items": sample_news_items})
        assert response1.status_code == 200

        # Second ingestion of same items
        response2 = client.post("/api/v1/ingest", json={"items": sample_news_items})
        assert response2.status_code == 200

        data2 = response2.json()
        summary2 = data2["summary"]
        assert summary2["total_received"] == 3
        assert summary2["duplicates"] == 3
        assert summary2["accepted"] == 0

    def test_ingest_malformed_json(self, client):
        """Test ingesting malformed JSON."""
        response = client.post(
            "/api/v1/ingest",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


# TODO: Additional tests for future phases:
# - test_ingest_large_batch - Test performance with large batches
# - test_ingest_mixed_valid_invalid - Test partial success scenarios
# - test_ingest_error_handling - Test server error scenarios
# - test_ingest_content_type_validation - Test various content types
# - test_ingest_rate_limiting - Test rate limiting (if implemented)
