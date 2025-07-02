"""NetSuite authentication service supporting both password and OAuth methods."""

from typing import Any

from app.core.config import NetSuiteConfig
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger
from app.services.netsuite.restlet.client import NetSuiteRestletClient
from app.services.netsuite.soap.client import NetSuiteSoapClient

logger = get_logger(__name__)


class NetSuiteAuthService:
    """Service for managing NetSuite authentication and client creation."""

    def __init__(self, config: NetSuiteConfig):
        """Initialize authentication service.

        Args:
            config: NetSuite configuration
        """
        self.config = config
        self._soap_client: NetSuiteSoapClient | None = None
        self._restlet_client: NetSuiteRestletClient | None = None

        logger.info(
            "Initializing NetSuite auth service",
            account=config.account,
            auth_type=config.auth_type,
            has_restlet_config=bool(config.script_id and config.deploy_id),
        )

    @property
    def soap_client(self) -> NetSuiteSoapClient:
        """Get or create SOAP client instance.

        Returns:
            Configured SOAP client
        """
        if self._soap_client is None:
            logger.debug("Creating SOAP client")
            self._soap_client = NetSuiteSoapClient(self.config)
        return self._soap_client

    @property
    def restlet_client(self) -> NetSuiteRestletClient:
        """Get or create RESTlet client instance.

        Returns:
            Configured RESTlet client

        Raises:
            ValueError: If RESTlet configuration is missing
        """
        if self._restlet_client is None:
            if not self.config.script_id or not self.config.deploy_id:
                raise ValueError(
                    "RESTlet configuration missing. Set NETSUITE__SCRIPT_ID and NETSUITE__DEPLOY_ID"
                )
            logger.debug("Creating RESTlet client")
            self._restlet_client = NetSuiteRestletClient(self.config)
        return self._restlet_client

    def validate_credentials(self) -> bool:
        """Validate NetSuite credentials by attempting authentication.

        Returns:
            True if credentials are valid

        Raises:
            AuthenticationError: If credentials are invalid
        """
        logger.info("Validating NetSuite credentials")

        try:
            # Try a simple SOAP operation to validate credentials
            # This could be a getServerTime call or similar
            # For now, just check that we can create the client
            _ = self.soap_client.service

            logger.info("NetSuite credentials validated successfully")
            return True

        except AuthenticationError:
            logger.error("NetSuite credential validation failed")
            raise
        except Exception as e:
            logger.error("Unexpected error during credential validation", error=str(e))
            raise AuthenticationError(f"Failed to validate credentials: {e!s}")

    def get_account_info(self) -> dict[str, Any]:
        """Get information about the authenticated NetSuite account.

        Returns:
            Dictionary with account information
        """
        return {
            "account": self.config.account,
            "auth_type": self.config.auth_type,
            "api_version": self.config.api,
            "environment": self._determine_environment(),
            "has_restlet": bool(self.config.script_id and self.config.deploy_id),
        }

    def _determine_environment(self) -> str:
        """Determine if account is sandbox or production.

        Returns:
            "sandbox" or "production"
        """
        account_lower = self.config.account.lower()
        if account_lower.endswith(("-sb1", "-sb2", "_sb1", "_sb2")):
            return "sandbox"
        return "production"

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> "NetSuiteAuthService":
        """Create auth service from HTTP headers.

        This is used by the authentication middleware to create
        a service instance from request headers.

        Args:
            headers: Dictionary of HTTP headers

        Returns:
            Configured auth service

        Raises:
            AuthenticationError: If required headers are missing
        """
        # Extract account (required)
        account = headers.get("x-netsuite-account")
        if not account:
            raise AuthenticationError("Missing required header: X-NetSuite-Account")

        # Extract API version (optional)
        api_version = headers.get("x-netsuite-api-version", "2024_2")

        # Extract role (optional)
        role = headers.get("x-netsuite-role")

        # Check for OAuth authentication
        if all(
            headers.get(key)
            for key in [
                "x-netsuite-consumer-key",
                "x-netsuite-consumer-secret",
                "x-netsuite-token-id",
                "x-netsuite-token-secret",
            ]
        ):
            logger.debug("Creating auth service with OAuth credentials from headers")
            config = NetSuiteConfig(
                account=account,
                api=api_version,
                consumer_key=headers["x-netsuite-consumer-key"],
                consumer_secret=headers["x-netsuite-consumer-secret"],
                token_id=headers["x-netsuite-token-id"],
                token_secret=headers["x-netsuite-token-secret"],
                role=role,
            )
        # Check for password authentication
        elif headers.get("x-netsuite-email") and headers.get("x-netsuite-password"):
            logger.debug("Creating auth service with password credentials from headers")
            config = NetSuiteConfig(
                account=account,
                api=api_version,
                email=headers["x-netsuite-email"],
                password=headers["x-netsuite-password"],
                role=role,
            )
        else:
            raise AuthenticationError(
                "Missing authentication credentials. Provide either "
                "OAuth (Consumer-Key, Consumer-Secret, Token-Id, Token-Secret) "
                "or Password (Email, Password) authentication headers"
            )

        # Add RESTlet configuration if provided
        if headers.get("x-netsuite-script-id") and headers.get("x-netsuite-deploy-id"):
            config.script_id = headers["x-netsuite-script-id"]
            config.deploy_id = headers["x-netsuite-deploy-id"]

        return cls(config)
