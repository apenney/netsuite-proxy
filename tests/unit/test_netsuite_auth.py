"""Tests for NetSuite authentication service."""

import pytest

from app.core.config import NetSuiteConfig
from app.core.exceptions import AuthenticationError
from app.services.netsuite.auth import NetSuiteAuthService


class TestNetSuiteAuthService:
    """Tests for NetSuiteAuthService."""

    def test_init_with_oauth_config(self):
        """Test initialization with OAuth configuration."""
        config = NetSuiteConfig(
            account="TEST123",
            consumer_key="key",
            consumer_secret="secret",
            token_id="token",
            token_secret="tokensecret",
        )

        service = NetSuiteAuthService(config)

        assert service.config == config
        assert service._soap_client is None
        assert service._restlet_client is None

    def test_init_with_password_config(self):
        """Test initialization with password configuration."""
        config = NetSuiteConfig(
            account="TEST123",
            email="test@example.com",
            password="password",
        )

        service = NetSuiteAuthService(config)

        assert service.config == config
        assert service._soap_client is None
        assert service._restlet_client is None

    def test_get_account_info_production(self):
        """Test get_account_info for production account."""
        config = NetSuiteConfig(
            account="TEST123",
            email="test@example.com",
            password="password",
        )
        service = NetSuiteAuthService(config)

        info = service.get_account_info()

        assert info == {
            "account": "TEST123",
            "auth_type": "password",
            "api_version": "2024_2",
            "environment": "production",
            "has_restlet": False,
        }

    def test_get_account_info_sandbox(self):
        """Test get_account_info for sandbox account."""
        config = NetSuiteConfig(
            account="TEST123_SB1",
            consumer_key="key",
            consumer_secret="secret",
            token_id="token",
            token_secret="tokensecret",
            script_id="123",
            deploy_id="1",
        )
        service = NetSuiteAuthService(config)

        info = service.get_account_info()

        assert info == {
            "account": "TEST123_SB1",
            "auth_type": "oauth",
            "api_version": "2024_2",
            "environment": "sandbox",
            "has_restlet": True,
        }

    def test_determine_environment(self):
        """Test environment determination."""
        # Production accounts
        for account in ["TEST123", "PROD456", "LIVE789"]:
            config = NetSuiteConfig(account=account)
            service = NetSuiteAuthService(config)
            assert service._determine_environment() == "production"

        # Sandbox accounts
        for account in ["TEST_SB1", "TEST_SB2", "TEST-SB1", "TEST-SB2"]:
            config = NetSuiteConfig(account=account)
            service = NetSuiteAuthService(config)
            assert service._determine_environment() == "sandbox"

    def test_restlet_client_missing_config(self):
        """Test restlet_client raises error when config is missing."""
        config = NetSuiteConfig(
            account="TEST123",
            email="test@example.com",
            password="password",
        )
        service = NetSuiteAuthService(config)

        with pytest.raises(ValueError, match="RESTlet configuration missing"):
            _ = service.restlet_client

    def test_from_headers_oauth(self):
        """Test creating service from OAuth headers."""
        headers = {
            "x-netsuite-account": "TEST123",
            "x-netsuite-consumer-key": "key",
            "x-netsuite-consumer-secret": "secret",
            "x-netsuite-token-id": "token",
            "x-netsuite-token-secret": "tokensecret",
            "x-netsuite-api-version": "2023_1",
        }

        service = NetSuiteAuthService.from_headers(headers)

        assert service.config.account == "TEST123"
        assert service.config.auth_type == "oauth"
        assert service.config.consumer_key == "key"
        assert service.config.consumer_secret == "secret"
        assert service.config.token_id == "token"
        assert service.config.token_secret == "tokensecret"
        assert service.config.api == "2023_1"

    def test_from_headers_password(self):
        """Test creating service from password headers."""
        headers = {
            "x-netsuite-account": "TEST123",
            "x-netsuite-email": "test@example.com",
            "x-netsuite-password": "password",
            "x-netsuite-role": "3",
        }

        service = NetSuiteAuthService.from_headers(headers)

        assert service.config.account == "TEST123"
        assert service.config.auth_type == "password"
        assert service.config.email == "test@example.com"
        assert service.config.password == "password"
        assert service.config.role == "3"
        assert service.config.api == "2024_2"  # Default

    def test_from_headers_with_restlet_config(self):
        """Test creating service with RESTlet configuration from headers."""
        headers = {
            "x-netsuite-account": "TEST123",
            "x-netsuite-email": "test@example.com",
            "x-netsuite-password": "password",
            "x-netsuite-script-id": "customscript123",
            "x-netsuite-deploy-id": "customdeploy1",
        }

        service = NetSuiteAuthService.from_headers(headers)

        assert service.config.script_id == "customscript123"
        assert service.config.deploy_id == "customdeploy1"

    def test_from_headers_missing_account(self):
        """Test from_headers raises error when account is missing."""
        headers = {
            "x-netsuite-email": "test@example.com",
            "x-netsuite-password": "password",
        }

        with pytest.raises(
            AuthenticationError, match="Missing required header: X-NetSuite-Account"
        ):
            NetSuiteAuthService.from_headers(headers)

    def test_from_headers_missing_credentials(self):
        """Test from_headers raises error when credentials are missing."""
        headers = {
            "x-netsuite-account": "TEST123",
        }

        with pytest.raises(AuthenticationError, match="Missing authentication credentials"):
            NetSuiteAuthService.from_headers(headers)

    def test_from_headers_incomplete_oauth(self):
        """Test from_headers raises error when OAuth credentials are incomplete."""
        headers = {
            "x-netsuite-account": "TEST123",
            "x-netsuite-consumer-key": "key",
            "x-netsuite-consumer-secret": "secret",
            # Missing token-id and token-secret
        }

        with pytest.raises(AuthenticationError, match="Missing authentication credentials"):
            NetSuiteAuthService.from_headers(headers)
