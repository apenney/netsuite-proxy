"""
Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_health_check(client: TestClient) -> None:
    """Test basic health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data


def test_detailed_health_check(client: TestClient) -> None:
    """Test detailed health check endpoint."""

    response = client.get("/api/health/detailed")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "debug" in data

    # Check NetSuite configuration details
    assert "netsuite" in data
    netsuite_data = data["netsuite"]
    assert netsuite_data["account"] == "TEST123"
    assert "api_version" in netsuite_data
    assert "auth_configured" in netsuite_data
    assert "auth_type" in netsuite_data
    assert "restlet_configured" in netsuite_data


def test_health_check_with_oauth_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test health check shows correct auth type for OAuth."""
    # Set OAuth environment variables (using double underscore for nested config)
    monkeypatch.setenv("SECRET_KEY_BASE", "test-secret")
    monkeypatch.setenv("NETSUITE__ACCOUNT", "TEST123")
    monkeypatch.setenv("NETSUITE__CONSUMER_KEY", "key")
    monkeypatch.setenv("NETSUITE__CONSUMER_SECRET", "secret")
    monkeypatch.setenv("NETSUITE__TOKEN_ID", "token")
    monkeypatch.setenv("NETSUITE__TOKEN_SECRET", "token_secret")

    # Clear the settings cache
    get_settings.cache_clear()
    
    # Import and create client after setting env vars
    from app.main import app
    client = TestClient(app)

    response = client.get("/api/health/detailed")
    assert response.status_code == 200

    data = response.json()
    assert data["netsuite"]["auth_configured"] is True
    assert data["netsuite"]["auth_type"] == "oauth"
