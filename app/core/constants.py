"""Application-wide constants.

This module contains constants used throughout the application,
promoting code reuse and maintainability.
"""

from typing import Final

# NetSuite Headers
NETSUITE_ACCOUNT_HEADER: Final[str] = "X-NetSuite-Account"
NETSUITE_EMAIL_HEADER: Final[str] = "X-NetSuite-Email"
NETSUITE_PASSWORD_HEADER: Final[str] = "X-NetSuite-Password"
NETSUITE_ROLE_HEADER: Final[str] = "X-NetSuite-Role"
NETSUITE_CONSUMER_KEY_HEADER: Final[str] = "X-NetSuite-Consumer-Key"
NETSUITE_CONSUMER_SECRET_HEADER: Final[str] = "X-NetSuite-Consumer-Secret"
NETSUITE_TOKEN_ID_HEADER: Final[str] = "X-NetSuite-Token-Id"
NETSUITE_TOKEN_SECRET_HEADER: Final[str] = "X-NetSuite-Token-Secret"
NETSUITE_SCRIPT_ID_HEADER: Final[str] = "X-NetSuite-Script-Id"
NETSUITE_DEPLOY_ID_HEADER: Final[str] = "X-NetSuite-Deploy-Id"
NETSUITE_API_VERSION_HEADER: Final[str] = "X-NetSuite-Api-Version"

# NetSuite Defaults
NETSUITE_DEFAULT_API_VERSION: Final[str] = "2024_2"
NETSUITE_DEFAULT_SOAP_TIMEOUT: Final[int] = 1200  # 20 minutes
NETSUITE_DEFAULT_RESTLET_TIMEOUT: Final[int] = 300  # 5 minutes
NETSUITE_DEFAULT_APPLICATION_ID: Final[str] = "A1B2C3D4-E5F6-G7H8-I9J0-K1L2M3N4O5P6"

# API Routes
API_PREFIX: Final[str] = "/api"
HEALTH_PATH: Final[str] = "/health"
HEALTH_DETAILED_PATH: Final[str] = "/health/detailed"
AUTH_PATH: Final[str] = "/auth"
AUTH_INFO_PATH: Final[str] = "/auth/info"

# Authentication Exempt Paths (relative to API prefix)
EXEMPT_PATHS: Final[list[str]] = [
    "",  # Root API path
    "/openapi.json",
    "/docs",
    "/redoc",
    HEALTH_PATH,
    HEALTH_DETAILED_PATH,
    "/test",  # Test endpoints for exception handling
]
