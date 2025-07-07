"""Mock news source for testing and development."""

from datetime import datetime, timezone
from typing import List

from loguru import logger

from src.models.news_item import NewsItem
from src.registry.interfaces import NewsSource


class MockNewsSource(NewsSource):
    """Mock news source that generates test data.

    This source creates realistic-looking news items for testing
    the filtering, storage, and API functionality without requiring
    external API calls or network connectivity.

    Features:
    - Generates IT-relevant news items
    - Configurable number of items
    - Realistic timestamps and content
    - No external dependencies
    """

    def __init__(self, name: str = "mock", item_count: int = 10):
        """Initialize the mock news source.

        Args:
            name: Name of the source (default: "mock")
            item_count: Number of items to generate (default: 10)
        """
        self._name = name
        self._item_count = item_count
        logger.info(f"MockNewsSource initialized: {name}, {item_count} items")

    @property
    def name(self) -> str:
        """Get the source name."""
        return self._name

    async def fetch_items(self) -> List[NewsItem]:
        """Fetch mock news items.

        Returns:
            List of mock NewsItem objects with IT-relevant content
        """
        logger.info(f"Fetching {self._item_count} mock news items")

        items = []
        base_time = datetime.now(timezone.utc)

        # Sample IT-relevant news data
        mock_data = [
            {
                "id": f"{self._name}_001",
                "title": "Critical Security Vulnerability in Apache Log4j",
                "body": (
                    "A zero-day vulnerability has been discovered in Apache Log4j "
                    "that allows remote code execution. IT administrators are "
                    "urged to patch immediately."
                ),
                "source": self._name,
                "hours_ago": 2,
            },
            {
                "id": f"{self._name}_002",
                "title": "Major Cloud Provider Outage Affects Multiple Services",
                "body": (
                    "A widespread outage at a major cloud provider is affecting "
                    "thousands of businesses worldwide. Services are gradually "
                    "being restored."
                ),
                "source": self._name,
                "hours_ago": 4,
            },
            {
                "id": f"{self._name}_003",
                "title": "New CVE-2024-1234: Windows Authentication Bypass",
                "body": (
                    "Microsoft has released a critical security patch for a "
                    "Windows authentication bypass vulnerability. All Windows "
                    "systems should be updated."
                ),
                "source": self._name,
                "hours_ago": 6,
            },
            {
                "id": f"{self._name}_004",
                "title": "Ransomware Attack Targets Healthcare Systems",
                "body": (
                    "A sophisticated ransomware attack has targeted multiple "
                    "healthcare systems, causing widespread disruption to "
                    "patient care services."
                ),
                "source": self._name,
                "hours_ago": 8,
            },
            {
                "id": f"{self._name}_005",
                "title": "Docker Container Escape Vulnerability Discovered",
                "body": (
                    "Security researchers have found a critical vulnerability "
                    "in Docker that could allow attackers to escape container "
                    "isolation."
                ),
                "source": self._name,
                "hours_ago": 12,
            },
        ]

        # Generate items from mock data
        for i, data in enumerate(mock_data[:self._item_count]):
            # Use timedelta to properly subtract hours
            from datetime import timedelta
            published_at = base_time - timedelta(hours=data["hours_ago"])

            item = NewsItem(
                id=data["id"],
                source=data["source"],
                title=data["title"],
                body=data["body"],
                published_at=published_at,
                version=1,
            )
            items.append(item)

        logger.info(f"Generated {len(items)} mock news items")
        return items
