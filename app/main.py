"""
Main application entry point for NetSuite Proxy.

This module creates and configures the FastAPI application instance.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth_demo import router as auth_router
from app.api.health import router as health_router
from app.api.middleware import NetSuiteAuthMiddleware, RequestLoggingMiddleware
from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    NetSuiteError,
    NetSuitePermissionError,
    PageBoundsError,
    RateLimitError,
    RecordNotFoundError,
    ValidationError,
)
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown tasks.
    """
    # Startup
    settings = get_settings()
    app.state.settings = settings

    # Configure logging
    configure_logging()
    logger = get_logger(__name__)
    logger.info(
        "Application started",
        app_name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        debug=settings.debug,
    )

    yield

    # Shutdown
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        lifespan=lifespan,
    )

    # Add middleware in order of execution
    # (FastAPI executes middleware in the order they are registered)

    # 1. CORS middleware (executes first - handles preflight requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Request logging middleware (executes second - sets up request context)
    app.add_middleware(RequestLoggingMiddleware)

    # 3. NetSuite authentication middleware (executes third - uses request context)
    app.add_middleware(NetSuiteAuthMiddleware)

    # Configure exception handlers
    @app.exception_handler(NetSuiteError)
    async def netsuite_exception_handler(  # pyright: ignore[reportUnusedFunction]
        _request: Request, exc: NetSuiteError
    ) -> JSONResponse:
        """Handle NetSuite-specific exceptions."""
        # Map exception types to HTTP status codes
        status_code_mapping: dict[type[NetSuiteError], int] = {
            AuthenticationError: 401,
            NetSuitePermissionError: 403,
            RecordNotFoundError: 404,
            PageBoundsError: 400,
            ValidationError: 400,
            RateLimitError: 429,
        }

        # Get the appropriate status code, defaulting to 500
        status_code = status_code_mapping.get(type(exc), 500)

        return JSONResponse(
            status_code=status_code,
            content={
                "error": exc.message,
                "error_type": exc.__class__.__name__,
                "details": exc.details,
            },
        )

    # Include routers
    app.include_router(health_router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(auth_router, prefix=settings.api_prefix, tags=["auth"])

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
