"""Core application utilities and configuration."""

from app.core.auth_config import AuthConfig, NoAuth, OAuthAuth, PasswordAuth
from app.core.config import NetSuiteConfig, Settings, get_netsuite_config, get_settings
from app.core.constants import EXEMPT_PATHS, APIRoutes, NetSuiteDefaults, NetSuiteHeaders
from app.core.exceptions import (
    AuthenticationError,
    ConcurrencyError,
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
from app.core.logging import add_request_context, configure_logging, get_logger

__all__ = [
    "EXEMPT_PATHS",
    "APIRoutes",
    "AuthConfig",
    "AuthenticationError",
    "ConcurrencyError",
    "NetSuiteConfig",
    "NetSuiteDefaults",
    "NetSuiteError",
    "NetSuiteHeaders",
    "NetSuitePermissionError",
    "NetSuiteTimeoutError",
    "NoAuth",
    "OAuthAuth",
    "PageBoundsError",
    "PasswordAuth",
    "RESTletError",
    "RateLimitError",
    "RecordNotFoundError",
    "SOAPFaultError",
    "Settings",
    "ValidationError",
    "add_request_context",
    "configure_logging",
    "get_logger",
    "get_netsuite_config",
    "get_settings",
]
