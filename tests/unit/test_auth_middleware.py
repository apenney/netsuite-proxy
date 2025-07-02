"""Tests for NetSuite authentication middleware."""

from typing import Annotated, Any

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from app.api.middleware import NetSuiteAuthMiddleware, get_netsuite_auth
from app.main import app


class TestNetSuiteAuthMiddleware:
    """Tests for NetSuite authentication middleware."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_app(self) -> FastAPI:
        """Create a test app with auth endpoint."""
        from fastapi.middleware.cors import CORSMiddleware  # noqa: PLC0415

        from app.api.middleware.logging import RequestLoggingMiddleware  # noqa: PLC0415

        test_app = FastAPI()

        # Add middlewares in correct order (same as main app)
        test_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        test_app.add_middleware(RequestLoggingMiddleware)
        test_app.add_middleware(NetSuiteAuthMiddleware)

        # Add a test endpoint that requires auth
        @test_app.get("/test-auth")
        async def test_auth(  # pyright: ignore[reportUnusedFunction]
            auth: Annotated[Any, Depends(get_netsuite_auth)],
        ) -> dict[str, Any]:
            return {"auth": auth}

        return test_app

    def test_exempt_paths_no_auth_required(self, client: TestClient) -> None:
        """Test that exempt paths don't require authentication."""
        # Health endpoints should work without auth
        response = client.get("/api/health")
        assert response.status_code == 200

        response = client.get("/api/health/detailed")
        assert response.status_code == 200

        # API docs should work without auth
        response = client.get("/api/docs")
        assert response.status_code == 200

    def test_missing_account_header(self, test_app: FastAPI) -> None:
        """Test that missing account header returns 400."""
        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get("/test-auth")

        assert response.status_code == 400
        assert "Missing required header: X-NetSuite-Account" in response.json()["detail"]

    def test_missing_auth_credentials(self, test_app: FastAPI) -> None:
        """Test that missing auth credentials returns 401."""
        client = TestClient(test_app, raise_server_exceptions=False)
        headers = {"X-NetSuite-Account": "TEST123"}
        response = client.get("/test-auth", headers=headers)

        assert response.status_code == 401
        assert "No valid authentication credentials provided" in response.json()["detail"]

    def test_password_auth_success(self, test_app: FastAPI) -> None:
        """Test successful password-based authentication."""
        client = TestClient(test_app)
        headers = {
            "X-NetSuite-Account": "TEST123",
            "X-NetSuite-Email": "test@example.com",
            "X-NetSuite-Password": "secret",
            "X-NetSuite-Role": "3",
            "X-NetSuite-Api-Version": "2024_2",
        }
        response = client.get("/test-auth", headers=headers)

        assert response.status_code == 200
        auth = response.json()["auth"]
        assert auth["account"] == "TEST123"
        assert auth["email"] == "test@example.com"
        assert auth["password"] == "secret"
        assert auth["role_id"] == "3"
        assert auth["api_version"] == "2024_2"
        assert auth["auth_type"] == "password"

    def test_oauth_auth_success(self, test_app: FastAPI) -> None:
        """Test successful OAuth authentication."""
        client = TestClient(test_app)
        headers = {
            "X-NetSuite-Account": "TEST123",
            "X-NetSuite-Consumer-Key": "consumer_key",
            "X-NetSuite-Consumer-Secret": "consumer_secret",
            "X-NetSuite-Token-Id": "token_id",
            "X-NetSuite-Token-Secret": "token_secret",
            "X-NetSuite-Api-Version": "2024_2",
        }
        response = client.get("/test-auth", headers=headers)

        assert response.status_code == 200
        auth = response.json()["auth"]
        assert auth["account"] == "TEST123"
        assert auth["consumer_key"] == "consumer_key"
        assert auth["consumer_secret"] == "consumer_secret"
        assert auth["token_id"] == "token_id"
        assert auth["token_secret"] == "token_secret"
        assert auth["api_version"] == "2024_2"
        assert auth["auth_type"] == "oauth"

    def test_partial_oauth_credentials_fail(self, test_app: FastAPI) -> None:
        """Test that partial OAuth credentials fail."""
        client = TestClient(test_app, raise_server_exceptions=False)
        headers = {
            "X-NetSuite-Account": "TEST123",
            "X-NetSuite-Consumer-Key": "consumer_key",
            "X-NetSuite-Consumer-Secret": "consumer_secret",
            # Missing token_id and token_secret
        }
        response = client.get("/test-auth", headers=headers)

        assert response.status_code == 401
        assert "No valid authentication credentials provided" in response.json()["detail"]

    def test_password_auth_without_role(self, test_app: FastAPI) -> None:
        """Test password auth works without role ID."""
        client = TestClient(test_app)
        headers = {
            "X-NetSuite-Account": "TEST123",
            "X-NetSuite-Email": "test@example.com",
            "X-NetSuite-Password": "secret",
            # No role header
        }
        response = client.get("/test-auth", headers=headers)

        assert response.status_code == 200
        auth = response.json()["auth"]
        assert auth["auth_type"] == "password"
        assert auth["role_id"] is None

    def test_get_netsuite_auth_dependency(self) -> None:
        """Test the get_netsuite_auth dependency function."""
        # Create a mock request with auth
        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/test",
            }
        )
        request.state.netsuite_auth = {"account": "TEST123", "auth_type": "oauth"}

        auth = get_netsuite_auth(request)
        assert auth is not None
        assert auth.get("account") == "TEST123"
        assert auth.get("auth_type") == "oauth"

    def test_get_netsuite_auth_dependency_missing(self) -> None:
        """Test get_netsuite_auth when auth is missing."""
        # Create a mock request without auth
        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/test",
            }
        )

        with pytest.raises(Exception) as exc_info:
            get_netsuite_auth(request)

        assert "NetSuite authentication not available" in str(exc_info.value)
