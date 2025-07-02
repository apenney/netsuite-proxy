"""Authentication dependencies for FastAPI endpoints.

This module provides reusable dependencies for extracting and validating
NetSuite authentication from request headers.
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from app.types import NetSuiteAuthBase, OptionalNetSuiteAuth

from app.core.constants import (
    NETSUITE_ACCOUNT_HEADER,
    NETSUITE_API_VERSION_HEADER,
    NETSUITE_CONSUMER_KEY_HEADER,
    NETSUITE_CONSUMER_SECRET_HEADER,
    NETSUITE_DEPLOY_ID_HEADER,
    NETSUITE_EMAIL_HEADER,
    NETSUITE_PASSWORD_HEADER,
    NETSUITE_ROLE_HEADER,
    NETSUITE_SCRIPT_ID_HEADER,
    NETSUITE_TOKEN_ID_HEADER,
    NETSUITE_TOKEN_SECRET_HEADER,
)
from app.core.logging import get_logger


async def extract_netsuite_auth(  # noqa: PLR0913
    request: Request,
    account: Annotated[str | None, Header(alias=NETSUITE_ACCOUNT_HEADER)] = None,
    email: Annotated[str | None, Header(alias=NETSUITE_EMAIL_HEADER)] = None,
    password: Annotated[str | None, Header(alias=NETSUITE_PASSWORD_HEADER)] = None,
    role: Annotated[str | None, Header(alias=NETSUITE_ROLE_HEADER)] = None,
    consumer_key: Annotated[str | None, Header(alias=NETSUITE_CONSUMER_KEY_HEADER)] = None,
    consumer_secret: Annotated[str | None, Header(alias=NETSUITE_CONSUMER_SECRET_HEADER)] = None,
    token_id: Annotated[str | None, Header(alias=NETSUITE_TOKEN_ID_HEADER)] = None,
    token_secret: Annotated[str | None, Header(alias=NETSUITE_TOKEN_SECRET_HEADER)] = None,
    script_id: Annotated[str | None, Header(alias=NETSUITE_SCRIPT_ID_HEADER)] = None,
    deploy_id: Annotated[str | None, Header(alias=NETSUITE_DEPLOY_ID_HEADER)] = None,
    api_version: Annotated[str | None, Header(alias=NETSUITE_API_VERSION_HEADER)] = None,
) -> NetSuiteAuthBase:
    """Extract NetSuite authentication from request headers.

    This dependency extracts all NetSuite-related headers and validates
    that proper authentication is provided.

    Returns:
        Dictionary containing NetSuite authentication information

    Raises:
        HTTPException: If required headers are missing or invalid
    """
    # Get logger with request context if available
    request_id = getattr(request.state, "request_id", None)
    logger = get_logger(__name__, request_id=request_id) if request_id else get_logger(__name__)

    # Account is always required
    if not account:
        logger.warning("Missing NetSuite account header")
        raise HTTPException(
            status_code=400,
            detail="Missing required header: X-NetSuite-Account",
        )

    # Build auth dict
    auth = {
        "account": account,
        "api_version": api_version,
        "role": role,
        "script_id": script_id,
        "deploy_id": deploy_id,
    }

    # Check authentication type
    has_password_auth = email and password
    has_oauth_auth = all([consumer_key, consumer_secret, token_id, token_secret])

    if has_oauth_auth:
        auth.update(
            {
                "auth_type": "oauth",
                "consumer_key": consumer_key,
                "consumer_secret": consumer_secret,
                "token_id": token_id,
                "token_secret": token_secret,
            }
        )
        logger.debug(
            "OAuth authentication extracted",
            account=account,
            has_restlet_config=bool(script_id and deploy_id),
        )
    elif has_password_auth:
        auth.update(
            {
                "auth_type": "password",
                "email": email,
                "password": password,
            }
        )
        logger.debug(
            "Password authentication extracted",
            account=account,
            email=email,
            has_role=bool(role),
        )
    else:
        logger.warning("Missing authentication credentials", account=account)
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide either password or OAuth credentials.",
        )

    # Return the auth dict directly - it matches NetSuiteAuthBase structure
    return auth  # type: ignore[return-value]


# Type alias for dependency injection
NetSuiteAuth = Annotated[NetSuiteAuthBase, Depends(extract_netsuite_auth)]


def get_netsuite_auth(request: Request) -> OptionalNetSuiteAuth:
    """Get NetSuite auth from request state if available.

    This is for optional auth scenarios where we want to check
    if auth was provided but don't require it.
    """
    return getattr(request.state, "netsuite_auth", None)
