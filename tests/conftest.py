"""
Shared pytest fixtures and configuration.
"""

import os
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.types import HeaderDict

# Set test environment variables before any imports
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY_BASE"] = "test-secret-key-for-tests-that-is-32-characters"

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture
def client() -> Generator[TestClient]:
    """Create a test client."""
    # Clear cache to ensure fresh settings
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    # Clear cache after test
    get_settings.cache_clear()


@pytest.fixture
def netsuite_auth_headers() -> HeaderDict:
    """Standard NetSuite password auth headers for testing."""
    return {
        "X-NetSuite-Account": "TEST123",
        "X-NetSuite-Email": "test@example.com",
        "X-NetSuite-Password": "test-password",
    }


@pytest.fixture
def netsuite_oauth_headers() -> HeaderDict:
    """Standard NetSuite OAuth headers for testing."""
    return {
        "X-NetSuite-Account": "TEST123",
        "X-NetSuite-Consumer-Key": "test-consumer-key",
        "X-NetSuite-Consumer-Secret": "test-consumer-secret",
        "X-NetSuite-Token-Id": "test-token-id",
        "X-NetSuite-Token-Secret": "test-token-secret",
    }


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch):
    """Helper to mock settings with sensible defaults."""

    def _mock_settings(**kwargs: Any) -> None:
        defaults = {
            "SECRET_KEY_BASE": "test-secret-key-for-tests-that-is-32-characters",
            "NETSUITE__ACCOUNT": "TEST123",
            "NETSUITE__API": "2024_2",
            "ENVIRONMENT": "test",
            "DEBUG": "false",
        }
        defaults.update(kwargs)

        for key, value in defaults.items():
            monkeypatch.setenv(key, str(value))

        # Clear cache to pick up new env vars
        get_settings.cache_clear()

    return _mock_settings
