"""Pytest configuration for integration tests."""

import os

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture(scope="session", autouse=True)
def set_test_mode():
    """Set TESTING environment variable for the entire test session."""
    os.environ["TESTING"] = "true"
    yield
    del os.environ["TESTING"]


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app in test mode.

    This fixture relies on the `set_test_mode` fixture to ensure that the
    application starts in a lightweight mode, without loading heavy models or
    starting background services. This makes integration tests significantly
    faster and more reliable.
    """
    with TestClient(app) as test_client:
        yield test_client
