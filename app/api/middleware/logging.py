"""API middleware for request logging and processing."""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import (
    add_request_context,
    clear_request_context,
    get_logger,
    set_request_context,
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and log details."""
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state for access in endpoints
        request.state.request_id = request_id

        # Get client IP
        client_ip = request.client.host if request.client else None

        # Create request context
        context = add_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
        )

        # Set context for all loggers in this request
        set_request_context(dict(context))

        # Get logger (context will be automatically included)
        logger = get_logger(__name__)

        # Log request start
        start_time = time.time()
        logger.info(
            "Request started",
            query_params=dict(request.query_params),
            headers={
                k: v
                for k, v in request.headers.items()
                if k.lower() not in ["authorization", "cookie"]
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log successful response
            logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            logger.exception(
                "Request failed",
                duration_ms=round(duration * 1000, 2),
                error_type=type(exc).__name__,
            )

            # Re-raise the exception to be handled by FastAPI
            raise
        finally:
            # Clear request context
            clear_request_context()
