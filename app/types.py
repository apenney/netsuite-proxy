"""
Type definitions for NetSuite Proxy.

This module contains TypedDict and type alias definitions used throughout
the application to provide better type safety and documentation.
"""

from typing import Any, Literal, TypedDict

# Authentication Types
class NetSuitePasswordAuth(TypedDict):
    """Password authentication fields."""
    
    account: str
    email: str
    password: str
    role: str | None
    api_version: str | None


class NetSuiteOAuthAuth(TypedDict):
    """OAuth authentication fields."""
    
    account: str
    consumer_key: str
    consumer_secret: str
    token_id: str
    token_secret: str
    role: str | None
    api_version: str | None


class NetSuiteAuthBase(TypedDict, total=False):
    """Base authentication data with all possible fields."""
    
    account: str
    auth_type: Literal["password", "oauth", "none"]
    api_version: str | None
    role: str | None
    # Password auth fields
    email: str | None
    password: str | None
    # OAuth fields
    consumer_key: str | None
    consumer_secret: str | None
    token_id: str | None
    token_secret: str | None
    # RESTlet fields
    script_id: str | None
    deploy_id: str | None


# NetSuite auth that comes from middleware (always has account and auth_type)
class NetSuiteAuth(TypedDict):
    """Authenticated NetSuite context from middleware."""
    
    account: str
    auth_type: Literal["password", "oauth"]
    api_version: str | None
    role: str | None
    # Password auth fields (present when auth_type="password")
    email: str | None
    password: str | None
    # OAuth fields (present when auth_type="oauth")
    consumer_key: str | None
    consumer_secret: str | None
    token_id: str | None
    token_secret: str | None
    # RESTlet fields
    script_id: str | None
    deploy_id: str | None


# Request Context for Logging
class RequestContext(TypedDict):
    """HTTP request context for structured logging."""
    
    request_id: str
    method: str
    path: str
    client_ip: str | None


# Exception Detail Types
class PageBoundsErrorDetails(TypedDict):
    """Details for page bounds errors."""
    
    page: int
    total_pages: int


class RecordNotFoundErrorDetails(TypedDict):
    """Details for record not found errors."""
    
    record_type: str
    record_id: str | int


class RateLimitErrorDetails(TypedDict):
    """Details for rate limit errors."""
    
    retry_after: int | None


class SOAPFaultErrorDetails(TypedDict):
    """Details for SOAP fault errors."""
    
    fault_code: str
    fault_string: str
    detail: str | None


class ValidationErrorDetails(TypedDict):
    """Details for validation errors."""
    
    field: str
    value: Any
    reason: str


class TimeoutErrorDetails(TypedDict):
    """Details for timeout errors."""
    
    operation: str
    timeout_seconds: int


class RESTletErrorDetails(TypedDict):
    """Details for RESTlet errors."""
    
    script_id: str
    error_code: str | None
    error_details: dict[str, Any]


# API Response Types
class PaginationInfo(TypedDict):
    """Pagination information for list responses."""
    
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ListResponse(TypedDict):
    """Generic list response with pagination."""
    
    data: list[dict[str, Any]]
    pagination: PaginationInfo


# NetSuite Operation Response Types
class SearchResult(TypedDict):
    """NetSuite search result."""
    
    total_records: int
    page_index: int
    total_pages: int
    search_id: str | None
    records: list[dict[str, Any]]


class RecordResponse(TypedDict):
    """Single NetSuite record response."""
    
    internal_id: str
    external_id: str | None
    record_type: str
    data: dict[str, Any]


# Type Aliases for common patterns
ErrorDetails = dict[str, Any]  # Generic error details when structure varies
RecordData = dict[str, Any]    # NetSuite record data (varies by record type)
HeaderDict = dict[str, str]     # HTTP headers
QueryParams = dict[str, str | list[str]]  # Query parameters

# Optional NetSuite auth (for dependency injection)
OptionalNetSuiteAuth = NetSuiteAuth | None