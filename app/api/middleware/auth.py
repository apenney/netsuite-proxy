"""Authentication middleware for extracting NetSuite credentials from headers."""

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger


class NetSuiteAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for extracting and validating NetSuite authentication headers."""

    # Header names for NetSuite credentials
    ACCOUNT_HEADER = "X-NetSuite-Account"
    EMAIL_HEADER = "X-NetSuite-Email"
    PASSWORD_HEADER = "X-NetSuite-Password"
    ROLE_HEADER = "X-NetSuite-Role"

    # OAuth headers
    CONSUMER_KEY_HEADER = "X-NetSuite-Consumer-Key"
    CONSUMER_SECRET_HEADER = "X-NetSuite-Consumer-Secret"
    TOKEN_ID_HEADER = "X-NetSuite-Token-Id"
    TOKEN_SECRET_HEADER = "X-NetSuite-Token-Secret"

    # API version header
    API_VERSION_HEADER = "X-NetSuite-Api-Version"

    # Endpoints that don't require NetSuite auth
    EXEMPT_PATHS: ClassVar[list[str]] = [
        "/api/health",
        "/api/health/detailed",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
    ]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Extract NetSuite credentials from headers and add to request state."""
        # Skip authentication for exempt paths and their sub-paths
        path = request.url.path
        if any(path == exempt or path.startswith(exempt + "/") for exempt in self.EXEMPT_PATHS):
            return await call_next(request)

        # Get logger with request context if available
        request_id = getattr(request.state, "request_id", None)
        logger = get_logger(__name__, request_id=request_id) if request_id else get_logger(__name__)

        # Extract headers
        headers = request.headers

        # Check for account header (always required for NetSuite operations)
        account = headers.get(self.ACCOUNT_HEADER)
        if not account:
            logger.warning("Missing NetSuite account header")
            return JSONResponse(
                status_code=400, content={"detail": "Missing required header: X-NetSuite-Account"}
            )

        # Extract authentication credentials
        netsuite_auth = {
            "account": account,
            "api_version": headers.get(self.API_VERSION_HEADER),
        }

        # Check for password-based auth
        email = headers.get(self.EMAIL_HEADER)
        password = headers.get(self.PASSWORD_HEADER)
        if email and password:
            netsuite_auth.update(
                {
                    "email": email,
                    "password": password,
                    "role_id": headers.get(self.ROLE_HEADER),
                    "auth_type": "password",
                }
            )
            logger.info("Using password-based authentication", account=account)

        # Check for OAuth auth
        consumer_key = headers.get(self.CONSUMER_KEY_HEADER)
        consumer_secret = headers.get(self.CONSUMER_SECRET_HEADER)
        token_id = headers.get(self.TOKEN_ID_HEADER)
        token_secret = headers.get(self.TOKEN_SECRET_HEADER)

        if all([consumer_key, consumer_secret, token_id, token_secret]):
            netsuite_auth.update(
                {
                    "consumer_key": consumer_key,
                    "consumer_secret": consumer_secret,
                    "token_id": token_id,
                    "token_secret": token_secret,
                    "auth_type": "oauth",
                }
            )
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
