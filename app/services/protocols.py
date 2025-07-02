"""Protocol definitions for type safety and testability."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NetSuiteClient(Protocol):
    """Protocol for NetSuite client implementations."""

    def search(self, search_record: Any, page_size: int = 100) -> Any:
        """Execute a search operation."""
        ...

    def get(self, record_ref: Any) -> Any:
        """Get a single record by reference."""
        ...

    def add(self, record: Any) -> Any:
        """Add a new record."""
        ...

    def update(self, record: Any) -> Any:
        """Update an existing record."""
        ...

    def delete(self, record_ref: Any) -> Any:
        """Delete a record."""
        ...


@runtime_checkable
class Serializer(Protocol):
    """Protocol for data serializers."""

    @classmethod
    def from_netsuite(cls, ns_record: Any) -> dict[str, Any]:
        """Convert NetSuite record to dictionary."""
        ...

    def to_netsuite(self) -> Any:
        """Convert to NetSuite record format."""
        ...


@runtime_checkable
class AuthenticationProvider(Protocol):
    """Protocol for authentication providers."""

    @property
    def auth_type(self) -> str:
        """Get authentication type."""
        ...

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        ...

    def validate_credentials(self) -> bool:
        """Validate credentials are valid."""
        ...
