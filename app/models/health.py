"""
Pydantic models for health check responses.
"""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Basic health check response model."""

    status: Literal["healthy"] = Field(description="Health status of the application")
    app_name: str = Field(description="Name of the application")
    version: str = Field(description="Application version")
    environment: str = Field(description="Current environment (development, staging, production)")


class NetSuiteHealthInfo(BaseModel):
    """NetSuite configuration health information."""

    account: str = Field(description="NetSuite account ID")
    api_version: str = Field(description="NetSuite API version")
    auth_configured: bool = Field(description="Whether authentication is configured")
    auth_type: Literal["password", "oauth", "none"] = Field(
        description="Type of authentication configured"
    )
    restlet_configured: bool = Field(description="Whether RESTlet endpoints are configured")


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response including NetSuite configuration."""

    debug: bool = Field(description="Whether debug mode is enabled")
    netsuite: NetSuiteHealthInfo = Field(description="NetSuite configuration health information")
