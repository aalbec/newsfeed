"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient
from sentence_transformers import SentenceTransformer

from src.api.main import app
from src.sources import RSSSource

# Global model cache to avoid repeated loading
_model_cache = {}
_rss_data_cache = {}


@pytest.fixture(scope="session")
def cached_semantic_model():
    """Shared semantic model cache for all integration tests.

    This fixture loads the sentence transformer model once and reuses it
    across all tests, significantly speeding up integration tests.
    """
    model_name = 'all-MiniLM-L6-v2'

    if model_name not in _model_cache:
        print(f"\n🔄 Loading semantic model '{model_name}' for integration tests...")
        _model_cache[model_name] = SentenceTransformer(model_name)
        print("✅ Model loaded successfully!")

    return _model_cache[model_name]


@pytest.fixture(scope="session")
def cached_rss_data():
    """Shared RSS data cache for all integration tests.

    This fixture fetches RSS data once and reuses it across all tests,
    avoiding repeated network requests.
    """
    cache_key = "rss_data"

    if cache_key not in _rss_data_cache:
        print("\n🔄 Fetching RSS data for integration tests...")

        # Use asyncio to run the async fetch in a synchronous context
        import asyncio

        async def fetch_rss_data():
            # Fetch from both RSS sources
            toms_hardware = RSSSource(
                "tomshardware",
                "https://www.tomshardware.com/feeds/all",
                max_items=5
            )
            ars_technica = RSSSource(
                "arstechnica",
                "https://feeds.arstechnica.com/arstechnica/index",
                max_items=5
            )

            # Get items from both sources
            toms_items = await toms_hardware.fetch_items()
            ars_items = await ars_technica.fetch_items()

            # Combine and return
            return toms_items + ars_items

        # Run the async function and cache the result
        all_items = asyncio.run(fetch_rss_data())
        _rss_data_cache[cache_key] = all_items

        print(f"✅ Fetched {len(all_items)} RSS items successfully!")

    return _rss_data_cache[cache_key]


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)
