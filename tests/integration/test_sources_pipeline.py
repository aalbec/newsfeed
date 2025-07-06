"""Comprehensive sources pipeline integration test.

Tests Registry + Real RSS Sources + Storage with error handling.
"""

import pytest
import pytest_asyncio

from src.registry import SourceRegistry
from src.sources import RSSSource
from src.storage import InMemoryStore


class TestSourcesPipeline:
    """Test the complete sources pipeline: Registry -> Real RSS Sources -> Storage."""

    @pytest_asyncio.fixture
    async def real_rss_data(self):
        """Fetch real RSS data from both sources for testing."""
        toms_hardware = RSSSource(
            "tomshardware",
            "https://www.tomshardware.com/feeds/all",
            max_items=3
        )
        ars_technica = RSSSource(
            "arstechnica",
            "https://feeds.arstechnica.com/arstechnica/index",
            max_items=3
        )
        toms_items = await toms_hardware.fetch_items()
        ars_items = await ars_technica.fetch_items()
        all_items = toms_items + ars_items
        return all_items

    def test_register_real_rss_source(self):
        """Test registering a real RSS source in the registry."""
        registry = SourceRegistry()
        rss_source = RSSSource(
            "tomshardware", "https://www.tomshardware.com/feeds/all", 3
        )
        registry.register(rss_source)
        assert registry.count() == 1
        assert registry.has_source("tomshardware")
        assert registry.list_sources() == ["tomshardware"]

    @pytest.mark.asyncio
    async def test_sources_pipeline_real_rss(self, real_rss_data):
        """Test complete pipeline with real RSS sources."""
        registry = SourceRegistry()
        storage = InMemoryStore()
        toms_hardware = RSSSource(
            "tomshardware",
            "https://www.tomshardware.com/feeds/all",
            max_items=3
        )
        ars_technica = RSSSource(
            "arstechnica",
            "https://feeds.arstechnica.com/arstechnica/index",
            max_items=3
        )
        registry.register(toms_hardware)
        registry.register(ars_technica)
        toms_source = registry.get_source("tomshardware")
        ars_source = registry.get_source("arstechnica")
        assert toms_source is not None
        assert ars_source is not None
        toms_items = await toms_source.fetch_items()
        ars_items = await ars_source.fetch_items()
        assert len(toms_items) > 0, "Should have items from Tom's Hardware"
        assert len(ars_items) > 0, "Should have items from Ars Technica"
        await storage.add_items(toms_items)
        await storage.add_items(ars_items)
        stored_items = await storage.get_all()
        assert len(stored_items) == len(toms_items) + len(ars_items)
        toms_stored = [item for item in stored_items if item.source == "tomshardware"]
        ars_stored = [item for item in stored_items if item.source == "arstechnica"]
        assert len(toms_stored) == len(toms_items)
        assert len(ars_stored) == len(ars_items)

    @pytest.mark.asyncio
    async def test_error_handling_with_real_sources(self):
        """Test error handling when real sources fail."""
        registry = SourceRegistry()
        invalid_source = RSSSource(
            "invalid", "https://invalid-feed-url-that-does-not-exist.com/feed", 3
        )
        registry.register(invalid_source)
        source = registry.get_source("invalid")
        assert source is not None
        items = await source.fetch_items()
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_duplicate_handling_real_sources(self, real_rss_data):
        """Test duplicate handling in the pipeline with real RSS sources."""
        registry = SourceRegistry()
        storage = InMemoryStore()
        toms_hardware = RSSSource(
            "tomshardware",
            "https://www.tomshardware.com/feeds/all",
            max_items=2
        )
        registry.register(toms_hardware)
        source = registry.get_source("tomshardware")
        assert source is not None
        items1 = await source.fetch_items()
        items2 = await source.fetch_items()
        await storage.add_items(items1)
        await storage.add_items(items2)
        stored_items = await storage.get_all()
        assert len(stored_items) <= len(items1) + len(items2)
        item_ids = [item.id for item in stored_items]
        assert len(item_ids) == len(set(item_ids)), "Should have no duplicate IDs"

    @pytest.mark.asyncio
    async def test_multiple_real_sources_to_storage(self, real_rss_data):
        """Test multiple real RSS sources feeding into storage."""
        registry = SourceRegistry()
        storage = InMemoryStore()
        toms_hardware = RSSSource(
            "tomshardware",
            "https://www.tomshardware.com/feeds/all",
            max_items=2
        )
        ars_technica = RSSSource(
            "arstechnica",
            "https://feeds.arstechnica.com/arstechnica/index",
            max_items=2
        )
        registry.register(toms_hardware)
        registry.register(ars_technica)
        all_items = []
        for source_name in ["tomshardware", "arstechnica"]:
            source = registry.get_source(source_name)
            assert source is not None
            items = await source.fetch_items()
            all_items.extend(items)
        assert len(all_items) > 0, "Should have items from real RSS sources"
        await storage.add_items(all_items)
        stored_items = await storage.get_all()
        assert len(stored_items) == len(all_items)
        toms_items = [item for item in stored_items if item.source == "tomshardware"]
        ars_items = [item for item in stored_items if item.source == "arstechnica"]
        assert len(toms_items) > 0, "Should have Tom's Hardware items"
        assert len(ars_items) > 0, "Should have Ars Technica items"

    @pytest.mark.asyncio
    async def test_real_sources_to_storage_pipeline(self):
        """Test complete pipeline with real sources: Registry -> Source -> Storage."""
        registry = SourceRegistry()
        storage = InMemoryStore()
        rss_source = RSSSource(
            "tomshardware", "https://www.tomshardware.com/feeds/all", 3
        )
        registry.register(rss_source)
        source = registry.get_source("tomshardware")
        assert source is not None
        items = await source.fetch_items()
        assert len(items) > 0
        await storage.add_items(items)
        stored_items = await storage.get_all()
        assert len(stored_items) == len(items)
        for original, stored in zip(items, stored_items):
            assert original.id == stored.id
            assert original.title == stored.title
            assert original.source == stored.source
            assert original.published_at == stored.published_at

# TODO: Nice-to-have tests for future robustness
# - test_multiple_real_sources_in_registry
# - test_fetch_from_real_rss_source
# - test_mixed_real_and_mock_sources
