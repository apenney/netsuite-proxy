"""Structured logging configuration using structlog.

This module configures structlog for the application with:
- JSON output in production
- Human-readable output in development
- Consistent log format across the application
- Integration with FastAPI request context
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any, cast

import structlog
from structlog.processors import CallsiteParameter

from app.core.config import get_settings
from app.types import RequestContext

# Context variable for storing request context
request_context_var: ContextVar[dict[str, Any] | None] = ContextVar("request_context", default=None)


def inject_request_context(
    _logger: logging.Logger,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Inject request context into log events.

    This processor adds request context (request_id, method, path, etc.)
    to all log events when available.
    """
    context = request_context_var.get()
    if context is not None:
        event_dict.update(context)
    return event_dict


def configure_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    # Determine if we should use JSON or console rendering
    use_json = settings.environment in ("production", "test") and not settings.debug

    # Common processors for all environments
    shared_processors = [
        inject_request_context,  # Add request context first
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.dict_tracebacks,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                CallsiteParameter.FILENAME,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            ]
        ),
    ]

    # Environment-specific processors
    if use_json:
        # Production: JSON output
        processors = [*shared_processors, structlog.processors.JSONRenderer()]
    else:
        # Development: Human-readable output with colors
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    # Configure structlog
    structlog.configure(
        processors=cast("Any", processors),  # structlog's type hints are incomplete
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None, **kwargs: object) -> structlog.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (defaults to module name)
        **kwargs: Additional context to bind to the logger

    Returns:
        A configured structlog logger
    """
    logger = structlog.get_logger(name)
    if kwargs:
        logger = logger.bind(**kwargs)
    return logger


def add_request_context(
    request_id: str,
    method: str,
    path: str,
    client_ip: str | None = None,
) -> RequestContext:
    """Create request context for logging.

    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        client_ip: Client IP address if available

    Returns:
        Dictionary of request context
    """
    return RequestContext(
        request_id=request_id,
        method=method,
        path=path,
        client_ip=client_ip,
    )


def set_request_context(context: dict[str, Any]) -> None:
    """Set the request context for the current async context.

    This context will be automatically included in all log messages
    within the same async context (request).

    Args:
        context: Dictionary of context values to include in logs
    """
    request_context_var.set(context)


def clear_request_context() -> None:
    """Clear the request context."""
    request_context_var.set(None)
