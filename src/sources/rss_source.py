"""RSS feed source for IT news websites."""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional

import feedparser
from loguru import logger

from src.models.news_item import NewsItem
from src.registry.interfaces import NewsSource


class RSSSource(NewsSource):
    """RSS feed source for IT news websites.

    This source fetches news from RSS feeds of IT-focused websites
    like Tom's Hardware, Ars Technica, etc.

    Features:
    - Async RSS feed parsing
    - Error handling and fallback
    - Configurable feed URLs
    - Realistic IT news content
    """

    def __init__(self, name: str, feed_url: str, max_items: int = 10):
        """Initialize the RSS source.

        Args:
            name: Name of the source (e.g., "tomshardware", "arstechnica")
            feed_url: URL of the RSS feed
            max_items: Maximum number of items to fetch (default: 10)
        """
        self._name = name
        self._feed_url = feed_url
        self._max_items = max_items
        logger.info(f"RSSSource initialized: {name}, {feed_url}, max {max_items} items")

    @property
    def name(self) -> str:
        """Get the source name."""
        return self._name

    async def fetch_items(self) -> List[NewsItem]:
        """Fetch news items from the RSS feed.

        Returns:
            List of NewsItem objects from the RSS feed
        """
        logger.info(f"Fetching RSS items from {self._name}: {self._feed_url}")

        try:
            # Use asyncio to run feedparser in a thread pool
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, self._parse_feed)

            if not feed or not feed.entries:
                logger.warning(f"No entries found in RSS feed: {self._feed_url}")
                return []

            items = []
            for i, entry in enumerate(feed.entries[:self._max_items]):
                try:
                    item = self._parse_entry(entry)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.error(f"Error parsing RSS entry {i}: {e}")
                    continue

            logger.info(f"Successfully fetched {len(items)} items from {self._name}")
            return items

        except Exception as e:
            logger.error(f"Error fetching RSS feed {self._feed_url}: {e}")
            return []

    def _parse_feed(self) -> Optional[feedparser.FeedParserDict]:
        """Parse the RSS feed synchronously.

        Returns:
            Parsed feed data or None if parsing fails
        """
        try:
            feed = feedparser.parse(self._feed_url)

            # Check for parsing errors
            if hasattr(feed, 'bozo') and feed.bozo:
                logger.warning(f"RSS feed parsing warnings for {self._feed_url}")

            return feed
        except Exception as e:
            logger.error(f"Failed to parse RSS feed {self._feed_url}: {e}")
            return None

    def _parse_entry(self, entry) -> Optional[NewsItem]:
        """Parse a single RSS entry into a NewsItem.

        Args:
            entry: RSS entry from feedparser

        Returns:
            NewsItem object or None if parsing fails
        """
        try:
            # Extract title
            title = getattr(entry, 'title', '')
            if not title:
                logger.warning(f"RSS entry missing title: {entry}")
                return None

            # Extract body/content
            body = ''
            if hasattr(entry, 'summary'):
                body = entry.summary
            elif hasattr(entry, 'description'):
                body = entry.description
            elif hasattr(entry, 'content') and entry.content:
                body = entry.content[0].value

            # Parse published date
            published_at = self._parse_date(entry)

            # Generate unique ID from source and title
            item_id = self._generate_id(entry)

            return NewsItem(
                id=item_id,
                source=self._name,
                title=title,
                body=body,
                published_at=published_at,
                version=1,
            )

        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None

    def _parse_date(self, entry) -> datetime:
        """Parse the published date from RSS entry.

        Args:
            entry: RSS entry from feedparser

        Returns:
            Parsed datetime object, defaults to current time if parsing fails
        """
        try:
            # Try different date fields
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'published'):
                # Try to parse string date
                from dateutil import parser
                return parser.parse(entry.published).replace(tzinfo=timezone.utc)
        except Exception as e:
            logger.warning(f"Could not parse date from RSS entry: {e}")

        # Fallback to current time
        return datetime.now(timezone.utc)

    def _generate_id(self, entry) -> str:
        """Generate a unique ID for the RSS entry.

        Args:
            entry: RSS entry from feedparser

        Returns:
            Unique string ID
        """
        # Try to use existing ID
        if hasattr(entry, 'id') and entry.id:
            return f"{self._name}_{entry.id}"

        # Use link as fallback
        if hasattr(entry, 'link') and entry.link:
            # Create hash from link
            import hashlib
            link_hash = hashlib.md5(entry.link.encode()).hexdigest()[:8]
            return f"{self._name}_{link_hash}"

        # Use title as last resort
        if hasattr(entry, 'title') and entry.title:
            import hashlib
            title_hash = hashlib.md5(entry.title.encode()).hexdigest()[:8]
            return f"{self._name}_{title_hash}"

        # Fallback to timestamp
        import time
        timestamp = int(time.time())
        return f"{self._name}_{timestamp}"
