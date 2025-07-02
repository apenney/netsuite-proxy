"""Tests for NetSuite RESTlet client."""

from unittest.mock import Mock, patch

import pytest
import requests

from app.core.config import NetSuiteConfig
from app.core.exceptions import (
    AuthenticationError,
    NetSuiteError,
    RESTletError,
)
from app.services.netsuite.restlet.client import NetSuiteRestletClient


class TestNetSuiteRestletClient:
    """Tests for NetSuiteRestletClient."""

    def test_init_success(self):
        """Test successful client initialization."""
        config = NetSuiteConfig(
            account="TEST123",
            email="test@example.com",
            password="password",
            script_id="customscript123",
            deploy_id="customdeploy1",
        )

        client = NetSuiteRestletClient(config)

        assert client.config == config
        assert client._session is None
        assert client.default_timeout == 300

    def test_init_missing_script_id(self):
        """Test initialization fails when script_id is missing."""
        config = NetSuiteConfig(
            account="TEST123",
            email="test@example.com",
            password="password",
            deploy_id="customdeploy1",
        )

        with pytest.raises(ValueError, match="RESTlet script_id and deploy_id are required"):
            NetSuiteRestletClient(config)

    def test_init_missing_deploy_id(self):
        """Test initialization fails when deploy_id is missing."""
        config = NetSuiteConfig(
            account="TEST123",
            email="test@example.com",
            password="password",
            script_id="customscript123",
        )

        with pytest.raises(ValueError, match="RESTlet script_id and deploy_id are required"):
            NetSuiteRestletClient(config)

    def test_base_url_production(self):
        """Test base URL generation for production account."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        assert (
            client.base_url
            == "https://test123.restlets.api.netsuite.com/app/site/hosting/restlet.nl"
        )

    def test_base_url_sandbox(self):
        """Test base URL generation for sandbox accounts."""
        for account in ["TEST123-SB1", "TEST123-SB2", "TEST_SB1", "TEST_SB2"]:
            config = NetSuiteConfig(
                account=account,
                script_id="script",
                deploy_id="deploy",
            )
            client = NetSuiteRestletClient(config)

            base_account = account.lower().replace("_", "-")
            expected = f"https://{base_account}.restlets.api.netsuite.com/app/site/hosting/restlet.nl"
            assert client.base_url == expected

    def test_build_url(self):
        """Test URL building with query parameters."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="customscript123",
            deploy_id="customdeploy1",
        )
        client = NetSuiteRestletClient(config)

        url = client._build_url(param1="value1", param2="value2")

        expected = "https://test123.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=customscript123&deploy=customdeploy1&param1=value1&param2=value2"
        assert url == expected

    @patch("requests.Session")
    def test_create_password_session(self, mock_session_class):
        """Test password session creation."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        config = NetSuiteConfig(
            account="TEST123",
            email="test@example.com",
            password="password",
            role="3",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        session = client._create_password_session()

        assert session == mock_session
        expected_headers = {
            "NS-Email": "test@example.com",
            "NS-Password": "password",
            "NS-Account": "TEST123",
            "NS-Role": "3",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "NetSuite-Proxy/1.0",
        }
        mock_session.headers.update.assert_called_once()
        actual_headers = mock_session.headers.update.call_args[0][0]
        assert actual_headers == expected_headers

    def test_create_password_session_missing_email(self):
        """Test password session creation fails when email is missing."""
        config = NetSuiteConfig(
            account="TEST123",
            password="password",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        with pytest.raises(AuthenticationError, match="Email and password required"):
            client._create_password_session()

    @patch("app.services.netsuite.restlet.client.OAuth1Session")
    def test_create_oauth_session(self, mock_oauth_class):
        """Test OAuth session creation."""
        mock_session = Mock()
        mock_oauth_class.return_value = mock_session

        config = NetSuiteConfig(
            account="TEST123",
            consumer_key="key",
            consumer_secret="secret",
            token_id="token",
            token_secret="tokensecret",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        session = client._create_oauth_session()

        assert session == mock_session
        mock_oauth_class.assert_called_once_with(
            client_key="key",
            client_secret="secret",
            resource_owner_key="token",
            resource_owner_secret="tokensecret",
            realm="TEST123",
            signature_method="HMAC-SHA256",
        )
        expected_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "NetSuite-Proxy/1.0",
        }
        mock_session.headers.update.assert_called_once_with(expected_headers)

    def test_create_oauth_session_missing_credentials(self):
        """Test OAuth session creation fails when credentials are missing."""
        config = NetSuiteConfig(
            account="TEST123",
            consumer_key="key",
            consumer_secret="secret",
            # Missing token credentials
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        with pytest.raises(AuthenticationError, match="OAuth credentials required"):
            client._create_oauth_session()

    def test_handle_response_success(self):
        """Test successful response handling."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        response = Mock()
        response.status_code = 200
        response.json.return_value = {"result": "success"}
        response.content = b'{"result": "success"}'

        result = client._handle_response(response)

        assert result == {"result": "success"}

    def test_handle_response_401(self):
        """Test handling 401 authentication error."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        response = Mock()
        response.status_code = 401
        response.content = b""

        with pytest.raises(AuthenticationError, match="RESTlet authentication failed"):
            client._handle_response(response)

    def test_handle_response_403(self):
        """Test handling 403 permission error."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        response = Mock()
        response.status_code = 403
        response.content = b""

        with pytest.raises(AuthenticationError, match="Insufficient permissions"):
            client._handle_response(response)

    def test_handle_response_error_with_json(self):
        """Test handling error response with JSON error message."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        response = Mock()
        response.status_code = 400
        response.json.return_value = {"error": {"message": "Invalid parameters"}}
        response.text = '{"error": {"message": "Invalid parameters"}}'
        response.content = response.text.encode()

        with pytest.raises(RESTletError) as exc_info:
            client._handle_response(response)

        assert exc_info.value.error_code == "400"
        assert exc_info.value.error_details["message"] == "Invalid parameters"

    def test_handle_response_error_without_json(self):
        """Test handling error response without JSON."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        response = Mock()
        response.status_code = 500
        response.json.side_effect = ValueError()
        response.text = "Internal Server Error"
        response.content = response.text.encode()

        with pytest.raises(RESTletError) as exc_info:
            client._handle_response(response)

        assert exc_info.value.error_code == "500"
        assert exc_info.value.error_details["message"] == "Internal Server Error"

    def test_handle_response_invalid_json(self):
        """Test handling response with invalid JSON."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        response = Mock()
        response.status_code = 200
        response.json.side_effect = ValueError("Invalid JSON")
        response.content = b"not json"

        with pytest.raises(RESTletError) as exc_info:
            client._handle_response(response)

        assert exc_info.value.error_code == "INVALID_JSON"

    def test_handle_response_with_error_in_data(self):
        """Test handling successful response with error in data."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "error": {
                "code": "INVALID_RECORD",
                "message": "Record not found",
            }
        }
        response.content = b'{"error": {"code": "INVALID_RECORD", "message": "Record not found"}}'

        with pytest.raises(RESTletError) as exc_info:
            client._handle_response(response)

        assert exc_info.value.error_code == "INVALID_RECORD"
        assert exc_info.value.error_details["message"] == "Record not found"

    def test_handle_request_error_connection(self):
        """Test handling connection errors."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        error = requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(NetSuiteError, match="Failed to connect to NetSuite"):
            client._handle_request_error(error)

    def test_handle_request_error_generic_request(self):
        """Test handling generic request errors."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        error = requests.exceptions.RequestException("Request failed")

        with pytest.raises(NetSuiteError, match="RESTlet request failed"):
            client._handle_request_error(error)

    def test_handle_request_error_other(self):
        """Test handling non-request errors."""
        config = NetSuiteConfig(
            account="TEST123",
            script_id="script",
            deploy_id="deploy",
        )
        client = NetSuiteRestletClient(config)

        error = ValueError("Some other error")

        with pytest.raises(ValueError, match="Some other error"):
            client._handle_request_error(error)
