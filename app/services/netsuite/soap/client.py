"""NetSuite SOAP client implementation using zeep."""

import base64
import hashlib
import hmac
import secrets
import time
from typing import Any

from zeep import Client, Settings
from zeep.transports import Transport

from app.core.config import NetSuiteConfig
from app.core.constants import (
    NETSUITE_DEFAULT_APPLICATION_ID,
    NETSUITE_DEFAULT_SOAP_TIMEOUT,
)
from app.core.exceptions import (
    AuthenticationError,
    NetSuiteError,
    NetSuiteTimeoutError,
    SOAPFaultError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class NetSuiteSoapClient:
    """Client for interacting with NetSuite's SOAP API (SuiteTalk)."""

    def __init__(self, config: NetSuiteConfig) -> None:
        """Initialize NetSuite SOAP client.

        Args:
            config: NetSuite configuration containing auth credentials
        """
        self.config = config
        self._client: Client | None = None
        self._service: Any = None

        # Configure zeep settings for NetSuite
        self.settings = Settings(
            xml_huge_tree=True,  # type: ignore[call-arg]  # Handle large XML responses
            strict=False,  # type: ignore[call-arg]  # NetSuite's WSDL sometimes has issues
            raw_response=False,  # type: ignore[call-arg]
        )

        # Configure transport with timeout from config or default
        self.timeout = config.timeout or NETSUITE_DEFAULT_SOAP_TIMEOUT
        self.transport = Transport(
            timeout=self.timeout,
            operation_timeout=self.timeout,
        )

        logger.info(
            "Initializing NetSuite SOAP client",
            account=config.account,
            api_version=config.api,
            auth_type=config.auth_type,
        )

    @property
    def wsdl_url(self) -> str:
        """Get NetSuite WSDL URL based on account and API version."""
        # NetSuite WSDL URL format
        # https://webservices.netsuite.com/wsdl/v{version}/netsuite.wsdl
        api_version = self.config.api.replace("_", ".")  # 2024_2 -> 2024.2
        return f"https://webservices.netsuite.com/wsdl/v{api_version}/netsuite.wsdl"

    @property
    def client(self) -> Client:
        """Get or create zeep client instance."""
        if self._client is None:
            logger.debug("Creating zeep client", wsdl_url=self.wsdl_url)
            try:
                self._client = Client(
                    wsdl=self.wsdl_url,
                    settings=self.settings,
                    transport=self.transport,
                )
            except Exception as e:
                logger.error("Failed to create SOAP client", error=str(e))
                raise NetSuiteError(f"Failed to initialize SOAP client: {e!s}") from e
        return self._client

    @property
    def service(self) -> Any:
        """Get SOAP service with authentication headers."""
        if self._service is None:
            self._service = self.client.service
            # Set authentication headers
            self._set_auth_headers()
        return self._service

    def _set_auth_headers(self) -> None:
        """Set authentication headers based on config."""
        # NetSuite uses Passport authentication in SOAP header
        passport = self._create_passport()

        # Create application info
        application_info = {
            "applicationId": self.config.application_id or NETSUITE_DEFAULT_APPLICATION_ID,
        }

        # Set SOAP headers
        self.client.set_default_soapheaders(  # type: ignore[arg-type]
            {
                "passport": passport,
                "applicationInfo": application_info,
            }
        )

        logger.debug("Set SOAP authentication headers")

    def _create_passport(self) -> dict[str, Any]:
        """Create passport object for authentication."""
        passport: dict[str, Any] = {
            "account": self.config.account,
        }

        if self.config.auth_type == "password":
            if not self.config.email or not self.config.password:
                raise AuthenticationError("Email and password required for password auth")

            passport.update(
                {
                    "email": self.config.email,
                    "password": self.config.password,
                }
            )

            if self.config.role:
                passport["role"] = {"internalId": self.config.role}

        elif self.config.auth_type == "oauth":
            if not all(
                [
                    self.config.consumer_key,
                    self.config.consumer_secret,
                    self.config.token_id,
                    self.config.token_secret,
                ]
            ):
                raise AuthenticationError(
                    "OAuth credentials required: consumer_key, consumer_secret, "
                    "token_id, token_secret"
                )

            # For OAuth, we need to use token passport
            passport = {
                "account": self.config.account,
                "consumerKey": self.config.consumer_key,
                "token": self.config.token_id,
                "nonce": self._generate_nonce(),
                "timestamp": self._get_timestamp(),
                "signature": {
                    "algorithm": "HMAC-SHA256",
                    "value": self._generate_signature(),
                },
            }
        else:
            raise AuthenticationError(f"Unsupported auth type: {self.config.auth_type}")

        return passport

    def _generate_nonce(self) -> str:
        """Generate nonce for OAuth."""
        return secrets.token_urlsafe(32)

    def _get_timestamp(self) -> str:
        """Get current timestamp for OAuth."""
        return str(int(time.time()))

    def _generate_signature(self) -> str:
        """Generate OAuth signature."""
        # This is a simplified version - actual implementation needs proper OAuth signing

        # Create base string
        nonce = self._generate_nonce()
        timestamp = self._get_timestamp()
        base_string = (
            f"{self.config.account}&{self.config.consumer_key}&"
            f"{self.config.token_id}&{nonce}&{timestamp}"
        )

        # Create signing key
        signing_key = f"{self.config.consumer_secret}&{self.config.token_secret}"

        # Generate signature
        signature = hmac.new(
            signing_key.encode(),
            base_string.encode(),
            hashlib.sha256,
        ).digest()

        return base64.b64encode(signature).decode()

    def search(
        self,
        search_record: Any,
        page_size: int = 100,
    ) -> Any:
        """Execute a search operation.

        Args:
            search_record: NetSuite search record object
            page_size: Number of results per page

        Returns:
            Search result from NetSuite
        """
        try:
            logger.info(
                "Executing SOAP search",
                record_type=type(search_record).__name__,
                page_size=page_size,
            )

            # Set search preferences
            search_prefs = {
                "pageSize": page_size,
                "returnSearchColumns": True,
            }

            self.client.set_options(searchPreferences=search_prefs)  # type: ignore[attr-defined]

            # Execute search
            response = self.service.search(searchRecord=search_record)

            logger.info(
                "Search completed",
                total_records=response.totalRecords if hasattr(response, "totalRecords") else 0,
                page_size=response.pageSize if hasattr(response, "pageSize") else 0,
            )

            return response

        except Exception as e:
            logger.error("SOAP search failed", error=str(e))
            self._handle_soap_error(e)

    def get(self, record_ref: Any) -> Any:
        """Get a single record by reference.

        Args:
            record_ref: NetSuite record reference

        Returns:
            Record from NetSuite
        """
        try:
            logger.info(
                "Getting record",
                internal_id=record_ref.internalId if hasattr(record_ref, "internalId") else None,
                record_type=record_ref.type if hasattr(record_ref, "type") else None,
            )

            response = self.service.get(baseRef=record_ref)

            if hasattr(response, "status") and not response.status.isSuccess:
                raise NetSuiteError(
                    f"Failed to get record: {response.status.statusDetail[0].message}"
                )

            return response.record

        except Exception as e:
            logger.error("SOAP get failed", error=str(e))
            self._handle_soap_error(e)

    def add(self, record: Any) -> Any:
        """Add a new record.

        Args:
            record: NetSuite record to add

        Returns:
            Response from NetSuite
        """
        try:
            logger.info("Adding record", record_type=type(record).__name__)

            response = self.service.add(record=record)

            if hasattr(response, "status") and not response.status.isSuccess:
                raise NetSuiteError(
                    f"Failed to add record: {response.status.statusDetail[0].message}"
                )

            return response

        except Exception as e:
            logger.error("SOAP add failed", error=str(e))
            self._handle_soap_error(e)

    def update(self, record: Any) -> Any:
        """Update an existing record.

        Args:
            record: NetSuite record to update

        Returns:
            Response from NetSuite
        """
        try:
            logger.info(
                "Updating record",
                record_type=type(record).__name__,
                internal_id=record.internalId if hasattr(record, "internalId") else None,
            )

            response = self.service.update(record=record)

            if hasattr(response, "status") and not response.status.isSuccess:
                raise NetSuiteError(
                    f"Failed to update record: {response.status.statusDetail[0].message}"
                )

            return response

        except Exception as e:
            logger.error("SOAP update failed", error=str(e))
            self._handle_soap_error(e)

    def delete(self, record_ref: Any) -> Any:
        """Delete a record.

        Args:
            record_ref: NetSuite record reference

        Returns:
            Response from NetSuite
        """
        try:
            logger.info(
                "Deleting record",
                internal_id=record_ref.internalId if hasattr(record_ref, "internalId") else None,
                record_type=record_ref.type if hasattr(record_ref, "type") else None,
            )

            response = self.service.delete(baseRef=record_ref)

            if hasattr(response, "status") and not response.status.isSuccess:
                raise NetSuiteError(
                    f"Failed to delete record: {response.status.statusDetail[0].message}"
                )

            return response

        except Exception as e:
            logger.error("SOAP delete failed", error=str(e))
            self._handle_soap_error(e)

    def _handle_soap_error(self, error: Exception) -> None:
        """Handle SOAP errors and raise appropriate exceptions."""
        error_str = str(error)

        if "timeout" in error_str.lower():
            raise NetSuiteTimeoutError("SOAP", self.timeout)
        if "authentication" in error_str.lower() or "invalid login" in error_str.lower():
            raise AuthenticationError("NetSuite authentication failed")
        if hasattr(error, "fault"):
            # SOAP fault
            fault = error.fault
            raise SOAPFaultError(
                getattr(fault, "faultcode", "Unknown"),
                getattr(fault, "faultstring", str(error)),
            )
        raise NetSuiteError(f"NetSuite SOAP error: {error_str}")
