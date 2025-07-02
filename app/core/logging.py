"""Structured logging configuration using structlog.

This module configures structlog for the application with:
- JSON output in production
- Human-readable output in development
- Consistent log format across the application
- Integration with FastAPI request context
"""

import logging
import sys
from typing import Any

import structlog
from structlog.processors import CallsiteParameter

from app.core.config import get_settings


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
    use_json = settings.environment == "production" and not settings.debug

    # Common processors for all environments
    shared_processors = [
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
        processors=processors,
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
) -> dict[str, Any]:
    """Create request context for logging.

    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        client_ip: Client IP address if available

    Returns:
        Dictionary of request context
    """
    context = {
        "request_id": request_id,
        "method": method,
        "path": path,
    }
    if client_ip:
        context["client_ip"] = client_ip
    return context
