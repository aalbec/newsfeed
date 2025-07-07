"""Unit tests for registry pattern classes."""

from src.registry import FilterRegistry, NewsFilter, NewsSource, SourceRegistry


class MockNewsSource(NewsSource):
    """Mock news source for testing."""

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def fetch_items(self):
        return []


class MockNewsFilter(NewsFilter):
    """Mock news filter for testing."""

    def __init__(self, name="mock"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def filter(self, items):
        from src.registry import FilteredItem

        return [
            FilteredItem(item=item, relevance_score=1.0, score_breakdown={"mock": 1.0})
            for item in items
        ]

    async def get_score_breakdown(self, item):
        return {"mock": 1.0}


class TestSourceRegistry:
    """Test cases for SourceRegistry class."""

    def test_init(self):
        """Test registry initialization."""
        registry = SourceRegistry()
        assert registry.count() == 0
        assert registry.list_sources() == []

    def test_register_source(self):
        """Test registering a single source."""
        registry = SourceRegistry()
        source = MockNewsSource("test-source")

        registry.register(source)

        assert registry.count() == 1
        assert registry.has_source("test-source")
        assert registry.list_sources() == ["test-source"]

    def test_get_source(self):
        """Test retrieving a source by name."""
        registry = SourceRegistry()
        source = MockNewsSource("test-source")
        registry.register(source)

        retrieved = registry.get_source("test-source")

        assert retrieved is source
        assert retrieved is not None
        assert retrieved.name == "test-source"

    def test_get_source_not_found(self):
        """Test retrieving a non-existent source."""
        registry = SourceRegistry()

        retrieved = registry.get_source("non-existent")

        assert retrieved is None


class TestFilterRegistry:
    """Test cases for FilterRegistry class."""

    def test_init(self):
        """Test registry initialization."""
        registry = FilterRegistry()
        assert registry.count() == 0
        assert registry.list_filters() == []

    def test_register_filter(self):
        """Test registering a single filter."""
        registry = FilterRegistry()
        filter_component = MockNewsFilter("test-filter")

        registry.register(filter_component)

        assert registry.count() == 1
        assert registry.has_filter("test-filter")
        assert registry.list_filters() == ["test-filter"]

    def test_get_filter(self):
        """Test retrieving a filter by name."""
        registry = FilterRegistry()
        filter_component = MockNewsFilter("test-filter")
        registry.register(filter_component)

        retrieved = registry.get_filter("test-filter")

        assert retrieved is filter_component
        assert retrieved is not None
        assert retrieved.name == "test-filter"

    def test_get_filter_not_found(self):
        """Test retrieving a non-existent filter."""
        registry = FilterRegistry()

        retrieved = registry.get_filter("non-existent")

        assert retrieved is None


# TODO: Future test enhancements (when time allows)  # noqa: E501 pylint: disable=fixme
#
# SourceRegistry additional tests:
# - test_get_sources: Test retrieving multiple sources by name
# - test_get_sources_partial_missing: Test when some requested sources
#   don't exist
# - test_has_source: Test existence checking convenience method
# - test_count: Test counting registered sources
# - test_register_duplicate: Test overwriting existing source with same name
# - test_register_invalid_source: Test registering non-NewsSource objects
#
# FilterRegistry additional tests:
# - test_get_filters: Test retrieving multiple filters by name
# - test_get_filters_partial_missing: Test when some requested filters
#   don't exist
# - test_has_filter: Test existence checking convenience method
# - test_count: Test counting registered filters
# - test_register_duplicate: Test overwriting existing filter with same name
# - test_register_invalid_filter: Test registering non-NewsFilter objects
#
# Interface compliance tests (if needed later):
# - test_source_interface_compliance: Ensure all sources implement required methods
# - test_filter_interface_compliance: Ensure all filters implement required methods
# - test_filtered_item_validation: Test FilteredItem score validation edge cases
#
# Integration tests (for future phases):
# - test_registry_with_real_sources: Test registry with actual RSS/Reddit sources
# - test_registry_with_real_filters: Test registry with actual keyword/semantic filters
# - test_registry_performance: Test registry performance with many components
