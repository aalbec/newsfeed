"""Unit tests for FilterOrchestration."""

from datetime import datetime, timezone

import pytest

from src.filtering import FilterOrchestration
from src.filters import KeywordFilter, SemanticFilter
from src.models.news_item import NewsItem
from src.registry import FilterRegistry


class TestFilterOrchestration:
    """Test FilterOrchestration functionality."""

    @pytest.fixture
    def registry(self):
        """Create a filter registry with test filters."""
        registry = FilterRegistry()
        registry.register(KeywordFilter())
        registry.register(SemanticFilter())
        return registry

    @pytest.fixture
    def orchestration(self, registry):
        """Create a filter orchestration with test weights."""
        weights = {"keyword": 0.6, "semantic": 0.4}
        return FilterOrchestration(registry, weights)

    @pytest.fixture
    def test_items(self):
        """Create test news items."""
        return [
            NewsItem(
                id="test_001",
                source="test",
                title=(
                    "Critical security vulnerability discovered"
                ),
                body=(
                    "A major security breach has been reported affecting "
                    "multiple systems."
                ),
                published_at=datetime.now(timezone.utc),
                version=1
            ),
            NewsItem(
                id="test_002",
                source="test",
                title="New software update available",
                body="Latest version includes performance improvements and bug fixes.",
                published_at=datetime.now(timezone.utc),
                version=1
            ),
            NewsItem(
                id="test_003",
                source="test",
                title="Weather forecast for tomorrow",
                body="Sunny skies expected with temperatures in the mid-70s.",
                published_at=datetime.now(timezone.utc),
                version=1
            )
        ]

    @pytest.mark.asyncio
    async def test_orchestration_initialization(self, registry):
        """Test orchestration initialization with registry and weights."""
        weights = {"keyword": 0.7, "semantic": 0.3}
        orchestration = FilterOrchestration(registry, weights)

        assert orchestration.registry == registry
        assert orchestration.weights == weights

    @pytest.mark.asyncio
    async def test_orchestration_no_weights(self, registry):
        """Test orchestration initialization without weights."""
        orchestration = FilterOrchestration(registry)

        assert orchestration.registry == registry
        assert orchestration.weights == {}

    @pytest.mark.asyncio
    async def test_apply_filters_with_items(self, orchestration, test_items):
        """Test applying filters to news items."""
        results = await orchestration.apply_filters(test_items)

        assert len(results) == 3

        # Security item should have highest score
        security_item = next(r for r in results if "security" in r.item.title.lower())
        weather_item = next(r for r in results if "weather" in r.item.title.lower())

        assert security_item.relevance_score > weather_item.relevance_score

    @pytest.mark.asyncio
    async def test_apply_filters_empty_input(self, orchestration):
        """Test applying filters to empty input."""
        results = await orchestration.apply_filters([])

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_apply_filters_no_registry_filters(self):
        """Test applying filters when no filters are registered."""
        # Use a fresh registry with no filters
        registry = FilterRegistry()
        orchestration = FilterOrchestration(registry)
        test_items = [
            NewsItem(
                id="test_001",
                source="test",
                title="Test item",
                body="Test content",
                published_at=datetime.now(timezone.utc),
                version=1
            )
        ]

        results = await orchestration.apply_filters(test_items)

        assert len(results) == 1
        assert results[0].relevance_score == 0.5  # Default score
        assert results[0].score_breakdown == {"default": 0.5}

    @pytest.mark.asyncio
    async def test_score_breakdown(self, orchestration, test_items):
        """Test getting detailed score breakdown."""
        item = test_items[0]  # Security item
        breakdown = await orchestration.get_score_breakdown(item)

        # Should have breakdowns from both filters
        assert "keyword" in breakdown
        assert "semantic" in breakdown

    def test_set_weights(self, orchestration):
        """Test updating filter weights."""
        new_weights = {"keyword": 0.8, "semantic": 0.2}
        orchestration.set_weights(new_weights)

        assert orchestration.weights == new_weights

    @pytest.mark.asyncio
    async def test_weighted_scoring(self, registry):
        """Test that weights are properly applied in scoring."""
        # Create orchestration with different weights
        weights = {"keyword": 0.9, "semantic": 0.1}  # Heavy keyword weight
        orchestration = FilterOrchestration(registry, weights)

        test_items = [
            NewsItem(
                id="test_001",
                source="test",
                title="Security vulnerability critical",
                body="Major security issue discovered.",
                published_at=datetime.now(timezone.utc),
                version=1
            )
        ]

        results = await orchestration.apply_filters(test_items)

        assert len(results) == 1
        result = results[0]

        # Should have scores from both filters
        assert "keyword" in result.score_breakdown
        assert "semantic" in result.score_breakdown

        # Keyword score should have more influence due to higher weight
        assert result.score_breakdown["keyword"] > 0
