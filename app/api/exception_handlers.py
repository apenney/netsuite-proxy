"""Exception handlers for FastAPI application.

This module defines exception handlers that convert application
exceptions to appropriate HTTP responses.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    NetSuiteError,
    NetSuitePermissionError,
    RateLimitError,
    RecordNotFoundError,
    ValidationError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


async def netsuite_exception_handler(_request: Request, exc: NetSuiteError) -> JSONResponse:
    """Handle general NetSuite exceptions."""
    logger.error(
        "NetSuite error occurred",
        error_type=exc.__class__.__name__,
        message=exc.message,
        details=exc.details,
    )

    # Map specific exceptions to HTTP status codes
    status_code = 500  # Default to internal server error

    if isinstance(exc, AuthenticationError):
        status_code = 401
    elif isinstance(exc, NetSuitePermissionError):
        status_code = 403
    elif isinstance(exc, RecordNotFoundError):
        status_code = 404
    elif isinstance(exc, ValidationError):
        status_code = 400
    elif isinstance(exc, RateLimitError):
        status_code = 429

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.message,
            "error_type": exc.__class__.__name__,
            "details": exc.details,
        },
    )


async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception("Unexpected error occurred", exc_info=exc)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_type": "InternalError",
            "details": {"message": "An unexpected error occurred"},
        },
    )
