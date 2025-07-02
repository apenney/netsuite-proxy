"""Authentication middleware for extracting NetSuite credentials from headers."""

from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.constants import (
    API_PREFIX,
    EXEMPT_PATHS,
    NETSUITE_ACCOUNT_HEADER,
    NETSUITE_API_VERSION_HEADER,
    NETSUITE_CONSUMER_KEY_HEADER,
    NETSUITE_CONSUMER_SECRET_HEADER,
    NETSUITE_EMAIL_HEADER,
    NETSUITE_PASSWORD_HEADER,
    NETSUITE_ROLE_HEADER,
    NETSUITE_TOKEN_ID_HEADER,
    NETSUITE_TOKEN_SECRET_HEADER,
)
from app.core.logging import get_logger
from app.types import NetSuiteAuthBase


class NetSuiteAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for extracting and validating NetSuite authentication headers."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Extract NetSuite credentials from headers and add to request state."""
        # Skip authentication for exempt paths and their sub-paths
        path = request.url.path
        exempt_full_paths = [f"{API_PREFIX}{path}" for path in EXEMPT_PATHS]
        if any(path == exempt or path.startswith(exempt + "/") for exempt in exempt_full_paths):
            return await call_next(request)

        # Get logger (request context will be automatically included if available)
        logger = get_logger(__name__)

        # Extract headers as lowercase dict for case-insensitive access
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Helper to get header value
        def get_header(header_name: str) -> str | None:
            return headers.get(header_name.lower())

        # Check for account header (always required for NetSuite operations)
        account = get_header(NETSUITE_ACCOUNT_HEADER)
        if not account:
            logger.warning("Missing NetSuite account header")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Missing required header: {NETSUITE_ACCOUNT_HEADER}"},
            )

        # Extract authentication credentials
        netsuite_auth = {
            "account": account,
            "api_version": get_header(NETSUITE_API_VERSION_HEADER),
        }

        # Check for password-based auth
        email = get_header(NETSUITE_EMAIL_HEADER)
        password = get_header(NETSUITE_PASSWORD_HEADER)
        if email and password:
            netsuite_auth.update(
                {
                    "email": email,
                    "password": password,
                    "role": get_header(NETSUITE_ROLE_HEADER),
                    "auth_type": "password",
                }
            )
            logger.info("Using password-based authentication", account=account)

        # Check for OAuth auth
        oauth_headers = {
            "consumer_key": get_header(NETSUITE_CONSUMER_KEY_HEADER),
            "consumer_secret": get_header(NETSUITE_CONSUMER_SECRET_HEADER),
            "token_id": get_header(NETSUITE_TOKEN_ID_HEADER),
            "token_secret": get_header(NETSUITE_TOKEN_SECRET_HEADER),
        }

        if all(oauth_headers.values()):
            netsuite_auth.update(oauth_headers)
            netsuite_auth["auth_type"] = "oauth"
            logger.info("Using OAuth authentication", account=account)

        # Verify we have some form of authentication
        if "auth_type" not in netsuite_auth:
            logger.warning("No valid authentication credentials provided")
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "No valid authentication credentials provided. "
                    "Either provide email/password or OAuth credentials."
                },
            )

        # Add NetSuite auth to request state
        request.state.netsuite_auth = netsuite_auth

        # Process request
        return await call_next(request)


def get_netsuite_auth(request: Request) -> NetSuiteAuthBase:
    """
    Get NetSuite authentication from request state.

    This is a dependency function that can be used in endpoints
    to access the NetSuite authentication information.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary containing NetSuite authentication details

    Raises:
        HTTPException: If authentication is not available
    """
    if not hasattr(request.state, "netsuite_auth"):
        raise HTTPException(
            status_code=500, detail="NetSuite authentication not available in request"
        )
    return request.state.netsuite_auth
