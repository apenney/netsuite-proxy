"""NetSuite RESTlet client implementation with OAuth1 support."""

from typing import Any

import requests
from requests_oauthlib import OAuth1Session

from app.core.config import NetSuiteConfig
from app.core.constants import NetSuiteDefaults
from app.core.exceptions import (
    AuthenticationError,
    NetSuiteError,
    NetSuiteTimeoutError,
    RESTletError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class NetSuiteRestletClient:
    """Client for interacting with NetSuite RESTlet scripts."""

    def __init__(self, config: NetSuiteConfig) -> None:
        """Initialize NetSuite RESTlet client.

        Args:
            config: NetSuite configuration containing auth credentials
        """
        self.config = config
        self._session: OAuth1Session | requests.Session | None = None
        self.default_timeout = NetSuiteDefaults.RESTLET_TIMEOUT

        # Validate RESTlet configuration
        if not config.script_id or not config.deploy_id:
            raise ValueError("RESTlet script_id and deploy_id are required")

        logger.info(
            "Initializing NetSuite RESTlet client",
            account=config.account,
            script_id=config.script_id,
            deploy_id=config.deploy_id,
            auth_type=config.auth_type,
        )

    @property
    def base_url(self) -> str:
        """Get NetSuite RESTlet base URL."""
        # NetSuite RESTlet URL format
        # https://{accountId}.restlets.api.netsuite.com/app/site/hosting/restlet.nl
        account_id = self.config.account.lower().replace("_", "-")

        # For sandbox accounts, use different subdomain
        # In this case, both branches are the same, so we can simplify
        subdomain = account_id

        return f"https://{subdomain}.restlets.api.netsuite.com/app/site/hosting/restlet.nl"

    @property
    def session(self) -> OAuth1Session | requests.Session:
        """Get or create HTTP session with authentication."""
        if self._session is None:
            if self.config.auth_type == "oauth":
                self._session = self._create_oauth_session()
            elif self.config.auth_type == "password":
                self._session = self._create_password_session()
            else:
                raise AuthenticationError(f"Unsupported auth type: {self.config.auth_type}")
        return self._session

    def _create_oauth_session(self) -> OAuth1Session:
        """Create OAuth1 session for RESTlet authentication."""
        if not all(
            [
                self.config.consumer_key,
                self.config.consumer_secret,
                self.config.token_id,
                self.config.token_secret,
            ]
        ):
            raise AuthenticationError(
                "OAuth credentials required: consumer_key, consumer_secret, token_id, token_secret"
            )

        # Create OAuth1 session with HMAC-SHA256
        session = OAuth1Session(
            client_key=self.config.consumer_key,
            client_secret=self.config.consumer_secret,
            resource_owner_key=self.config.token_id,
            resource_owner_secret=self.config.token_secret,
            realm=self.config.account,
            signature_method="HMAC-SHA256",
        )

        # Set common headers
        session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "NetSuite-Proxy/1.0",
            }
        )

        logger.debug("Created OAuth session for RESTlet")
        return session

    def _create_password_session(self) -> requests.Session:
        """Create session with password authentication headers."""
        if not self.config.email or not self.config.password:
            raise AuthenticationError("Email and password required for password auth")

        session = requests.Session()

        # NetSuite RESTlet password auth uses custom headers
        auth_headers = {
            "NS-Email": self.config.email,
            "NS-Password": self.config.password,
            "NS-Account": self.config.account,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "NetSuite-Proxy/1.0",
        }

        if self.config.role:
            auth_headers["NS-Role"] = self.config.role

        session.headers.update(auth_headers)

        logger.debug("Created password session for RESTlet")
        return session

    def _build_url(self, **params: Any) -> str:
        """Build full RESTlet URL with required parameters.

        Args:
            **params: Additional query parameters

        Returns:
            Full URL with query parameters
        """
        # Required parameters for RESTlet
        query_params = {
            "script": self.config.script_id,
            "deploy": self.config.deploy_id,
        }

        # Add any additional parameters
        query_params.update(params)

        # Build query string
        query_string = "&".join(f"{k}={v}" for k, v in query_params.items())

        return f"{self.base_url}?{query_string}"

    def get(
        self,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> Any:
        """Execute GET request to RESTlet.

        Args:
            params: Query parameters to send
            timeout: Request timeout in seconds

        Returns:
            Response data from RESTlet
        """
        url = self._build_url(**(params or {}))
        timeout = timeout or self.default_timeout

        try:
            logger.info(
                "Executing RESTlet GET request",
                script_id=self.config.script_id,
                deploy_id=self.config.deploy_id,
                params=params,
            )

            response = self.session.get(url, timeout=timeout)
            return self._handle_response(response)

        except requests.exceptions.Timeout as e:
            logger.error("RESTlet request timed out", timeout=timeout)
            raise NetSuiteTimeoutError("RESTlet GET", timeout) from e
        except Exception as e:
            logger.error("RESTlet GET failed", error=str(e))
            self._handle_request_error(e)

    def post(
        self,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> Any:
        """Execute POST request to RESTlet.

        Args:
            data: JSON data to send in request body
            params: Query parameters to send
            timeout: Request timeout in seconds

        Returns:
            Response data from RESTlet
        """
        url = self._build_url(**(params or {}))
        timeout = timeout or self.default_timeout

        try:
            logger.info(
                "Executing RESTlet POST request",
                script_id=self.config.script_id,
                deploy_id=self.config.deploy_id,
                has_data=data is not None,
            )

            response = self.session.post(url, json=data, timeout=timeout)
            return self._handle_response(response)

        except requests.exceptions.Timeout as e:
            logger.error("RESTlet request timed out", timeout=timeout)
            raise NetSuiteTimeoutError("RESTlet POST", timeout) from e
        except Exception as e:
            logger.error("RESTlet POST failed", error=str(e))
            self._handle_request_error(e)

    def put(
        self,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> Any:
        """Execute PUT request to RESTlet.

        Args:
            data: JSON data to send in request body
            params: Query parameters to send
            timeout: Request timeout in seconds

        Returns:
            Response data from RESTlet
        """
        url = self._build_url(**(params or {}))
        timeout = timeout or self.default_timeout

        try:
            logger.info(
                "Executing RESTlet PUT request",
                script_id=self.config.script_id,
                deploy_id=self.config.deploy_id,
                has_data=data is not None,
            )

            response = self.session.put(url, json=data, timeout=timeout)
            return self._handle_response(response)

        except requests.exceptions.Timeout as e:
            logger.error("RESTlet request timed out", timeout=timeout)
            raise NetSuiteTimeoutError("RESTlet PUT", timeout) from e
        except Exception as e:
            logger.error("RESTlet PUT failed", error=str(e))
            self._handle_request_error(e)

    def delete(
        self,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> Any:
        """Execute DELETE request to RESTlet.

        Args:
            params: Query parameters to send
            timeout: Request timeout in seconds

        Returns:
            Response data from RESTlet
        """
        url = self._build_url(**(params or {}))
        timeout = timeout or self.default_timeout

        try:
            logger.info(
                "Executing RESTlet DELETE request",
                script_id=self.config.script_id,
                deploy_id=self.config.deploy_id,
                params=params,
            )

            response = self.session.delete(url, timeout=timeout)
            return self._handle_response(response)

        except requests.exceptions.Timeout as e:
            logger.error("RESTlet request timed out", timeout=timeout)
            raise NetSuiteTimeoutError("RESTlet DELETE", timeout) from e
        except Exception as e:
            logger.error("RESTlet DELETE failed", error=str(e))
            self._handle_request_error(e)

    def _handle_response(self, response: requests.Response) -> Any:
        """Handle RESTlet response and raise appropriate exceptions.

        Args:
            response: HTTP response from RESTlet

        Returns:
            Parsed JSON response data
        """
        logger.debug(
            "RESTlet response received",
            status_code=response.status_code,
            content_length=len(response.content),
        )

        # Check for HTTP errors
        if response.status_code == 401:
            raise AuthenticationError("RESTlet authentication failed")
        if response.status_code == 403:
            raise AuthenticationError("Insufficient permissions for RESTlet")
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
            except Exception:
                error_msg = response.text

            raise RESTletError(
                self.config.script_id or "unknown",
                error_code=str(response.status_code),
                error_details={"message": error_msg, "response_text": response.text},
            )

        # Parse JSON response
        try:
            data = response.json()

            # Check for NetSuite error in response
            if isinstance(data, dict) and data.get("error"):
                error = data["error"]
                raise RESTletError(
                    self.config.script_id or "unknown",
                    error_code=error.get("code"),
                    error_details=error,
                )

            return data

        except ValueError as e:
            logger.error("Failed to parse RESTlet response", error=str(e))
            raise RESTletError(
                self.config.script_id or "unknown",
                error_code="INVALID_JSON",
                error_details={"message": f"Invalid JSON response: {e!s}"},
            ) from e

    def _handle_request_error(self, error: Exception) -> None:
        """Handle request errors and raise appropriate exceptions.

        Args:
            error: Original exception
        """
        if isinstance(error, requests.exceptions.ConnectionError):
            raise NetSuiteError(f"Failed to connect to NetSuite: {error!s}")
        if isinstance(error, requests.exceptions.RequestException):
            raise NetSuiteError(f"RESTlet request failed: {error!s}")
        raise error
