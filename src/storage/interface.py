"""Abstract storage interface for the newsfeed system."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.models.news_item import NewsItem


class NewsStore(ABC):
    """Abstract interface for news item storage operations.

    This interface defines the contract for storing and retrieving news items.
    Implementations can be in-memory, database, or vector store based.

    Design goals:
    - Thread-safe operations
    - Duplicate detection and handling
    - Easy migration between storage backends
    - Consistent API for all storage types
    """

    @abstractmethod
    async def add_item(self, item: NewsItem) -> bool:
        """Add a single news item to storage.

        Args:
            item: The news item to add

        Returns:
            True if item was added, False if duplicate or error

        Note:
            - Should handle duplicate detection (same ID)
            - Should be thread-safe
            - Should log the operation
        """
        pass

    @abstractmethod
    async def add_items(self, items: List[NewsItem]) -> int:
        """Add multiple news items to storage.

        Args:
            items: List of news items to add

        Returns:
            Number of items successfully added (excluding duplicates)

        Note:
            - Should handle duplicate detection efficiently
            - Should be thread-safe
            - Should log the operation with count
        """
        pass

    @abstractmethod
    async def get_all(self) -> List[NewsItem]:
        """Retrieve all news items from storage.

        Returns:
            List of all stored news items

        Note:
            - Should return items in consistent order (for deterministic
              testing)
            - Should be thread-safe
            - Should log the operation
        """
        pass

    @abstractmethod
    async def get_by_id(self, item_id: str) -> Optional[NewsItem]:
        """Retrieve a specific news item by its ID.

        Args:
            item_id: The unique identifier of the news item

        Returns:
            The news item if found, None otherwise

        Note:
            - Should be thread-safe
            - Should handle non-existent IDs gracefully
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """Get the total number of news items in storage.

        Returns:
            Total count of stored items

        Note:
            - Should be thread-safe
            - Should be efficient (O(1) if possible)
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all data from storage.

        Note:
            - Should be thread-safe
            - Should log the operation
            - Primarily used for testing
        """
        pass
