"""
Main application entry point for NetSuite Proxy.

This module creates and configures the FastAPI application instance.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import NetSuiteError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown tasks.
    """
    # Startup
    settings = get_settings()
    app.state.settings = settings

    yield

    # Shutdown
    # Add cleanup tasks here if needed


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

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure exception handlers
    @app.exception_handler(NetSuiteError)
    async def netsuite_exception_handler(_request: Request, exc: NetSuiteError) -> JSONResponse:
        """Handle NetSuite-specific exceptions."""
        return JSONResponse(
            status_code=500,
            content={
                "error": exc.message,
                "error_type": exc.__class__.__name__,
                "details": exc.details,
            },
        )

    # Include routers
    app.include_router(health_router, prefix=settings.api_prefix, tags=["health"])

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
