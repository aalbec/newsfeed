"""Semantic filter using sentence embeddings for relevance scoring."""

from typing import Dict, List, Optional

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from src.models.news_item import NewsItem
from src.registry import FilteredItem, NewsFilter


class SemanticFilter(NewsFilter):
    """Semantic filter using sentence embeddings for IT news relevance.

    This filter uses sentence embeddings to calculate semantic similarity
    between news items and IT-relevant topics. It's designed to identify
    news that is semantically related to IT management concerns.

    Uses sentence-transformers with all-MiniLM-L6-v2 for semantic understanding.
    """

    def __init__(self, model: Optional[SentenceTransformer] = None):
        """Initialize the semantic filter with sentence embeddings.

        Args:
            model: Optional pre-loaded SentenceTransformer model for testing
        """
        # IT-relevant topic phrases for semantic matching
        self.it_topics = [
            "system administration",
            "network security",
            "data breach",
            "service outage",
            "software vulnerability",
            "cybersecurity incident",
            "IT infrastructure",
            "system maintenance",
            "performance monitoring",
            "disaster recovery",
        ]

        # Initialize sentence transformer model
        # Using all-MiniLM-L6-v2 for optimal balance of speed and accuracy
        if model is not None:
            self.model = model
            logger.info("Semantic filter initialized with provided model")
        else:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Semantic filter initialized with sentence-transformers")

        self.topic_embeddings = self.model.encode(self.it_topics)

    @property
    def name(self) -> str:
        """Get the filter name."""
        return "semantic"

    async def filter(self, items: List[NewsItem]) -> List[FilteredItem]:
        """Filter news items based on semantic relevance.

        Args:
            items: List of news items to filter

        Returns:
            List of FilteredItem objects with semantic-based scores
        """
        filtered_items = []

        for item in items:
            score_breakdown = await self.get_score_breakdown(item)
            relevance_score = score_breakdown.get("overall_semantic", 0.0)

            filtered_item = FilteredItem(
                item=item,
                relevance_score=relevance_score,
                score_breakdown=score_breakdown,
            )
            filtered_items.append(filtered_item)

        logger.debug(f"Semantic filter processed {len(filtered_items)} items")
        return filtered_items

    async def get_score_breakdown(self, item: NewsItem) -> Dict[str, float]:
        """Get detailed semantic score breakdown for an item.

        Args:
            item: News item to analyze

        Returns:
            Dictionary of semantic similarity scores
        """
        # Combine title and body for analysis
        text = f"{item.title} {item.body or ''}".lower()

        # Calculate semantic similarity to IT topics
        topic_scores = {}

        for i, topic in enumerate(self.it_topics):
            similarity = self._calculate_similarity(text, i)
            topic_scores[f"topic_{topic.replace(' ', '_')}"] = similarity

        # Calculate overall semantic score (maximum similarity)
        if topic_scores:
            max_similarity = max(topic_scores.values())
            topic_scores["overall_semantic"] = float(max_similarity)
        else:
            topic_scores["overall_semantic"] = 0.0

        # Ensure all values are Python floats for Pydantic serialization
        return {k: float(v) for k, v in topic_scores.items()}

    def _calculate_similarity(self, text: str, topic_index: int) -> float:
        """Calculate semantic similarity between text and topic.

        Args:
            text: Text to analyze
            topic_index: Index of topic in self.it_topics

        Returns:
            Cosine similarity score between 0.0 and 1.0
        """
        # Encode the text
        text_embedding = self.model.encode([text])[0]

        # Get pre-computed topic embedding
        topic_embedding = self.topic_embeddings[topic_index]

        # Calculate cosine similarity
        similarity = self._cosine_similarity(text_embedding, topic_embedding)

        # Ensure non-negative score
        return max(0.0, similarity)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Convert numpy.float32 to Python float for Pydantic serialization
        return float(dot_product / (norm1 * norm2))
