"""Unit tests for MockNewsSource."""

from datetime import datetime, timezone

import pytest

from src.sources import MockNewsSource


class TestMockNewsSource:
    """Test cases for MockNewsSource class."""

    def test_init(self):
        """Test mock source initialization."""
        source = MockNewsSource("test-mock", 5)

        assert source.name == "test-mock"
        assert source._item_count == 5

    def test_init_defaults(self):
        """Test mock source initialization with defaults."""
        source = MockNewsSource()

        assert source.name == "mock"
        assert source._item_count == 10

    @pytest.mark.asyncio
    async def test_fetch_items(self):
        """Test fetching mock news items."""
        source = MockNewsSource("test-mock", 3)

        items = await source.fetch_items()

        assert len(items) == 3
        assert all(item.source == "test-mock" for item in items)
        assert all(item.version == 1 for item in items)

    @pytest.mark.asyncio
    async def test_fetch_items_content(self):
        """Test that fetched items have proper content."""
        source = MockNewsSource("test-mock", 1)

        items = await source.fetch_items()

        assert len(items) == 1
        item = items[0]

        # Check required fields
        assert item.id.startswith("test-mock_")
        assert item.title
        assert item.body
        assert item.published_at.tzinfo is not None  # timezone-aware

        # Check content is IT-relevant
        it_keywords = ["vulnerability", "security", "outage", "CVE", "patch"]
        content = f"{item.title} {item.body}".lower()
        assert any(keyword in content for keyword in it_keywords)

    @pytest.mark.asyncio
    async def test_fetch_items_timestamps(self):
        """Test that timestamps are properly set."""
        source = MockNewsSource("test-mock", 2)

        before_fetch = datetime.now(timezone.utc)
        items = await source.fetch_items()
        after_fetch = datetime.now(timezone.utc)

        assert len(items) == 2

        # Check timestamps are within reasonable range
        for item in items:
            assert before_fetch > item.published_at
            assert item.published_at < after_fetch
