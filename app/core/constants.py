"""Application-wide constants.

This module contains constants used throughout the application,
promoting code reuse and maintainability.
"""

from typing import Final


class NetSuiteHeaders:
    """HTTP header names for NetSuite authentication."""

    # Required header
    ACCOUNT: Final[str] = "X-NetSuite-Account"

    # Password authentication
    EMAIL: Final[str] = "X-NetSuite-Email"
    PASSWORD: Final[str] = "X-NetSuite-Password"
    ROLE: Final[str] = "X-NetSuite-Role"

    # OAuth authentication
    CONSUMER_KEY: Final[str] = "X-NetSuite-Consumer-Key"
    CONSUMER_SECRET: Final[str] = "X-NetSuite-Consumer-Secret"
    TOKEN_ID: Final[str] = "X-NetSuite-Token-Id"
    TOKEN_SECRET: Final[str] = "X-NetSuite-Token-Secret"

    # RESTlet configuration
    SCRIPT_ID: Final[str] = "X-NetSuite-Script-Id"
    DEPLOY_ID: Final[str] = "X-NetSuite-Deploy-Id"

    # Optional
    API_VERSION: Final[str] = "X-NetSuite-Api-Version"


class NetSuiteDefaults:
    """Default values for NetSuite configuration."""

    API_VERSION: Final[str] = "2024_2"
    SOAP_TIMEOUT: Final[int] = 1200  # 20 minutes
    RESTLET_TIMEOUT: Final[int] = 300  # 5 minutes
    APPLICATION_ID: Final[str] = "netsuite-proxy"


class APIRoutes:
    """API route prefixes and paths."""

    PREFIX: Final[str] = "/api"
    HEALTH: Final[str] = "/health"
    HEALTH_DETAILED: Final[str] = "/health/detailed"
    AUTH_INFO: Final[str] = "/auth/info"
    DOCS: Final[str] = "/docs"
    REDOC: Final[str] = "/redoc"
    OPENAPI: Final[str] = "/openapi.json"


# List of paths that don't require authentication
EXEMPT_PATHS: Final[list[str]] = [
    APIRoutes.HEALTH,
    APIRoutes.HEALTH_DETAILED,
    APIRoutes.DOCS,
    APIRoutes.REDOC,
    APIRoutes.OPENAPI,
]
