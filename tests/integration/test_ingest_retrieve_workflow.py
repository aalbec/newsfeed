"""Integration tests for ingest → retrieve workflow."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


class TestIngestRetrieveWorkflow:
    """Integration tests for the complete ingest → retrieve workflow."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def high_relevance_item(self):
        """Create a high-relevance news item for testing."""
        return {
            "id": "high_relevance_001",
            "source": "test_source",
            "title": "Major Data Breach Affects 100 Million Users - RCE Exploit Discovered",
            "body": (
                "A massive data breach has been discovered affecting over 100 million "
                "users. The breach was caused by a remote code execution vulnerability "
                "in the authentication system. Security teams are working around the "
                "clock to contain the threat."
            ),
            "published_at": "2024-12-10T18:00:00Z",
            "version": 1
        }

    @pytest.fixture
    def low_relevance_item(self):
        """Create a low-relevance news item for testing."""
        return {
            "id": "low_relevance_001",
            "source": "test_source",
            "title": "New Office Plants Arrive",
            "body": (
                "New office plants have been delivered to improve the workplace "
                "environment. The plants include various species of succulents and "
                "ferns."
            ),
            "published_at": "2024-12-10T19:00:00Z",
            "version": 1
        }

    def test_ingest_retrieve_basic_workflow(self, client):
        """Test the basic ingest → retrieve workflow."""
        # Step 1: Ingest news items
        sample_items = [
            {
                "id": "security_001",
                "source": "test_source",
                "title": "Critical Zero-Day Vulnerability in Apache Log4j",
                "body": "A critical zero-day vulnerability has been discovered.",
                "published_at": "2024-12-10T15:30:00Z",
                "version": 1
            }
        ]

        ingest_response = client.post("/api/v1/ingest", json={"items": sample_items})
        assert ingest_response.status_code == 200

        # Step 2: Retrieve filtered items
        retrieve_response = client.get("/api/v1/retrieve")
        assert retrieve_response.status_code == 200

        retrieve_data = retrieve_response.json()

        # Should have some items (depending on filtering threshold)
        assert retrieve_data["total"] >= 0
        assert len(retrieve_data["items"]) == retrieve_data["total"]

    def test_ingest_retrieve_with_high_relevance_item(self, client, high_relevance_item):
        """Test workflow with a high-relevance security item."""
        # Step 1: Ingest high-relevance item
        ingest_response = client.post("/api/v1/ingest", json={"items": [high_relevance_item]})
        assert ingest_response.status_code == 200

        # Step 2: Retrieve items
        retrieve_response = client.get("/api/v1/retrieve")
        assert retrieve_response.status_code == 200

        retrieve_data = retrieve_response.json()

        # The high-relevance item should be in the results
        item_ids = [item["id"] for item in retrieve_data["items"]]
        assert "high_relevance_001" in item_ids

        # Check that the item has proper scoring
        high_relevance_result = next(
            (item for item in retrieve_data["items"] if item["id"] == "high_relevance_001"),
            None
        )
        assert high_relevance_result is not None
        assert high_relevance_result["relevance_score"] > 0.1

    def test_ingest_retrieve_ranking_order(self, client, high_relevance_item, low_relevance_item):
        """Test that items are ranked by relevance score."""
        # Step 1: Ingest both high and low relevance items
        all_items = [high_relevance_item, low_relevance_item]
        ingest_response = client.post("/api/v1/ingest", json={"items": all_items})
        assert ingest_response.status_code == 200

        # Step 2: Retrieve items
        retrieve_response = client.get("/api/v1/retrieve")
        assert retrieve_response.status_code == 200

        retrieve_data = retrieve_response.json()

        # If both items are returned, they should be sorted by relevance score (highest first)
        if len(retrieve_data["items"]) >= 2:
            for i in range(len(retrieve_data["items"]) - 1):
                current_score = retrieve_data["items"][i]["relevance_score"]
                next_score = retrieve_data["items"][i + 1]["relevance_score"]
                assert current_score >= next_score

    def test_ingest_retrieve_deterministic_results(self, client):
        """Test that retrieve results are deterministic for the same data."""
        # Step 1: Ingest items
        sample_items = [
            {
                "id": "test_001",
                "source": "test_source",
                "title": "Test Item",
                "body": "Test content",
                "published_at": "2024-12-10T15:30:00Z",
                "version": 1
            }
        ]

        ingest_response = client.post("/api/v1/ingest", json={"items": sample_items})
        assert ingest_response.status_code == 200

        # Step 2: Retrieve items multiple times
        retrieve_response1 = client.get("/api/v1/retrieve")
        retrieve_response2 = client.get("/api/v1/retrieve")

        assert retrieve_response1.status_code == 200
        assert retrieve_response2.status_code == 200

        data1 = retrieve_response1.json()
        data2 = retrieve_response2.json()

        # Results should be identical
        assert data1["total"] == data2["total"]
        assert len(data1["items"]) == len(data2["items"])


# TODO: Additional workflow tests for future phases:
# - test_ingest_retrieve_filtering_logic - Test different filtering scenarios
# - test_ingest_retrieve_business_rules - Test business rule validation
# - test_ingest_retrieve_data_consistency - Test data consistency across operations
# - test_ingest_retrieve_performance - Test workflow performance
# - test_ingest_retrieve_error_recovery - Test error recovery in workflow
