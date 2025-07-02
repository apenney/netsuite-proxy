"""
NetSuite-specific exception classes.

This module defines custom exceptions for handling various NetSuite API errors
and application-specific error conditions.
"""

from app.types import ErrorDetails


class NetSuiteError(Exception):
    """Base exception for all NetSuite-related errors."""

    def __init__(self, message: str, details: ErrorDetails | None = None) -> None:
        """
        Initialize NetSuiteError.

        Args:
            message: Error message
            details: Additional error details (optional)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(NetSuiteError):
    """Raised when NetSuite authentication fails."""


class NetSuitePermissionError(NetSuiteError):
    """Raised when the user lacks permissions for the requested operation."""


class PageBoundsError(NetSuiteError):
    """Raised when requesting a page beyond available results."""

    def __init__(self, page: int, total_pages: int) -> None:
        """
        Initialize PageBoundsError.

        Args:
            page: Requested page number
            total_pages: Total available pages
        """
        message = f"Page {page} is out of bounds. Total pages: {total_pages}"
        super().__init__(message, {"page": page, "total_pages": total_pages})
        self.page = page
        self.total_pages = total_pages


class RecordNotFoundError(NetSuiteError):
    """Raised when a requested record is not found."""

    def __init__(self, record_type: str, record_id: str | int) -> None:
        """
        Initialize RecordNotFoundError.

        Args:
            record_type: Type of record (e.g., "Customer", "Invoice")
            record_id: ID of the record that was not found
        """
        message = f"{record_type} with ID {record_id} not found"
        super().__init__(message, {"record_type": record_type, "record_id": record_id})
        self.record_type = record_type
        self.record_id = record_id


class InvalidSearchCriteriaError(NetSuiteError):
    """Raised when search criteria is invalid."""


class RateLimitError(NetSuiteError):
    """Raised when NetSuite API rate limits are exceeded."""

    def __init__(self, retry_after: int | None = None) -> None:
        """
        Initialize RateLimitError.

        Args:
            retry_after: Number of seconds to wait before retrying (optional)
        """
        message = "NetSuite API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, {"retry_after": retry_after})
        self.retry_after = retry_after


class SOAPFaultError(NetSuiteError):
    """Raised when NetSuite returns a SOAP fault."""

    def __init__(self, fault_code: str, fault_string: str, detail: str | None = None) -> None:
        """
        Initialize SOAPFaultError.

        Args:
            fault_code: SOAP fault code
            fault_string: SOAP fault string
            detail: Additional fault details (optional)
        """
        message = f"SOAP Fault: {fault_code} - {fault_string}"
        super().__init__(
            message,
            {
                "fault_code": fault_code,
                "fault_string": fault_string,
                "detail": detail,
            },
        )
        self.fault_code = fault_code
        self.fault_string = fault_string
        self.detail = detail


class ConcurrencyError(NetSuiteError):
    """Raised when a record has been modified by another process."""

    def __init__(self, record_type: str, record_id: str | int) -> None:
        """
        Initialize ConcurrencyError.

        Args:
            record_type: Type of record
            record_id: ID of the record with concurrency conflict
        """
        message = (
            f"Concurrency error: {record_type} with ID {record_id} "
            "has been modified by another process"
        )
        super().__init__(message, {"record_type": record_type, "record_id": record_id})
        self.record_type = record_type
        self.record_id = record_id


class ValidationError(NetSuiteError):
    """Raised when data validation fails."""

    def __init__(self, field: str, value: object, reason: str) -> None:
        """
        Initialize ValidationError.

        Args:
            field: Field that failed validation
            value: Value that was invalid
            reason: Reason for validation failure
        """
        message = f"Validation error for field '{field}': {reason}"
        super().__init__(
            message,
            {
                "field": field,
                "value": value,
                "reason": reason,
            },
        )
        self.field = field
        self.value = value
        self.reason = reason


class ConfigurationError(NetSuiteError):
    """Raised when there's a configuration issue."""


class NetSuiteTimeoutError(NetSuiteError):
    """Raised when a NetSuite API request times out."""

    def __init__(self, operation: str, timeout_seconds: int) -> None:
        """
        Initialize TimeoutError.

        Args:
            operation: Operation that timed out
            timeout_seconds: Timeout duration in seconds
        """
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(
            message,
            {
                "operation": operation,
                "timeout_seconds": timeout_seconds,
            },
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class RESTletError(NetSuiteError):
    """Raised when a RESTlet script returns an error."""

    def __init__(
        self,
        script_id: str,
        error_code: str | None = None,
        error_details: ErrorDetails | None = None,
    ) -> None:
        """
        Initialize RESTletError.

        Args:
            script_id: ID of the RESTlet script
            error_code: Error code from the RESTlet (optional)
            error_details: Additional error details from the RESTlet (optional)
        """
        message = f"RESTlet error in script {script_id}"
        if error_code:
            message += f": {error_code}"
        super().__init__(
            message,
            {
                "script_id": script_id,
                "error_code": error_code,
                "error_details": error_details,
            },
        )
        self.script_id = script_id
        self.error_code = error_code
        self.error_details = error_details
