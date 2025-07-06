"""Storage abstraction layer for the newsfeed system."""

from .in_memory import InMemoryStore
from .interface import NewsStore

__all__ = ["NewsStore", "InMemoryStore"]
