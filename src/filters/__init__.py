"""Concrete filter implementations for news filtering."""

from .keyword_filter import KeywordFilter
from .semantic_filter import SemanticFilter

__all__ = ["KeywordFilter", "SemanticFilter"]
