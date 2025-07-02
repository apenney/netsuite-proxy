"""Demo endpoint to show NetSuite authentication usage."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.middleware import get_netsuite_auth

router = APIRouter()

# Type alias for NetSuite auth dependency
NetSuiteAuth = Annotated[dict[str, str | None], Depends(get_netsuite_auth)]


@router.get("/auth/info")
async def get_auth_info(auth: NetSuiteAuth) -> dict[str, str | bool]:
    """
    Get information about the current NetSuite authentication.

    This endpoint demonstrates how to use the NetSuite auth dependency.
    It requires valid NetSuite credentials to be provided in headers.
    """
    return {
        "account": auth["account"] or "",
        "auth_type": auth["auth_type"] or "unknown",
        "api_version": auth.get("api_version") or "default",
        "has_role": auth.get("role_id") is not None,
    }
