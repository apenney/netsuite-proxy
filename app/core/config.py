"""
Configuration management for NetSuite Proxy.

This module handles all environment variable loading and configuration
for the application, including NetSuite credentials and API settings.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class NetSuiteConfig(BaseSettings):
    """NetSuite-specific configuration settings."""

    # Core NetSuite settings
    account: str = Field(..., description="NetSuite account ID")
    api: str = Field(default="2024_2", description="NetSuite API version")
    wsdl_url: str | None = Field(
        default=None,
        description="NetSuite WSDL URL (auto-generated if not provided)",
    )

    # Authentication - Password-based (legacy)
    email: str | None = Field(default=None, description="NetSuite user email")
    password: str | None = Field(default=None, description="NetSuite user password")
    role_id: str | None = Field(default=None, description="NetSuite role ID")

    # Authentication - OAuth/Token-based (recommended)
    consumer_key: str | None = Field(default=None, description="OAuth consumer key")
    consumer_secret: str | None = Field(default=None, description="OAuth consumer secret")
    token_id: str | None = Field(default=None, description="OAuth token ID")
    token_secret: str | None = Field(default=None, description="OAuth token secret")

    # RESTlet configuration
    script_id: str | None = Field(default=None, description="NetSuite RESTlet script ID")
    deploy_id: str | None = Field(default=None, description="NetSuite RESTlet deployment ID")

    # Additional settings
    limited_role: str | None = Field(default=None, description="Limited role ID for testing")
    production: bool = Field(default=True, description="Whether this is a production account")
    silent: bool = Field(default=True, description="Suppress NetSuite warnings")
    timeout: int = Field(default=1200, description="Request timeout in seconds (20 minutes)")

    @field_validator("api")
    @classmethod
    def validate_api_version(cls, v: str) -> str:
        """Validate API version format."""
        # Expected format: YYYY_N (e.g., 2024_2)
        parts = v.split("_")
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            msg = f"Invalid API version format: {v}. Expected format: YYYY_N (e.g., 2024_2)"
            raise ValueError(msg)
        return v

    @property
    def has_password_auth(self) -> bool:
        """Check if password authentication is configured."""
        return all([self.email, self.password])

    @property
    def has_oauth_auth(self) -> bool:
        """Check if OAuth authentication is configured."""
        return all([self.consumer_key, self.consumer_secret, self.token_id, self.token_secret])

    @property
    def auth_type(self) -> Literal["password", "oauth", "none"]:
        """Determine the authentication type available."""
        if self.has_oauth_auth:
            return "oauth"
        if self.has_password_auth:
            return "password"
        return "none"

    def get_wsdl_url(self) -> str:
        """Generate or return the WSDL URL."""
        if self.wsdl_url:
            return self.wsdl_url

        # Generate WSDL URL based on account and API version
        account_id = self.account.lower().replace("_", "-")
        return f"https://{account_id}.suitetalk.api.netsuite.com/wsdl/v{self.api}_0/netsuite.wsdl"

    model_config = SettingsConfigDict(
        env_prefix="NETSUITE_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from env
    )


class Settings(BaseSettings):
    """Application-wide settings."""

    # Application metadata
    app_name: str = Field(default="NetSuite Proxy", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment",
    )

    # API settings
    api_prefix: str = Field(default="/api", description="API route prefix")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS origins",
    )

    # Security
    secret_key_base: str = Field(..., description="Secret key for signing")
    endpoint_basic_auth_token: str | None = Field(
        default=None,
        description="Basic auth token for endpoint protection",
    )

    # NetSuite configuration
    netsuite: NetSuiteConfig | None = None

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: Literal["json", "console"] = Field(
        default="json",
        description="Logging format",
    )

    # External services
    sentry_dsn: str | None = Field(default=None, description="Sentry DSN for error tracking")
    new_relic_license_key: str | None = Field(
        default=None,
        description="New Relic license key",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        # Allow NetSuite settings to be set at the top level
        env_nested_delimiter="__",
        extra="ignore",  # Ignore extra fields from env
    )

    @model_validator(mode="after")
    def populate_netsuite(self) -> "Settings":
        """Populate NetSuite config from environment if not provided."""
        if self.netsuite is None:
            # Create NetSuiteConfig from environment
            self.netsuite = NetSuiteConfig()
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    This function returns a cached instance of the Settings object,
    ensuring that environment variables are only read once.
    """
    # Settings will be populated from environment variables
    return Settings()


# Convenience function for getting NetSuite config directly
def get_netsuite_config() -> NetSuiteConfig:
    """Get NetSuite configuration."""
    settings = get_settings()
    if settings.netsuite is None:
        raise RuntimeError("NetSuite configuration not available")
    return settings.netsuite
