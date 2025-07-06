"""Registry pattern for managing news sources and filters."""

from .filter_registry import FilterRegistry
from .interfaces import FilteredItem, NewsFilter, NewsSource
from .source_registry import SourceRegistry

__all__ = [
    "NewsSource",
    "NewsFilter",
    "FilteredItem",
    "SourceRegistry",
    "FilterRegistry",
]
