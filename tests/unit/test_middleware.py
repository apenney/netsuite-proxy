"""Tests for API middleware."""


import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestRequestLoggingMiddleware:
    """Tests for request logging middleware."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_request_id_header(self, client: TestClient) -> None:
        """Test that X-Request-ID header is added to response."""
        response = client.get("/api/health")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID format

    def test_multiple_requests_have_different_ids(self, client: TestClient) -> None:
        """Test that each request gets a unique ID."""
        response1 = client.get("/api/health")
        response2 = client.get("/api/health")

        assert response1.status_code == 200
        assert response2.status_code == 200

        id1 = response1.headers["X-Request-ID"]
        id2 = response2.headers["X-Request-ID"]

        assert id1 != id2

    def test_request_with_query_params(self, client: TestClient) -> None:
        """Test that requests with query params work correctly."""
        response = client.get("/api/health?test=true&foo=bar")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_request_with_headers(self, client: TestClient) -> None:
        """Test that requests with various headers work correctly."""
        headers = {
            "Authorization": "Bearer secret-token",
            "Cookie": "session=secret",
            "User-Agent": "TestClient",
            "X-Custom-Header": "custom-value",
        }

        response = client.get("/api/health", headers=headers)

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_request_error_handling(self, client: TestClient) -> None:
        """Test that middleware handles errors properly."""
        # Try to access a non-existent endpoint
        # Use an endpoint that's exempt from auth to test 404
        response = client.get("/api/health/nonexistent")

        assert response.status_code == 404
        # Even error responses should have request ID
        assert "X-Request-ID" in response.headers
