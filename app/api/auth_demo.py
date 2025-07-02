"""Demo endpoint to show NetSuite authentication usage."""

from typing import Annotated, TypedDict

from fastapi import APIRouter, Depends

from app.api.middleware import get_netsuite_auth
from app.core.logging import get_logger
from app.types import OptionalNetSuiteAuth

router = APIRouter()
logger = get_logger(__name__)


class AuthInfoResponse(TypedDict):
    """Response model for auth info endpoint."""

    account: str
    auth_type: str
    api_version: str
    has_role: bool


# Type alias for NetSuite auth dependency
NetSuiteAuth = Annotated[OptionalNetSuiteAuth, Depends(get_netsuite_auth)]


@router.get("/auth/info", response_model=AuthInfoResponse)
async def get_auth_info(auth: NetSuiteAuth) -> AuthInfoResponse:
    """
    Get information about the current NetSuite authentication.

    This endpoint demonstrates how to use the NetSuite auth dependency.
    It requires valid NetSuite credentials to be provided in headers.
    """
    if not auth:
        # This shouldn't happen with the middleware, but handle it gracefully
        logger.warning("Auth info requested but no auth available")
        return AuthInfoResponse(
            account="",
            auth_type="none",
            api_version="default",
            has_role=False,
        )

    # Log with context automatically included (request_id, method, path, etc.)
    logger.info(
        "Auth info requested",
        account=auth["account"],
        auth_type=auth.get("auth_type", "unknown"),
    )

    return AuthInfoResponse(
        account=auth["account"],
        auth_type=auth.get("auth_type", "unknown"),
        api_version=auth.get("api_version") or "default",
        has_role=auth.get("role") is not None,
    )
