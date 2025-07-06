"""Abstract interfaces for the registry pattern."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

from src.models.news_item import NewsItem


@dataclass
class FilteredItem:
    """A news item with filtering scores and metadata.

    This represents a news item that has been processed by the filtering
    system, including relevance scores and breakdown for explainability.
    """

    item: NewsItem
    relevance_score: float
    score_breakdown: Dict[str, float]

    def __post_init__(self):
        """Validate the filtered item after initialization."""
        if not 0.0 <= self.relevance_score <= 1.0:
            raise ValueError("relevance_score must be between 0.0 and 1.0")

        # Validate score breakdown
        for score_name, score_value in self.score_breakdown.items():
            if not 0.0 <= score_value <= 1.0:
                raise ValueError(f"Score {score_name} must be between 0.0 and 1.0")


class NewsSource(ABC):
    """Abstract interface for news data sources.

    All data sources (Reddit, RSS, Mock) must implement this interface.
    This ensures consistent behavior across different sources.
    """

    @abstractmethod
    async def fetch_items(self) -> List[NewsItem]:
        """Fetch news items from this source.

        Returns:
            List of news items from this source

        Note:
            - Should handle errors gracefully
            - Should return empty list if no items available
            - Should be async for non-blocking operation
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this source.

        Returns:
            Source name (e.g., 'reddit', 'rss', 'mock')
        """


class NewsFilter(ABC):
    """Abstract interface for news filtering components.

    This interface defines the contract for all filtering components
    in the newsfeed system. Filters can be keyword-based, semantic,
    or any other filtering approach.

    Design goals:
    - Async for future AI model integration
    - Score breakdown for explainability
    - Deterministic results
    - Easy composition and testing
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the filter name for registry identification."""
        pass

    @abstractmethod
    async def filter(self, items: List[NewsItem]) -> List[FilteredItem]:
        """Filter a list of news items and return scored results.

        Args:
            items: List of news items to filter

        Returns:
            List of FilteredItem objects with relevance scores and breakdown

        Note:
            - Should be deterministic (same input = same output)
            - Should handle empty input gracefully
            - Should provide score breakdown for explainability
            - Should be async for future AI model integration
        """
        pass

    @abstractmethod
    async def get_score_breakdown(self, item: NewsItem) -> Dict[str, float]:
        """Get detailed score breakdown for a single item.

        Args:
            item: News item to analyze

        Returns:
            Dictionary of score components (e.g., {"keyword": 0.8, "semantic": 0.6})

        Note:
            - Used for explainability and debugging
            - Should be consistent with filter() results
        """
        pass
