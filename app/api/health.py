"""
Health check endpoints for monitoring application status.
"""

from fastapi import APIRouter

from app.api.dependencies import NetSuiteConfigDep, SettingsDep
from app.models.health import DetailedHealthResponse, HealthResponse, NetSuiteHealthInfo

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Returns basic application health status and metadata",
    responses={
        200: {
            "description": "Application is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "app_name": "NetSuite Proxy",
                        "version": "0.1.0",
                        "environment": "development",
                    }
                }
            },
        }
    },
)
async def health_check(settings: SettingsDep) -> HealthResponse:
    """
    Basic health check endpoint.

    Returns:
        Health status and basic application info
    """
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
    )


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    summary="Detailed health check",
    description="Returns detailed application health status including NetSuite configuration",
    responses={
        200: {
            "description": "Application is healthy with detailed configuration",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "app_name": "NetSuite Proxy",
                        "version": "0.1.0",
                        "environment": "development",
                        "debug": False,
                        "netsuite": {
                            "account": "TSTDRV123456",
                            "api_version": "2024_2",
                            "auth_configured": True,
                            "auth_type": "oauth",
                            "restlet_configured": True,
                        },
                    }
                }
            },
        }
    },
)
async def detailed_health_check(
    settings: SettingsDep, netsuite_config: NetSuiteConfigDep
) -> DetailedHealthResponse:
    """
    Detailed health check with configuration status.

    Returns:
        Detailed health status including NetSuite configuration
    """
    netsuite_info = NetSuiteHealthInfo(
        account=netsuite_config.account,
        api_version=netsuite_config.api,
        auth_configured=netsuite_config.auth_type != "none",
        auth_type=netsuite_config.auth_type,
        restlet_configured=bool(netsuite_config.script_id and netsuite_config.deploy_id),
    )

    return DetailedHealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        debug=settings.debug,
        netsuite=netsuite_info,
    )
