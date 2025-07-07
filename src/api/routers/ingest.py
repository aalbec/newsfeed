"""Ingest endpoint router for processing news items (modular refactor)."""

import os
from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from src.models.api import (
    BadRequestErrorResponse,
    IngestRequest,
    IngestResponse,
    IngestSummary,
    InternalServerErrorResponse,
    ValidationErrorResponse,
)
from src.registry import FilterRegistry, SourceRegistry
from src.storage import NewsStore

# Configuration constants
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.1"))


def get_storage(request: Request) -> NewsStore:
    """Dependency to get the storage instance from app state."""
    return request.app.state.storage


def get_filter_registry(request: Request) -> FilterRegistry:
    """Dependency to get the filter registry from app state."""
    return request.app.state.filter_registry


def get_source_registry(request: Request) -> SourceRegistry:
    """Dependency to get the source registry from app state."""
    return request.app.state.source_registry


def validate_item_fields(item) -> bool:
    """Check if required fields are present and non-empty."""
    return bool(item.id and item.title and item.published_at)


async def is_duplicate(item, storage: NewsStore) -> bool:
    """Check if the item already exists in storage by id."""
    existing_item = await storage.get_by_id(item.id)
    return existing_item is not None


async def filter_item(item, filter_registry: FilterRegistry) -> Tuple[float, str, bool]:
    """Apply all filters to the item. Return (score, reason, is_relevant)."""
    filter_names = filter_registry.list_filters()
    if not filter_names:
        logger.warning("No filters available - accepting all items")
        return 1.0, "No filters configured", True
    logger.debug(
        f"Applying {len(filter_names)} filters with threshold: {RELEVANCE_THRESHOLD}"
    )
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
                logger.error(
                    f"Filter {filter_name} failed for item {item.id}: {e}"
                )
    # Take the highest score from all filters (highest signal wins)
    filter_score = max(scores) if scores else 0.0
    filter_reason = "; ".join(reasons) if reasons else "No specific reason"
    is_relevant = filter_score >= RELEVANCE_THRESHOLD
    return filter_score, filter_reason, is_relevant


async def store_item(item, storage: NewsStore) -> None:
    """Add the item to storage."""
    await storage.add_item(item)


def summarize_results(results: List[Dict]) -> Dict:
    """Aggregate stats for the response."""
    summary = {
        "total_received": len(results),
        "accepted": 0,
        "rejected": 0,
        "duplicates": 0,
        "errors": 0
    }
    for r in results:
        summary[r["result"]] += 1
    return summary


async def process_item(item, storage, filter_registry) -> Dict:
    """Process a single item: validate, check duplicate, filter, store if accepted."""
    try:
        if not validate_item_fields(item):
            logger.warning(f"Invalid item skipped: missing required fields - {item.id}")
            return {"result": "errors", "id": item.id, "reason": "missing fields"}
        if await is_duplicate(item, storage):
            logger.info(f"Duplicate item skipped: {item.id}")
            return {"result": "duplicates", "id": item.id, "reason": "duplicate"}
        score, reason, is_relevant = await filter_item(item, filter_registry)
        if is_relevant:
            await store_item(item, storage)
            logger.info(
                f"✅ Item accepted: {item.id} (score: {score:.3f}) - {reason}"
            )
            return {"result": "accepted", "id": item.id, "score": score, "reason": reason}
        else:
            logger.info(
                f"❌ Item rejected: {item.id} (score: {score:.3f}) - {reason}"
            )
            return {"result": "rejected", "id": item.id, "score": score, "reason": reason}
    except Exception as e:
        logger.error(f"Error processing item {item.id}: {e}")
        return {"result": "errors", "id": item.id, "reason": str(e)}


router = APIRouter()


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=200,
    tags=["Ingest"],
    responses={
        200: {"description": "News items processed successfully"},
        400: {
            "model": BadRequestErrorResponse,
            "description": (
                "Bad request - no items provided or invalid request format"
            )
        },
        422: {
            "model": ValidationErrorResponse,
            "description": (
                "Validation error - invalid item data or schema violations"
            )
        },
        500: {
            "model": InternalServerErrorResponse,
            "description": "Internal server error during processing"
        }
    }
)
async def ingest_news(
    request_data: IngestRequest,
    storage: NewsStore = Depends(get_storage),
    filter_registry: FilterRegistry = Depends(get_filter_registry),
    source_registry: SourceRegistry = Depends(get_source_registry),
) -> IngestResponse:
    """Ingest and process raw news events with AI-powered filtering and storage.

    This is the primary data ingestion endpoint that processes news items from various sources.
    Each item goes through a comprehensive pipeline:

    1. **Validation**: Ensures all required fields are present and valid
    2. **Duplicate Detection**: Checks if the item already exists in storage
    3. **AI Filtering**: Applies semantic and keyword filters to determine relevance
    4. **Storage**: Stores accepted items for later retrieval

    The endpoint returns detailed statistics including:
    - Total items received
    - Number of items accepted/rejected
    - Duplicate detection results
    - Processing errors

    This endpoint implements the exact API contract
    and provides deterministic results for given input batches.

    **Example Use Cases:**
    - Batch ingestion from RSS feeds
    - Real-time news processing
    - Test data injection for evaluation
    """
    try:
        logger.info(f"📥 Ingesting {len(request_data.items)} news items")
        if not request_data.items:
            raise HTTPException(status_code=400, detail="No items provided in request")
        results = []
        for item in request_data.items:
            result = await process_item(item, storage, filter_registry)
            results.append(result)
        summary_data = summarize_results(results)
        summary = IngestSummary(**summary_data)
        logger.info(f"📊 Ingest summary: {summary_data}")
        return IngestResponse(
            status="ACK",
            message="News items processed successfully",
            summary=summary
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during ingest: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during ingest processing"
        )
