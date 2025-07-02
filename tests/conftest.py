"""
Shared pytest fixtures and configuration.
"""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before any imports
os.environ["SECRET_KEY_BASE"] = "test-secret-key-for-tests"
os.environ["NETSUITE__ACCOUNT"] = "TEST123"  # Note the double underscore for nested config

# Clear any cached settings
from app.core.config import get_settings

get_settings.cache_clear()


@pytest.fixture
def client() -> Generator[TestClient]:
    """Create a test client with mocked settings."""
    # Import app after env vars are set
    from app.main import app  # noqa: PLC0415

    with TestClient(app) as test_client:
        yield test_client
