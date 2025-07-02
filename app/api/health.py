"""
Health check endpoints for monitoring application status.
"""

from typing import Any

from fastapi import APIRouter

from app.core.config import get_netsuite_config, get_settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.

    Returns:
        Health status and basic application info
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }


@router.get("/health/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """
    Detailed health check with configuration status.

    Returns:
        Detailed health status including NetSuite configuration
    """
    settings = get_settings()
    netsuite_config = get_netsuite_config()

    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "debug": settings.debug,
        "netsuite": {
            "account": netsuite_config.account,
            "api_version": netsuite_config.api,
            "auth_configured": netsuite_config.auth_type != "none",
            "auth_type": netsuite_config.auth_type,
            "restlet_configured": bool(netsuite_config.script_id and netsuite_config.deploy_id),
        },
    }
