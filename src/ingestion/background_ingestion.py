"""Simplified background ingestion service for continuous news fetching.

This module implements a simple background ingestion that fetches news from sources
at regular intervals, applies filtering, and stores relevant items.

Key Features:
- Simple background fetching from registered sources
- Integration with existing registry pattern
- Basic error handling and logging
- Thread-safe operations
"""

import asyncio
import threading
import time
from typing import Dict, List

from loguru import logger

from src.models.news_item import NewsItem
from src.registry import FilterRegistry, SourceRegistry
from src.storage import NewsStore


class BackgroundIngestionService:
    """Simplified background service for continuous news ingestion.

    This service implements the "continuously fetch IT-related news" requirement
    with a simple approach that's easier to understand and maintain.
    """

    def __init__(
        self,
        storage: NewsStore,
        source_registry: SourceRegistry,
        filter_registry: FilterRegistry,
    ):
        """Initialize the background ingestion service.

        Args:
            storage: Storage instance for persisting items
            source_registry: Registry containing news sources
            filter_registry: Registry containing filters
        """
        self.storage = storage
        self.source_registry = source_registry
        self.filter_registry = filter_registry

        # Simple state management
        self.running = False
        self.thread = None

        # Track processed items to avoid duplicates
        self.processed_items: set[str] = set()

        logger.info("BackgroundIngestionService initialized")

    async def start(self) -> None:
        """Start the background ingestion service."""
        try:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop)
            self.thread.daemon = True  # Don't block app shutdown
            self.thread.start()

            logger.info("✅ Background ingestion service started")

            # Run initial fetch
            await self._fetch_all_sources()

        except Exception as e:
            logger.error(f"❌ Failed to start background ingestion service: {e}")
            raise

    async def stop(self) -> None:
        """Stop the background ingestion service."""
        try:
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)  # Wait max 5 seconds
                logger.info("🛑 Background ingestion service stopped")

        except Exception as e:
            logger.error(f"❌ Error stopping background ingestion service: {e}")

    def _run_loop(self) -> None:
        """Main background loop that runs in a separate thread."""
        while self.running:
            try:
                # Run the async fetch in the thread
                asyncio.run(self._fetch_all_sources())
            except Exception as e:
                logger.error(f"❌ Background ingestion error: {e}")

            # Wait 5 minutes before next fetch
            time.sleep(300)

    async def _fetch_all_sources(self) -> None:
        """Fetch from all registered sources."""
        logger.info("🔄 Starting background fetch from all sources")

        try:
            sources = self.source_registry.list_sources()

            for source_name in sources:
                try:
                    source = self.source_registry.get_source(source_name)
                    if source:
                        items = await source.fetch_items()
                        await self._process_items(items, source_name)
                except Exception as e:
                    logger.error(f"❌ Error fetching from {source_name}: {e}")

            logger.info("✅ Background fetch complete")

        except Exception as e:
            logger.error(f"❌ Error in background fetch: {e}")

    async def _process_items(self, items: List[NewsItem], source_name: str) -> None:
        """Process items from a source: filter and store relevant ones."""
        if not items:
            return

        accepted_count = 0

        for item in items:
            try:
                # Skip if already processed
                if item.id in self.processed_items:
                    continue

                # Apply filters
                score, reason, is_relevant = await self._apply_filters(item)

                if is_relevant:
                    # Store the item
                    await self.storage.add_item(item)
                    accepted_count += 1
                    logger.debug(f"✅ Accepted item {item.id} (score: {score:.2f})")
                else:
                    logger.debug(f"❌ Rejected item {item.id} (score: {score:.2f})")

                # Mark as processed
                self.processed_items.add(item.id)

            except Exception as e:
                logger.error(f"❌ Error processing item {item.id}: {e}")

        if accepted_count > 0:
            logger.info(
                f"📊 Processed {len(items)} items from {source_name}, "
                f"accepted {accepted_count}"
            )

    async def _apply_filters(self, item: NewsItem) -> tuple[float, str, bool]:
        """Apply filters to a news item. Return (score, reason, is_relevant)."""
        try:
            filter_names = self.filter_registry.list_filters()
            if not filter_names:
                logger.warning("⚠️ No filters available - accepting all items")
                return 1.0, "No filters configured", True

            total_score = 0.0
            reasons = []

            for filter_name in filter_names:
                filter_instance = self.filter_registry.get_filter(filter_name)
                if filter_instance:
                    try:
                        filtered_items = await filter_instance.filter([item])
                        if filtered_items:
                            filtered_item = filtered_items[0]
                            total_score += filtered_item.relevance_score
                            breakdown = filtered_item.score_breakdown
                            if breakdown:
                                reasons.append(f"{filter_name}: {breakdown}")
                    except Exception as e:
                        logger.error(f"❌ Filter {filter_name} failed for item {item.id}: {e}")

            filter_score = total_score / len(filter_names) if filter_names else 0.0
            filter_reason = "; ".join(reasons) if reasons else "No specific reason"

            # Use same threshold as ingest endpoint
            import os
            relevance_threshold = float(
                os.getenv("RELEVANCE_THRESHOLD", "0.1")
            )
            is_relevant = filter_score >= relevance_threshold

            return filter_score, filter_reason, is_relevant

        except Exception as e:
            logger.error(f"❌ Error applying filters to item {item.id}: {e}")
            return 0.0, f"Filter error: {e}", False

    def get_stats(self) -> Dict:
        """Get basic statistics for monitoring."""
        return {
            "running": self.running,
            "processed_items_count": len(self.processed_items),
            "thread_alive": self.thread.is_alive() if self.thread else False
        }


# TODO: Future Enhancements (Post-MVP)
# =================================
#
# 1. Circuit Breaker & Error Handling
#    - Prevent repeated failures from a single source from affecting the whole
#      system.
#    - Add automatic retries and fallback to mock data if a source fails.
#
# 2. Configurable Fetch Intervals
#    - Allow different fetch intervals per source via config or environment
#      variables.
#
# 3. Batch Processing
#    - Support batch processing for large numbers of items to improve
#      efficiency.
#
# 4. Performance & Health Monitoring
#    - Add basic metrics (fetch times, error counts) and simple health checks
#      for sources.
#
# 5. Move Hardcoded Values to Config
#    - Use config files or environment variables for all tunable parameters.
