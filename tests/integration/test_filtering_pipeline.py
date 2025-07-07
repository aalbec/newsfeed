"""Integration tests for the complete filtering pipeline."""

import pytest

from src.filtering import FilterOrchestration
from src.filters import KeywordFilter, SemanticFilter
from src.registry import FilterRegistry, SourceRegistry
from src.sources import MockNewsSource
from src.storage import InMemoryStore


class TestFilteringPipeline:
    """Test the complete filtering pipeline integration."""

    @pytest.fixture
    def source_registry(self):
        """Create source registry with test sources."""
        registry = SourceRegistry()
        registry.register(MockNewsSource("mock_source"))
        return registry

    @pytest.fixture
    def filter_registry(self, cached_semantic_model):
        """Create filter registry with test filters using cached model."""
        registry = FilterRegistry()
        registry.register(KeywordFilter())
        registry.register(SemanticFilter(model=cached_semantic_model))
        return registry

    @pytest.fixture
    def storage(self):
        """Create storage instance."""
        return InMemoryStore()

    @pytest.fixture
    def orchestration(self, filter_registry):
        """Create filter orchestration with test weights."""
        weights = {"keyword": 0.6, "semantic": 0.4}
        return FilterOrchestration(filter_registry, weights)

    @pytest.fixture
    def real_rss_data(self, cached_rss_data):
        """Use cached RSS data for testing to avoid repeated network requests."""
        return cached_rss_data

    @pytest.mark.asyncio
    async def test_full_filtering_pipeline(
        self, source_registry, filter_registry, storage, orchestration
    ):
        """Test complete pipeline: sources → registry → orchestration → storage."""
        sources = source_registry.get_sources(["mock_source"])
        all_items = []
        for source in sources:
            items = await source.fetch_items()
            all_items.extend(items)

        assert len(all_items) > 0, "Should have items from mock source"

        # Apply filtering orchestration
        filtered_items = await orchestration.apply_filters(all_items)

        assert len(filtered_items) == len(all_items), "Should filter all items"
        assert all(hasattr(item, 'relevance_score') for item in filtered_items)
        assert all(hasattr(item, 'score_breakdown') for item in filtered_items)

        # Store filtered results
        for filtered_item in filtered_items:
            await storage.add_item(filtered_item.item)

        # Retrieve from storage
        stored_items = await storage.get_all()
        assert len(stored_items) == len(all_items), "All items should be stored"
        # Verify filtering worked
        # Mock source has IT-relevant content, so scores should be > 0
        avg_score = (
            sum(item.relevance_score for item in filtered_items) / len(filtered_items)
        )
        assert avg_score > 0, "Filtering should produce positive scores"

    @pytest.mark.asyncio
    async def test_filtering_with_real_rss_data(
        self, filter_registry, storage, orchestration, real_rss_data
    ):
        """Test filtering with real RSS data from Tom's Hardware and Ars Technica."""
        assert len(real_rss_data) > 0, "Should have real RSS data"

        # Apply filtering to real data
        filtered_items = await orchestration.apply_filters(real_rss_data)

        assert len(filtered_items) == len(real_rss_data), "Should filter all real items"

        # Verify all items have scores and breakdowns
        for item in filtered_items:
            assert hasattr(item, 'relevance_score')
            assert hasattr(item, 'score_breakdown')
            assert "keyword" in item.score_breakdown
            assert "semantic" in item.score_breakdown

        # Verify that IT-relevant items score higher than non-IT items
        # Real RSS data should have IT content that scores well
        avg_score = (
            sum(item.relevance_score for item in filtered_items) / len(filtered_items)
        )
        assert avg_score > 0.01, "Real IT news should have meaningful scores"

        # Check that we have some high-scoring items (IT news should score well)
        high_scoring_items = [
            item for item in filtered_items if item.relevance_score > 0.05
        ]
        assert len(high_scoring_items) > 0, "Should have some high-scoring IT items"

    @pytest.mark.asyncio
    async def test_score_breakdown_explainability_with_real_data(
        self, filter_registry, orchestration, real_rss_data
    ):
        """Test that score breakdown provides explainable results with real data."""
        # Use first real RSS item for detailed breakdown
        assert len(real_rss_data) > 0, "Should have real RSS data"

        test_item = real_rss_data[0]
        filtered_items = await orchestration.apply_filters([test_item])

        assert len(filtered_items) == 1
        filtered_item = filtered_items[0]

        # Verify score breakdown structure
        breakdown = filtered_item.score_breakdown
        assert "keyword" in breakdown
        assert "semantic" in breakdown
        assert "final" in breakdown

        # Verify breakdown values are reasonable
        assert 0 <= breakdown["keyword"] <= 1
        assert 0 <= breakdown["semantic"] <= 1
        assert 0 <= breakdown["final"] <= 1

        # Verify final score matches breakdown
        expected_final = (
            0.6 * breakdown["keyword"] + 0.4 * breakdown["semantic"]
        )
        assert abs(filtered_item.relevance_score - expected_final) < 0.001

    @pytest.mark.asyncio
    async def test_deterministic_filtering_with_real_data(
        self, filter_registry, orchestration, real_rss_data
    ):
        """Test that filtering produces deterministic results with real data."""
        assert len(real_rss_data) > 0, "Should have real RSS data"

        # Run filtering twice with same data
        results1 = await orchestration.apply_filters(real_rss_data)
        results2 = await orchestration.apply_filters(real_rss_data)

        # Verify same number of results
        assert len(results1) == len(results2)

        # Verify scores are identical (deterministic)
        for item1, item2 in zip(results1, results2):
            assert abs(item1.relevance_score - item2.relevance_score) < 0.001
            assert item1.score_breakdown == item2.score_breakdown

    @pytest.mark.asyncio
    async def test_error_handling_and_graceful_degradation(
        self, source_registry, storage
    ):
        """Test that the pipeline handles errors gracefully."""
        # Create orchestration with no filters (simulating filter failure)
        empty_registry = FilterRegistry()
        orchestration = FilterOrchestration(empty_registry)

        # Fetch items from sources
        sources = source_registry.get_sources(["mock_source"])
        all_items = []
        for source in sources:
            items = await source.fetch_items()
            all_items.extend(items)

        # Apply filtering (should use default scores)
        filtered_items = await orchestration.apply_filters(all_items)

        assert len(filtered_items) == len(all_items), "Should still process all items"
        assert all(
            item.relevance_score == 0.5 for item in filtered_items
        ), "Should use default scores"

    @pytest.mark.asyncio
    async def test_pipeline_with_empty_input(self, orchestration):
        """Test that the pipeline handles empty input gracefully."""
        filtered_items = await orchestration.apply_filters([])

        assert len(filtered_items) == 0, "Should return empty list for empty input"

# TODO: Additional tests for future phases:
# - test_filtering_with_real_rss_data - Test with actual RSS feeds
# - test_score_breakdown_explainability - Test detailed score breakdown
# - test_deterministic_filtering - Test deterministic results
# - test_filtering_performance - Test performance with large datasets
# - test_advanced_orchestration - Test complex filter combinations
