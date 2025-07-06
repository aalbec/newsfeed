"""Unit tests for the storage implementations."""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from src.models.news_item import NewsItem
from src.storage.in_memory import InMemoryStore


class TestInMemoryStore:
    """Test cases for the InMemoryStore implementation."""

    @pytest_asyncio.fixture
    async def store(self):
        """Create a fresh InMemoryStore for each test."""
        store = InMemoryStore()
        yield store
        await store.clear()

    @pytest.fixture
    def sample_item(self):
        """Create a sample news item for testing."""
        return NewsItem(
            id="test_001",
            source="reddit",
            title="Test Security Vulnerability",
            body="This is a test security issue",
            published_at=datetime.now(timezone.utc),
            version=1,
        )

    @pytest.mark.asyncio
    async def test_add_item_success(self, store, sample_item):
        """Test successfully adding a single item."""
        result = await store.add_item(sample_item)
        assert result is True
        assert await store.count() == 1

    @pytest.mark.asyncio
    async def test_add_item_duplicate(self, store, sample_item):
        """Test that duplicate items are rejected."""
        # Add item first time
        result1 = await store.add_item(sample_item)
        assert result1 is True

        # Try to add same item again
        result2 = await store.add_item(sample_item)
        assert result2 is False
        assert await store.count() == 1

    @pytest.mark.asyncio
    async def test_add_items_success(self, store):
        """Test successfully adding multiple items."""
        items = [
            NewsItem(
                id=f"test_{i:03d}",
                source="reddit",
                title=f"Test Item {i}",
                body=f"Test body for item {i}",
                published_at=datetime.now(timezone.utc),
            )
            for i in range(1, 4)
        ]

        added_count = await store.add_items(items)
        assert added_count == 3
        assert await store.count() == 3

    @pytest.mark.asyncio
    async def test_get_all_with_items(self, store):
        """Test getting all items with consistent ordering."""
        # Create items with different timestamps
        now = datetime.now(timezone.utc)
        items = [
            NewsItem(
                id="test_001",
                source="reddit",
                title="Older Item",
                body="Older item body",
                published_at=now,
            ),
            NewsItem(
                id="test_002",
                source="rss",
                title="Newer Item",
                body="Newer item body",
                published_at=now + timedelta(seconds=1),
            ),
        ]

        await store.add_items(items)
        retrieved_items = await store.get_all()

        # Should be sorted by published_at DESC, then by id ASC
        assert len(retrieved_items) == 2
        assert retrieved_items[0].id == "test_002"  # Newer first
        assert retrieved_items[1].id == "test_001"  # Older second
