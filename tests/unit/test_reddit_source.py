"""
Unit tests for Reddit source implementation.
"""

import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from src.sources.reddit_source import RedditSource, create_reddit_source


class TestRedditSource:
    """Test cases for RedditSource class."""

    def test_reddit_source_initialization_without_credentials(self):
        """Test Reddit source initialization without credentials."""
        # Clear any existing environment variables
        with patch.dict(os.environ, {}, clear=True):
            source = RedditSource()
            assert source.reddit is None
            assert source.subreddit is None
            assert source.source_name == "reddit_sysadmin"

    def test_reddit_source_initialization_with_credentials(self):
        """Test Reddit source initialization with credentials."""
        mock_reddit = Mock()
        mock_subreddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit

        with patch.dict(
            os.environ,
            {
                "REDDIT_CLIENT_ID": "test_client_id",
                "REDDIT_CLIENT_SECRET": "test_client_secret"
            }
        ):
            with patch(
                'src.sources.reddit_source.praw.Reddit', return_value=mock_reddit
            ):
                source = RedditSource()
                assert source.reddit is not None
                assert source.subreddit is not None
                assert source.source_name == "reddit_sysadmin"

    def test_get_source_name(self):
        """Test get_source_name method."""
        source = RedditSource(subreddit_name="test_subreddit")
        assert source.get_source_name() == "reddit_test_subreddit"

    def test_convert_post_to_news_item(self):
        """Test converting Reddit post to NewsItem."""
        source = RedditSource()

        # Mock Reddit post
        mock_post = Mock()
        mock_post.id = "test_post_id"
        mock_post.title = "Test IT Issue"
        mock_post.selftext = "This is a test IT issue description"
        mock_post.created_utc = 1640995200  # 2022-01-01 00:00:00 UTC

        news_item = source._convert_post_to_news_item(mock_post)

        assert news_item is not None
        assert news_item.id == "reddit_sysadmin_test_post_id"
        assert news_item.title == "Test IT Issue"
        assert news_item.body == "This is a test IT issue description"
        assert news_item.source == "reddit_sysadmin"
        assert news_item.published_at == datetime(
            2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc
        )

    @pytest.mark.asyncio
    async def test_fetch_items_without_client(self):
        """Test fetch_items when Reddit client is not available."""
        source = RedditSource()
        source.reddit = None

        items = await source.fetch_items()
        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_items_with_client(self):
        """Test fetch_items with available Reddit client."""
        source = RedditSource()

        # Mock Reddit client and subreddit
        mock_reddit = Mock()
        mock_subreddit = Mock()
        source.reddit = mock_reddit
        source.subreddit = mock_subreddit

        # Mock posts
        mock_post1 = Mock()
        mock_post1.id = "post1"
        mock_post1.title = "IT Issue 1"
        mock_post1.selftext = "Description 1"
        mock_post1.created_utc = 1640995200

        mock_post2 = Mock()
        mock_post2.id = "post2"
        mock_post2.title = "IT Issue 2"
        mock_post2.selftext = "Description 2"
        mock_post2.created_utc = 1640995200

        # Mock subreddit.hot() to return our posts
        mock_subreddit.hot.return_value = [mock_post1, mock_post2]

        items = await source.fetch_items()

        assert len(items) == 2
        assert items[0].title == "IT Issue 1"
        assert items[1].title == "IT Issue 2"

    @pytest.mark.asyncio
    async def test_fetch_items_with_error(self):
        """Test fetch_items when an error occurs."""
        source = RedditSource()

        # Mock Reddit client that raises an exception
        mock_reddit = Mock()
        mock_subreddit = Mock()
        mock_subreddit.hot.side_effect = Exception("Reddit API error")
        source.reddit = mock_reddit
        source.subreddit = mock_subreddit

        items = await source.fetch_items()
        assert items == []


class TestCreateRedditSource:
    """Test cases for create_reddit_source factory function."""

    def test_create_reddit_source_without_credentials(self):
        """Test creating Reddit source without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            source = create_reddit_source()
            assert source is None

    def test_create_reddit_source_with_credentials(self):
        """Test creating Reddit source with credentials."""
        mock_reddit = Mock()
        mock_subreddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit

        with patch.dict(
            os.environ,
            {
                "REDDIT_CLIENT_ID": "test_client_id",
                "REDDIT_CLIENT_SECRET": "test_client_secret"
            }
        ):
            with patch(
                'src.sources.reddit_source.praw.Reddit', return_value=mock_reddit
            ):
                source = create_reddit_source()
                assert source is not None
                assert source.source_name == "reddit_sysadmin"

    def test_create_reddit_source_with_custom_subreddit(self):
        """Test creating Reddit source with custom subreddit."""
        mock_reddit = Mock()
        mock_subreddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit

        with patch.dict(
            os.environ,
            {
                "REDDIT_CLIENT_ID": "test_client_id",
                "REDDIT_CLIENT_SECRET": "test_client_secret"
            }
        ):
            with patch(
                'src.sources.reddit_source.praw.Reddit', return_value=mock_reddit
            ):
                source = create_reddit_source(subreddit_name="networking", limit=5)
                assert source is not None
                assert source.source_name == "reddit_networking"
                assert source.limit == 5
