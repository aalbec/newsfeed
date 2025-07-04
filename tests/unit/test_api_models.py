"""Unit tests for the API models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models.api import IngestRequest, RetrieveResponse
from src.models.news_item import NewsItem


class TestIngestRequest:
    """Test cases for the IngestRequest model."""

    def test_valid_ingest_request(self):
        """Test creating a valid IngestRequest with news items."""
        # Arrange
        now = datetime.now(timezone.utc)
        news_item = NewsItem(
            id="test_001",
            source="reddit",
            title="Test News",
            body="Test body",
            published_at=now
        )

        # Act
        request = IngestRequest(items=[news_item])

        # Assert
        assert len(request.items) == 1
        assert request.items[0].id == "test_001"
        assert request.items[0].source == "reddit"

    def test_multiple_items(self):
        """Test IngestRequest with multiple news items."""
        # Arrange
        now = datetime.now(timezone.utc)
        item1 = NewsItem(
            id="test_001",
            source="reddit",
            title="First News",
            published_at=now
        )
        item2 = NewsItem(
            id="test_002",
            source="rss",
            title="Second News",
            published_at=now
        )

        # Act
        request = IngestRequest(items=[item1, item2])

        # Assert
        assert len(request.items) == 2
        assert request.items[0].id == "test_001"
        assert request.items[1].id == "test_002"

    def test_empty_items_raises_error(self):
        """Test that empty items list raises ValidationError."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            IngestRequest(items=[])

        assert "too_short" in str(exc_info.value)

    def test_json_serialization(self):
        """Test JSON serialization of IngestRequest."""
        # Arrange
        now = datetime(2024, 12, 10, 15, 30, 0, tzinfo=timezone.utc)
        news_item = NewsItem(
            id="test_001",
            source="reddit",
            title="Test News",
            body="Test body",
            published_at=now
        )
        request = IngestRequest(items=[news_item])

        # Act
        json_data = request.model_dump_json()

        # Assert
        assert '"items":' in json_data
        assert '"id":"test_001"' in json_data
        assert '"source":"reddit"' in json_data


class TestRetrieveResponse:
    """Test cases for the RetrieveResponse model."""

    def test_valid_retrieve_response(self):
        """Test creating a valid RetrieveResponse with items."""
        # Arrange
        now = datetime.now(timezone.utc)
        news_item = NewsItem(
            id="test_001",
            source="reddit",
            title="Test News",
            body="Test body",
            published_at=now
        )

        # Act
        response = RetrieveResponse(items=[news_item], total=1)

        # Assert
        assert len(response.items) == 1
        assert response.total == 1
        assert response.items[0].id == "test_001"

    def test_empty_response(self):
        """Test RetrieveResponse with no items."""
        # Act
        response = RetrieveResponse()

        # Assert
        assert len(response.items) == 0
        assert response.total == 0

    def test_multiple_items(self):
        """Test RetrieveResponse with multiple items."""
        # Arrange
        now = datetime.now(timezone.utc)
        item1 = NewsItem(
            id="test_001",
            source="reddit",
            title="First News",
            published_at=now
        )
        item2 = NewsItem(
            id="test_002",
            source="rss",
            title="Second News",
            published_at=now
        )

        # Act
        response = RetrieveResponse(items=[item1, item2], total=2)

        # Assert
        assert len(response.items) == 2
        assert response.total == 2
        assert response.items[0].id == "test_001"
        assert response.items[1].id == "test_002"

    def test_json_serialization(self):
        """Test JSON serialization of RetrieveResponse."""
        # Arrange
        now = datetime(2024, 12, 10, 15, 30, 0, tzinfo=timezone.utc)
        news_item = NewsItem(
            id="test_001",
            source="reddit",
            title="Test News",
            body="Test body",
            published_at=now
        )
        response = RetrieveResponse(items=[news_item], total=1)

        # Act
        json_data = response.model_dump_json()

        # Assert
        assert '"items":' in json_data
        assert '"total":1' in json_data
        assert '"id":"test_001"' in json_data


class TestAssignmentCompliance:
    """Test cases for assignment API contract compliance."""

    def test_ingest_request_contract(self):
        """Test that IngestRequest matches assignment contract."""
        # Arrange
        now = datetime.now(timezone.utc)
        news_item = NewsItem(
            id="contract_test",
            source="mock",
            title="Contract Test",
            body="Test body",
            published_at=now
        )

        # Act
        request = IngestRequest(items=[news_item])

        # Assert - Check structure matches assignment
        assert hasattr(request, 'items')
        assert isinstance(request.items, list)
        assert len(request.items) > 0

        # Check that items contain required fields
        item = request.items[0]
        assert hasattr(item, 'id')
        assert hasattr(item, 'source')
        assert hasattr(item, 'title')
        assert hasattr(item, 'body')
        assert hasattr(item, 'published_at')

    def test_retrieve_response_contract(self):
        """Test that RetrieveResponse matches assignment contract."""
        # Arrange
        now = datetime.now(timezone.utc)
        news_item = NewsItem(
            id="contract_test",
            source="mock",
            title="Contract Test",
            body="Test body",
            published_at=now
        )

        # Act
        response = RetrieveResponse(items=[news_item], total=1)

        # Assert - Check structure matches assignment
        assert hasattr(response, 'items')
        assert isinstance(response.items, list)
        assert hasattr(response, 'total')
        assert isinstance(response.total, int)

        # Check that items contain required fields
        item = response.items[0]
        assert hasattr(item, 'id')
        assert hasattr(item, 'source')
        assert hasattr(item, 'title')
        assert hasattr(item, 'body')
        assert hasattr(item, 'published_at')
