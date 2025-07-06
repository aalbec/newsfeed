"""Filter registry for managing news filtering components."""

from typing import Dict, List, Optional

from loguru import logger

from .interfaces import NewsFilter


class FilterRegistry:
    """Registry for managing news filtering components.

    This class acts as a "phone book" for filters, allowing easy
    registration, lookup, and management of different filtering components.

    Features:
    - Register filters by name
    - Look up filters by name
    - Get all registered filters
    - Enable/disable specific filters
    """

    def __init__(self):
        """Initialize an empty filter registry."""
        self._filters: Dict[str, NewsFilter] = {}
        logger.info("FilterRegistry initialized")

    def register(self, filter_component: NewsFilter) -> None:
        """Register a news filter in the registry.

        Args:
            filter_component: The news filter to register

        Note:
            - Uses the filter's name property as the key
            - Logs the registration for observability
        """
        filter_name = filter_component.name
        self._filters[filter_name] = filter_component
        logger.info(f"Registered filter: {filter_name}")

    def get_filter(self, name: str) -> Optional[NewsFilter]:
        """Get a filter by name.

        Args:
            name: The name of the filter to retrieve

        Returns:
            The filter if found, None otherwise
        """
        filter_component = self._filters.get(name)
        if filter_component:
            logger.debug(f"Retrieved filter: {name}")
        else:
            logger.warning(f"Filter not found: {name}")
        return filter_component

    def get_filters(self, names: List[str]) -> List[NewsFilter]:
        """Get multiple filters by name.

        Args:
            names: List of filter names to retrieve

        Returns:
            List of found filters (may be shorter than input if some not found)
        """
        filters = []
        for name in names:
            filter_component = self.get_filter(name)
            if filter_component:
                filters.append(filter_component)

        logger.info(f"Retrieved {len(filters)}/{len(names)} filters")
        return filters

    def list_filters(self) -> List[str]:
        """Get list of all registered filter names.

        Returns:
            List of all registered filter names
        """
        return list(self._filters.keys())

    def has_filter(self, name: str) -> bool:
        """Check if a filter is registered.

        Args:
            name: The name of the filter to check

        Returns:
            True if filter is registered, False otherwise
        """
        return name in self._filters

    def count(self) -> int:
        """Get the total number of registered filters.

        Returns:
            Number of registered filters
        """
        return len(self._filters)
