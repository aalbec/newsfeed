"""Unit tests for RSSSource."""

from unittest.mock import MagicMock, patch

import pytest

from src.sources import RSSSource


class TestRSSSource:
    """Test RSSSource functionality."""

    def test_rss_source_initialization(self):
        """Test RSSSource initialization."""
        source = RSSSource("test-rss", "https://example.com/feed.xml", 5)

        assert source.name == "test-rss"
        assert source._feed_url == "https://example.com/feed.xml"
        assert source._max_items == 5

    @pytest.mark.asyncio
    async def test_fetch_items_success(self):
        """Test successful RSS feed fetching."""
        # Mock feedparser response
        mock_entry = MagicMock()
        mock_entry.title = "Test Article"
        mock_entry.summary = "Test summary"
        mock_entry.published_parsed = (2025, 1, 1, 12, 0, 0, 0, 0, 0)
        mock_entry.id = "test-id"

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_feed.bozo = False

        with patch("src.sources.rss_source.feedparser") as mock_feedparser:
            mock_feedparser.parse.return_value = mock_feed

            source = RSSSource("test-rss", "https://example.com/feed.xml")
            items = await source.fetch_items()

            assert len(items) == 1
            assert items[0].title == "Test Article"
            assert items[0].body == "Test summary"
            assert items[0].source == "test-rss"
            assert items[0].id == "test-rss_test-id"

    @pytest.mark.asyncio
    async def test_fetch_items_empty_feed(self):
        """Test handling of empty RSS feed."""
        mock_feed = MagicMock()
        mock_feed.entries = []

        with patch("src.sources.rss_source.feedparser") as mock_feedparser:
            mock_feedparser.parse.return_value = mock_feed

            source = RSSSource("test-rss", "https://example.com/feed.xml")
            items = await source.fetch_items()

            assert len(items) == 0

    @pytest.mark.asyncio
    async def test_fetch_items_parsing_error(self):
        """Test handling of RSS parsing errors."""
        with patch("src.sources.rss_source.feedparser") as mock_feedparser:
            mock_feedparser.parse.side_effect = Exception("Network error")

            source = RSSSource("test-rss", "https://example.com/feed.xml")
            items = await source.fetch_items()

            assert len(items) == 0

    @pytest.mark.asyncio
    async def test_fetch_items_max_items_limit(self):
        """Test that max_items limit is respected."""
        # Create multiple mock entries
        mock_entries = []
        for i in range(5):
            entry = MagicMock()
            entry.title = f"Article {i}"
            entry.summary = f"Summary {i}"
            entry.published_parsed = (2025, 1, 1, 12, 0, 0, 0, 0, 0)
            entry.id = f"id-{i}"
            mock_entries.append(entry)

        mock_feed = MagicMock()
        mock_feed.entries = mock_entries
        mock_feed.bozo = False

        with patch("src.sources.rss_source.feedparser") as mock_feedparser:
            mock_feedparser.parse.return_value = mock_feed

            # Test with max_items=3
            source = RSSSource("test-rss", "https://example.com/feed.xml", max_items=3)
            items = await source.fetch_items()

            assert len(items) == 3
            assert items[0].title == "Article 0"
            assert items[1].title == "Article 1"
            assert items[2].title == "Article 2"

    @pytest.mark.asyncio
    async def test_fetch_items_missing_title(self):
        """Test handling of entries without title."""
        mock_entry = MagicMock()
        mock_entry.title = ""  # Missing title
        mock_entry.summary = "Test summary"

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_feed.bozo = False

        with patch("src.sources.rss_source.feedparser") as mock_feedparser:
            mock_feedparser.parse.return_value = mock_feed

            source = RSSSource("test-rss", "https://example.com/feed.xml")
            items = await source.fetch_items()

            assert len(items) == 0  # Should skip entries without title

    @pytest.mark.asyncio
    async def test_id_generation_with_link(self):
        """Test ID generation using link when ID is not available."""
        mock_entry = MagicMock()
        mock_entry.title = "Test Article"
        mock_entry.summary = "Test summary"
        mock_entry.published_parsed = (2025, 1, 1, 12, 0, 0, 0, 0, 0)
        mock_entry.id = None  # No ID
        mock_entry.link = "https://example.com/article"

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_feed.bozo = False

        with patch("src.sources.rss_source.feedparser") as mock_feedparser:
            mock_feedparser.parse.return_value = mock_feed

            source = RSSSource("test-rss", "https://example.com/feed.xml")
            items = await source.fetch_items()

            assert len(items) == 1
            # Should generate ID from link hash
            assert items[0].id.startswith("test-rss_")
            assert len(items[0].id) > len("test-rss_")
