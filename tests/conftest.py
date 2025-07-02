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
def clear_settings_cache(monkeypatch: pytest.MonkeyPatch):
    """Clear settings cache before each test and reset NetSuite env vars."""

    from app.core.config import get_settings  # noqa: PLC0415

    # Clear any NetSuite environment variables to prevent test pollution
    netsuite_env_vars = [
        "NETSUITE_ACCOUNT",
        "NETSUITE_API",
        "NETSUITE_EMAIL",
        "NETSUITE_PASSWORD",
        "NETSUITE_CONSUMER_KEY",
        "NETSUITE_CONSUMER_SECRET",
        "NETSUITE_TOKEN_ID",
        "NETSUITE_TOKEN_SECRET",
        "NETSUITE_SCRIPT_ID",
        "NETSUITE_DEPLOY_ID",
        "NETSUITE_ROLE",
        "NETSUITE__ACCOUNT",
        "NETSUITE__API",
        "NETSUITE__EMAIL",
        "NETSUITE__PASSWORD",
        "NETSUITE__CONSUMER_KEY",
        "NETSUITE__CONSUMER_SECRET",
        "NETSUITE__TOKEN_ID",
        "NETSUITE__TOKEN_SECRET",
        "NETSUITE__SCRIPT_ID",
        "NETSUITE__DEPLOY_ID",
        "NETSUITE__ROLE",
    ]

    for var in netsuite_env_vars:
        monkeypatch.delenv(var, raising=False)

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
