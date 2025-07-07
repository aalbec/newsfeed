"""Retrieve endpoint router for getting filtered news items."""

import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from src.models.api import (
    BadRequestErrorResponse,
    InternalServerErrorResponse,
    RetrieveResponse,
    ValidationErrorResponse,
)
from src.models.news_item import NewsItem
from src.registry import FilterRegistry
from src.storage import NewsStore

# Configuration constants
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.1"))


def get_storage(request: Request) -> NewsStore:
    """Dependency to get the storage instance from app state."""
    return request.app.state.storage


def get_filter_registry(request: Request) -> FilterRegistry:
    """Dependency to get the filter registry from app state."""
    return request.app.state.filter_registry


async def retrieve_and_filter_items(storage: NewsStore, filter_registry: FilterRegistry) -> List[NewsItem]:
    """Retrieve all items from storage and apply filters for ranking."""
    try:
        # Get all items from storage
        all_items = await storage.get_all()
        logger.info(f"📊 Retrieved {len(all_items)} items from storage")

        if not all_items:
            logger.info("📭 No items in storage")
            return []

        # Apply filters if available
        filter_names = filter_registry.list_filters()
        if not filter_names:
            logger.warning("⚠️ No filters available - returning all items without ranking")
            # Sort by published_at (newest first) as fallback
            sorted_items = sorted(all_items, key=lambda x: x.published_at, reverse=True)
            return sorted_items

        logger.info(f"🔍 Applying {len(filter_names)} filters to {len(all_items)} items")

        # Apply each filter and collect scores
        for item in all_items:
            scores = []
            reasons = []

            for filter_name in filter_names:
                filter_instance = filter_registry.get_filter(filter_name)
                if filter_instance:
                    try:
                        filtered_items = await filter_instance.filter([item])
                        if filtered_items:
                            filtered_item = filtered_items[0]
                            # The filters now return clean numerical scores directly
                            scores.append(filtered_item.relevance_score)
                            breakdown = filtered_item.score_breakdown
                            if breakdown:
                                reasons.append(f"{filter_name}: {breakdown}")
                    except Exception as e:
                        logger.error(f"Filter {filter_name} failed for item {item.id}: {e}")

            # Take the highest score from all filters (highest signal wins)
            item.relevance_score = max(scores) if scores else 0.0
            item.score_breakdown = "; ".join(reasons) if reasons else "No specific reason"

        # Filter by relevance threshold and sort by score (highest first)
        relevant_items = [
            item for item in all_items
            if hasattr(item, 'relevance_score') and item.relevance_score is not None
            and item.relevance_score >= RELEVANCE_THRESHOLD
        ]

        # Sort by relevance score (descending), then by published_at (newest first)
        sorted_items = sorted(
            relevant_items,
            key=lambda x: (x.relevance_score, x.published_at),
            reverse=True
        )

        logger.info(f"✅ Filtered {len(all_items)} items to {len(sorted_items)} relevant items")
        return sorted_items

    except Exception as e:
        logger.error(f"Error retrieving and filtering items: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve items: {str(e)}")


router = APIRouter()


@router.get(
    "/retrieve",
    response_model=RetrieveResponse,
    status_code=200,
    tags=["Retrieve"],
    responses={
        200: {"description": "News items retrieved and filtered successfully"},
        400: {
            "model": BadRequestErrorResponse,
            "description": "Bad request - invalid parameters"
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation error - invalid request format"
        },
        500: {
            "model": InternalServerErrorResponse,
            "description": "Internal server error during retrieval"
        }
    }
)
async def retrieve_news(
    storage: NewsStore = Depends(get_storage),
    filter_registry: FilterRegistry = Depends(get_filter_registry),
) -> RetrieveResponse:
    """Retrieve filtered news events with AI-powered ranking and relevance scoring.

    This endpoint implements the exact API contract:
    - Returns only events that passed the filtering criteria
    - Sorts by importance × recency (relevance score × timestamp)
    - Provides deterministic results for given data
    - Returns items in the same JSON shape as ingested

    The filtering process:
    1. **Retrieves all items** from storage
    2. **Applies AI filters** (semantic similarity, keyword matching)
    3. **Calculates relevance scores** based on IT manager relevance
    4. **Filters by threshold** (default: 0.1 - for testing purposes)
    5. **Sorts by score** (highest first, then by recency)

    Returns detailed information including:
    - Filtered and ranked news items
    - Total count of returned items
    - Optional filtering statistics

    This endpoint is deterministic and will return the same results
    for identical data sets, making it suitable for automated testing.
    """
    try:
        logger.info("📥 Retrieving filtered news items")

        # Retrieve and filter items
        items = await retrieve_and_filter_items(storage, filter_registry)

        # Get total count for statistics
        total_items_in_storage = len(await storage.get_all())

        # Build filtering info
        filtering_info = {
            "total_items_in_storage": total_items_in_storage,
            "items_passing_filters": len(items),
            "relevance_threshold": RELEVANCE_THRESHOLD
        }

        logger.info(f"📊 Retrieved {len(items)} items (from {total_items_in_storage} total)")

        return RetrieveResponse(
            items=items,
            total=len(items),
            filtering_info=filtering_info
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in retrieve endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during retrieval: {str(e)}"
        )
