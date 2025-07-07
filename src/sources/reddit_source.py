"""
Reddit Source Implementation

Fetches IT-related posts from r/sysadmin subreddit using the praw library.
"""

import os
from datetime import datetime, timezone
from typing import List, Optional

import praw
from loguru import logger

from src.models.news_item import NewsItem
from src.registry.interfaces import NewsSource


class RedditSource(NewsSource):
    """Reddit source for fetching IT-related posts from r/sysadmin."""

    def __init__(self, subreddit_name: str = "sysadmin", limit: int = 10):
        """Initialize Reddit source.

        Args:
            subreddit_name: Name of the subreddit to fetch from (default: sysadmin)
            limit: Maximum number of posts to fetch (default: 10)
        """
        self.subreddit_name = subreddit_name
        self.limit = limit
        self.source_name = f"reddit_{subreddit_name}"

        # Initialize Reddit client
        self.reddit = self._initialize_reddit_client()
        self.subreddit = self.reddit.subreddit(subreddit_name) if self.reddit else None

    def _initialize_reddit_client(self) -> Optional[praw.Reddit]:
        """Initialize Reddit client with credentials from environment variables."""
        try:
            # Get credentials from environment variables
            client_id = os.getenv("REDDIT_CLIENT_ID")
            client_secret = os.getenv("REDDIT_CLIENT_SECRET")
            user_agent = os.getenv("REDDIT_USER_AGENT", "IT-Newsfeed-Bot/1.0")

            if not client_id or not client_secret:
                logger.warning("Reddit credentials not found in environment variables")
                logger.info("Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to enable Reddit source")
                return None

            # Initialize Reddit client
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )

            # Test connection
            reddit.read_only = True
            logger.info(f"✅ Reddit client initialized for r/{self.subreddit_name}")
            return reddit

        except Exception as e:
            logger.error(f"❌ Failed to initialize Reddit client: {e}")
            return None

    async def fetch_items(self) -> List[NewsItem]:
        """Fetch posts from the subreddit and convert to NewsItem format."""
        if not self.reddit or not self.subreddit:
            logger.warning(
                "Reddit client not available, skipping Reddit fetch"
            )
            return []

        try:
            logger.info(
                f"Fetching {self.limit} posts from r/{self.subreddit_name}"
            )

            items = []
            # Fetch hot posts from the subreddit
            for post in self.subreddit.hot(limit=self.limit):
                try:
                    # Convert Reddit post to NewsItem
                    news_item = self._convert_post_to_news_item(post)
                    if news_item:
                        items.append(news_item)

                except Exception as e:
                    logger.error(
                        f"Error processing Reddit post {post.id}: {e}"
                    )
                    continue

            logger.info(
                f"✅ Successfully fetched {len(items)} items from r/"
                f"{self.subreddit_name}"
            )
            return items

        except Exception as e:
            logger.error(f"❌ Error fetching from Reddit: {e}")
            return []

    def _convert_post_to_news_item(self, post) -> Optional[NewsItem]:
        """Convert a Reddit post to NewsItem format."""
        try:
            # Create unique ID
            item_id = (
                f"reddit_{self.subreddit_name}_"
                f"{post.id}"
            )

            # Get post content
            title = post.title
            # Ensure body is always a string
            body = getattr(post, 'selftext', None)
            if body is None:
                body = ""

            # Convert timestamp to datetime
            created_utc = datetime.fromtimestamp(
                post.created_utc, tz=timezone.utc
            )

            # Create NewsItem
            news_item = NewsItem(
                id=item_id,
                source=self.source_name,
                title=title,
                body=body,
                published_at=created_utc,
                version=1,
                relevance_score=None,
                score_breakdown=None,
            )

            return news_item

        except Exception as e:
            logger.error(
                f"Error converting Reddit post to NewsItem: {e}"
            )
            return None

    @property
    def name(self) -> str:
        """Get the source name."""
        return self.source_name

    def get_source_name(self) -> str:
        """Get the source name (legacy method for compatibility)."""
        return self.source_name


def create_reddit_source(subreddit_name: str = "sysadmin", limit: int = 10) -> Optional[RedditSource]:
    """Factory function to create a Reddit source with error handling."""
    try:
        source = RedditSource(subreddit_name=subreddit_name, limit=limit)
        if source.reddit:
            return source
        else:
            logger.warning("Reddit source creation failed - no valid client")
            return None
    except Exception as e:
        logger.error(f"Error creating Reddit source: {e}")
        return None
