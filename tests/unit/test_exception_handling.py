"""Tests for exception handling and status code mapping."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import (
    AuthenticationError,
    NetSuiteError,
    NetSuitePermissionError,
    PageBoundsError,
    RateLimitError,
    RecordNotFoundError,
    ValidationError,
)
from app.main import create_app


class TestExceptionHandling:
    """Test exception handling and status code mapping."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create test app with exception handlers."""
        return create_app()

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create test client."""

        # Add test endpoints that raise exceptions
        @app.get("/api/test/auth-error")
        async def raise_auth_error():  # pyright: ignore[reportUnusedFunction]
            raise AuthenticationError("Invalid credentials")

        @app.get("/api/test/permission-error")
        async def raise_permission_error():  # pyright: ignore[reportUnusedFunction]
            raise NetSuitePermissionError("Access denied")

        @app.get("/api/test/not-found")
        async def raise_not_found():  # pyright: ignore[reportUnusedFunction]
            raise RecordNotFoundError("Customer", "123")

        @app.get("/api/test/page-bounds")
        async def raise_page_bounds():  # pyright: ignore[reportUnusedFunction]
            raise PageBoundsError(10, 5)

        @app.get("/api/test/validation-error")
        async def raise_validation():  # pyright: ignore[reportUnusedFunction]
            raise ValidationError("email", "invalid@", "Invalid email format")

        @app.get("/api/test/rate-limit")
        async def raise_rate_limit():  # pyright: ignore[reportUnusedFunction]
            raise RateLimitError(60)

        @app.get("/api/test/generic-error")
        async def raise_generic():  # pyright: ignore[reportUnusedFunction]
            raise NetSuiteError("Something went wrong")

        return TestClient(app)

    def test_authentication_error_returns_401(self, client: TestClient):
        """Test that AuthenticationError returns 401."""
        response = client.get("/api/test/auth-error")
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "Invalid credentials"
        assert data["error_type"] == "AuthenticationError"
        assert data["details"] == {}

    def test_permission_error_returns_403(self, client: TestClient):
        """Test that NetSuitePermissionError returns 403."""
        response = client.get("/api/test/permission-error")
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "Access denied"
        assert data["error_type"] == "NetSuitePermissionError"

    def test_not_found_error_returns_404(self, client: TestClient):
        """Test that RecordNotFoundError returns 404."""
        response = client.get("/api/test/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Customer with ID 123 not found"
        assert data["error_type"] == "RecordNotFoundError"
        assert data["details"]["record_type"] == "Customer"
        assert data["details"]["record_id"] == "123"

    def test_page_bounds_error_returns_400(self, client: TestClient):
        """Test that PageBoundsError returns 400."""
        response = client.get("/api/test/page-bounds")
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Page 10 is out of bounds. Total pages: 5"
        assert data["error_type"] == "PageBoundsError"
        assert data["details"]["page"] == 10
        assert data["details"]["total_pages"] == 5

    def test_validation_error_returns_400(self, client: TestClient):
        """Test that ValidationError returns 400."""
        response = client.get("/api/test/validation-error")
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Validation error for field 'email': Invalid email format"
        assert data["error_type"] == "ValidationError"
        assert data["details"]["field"] == "email"
        assert data["details"]["value"] == "invalid@"
        assert data["details"]["reason"] == "Invalid email format"

    def test_rate_limit_error_returns_429(self, client: TestClient):
        """Test that RateLimitError returns 429."""
        response = client.get("/api/test/rate-limit")
        assert response.status_code == 429
        data = response.json()
        assert data["error"] == "NetSuite API rate limit exceeded. Retry after 60 seconds"
        assert data["error_type"] == "RateLimitError"
        assert data["details"]["retry_after"] == 60

    def test_generic_error_returns_500(self, client: TestClient):
        """Test that generic NetSuiteError returns 500."""
        response = client.get("/api/test/generic-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Something went wrong"
        assert data["error_type"] == "NetSuiteError"
        assert data["details"] == {}
