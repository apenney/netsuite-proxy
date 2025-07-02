"""
Shared pytest fixtures and configuration.
"""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before any imports
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY_BASE"] = "test-secret-key-for-tests"


@pytest.fixture
def client() -> Generator[TestClient]:
    """Create a test client with mocked settings."""
    # Import app after env vars are set
    from app.main import app  # noqa: PLC0415

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear settings cache before each test."""
    from app.core.config import get_settings  # noqa: PLC0415

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
