"""In-memory storage implementation for the newsfeed system."""

import asyncio
from typing import Dict, List, Optional

from loguru import logger

from src.models.news_item import NewsItem

from .interface import NewsStore


class InMemoryStore(NewsStore):
    """In-memory storage implementation using Python dictionaries.

    Features:
    - Thread-safe operations using asyncio.Lock
    - Duplicate detection by ID
    - Efficient O(1) lookups
    - Consistent ordering for deterministic results
    - Structured logging for all operations
    """

    def __init__(self):
        """Initialize the in-memory store."""
        self._items: Dict[str, NewsItem] = {}
        self._lock = asyncio.Lock()
        logger.info("InMemoryStore initialized")

    async def add_item(self, item: NewsItem) -> bool:
        """Add a single news item to storage.

        Args:
            item: The news item to add

        Returns:
            True if item was added, False if duplicate
        """
        async with self._lock:
            if item.id in self._items:
                logger.warning(f"Duplicate item ID: {item.id}")
                return False

            self._items[item.id] = item
            logger.info(f"Added item: {item.id} from {item.source}")
            return True

    async def add_items(self, items: List[NewsItem]) -> int:
        """Add multiple news items to storage.

        Args:
            items: List of news items to add

        Returns:
            Number of items successfully added (excluding duplicates)
        """
        async with self._lock:
            added_count = 0
            for item in items:
                if item.id not in self._items:
                    self._items[item.id] = item
                    added_count += 1
                    logger.debug(f"Added item: {item.id}")
                else:
                    logger.debug(f"Skipped duplicate: {item.id}")

            logger.info(f"Added {added_count}/{len(items)} items")
            return added_count

    async def get_all(self) -> List[NewsItem]:
        """Retrieve all news items from storage.

        Returns:
            List of all stored news items in consistent order
        """
        async with self._lock:
            # Sort by published_at DESC, then by id ASC for consistent ordering
            items = list(self._items.values())
            items.sort(key=lambda x: (x.published_at, x.id), reverse=True)
            logger.info(f"Retrieved {len(items)} items")
            return items

    async def get_by_id(self, item_id: str) -> Optional[NewsItem]:
        """Retrieve a specific news item by its ID.

        Args:
            item_id: The unique identifier of the news item

        Returns:
            The news item if found, None otherwise
        """
        async with self._lock:
            item = self._items.get(item_id)
            if item:
                logger.debug(f"Retrieved item: {item_id}")
            else:
                logger.debug(f"Item not found: {item_id}")
            return item

    async def count(self) -> int:
        """Get the total number of news items in storage.

        Returns:
            Total count of stored items
        """
        async with self._lock:
            count = len(self._items)
            logger.debug(f"Current item count: {count}")
            return count

    async def clear(self) -> None:
        """Clear all data from storage.

        Note: Primarily used for testing
        """
        async with self._lock:
            item_count = len(self._items)
            self._items.clear()
            logger.info(f"Cleared {item_count} items from storage")
