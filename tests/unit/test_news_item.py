"""Unit tests for the NewsItem model (essentials only).

TODO: Add more edge case and normalization tests for NewsItem in future
iterations.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models.news_item import NewsItem


class TestNewsItem:
    def test_valid_news_item_creation(self):
        """Test creating a valid NewsItem with all required fields."""
        now = datetime.now(timezone.utc)
        news_item = NewsItem(
            id="test_001",
            source="reddit",
            title="Test Security Vulnerability",
            body="This is a test security issue",
            published_at=now,
            version=1,
        )
        assert news_item.id == "test_001"
        assert news_item.source == "reddit"
        assert news_item.title == "Test Security Vulnerability"
        assert news_item.body == "This is a test security issue"
        assert news_item.published_at == now
        assert news_item.version == 1

    def test_required_fields_validation(self):
        """Test that missing or empty required fields raise ValidationError."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            NewsItem(id="", source="reddit", title="Test", body="", published_at=now)
        with pytest.raises(ValidationError):
            NewsItem(id="test", source="", title="Test", body="", published_at=now)
        with pytest.raises(ValidationError):
            NewsItem(id="test", source="reddit", title="", body="", published_at=now)
        with pytest.raises(ValidationError):
            NewsItem(
                id="test",
                source="reddit",
                title="Test",
                body="",
                published_at=datetime.now(),  # naive
            )
        with pytest.raises(ValidationError):
            NewsItem(id="", source="reddit", title="Test", body="", published_at=now)
        with pytest.raises(ValidationError):
            NewsItem(id="test", source="", title="Test", body="", published_at=now)
        with pytest.raises(ValidationError):
            NewsItem(id="test", source="reddit", title="", body="", published_at=now)

    def test_json_contract_compliance(self):
        """Test JSON serialization produces assignment-compliant format."""
        now = datetime(2024, 12, 10, 15, 30, 0, tzinfo=timezone.utc)
        news_item = NewsItem(
            id="test_009",
            source="reddit",
            title="Test Serialization",
            body="Test body content",
            published_at=now,
            version=2,
        )
        expected = {
            "id": "test_009",
            "source": "reddit",
            "title": "Test Serialization",
            "body": "Test body content",
            "published_at": "2024-12-10T15:30:00+00:00Z",
            "version": 2,
        }
        actual = news_item.model_dump(mode="json", exclude_none=True)
        assert actual == expected
