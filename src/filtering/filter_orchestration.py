"""Filter orchestration for coordinating multiple filters and scoring."""

from typing import Dict, List

from loguru import logger

from src.models.news_item import NewsItem
from src.registry import FilteredItem, FilterRegistry


class FilterOrchestration:
    """Orchestrates multiple filters to process news items with scoring.

    This class coordinates the application of multiple filters to news items,
    combining their scores using configurable weights and providing detailed
    score breakdowns for explainability.

    Features:
    - Apply multiple filters to news items
    - Combine scores using configurable weights
    - Provide score breakdown for explainability
    - Deterministic ranking and filtering
    - Error handling and graceful degradation
    """

    def __init__(
        self, registry: FilterRegistry, weights: Dict[str, float] | None = None
    ):
        """Initialize the filter orchestration.

        Args:
            registry: The filter registry containing registered filters
            weights: Dictionary mapping filter names to their weights in scoring
                    (default: equal weights for all filters)
        """
        self.registry = registry
        self.weights = weights or {}
        logger.info(f"FilterOrchestration initialized with {len(self.weights)} weights")

    def set_weights(self, weights: Dict[str, float]) -> None:
        """Set the weights for filter scoring.

        Args:
            weights: Dictionary mapping filter names to their weights
        """
        self.weights = weights
        logger.info(f"Updated filter weights: {weights}")

    async def apply_filters(self, items: List[NewsItem]) -> List[FilteredItem]:
        """Apply all registered filters to news items.

        Args:
            items: List of news items to filter

        Returns:
            List of FilteredItem objects with combined scores

        Note:
            - Applies each filter individually
            - Combines scores using configured weights
            - Provides detailed score breakdown
            - Returns deterministic results
            - Handles errors gracefully
        """
        if not items:
            logger.info("No items to filter")
            return []

        # Get filters from registry
        filter_names = (
            list(self.weights.keys()) if self.weights else self.registry.list_filters()
        )
        filters = self.registry.get_filters(filter_names)

        if not filters:
            logger.warning(
                "No filters available, returning all items with default scores"
            )
            return [
                FilteredItem(
                    item=item,
                    relevance_score=0.5,  # Default neutral score
                    score_breakdown={"default": 0.5},
                )
                for item in items
            ]

        logger.info(f"Applying {len(filters)} filters to {len(items)} items")

        # Apply each filter and collect results
        filter_results: Dict[str, List[FilteredItem]] = {}
        for filter_component in filters:
            try:
                results = await filter_component.filter(items)
                filter_results[filter_component.name] = results
                logger.debug(
                    f"Filter {filter_component.name} processed {len(results)} items"
                )
            except Exception as e:
                logger.error(f"Error applying filter {filter_component.name}: {e}")
                # Continue with other filters
                continue

        # Combine scores from all filters
        combined_items = self._combine_scores(items, filter_results)

        logger.info(f"Filtering complete: {len(combined_items)} items processed")
        return combined_items

    def _combine_scores(
        self, items: List[NewsItem], filter_results: Dict[str, List[FilteredItem]]
    ) -> List[FilteredItem]:
        """Combine scores from multiple filters.

        Args:
            items: Original list of news items
            filter_results: Results from each filter

        Returns:
            List of FilteredItem objects with combined scores
        """
        combined_items = []

        for item in items:
            # Collect scores from all filters
            score_breakdown = {}
            total_weighted_score = 0.0
            total_weight = 0.0

            for filter_name, filter_weight in self.weights.items():
                if filter_name in filter_results:
                    # Find this item's score from this filter
                    filter_result = next(
                        (
                            fr
                            for fr in filter_results[filter_name]
                            if fr.item.id == item.id
                        ),
                        None,
                    )

                    if filter_result:
                        score = filter_result.relevance_score
                        score_breakdown[filter_name] = score
                        total_weighted_score += score * filter_weight
                        total_weight += filter_weight
                    else:
                        # Item not found in this filter's results
                        score_breakdown[filter_name] = 0.0
                else:
                    # Filter failed or not available
                    score_breakdown[filter_name] = 0.0

            # Calculate final weighted score
            if total_weight > 0:
                final_score = total_weighted_score / total_weight
            else:
                final_score = 0.0

            # Add final score to breakdown
            score_breakdown["final"] = final_score

            # Create combined filtered item
            combined_item = FilteredItem(
                item=item, relevance_score=final_score, score_breakdown=score_breakdown
            )
            combined_items.append(combined_item)

        return combined_items

    async def get_score_breakdown(self, item: NewsItem) -> Dict[str, float]:
        """Get detailed score breakdown for a single item.

        Args:
            item: News item to analyze

        Returns:
            Dictionary of score components from each filter
        """
        filter_names = (
            list(self.weights.keys()) if self.weights else self.registry.list_filters()
        )
        filters = self.registry.get_filters(filter_names)

        breakdown = {}
        for filter_component in filters:
            try:
                filter_breakdown = await filter_component.get_score_breakdown(item)
                breakdown[filter_component.name] = filter_breakdown
            except Exception as e:
                logger.error(
                    f"Error getting breakdown from {filter_component.name}: {e}"
                )
                breakdown[filter_component.name] = {}

        return breakdown
