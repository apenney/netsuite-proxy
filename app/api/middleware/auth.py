"""Authentication middleware for extracting NetSuite credentials from headers."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.constants import EXEMPT_PATHS, APIRoutes, NetSuiteHeaders
from app.core.logging import get_logger


class NetSuiteAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for extracting and validating NetSuite authentication headers."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Extract NetSuite credentials from headers and add to request state."""
        # Skip authentication for exempt paths and their sub-paths
        path = request.url.path
        exempt_full_paths = [f"{APIRoutes.PREFIX}{path}" for path in EXEMPT_PATHS]
        if any(path == exempt or path.startswith(exempt + "/") for exempt in exempt_full_paths):
            return await call_next(request)

        # Get logger with request context if available
        request_id = getattr(request.state, "request_id", None)
        logger = get_logger(__name__, request_id=request_id) if request_id else get_logger(__name__)

        # Extract headers as lowercase dict for case-insensitive access
        headers = {k.lower(): v for k, v in request.headers.items()}

        # Helper to get header value
        def get_header(header_name: str) -> str | None:
            return headers.get(header_name.lower())

        # Check for account header (always required for NetSuite operations)
        account = get_header(NetSuiteHeaders.ACCOUNT)
        if not account:
            logger.warning("Missing NetSuite account header")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Missing required header: {NetSuiteHeaders.ACCOUNT}"},
            )

        # Extract authentication credentials
        netsuite_auth = {
            "account": account,
            "api_version": get_header(NetSuiteHeaders.API_VERSION),
        }

        # Check for password-based auth
        email = get_header(NetSuiteHeaders.EMAIL)
        password = get_header(NetSuiteHeaders.PASSWORD)
        if email and password:
            netsuite_auth.update(
                {
                    "email": email,
                    "password": password,
                    "role_id": get_header(NetSuiteHeaders.ROLE),
                    "auth_type": "password",
                }
            )
            logger.info("Using password-based authentication", account=account)

        # Check for OAuth auth
        oauth_headers = {
            "consumer_key": get_header(NetSuiteHeaders.CONSUMER_KEY),
            "consumer_secret": get_header(NetSuiteHeaders.CONSUMER_SECRET),
            "token_id": get_header(NetSuiteHeaders.TOKEN_ID),
            "token_secret": get_header(NetSuiteHeaders.TOKEN_SECRET),
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


def get_netsuite_auth(request: Request) -> dict[str, Any]:
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
