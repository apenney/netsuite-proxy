"""
Tests for NetSuite exception classes.
"""

import pytest

from app.core.exceptions import (
    AuthenticationError,
    ConcurrencyError,
    ConfigurationError,
    InvalidSearchCriteriaError,
    NetSuiteError,
    NetSuitePermissionError,
    NetSuiteTimeoutError,
    PageBoundsError,
    RateLimitError,
    RecordNotFoundError,
    RESTletError,
    SOAPFaultError,
    ValidationError,
)


class TestNetSuiteError:
    """Tests for base NetSuiteError."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = NetSuiteError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.details == {}

    def test_error_with_details(self) -> None:
        """Test error with additional details."""
        details = {"code": "ERR001", "field": "customer_id"}
        error = NetSuiteError("Validation failed", details)
        assert error.message == "Validation failed"
        assert error.details == details
        assert error.details["code"] == "ERR001"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_authentication_error(self) -> None:
        """Test authentication error creation."""
        error = AuthenticationError("Invalid credentials")
        assert isinstance(error, NetSuiteError)
        assert str(error) == "Invalid credentials"


class TestNetSuitePermissionError:
    """Tests for NetSuitePermissionError."""

    def test_permission_error(self) -> None:
        """Test permission error creation."""
        error = NetSuitePermissionError("Access denied to Customer record")
        assert isinstance(error, NetSuiteError)
        assert str(error) == "Access denied to Customer record"


class TestPageBoundsError:
    """Tests for PageBoundsError."""

    def test_page_bounds_error(self) -> None:
        """Test page bounds error creation."""
        error = PageBoundsError(page=10, total_pages=5)
        assert isinstance(error, NetSuiteError)
        assert str(error) == "Page 10 is out of bounds. Total pages: 5"
        assert error.page == 10
        assert error.total_pages == 5
        assert error.details["page"] == 10
        assert error.details["total_pages"] == 5


class TestRecordNotFoundError:
    """Tests for RecordNotFoundError."""

    def test_record_not_found_error(self) -> None:
        """Test record not found error creation."""
        error = RecordNotFoundError("Customer", 12345)
        assert isinstance(error, NetSuiteError)
        assert str(error) == "Customer with ID 12345 not found"
        assert error.record_type == "Customer"
        assert error.record_id == 12345

    def test_record_not_found_with_string_id(self) -> None:
        """Test record not found error with string ID."""
        error = RecordNotFoundError("Invoice", "INV-001")
        assert str(error) == "Invoice with ID INV-001 not found"
        assert error.record_id == "INV-001"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_rate_limit_error_basic(self) -> None:
        """Test basic rate limit error."""
        error = RateLimitError()
        assert str(error) == "NetSuite API rate limit exceeded"
        assert error.retry_after is None

    def test_rate_limit_error_with_retry(self) -> None:
        """Test rate limit error with retry information."""
        error = RateLimitError(retry_after=60)
        assert str(error) == "NetSuite API rate limit exceeded. Retry after 60 seconds"
        assert error.retry_after == 60
        assert error.details["retry_after"] == 60


class TestSOAPFaultError:
    """Tests for SOAPFaultError."""

    def test_soap_fault_basic(self) -> None:
        """Test basic SOAP fault error."""
        error = SOAPFaultError("Server", "Internal server error")
        assert str(error) == "SOAP Fault: Server - Internal server error"
        assert error.fault_code == "Server"
        assert error.fault_string == "Internal server error"
        assert error.detail is None

    def test_soap_fault_with_detail(self) -> None:
        """Test SOAP fault error with details."""
        error = SOAPFaultError(
            "Client",
            "Invalid request",
            "Missing required field: customerId",
        )
        assert error.detail == "Missing required field: customerId"
        assert error.details["detail"] == "Missing required field: customerId"


class TestConcurrencyError:
    """Tests for ConcurrencyError."""

    def test_concurrency_error(self) -> None:
        """Test concurrency error creation."""
        error = ConcurrencyError("Customer", 789)
        expected_msg = (
            "Concurrency error: Customer with ID 789 has been modified by another process"
        )
        assert str(error) == expected_msg
        assert error.record_type == "Customer"
        assert error.record_id == 789


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error(self) -> None:
        """Test validation error creation."""
        error = ValidationError("email", "invalid@", "Invalid email format")
        assert str(error) == "Validation error for field 'email': Invalid email format"
        assert error.field == "email"
        assert error.value == "invalid@"
        assert error.reason == "Invalid email format"

    def test_validation_error_with_complex_value(self) -> None:
        """Test validation error with complex value."""
        value = {"nested": {"field": "value"}}
        error = ValidationError("data", value, "Invalid structure")
        assert error.value == value
        assert error.details["value"] == value


class TestNetSuiteTimeoutError:
    """Tests for NetSuiteTimeoutError."""

    def test_timeout_error(self) -> None:
        """Test timeout error creation."""
        error = NetSuiteTimeoutError("searchRecords", 30)
        assert str(error) == "Operation 'searchRecords' timed out after 30 seconds"
        assert error.operation == "searchRecords"
        assert error.timeout_seconds == 30


class TestRESTletError:
    """Tests for RESTletError."""

    def test_restlet_error_basic(self) -> None:
        """Test basic RESTlet error."""
        error = RESTletError("customscript123")
        assert str(error) == "RESTlet error in script customscript123"
        assert error.script_id == "customscript123"
        assert error.error_code is None
        assert error.error_details is None

    def test_restlet_error_with_code(self) -> None:
        """Test RESTlet error with error code."""
        error = RESTletError("customscript123", "INVALID_PARAMS")
        assert str(error) == "RESTlet error in script customscript123: INVALID_PARAMS"
        assert error.error_code == "INVALID_PARAMS"

    def test_restlet_error_with_details(self) -> None:
        """Test RESTlet error with additional details."""
        details = {"missing_field": "customer_id", "line": 42}
        error = RESTletError("customscript123", "VALIDATION_ERROR", details)
        assert error.error_details == details
        assert error.details["error_details"] == details


class TestErrorInheritance:
    """Test error inheritance hierarchy."""

    def test_all_errors_inherit_from_base(self) -> None:
        """Test that all custom exceptions inherit from NetSuiteError."""
        error_classes = [
            AuthenticationError,
            NetSuitePermissionError,
            PageBoundsError,
            RecordNotFoundError,
            InvalidSearchCriteriaError,
            RateLimitError,
            SOAPFaultError,
            ConcurrencyError,
            ValidationError,
            ConfigurationError,
            NetSuiteTimeoutError,
            RESTletError,
        ]

        for error_class in error_classes:
            assert issubclass(error_class, NetSuiteError)
            assert issubclass(error_class, Exception)