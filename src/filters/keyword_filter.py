"""Keyword-based filter for IT news relevance."""

import re
from typing import Dict, List

from loguru import logger

from src.models.news_item import NewsItem
from src.registry import FilteredItem, NewsFilter


class KeywordFilter(NewsFilter):
    """Keyword-based filter for IT news relevance.

    This filter scores news items based on the presence of IT-relevant keywords
    such as security, outages, vulnerabilities, etc. It's designed to identify
    news that would be relevant to IT managers.

    Keywords are weighted by importance and the filter provides detailed
    breakdown of which keywords contributed to the score.
    """

    def __init__(self):
        """Initialize the keyword filter with IT-relevant keywords."""
        # High-priority keywords (security, outages, critical issues)
        self.high_priority_keywords = {
            'security', 'vulnerability', 'breach', 'hack', 'cyber',
            'outage', 'downtime', 'crash', 'failure', 'bug',
            'cve', 'exploit', 'malware', 'ransomware', 'phishing',
            'patch', 'update', 'fix', 'critical', 'urgent',
            # Vendor-specific critical terms (high impact)
            'aws', 'amazon web services', 'azure', 'microsoft azure',
            'gcp', 'google cloud', 'office 365', 'o365', 'github', 'zoom'
        }

        # Medium-priority keywords (general IT topics)
        self.medium_priority_keywords = {
            'update', 'upgrade', 'maintenance', 'performance',
            'compatibility', 'integration', 'deployment',
            'monitoring', 'backup', 'recovery', 'disaster',
            'compliance', 'regulation', 'policy', 'governance'
        }

        # Low-priority keywords (general tech)
        self.low_priority_keywords = {
            'technology', 'software', 'hardware', 'cloud',
            'data', 'network', 'server', 'database', 'api',
            'development', 'testing', 'release', 'version'
        }

    @property
    def name(self) -> str:
        """Get the filter name."""
        return "keyword"

    async def filter(self, items: List[NewsItem]) -> List[FilteredItem]:
        """Filter news items based on keyword relevance.

        Args:
            items: List of news items to filter

        Returns:
            List of FilteredItem objects with keyword-based scores
        """
        filtered_items = []

        for item in items:
            score_breakdown = await self.get_score_breakdown(item)
            # The relevance score is the highest score from any category,
            # not the average. This ensures that a high-priority keyword
            # hit is not diluted by zero scores in other categories.
            relevance_score = (
                max(score_breakdown.values()) if score_breakdown else 0.0
            )

            filtered_item = FilteredItem(
                item=item,
                relevance_score=relevance_score,
                score_breakdown=score_breakdown
            )
            filtered_items.append(filtered_item)

        logger.debug(f"Keyword filter processed {len(filtered_items)} items")
        return filtered_items

    async def get_score_breakdown(self, item: NewsItem) -> Dict[str, float]:
        """Get detailed keyword score breakdown for an item.

        Args:
            item: News item to analyze

        Returns:
            Dictionary of keyword category scores
        """
        # Combine title and body for analysis
        text = f"{item.title} {item.body or ''}".lower()

        # Count keyword matches by priority
        high_matches = self._count_keywords(text, self.high_priority_keywords)
        medium_matches = self._count_keywords(text, self.medium_priority_keywords)
        low_matches = self._count_keywords(text, self.low_priority_keywords)

        # Calculate scores (high priority gets more weight)
        high_score = min(high_matches * 0.3, 1.0)  # Max 1.0
        medium_score = min(medium_matches * 0.2, 0.8)  # Max 0.8
        low_score = min(low_matches * 0.1, 0.5)  # Max 0.5

        breakdown = {
            "high_priority_keywords": high_score,
            "medium_priority_keywords": medium_score,
            "low_priority_keywords": low_score
        }

        return breakdown

    def _count_keywords(self, text: str, keywords: set) -> int:
        """Count occurrences of keywords in text.

        Args:
            text: Text to search in
            keywords: Set of keywords to search for

        Returns:
            Number of keyword matches found
        """
        count = 0
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, text)
            count += len(matches)

        return count
