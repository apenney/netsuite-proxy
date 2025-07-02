"""Base classes for NetSuite service implementations."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.config import NetSuiteConfig
from app.core.exceptions import (
    AuthenticationError,
    NetSuiteError,
    NetSuiteTimeoutError,
)
from app.core.logging import get_logger


class BaseNetSuiteClient(ABC):
    """Abstract base class for NetSuite clients."""

    def __init__(self, config: NetSuiteConfig) -> None:
        """Initialize base NetSuite client.

        Args:
            config: NetSuite configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # Validate authentication
        if config.auth_type == "none":
            raise AuthenticationError("No authentication credentials provided")

    @abstractmethod
    def authenticate(self) -> None:
        """Authenticate with NetSuite.

        This method should set up any necessary authentication
        headers or session configuration.
        """

    def handle_timeout_error(self, operation: str, timeout: int) -> None:
        """Handle timeout errors consistently.

        Args:
            operation: Name of the operation that timed out
            timeout: Timeout value in seconds

        Raises:
            NetSuiteTimeoutError: Always raises this exception
        """
        self.logger.error(f"{operation} timed out", timeout=timeout)
        raise NetSuiteTimeoutError(operation, timeout)

    def handle_authentication_error(self, details: str | None = None) -> None:
        """Handle authentication errors consistently.

        Args:
            details: Additional error details

        Raises:
            AuthenticationError: Always raises this exception
        """
        message = "NetSuite authentication failed"
        if details:
            message = f"{message}: {details}"
        self.logger.error(message)
        raise AuthenticationError(message)

    def handle_generic_error(self, error: Exception, operation: str) -> None:
        """Handle generic errors consistently.

        Args:
            error: The original exception
            operation: Name of the operation that failed

        Raises:
            NetSuiteError: Always raises this exception
        """
        error_str = str(error)
        self.logger.error(f"{operation} failed", error=error_str)
        raise NetSuiteError(f"NetSuite {operation} error: {error_str}")


class BaseNetSuiteService(ABC):
    """Abstract base class for NetSuite business services."""

    def __init__(self, client: BaseNetSuiteClient) -> None:
        """Initialize base service.

        Args:
            client: NetSuite client instance
        """
        self.client = client
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def search(self, criteria: dict[str, Any]) -> list[dict[str, Any]]:
        """Search for records matching criteria.

        Args:
            criteria: Search criteria

        Returns:
            List of matching records
        """

    @abstractmethod
    async def get(self, record_id: str) -> dict[str, Any]:
        """Get a single record by ID.

        Args:
            record_id: Record internal ID

        Returns:
            Record data
        """

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> str:
        """Create a new record.

        Args:
            data: Record data

        Returns:
            Created record ID
        """

    @abstractmethod
    async def update(self, record_id: str, data: dict[str, Any]) -> None:
        """Update an existing record.

        Args:
            record_id: Record internal ID
            data: Updated record data
        """

    @abstractmethod
    async def delete(self, record_id: str) -> None:
        """Delete a record.

        Args:
            record_id: Record internal ID
        """
