"""Source registry for managing news data sources."""

from typing import Dict, List, Optional

from loguru import logger

from .interfaces import NewsSource


class SourceRegistry:
    """Registry for managing news data sources.

    This class acts as a "phone book" for data sources, allowing easy
    registration, lookup, and management of different news sources.

    Features:
    - Register sources by name
    - Look up sources by name
    - Get all registered sources
    - Enable/disable specific sources
    """

    def __init__(self):
        """Initialize an empty source registry."""
        self._sources: Dict[str, NewsSource] = {}
        logger.info("SourceRegistry initialized")

    def register(self, source: NewsSource) -> None:
        """Register a news source in the registry.

        Args:
            source: The news source to register

        Note:
            - Uses the source's name property as the key
            - Logs the registration for observability
        """
        source_name = source.name
        self._sources[source_name] = source
        logger.info(f"Registered source: {source_name}")

    def get_source(self, name: str) -> Optional[NewsSource]:
        """Get a source by name.

        Args:
            name: The name of the source to retrieve

        Returns:
            The source if found, None otherwise
        """
        source = self._sources.get(name)
        if source:
            logger.debug(f"Retrieved source: {name}")
        else:
            logger.warning(f"Source not found: {name}")
        return source

    def get_sources(self, names: List[str]) -> List[NewsSource]:
        """Get multiple sources by name.

        Args:
            names: List of source names to retrieve

        Returns:
            List of found sources (may be shorter than input if some not found)
        """
        sources = []
        for name in names:
            source = self.get_source(name)
            if source:
                sources.append(source)

        logger.info(f"Retrieved {len(sources)}/{len(names)} sources")
        return sources

    def list_sources(self) -> List[str]:
        """Get list of all registered source names.

        Returns:
            List of all registered source names
        """
        return list(self._sources.keys())

    def has_source(self, name: str) -> bool:
        """Check if a source is registered.

        Args:
            name: The name of the source to check

        Returns:
            True if source is registered, False otherwise
        """
        return name in self._sources

    def count(self) -> int:
        """Get the total number of registered sources.

        Returns:
            Number of registered sources
        """
        return len(self._sources)
