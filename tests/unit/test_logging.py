"""Tests for structured logging configuration."""

import logging

import pytest
import structlog
from structlog.testing import LogCapture

from app.core.logging import add_request_context, configure_logging, get_logger


class TestLoggingConfiguration:
    """Tests for logging configuration."""

    def test_configure_logging_development(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test logging configuration in development environment."""
        # Set development environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        # Clear any existing configuration
        structlog.reset_defaults()

        # Configure logging
        configure_logging()

        # Verify logger can be created
        logger = get_logger("test")
        assert logger is not None

    def test_configure_logging_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test logging configuration in production environment."""
        # Set production environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("LOG_LEVEL", "INFO")

        # Clear any existing configuration
        structlog.reset_defaults()

        # Configure logging
        configure_logging()

        # Create a logger
        logger = get_logger("test")
        assert logger is not None

    def test_get_logger_with_context(self) -> None:
        """Test getting logger with bound context."""
        logger = get_logger("test", user_id="123", request_id="abc")

        # Verify logger is created
        assert logger is not None

        # Note: We can't easily test the bound context without actually logging
        # This would require more complex setup with log capture

    def test_add_request_context(self) -> None:
        """Test creating request context for logging."""
        context = add_request_context(
            request_id="test-123", method="GET", path="/api/health", client_ip="192.168.1.1"
        )

        assert context == {
            "request_id": "test-123",
            "method": "GET",
            "path": "/api/health",
            "client_ip": "192.168.1.1",
        }

    def test_add_request_context_without_client_ip(self) -> None:
        """Test creating request context without client IP."""
        context = add_request_context(request_id="test-123", method="POST", path="/api/customers")

        assert context == {
            "request_id": "test-123",
            "method": "POST",
            "path": "/api/customers",
            "client_ip": None,
        }

    def test_logger_output_format(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that logger outputs in expected format."""
        # Configure for console output
        structlog.reset_defaults()
        configure_logging()

        # Get logger and log a message
        logger = get_logger("test")
        with caplog.at_level(logging.INFO):
            logger.info("Test message", key="value", number=42)

        # Verify output contains expected elements
        assert "Test message" in caplog.text
        assert "key" in caplog.text
        assert "value" in caplog.text

    def test_logger_exception_formatting(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that exceptions are properly formatted."""
        structlog.reset_defaults()
        configure_logging()

        logger = get_logger("test")

        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("Test exception")
            except ValueError:
                logger.exception("Error occurred")

        assert "Error occurred" in caplog.text
        assert "ValueError" in caplog.text
        assert "Test exception" in caplog.text


class TestStructuredLogging:
    """Tests for structured logging functionality."""

    @pytest.fixture
    def log_capture(self) -> LogCapture:
        """Fixture to capture structured logs."""
        return LogCapture()

    @pytest.fixture(autouse=True)
    def configure_test_logging(self, log_capture: LogCapture) -> None:
        """Configure structlog for testing."""
        structlog.configure(
            processors=[log_capture],
            logger_factory=structlog.PrintLoggerFactory(),
        )

    def test_structured_log_output(self, log_capture: LogCapture) -> None:
        """Test that logs are properly structured."""
        logger = get_logger("test")

        logger.info("User action", action="login", user_id="123", success=True)

        # Verify log was captured
        assert len(log_capture.entries) == 1

        # Verify log structure
        log_entry = log_capture.entries[0]
        assert log_entry["event"] == "User action"
        assert log_entry["action"] == "login"
        assert log_entry["user_id"] == "123"
        assert log_entry["success"] is True
        assert log_entry["log_level"] == "info"

    def test_logger_with_bound_context(self, log_capture: LogCapture) -> None:
        """Test logger with bound context."""
        base_logger = get_logger("test")
        logger = base_logger.bind(request_id="req-123", user_id="user-456")

        logger.info("Processing request")

        # Verify context is included
        assert len(log_capture.entries) == 1
        log_entry = log_capture.entries[0]
        assert log_entry["request_id"] == "req-123"
        assert log_entry["user_id"] == "user-456"
        assert log_entry["event"] == "Processing request"
