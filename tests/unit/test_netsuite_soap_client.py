"""Tests for NetSuite SOAP client."""

# pyright: reportPrivateUsage=false

from unittest.mock import Mock, patch

import pytest

from app.core.config import NetSuiteConfig
from app.core.exceptions import (
    AuthenticationError,
    NetSuiteError,
    NetSuiteTimeoutError,
    SOAPFaultError,
)
from app.services.netsuite.soap.client import NetSuiteSoapClient


class TestNetSuiteSoapClient:
    """Tests for NetSuiteSoapClient."""

    def test_init(self):
        """Test client initialization."""
        config = NetSuiteConfig(
            account="TEST123",
            email="test@example.com",
            password="password",
        )

        client = NetSuiteSoapClient(config)

        assert client.config == config
        assert client._client is None
        assert client._service is None
        assert client.settings.xml_huge_tree is True
        assert client.settings.strict is False
        # Transport timeout is set via constructor, not attribute
        assert client.transport is not None

    def test_wsdl_url_generation(self):
        """Test WSDL URL generation."""
        config = NetSuiteConfig(
            account="TEST123",
            api="2024_2",
        )
        client = NetSuiteSoapClient(config)

        assert client.wsdl_url == "https://webservices.netsuite.com/wsdl/v2024.2/netsuite.wsdl"

    def test_wsdl_url_with_different_api_version(self):
        """Test WSDL URL with different API version."""
        config = NetSuiteConfig(
            account="TEST123",
            api="2023_1",
        )
        client = NetSuiteSoapClient(config)

        assert client.wsdl_url == "https://webservices.netsuite.com/wsdl/v2023.1/netsuite.wsdl"

    def test_create_passport_password_auth(self):
        """Test passport creation for password authentication."""
        config = NetSuiteConfig(
            account="TEST123",
            email="test@example.com",
            password="password",
            role="3",
        )
        client = NetSuiteSoapClient(config)

        passport = client._create_passport()

        assert passport == {
            "account": "TEST123",
            "email": "test@example.com",
            "password": "password",
            "role": {"internalId": "3"},
        }

    def test_create_passport_password_auth_missing_credentials(self):
        """Test passport creation fails when password credentials are missing."""
        config = NetSuiteConfig(
            account="TEST123",
            email="test@example.com",
            # Missing password
        )
        client = NetSuiteSoapClient(config)

        # When password is missing, auth_type is "none"
        with pytest.raises(AuthenticationError, match="Unsupported auth type: none"):
            client._create_passport()

    @patch("app.services.netsuite.soap.client.NetSuiteSoapClient._generate_nonce")
    @patch("app.services.netsuite.soap.client.NetSuiteSoapClient._get_timestamp")
    @patch("app.services.netsuite.soap.client.NetSuiteSoapClient._generate_signature")
    def test_create_passport_oauth_auth(
        self, mock_signature: Mock, mock_timestamp: Mock, mock_nonce: Mock
    ):
        """Test passport creation for OAuth authentication."""
        mock_nonce.return_value = "test-nonce"
        mock_timestamp.return_value = "1234567890"
        mock_signature.return_value = "test-signature"

        config = NetSuiteConfig(
            account="TEST123",
            consumer_key="key",
            consumer_secret="secret",
            token_id="token",
            token_secret="tokensecret",
        )
        client = NetSuiteSoapClient(config)

        passport = client._create_passport()

        assert passport == {
            "account": "TEST123",
            "consumerKey": "key",
            "token": "token",
            "nonce": "test-nonce",
            "timestamp": "1234567890",
            "signature": {
                "algorithm": "HMAC-SHA256",
                "value": "test-signature",
            },
        }

    def test_create_passport_oauth_auth_missing_credentials(self):
        """Test passport creation fails when OAuth credentials are missing."""
        # The validation now happens at config creation time
        with pytest.raises(ValueError, match="OAuth authentication requires all four fields"):
            NetSuiteConfig(
                account="TEST123",
                consumer_key="key",
                consumer_secret="secret",
                # Missing token_id and token_secret
            )

    def test_create_passport_no_auth(self):
        """Test passport creation fails when no auth is configured."""
        config = NetSuiteConfig(account="TEST123")
        client = NetSuiteSoapClient(config)

        with pytest.raises(AuthenticationError, match="Unsupported auth type: none"):
            client._create_passport()

    def test_handle_soap_error_timeout(self):
        """Test handling timeout errors."""
        config = NetSuiteConfig(account="TEST123")
        client = NetSuiteSoapClient(config)

        error = Exception("Connection timeout occurred")

        with pytest.raises(NetSuiteTimeoutError):
            client._handle_soap_error(error)

    def test_handle_soap_error_authentication(self):
        """Test handling authentication errors."""
        config = NetSuiteConfig(account="TEST123")
        client = NetSuiteSoapClient(config)

        error = Exception("Invalid login attempt")

        with pytest.raises(AuthenticationError, match="NetSuite authentication failed"):
            client._handle_soap_error(error)

    def test_handle_soap_error_fault(self):
        """Test handling SOAP fault errors."""
        config = NetSuiteConfig(account="TEST123")
        client = NetSuiteSoapClient(config)

        error = Mock()
        error.fault = Mock()
        error.fault.faultcode = "INVALID_REQUEST"
        error.fault.faultstring = "Invalid request format"

        with pytest.raises(SOAPFaultError) as exc_info:
            client._handle_soap_error(error)

        assert exc_info.value.fault_code == "INVALID_REQUEST"
        assert exc_info.value.fault_string == "Invalid request format"
        assert str(exc_info.value) == "SOAP Fault: INVALID_REQUEST - Invalid request format"

    def test_handle_soap_error_generic(self):
        """Test handling generic errors."""
        config = NetSuiteConfig(account="TEST123")
        client = NetSuiteSoapClient(config)

        error = Exception("Something went wrong")

        with pytest.raises(NetSuiteError, match="NetSuite SOAP error: Something went wrong"):
            client._handle_soap_error(error)

    @patch("zeep.Client")
    def test_client_creation_error(self, mock_zeep_client: Mock):
        """Test error handling during client creation."""
        mock_zeep_client.side_effect = Exception("Failed to parse WSDL")

        config = NetSuiteConfig(account="TEST123")
        client = NetSuiteSoapClient(config)

        with pytest.raises(NetSuiteError, match="Failed to initialize SOAP client"):
            _ = client.client
