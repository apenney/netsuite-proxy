"""
Configuration management for NetSuite Proxy.

This module handles all environment variable loading and configuration
for the application, including NetSuite credentials and API settings.
"""

import os
import re
from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class NetSuiteConfig(BaseSettings):
    """NetSuite-specific configuration settings."""

    # Core NetSuite settings
    account: str = Field(
        default="",
        description="NetSuite account ID",
        pattern=r"^[A-Za-z0-9_-]*$",  # Allow empty for test environments
    )
    api: str = Field(default="2024_2", description="NetSuite API version")
    wsdl_url: str | None = Field(
        default=None,
        description="NetSuite WSDL URL (auto-generated if not provided)",
    )

    # Authentication - Password-based (legacy)
    email: str | None = Field(default=None, description="NetSuite user email")
    password: str | None = Field(default=None, description="NetSuite user password")
    role: str | None = Field(default=None, description="NetSuite role ID")

    # Authentication - OAuth/Token-based (recommended)
    consumer_key: str | None = Field(default=None, description="OAuth consumer key")
    consumer_secret: str | None = Field(default=None, description="OAuth consumer secret")
    token_id: str | None = Field(default=None, description="OAuth token ID")
    token_secret: str | None = Field(default=None, description="OAuth token secret")

    # RESTlet configuration
    script_id: str | None = Field(default=None, description="NetSuite RESTlet script ID")
    deploy_id: str | None = Field(default=None, description="NetSuite RESTlet deployment ID")

    # Additional settings
    application_id: str | None = Field(default=None, description="Application ID for SOAP requests")
    limited_role: str | None = Field(default=None, description="Limited role ID for testing")
    production: bool = Field(default=True, description="Whether this is a production account")
    silent: bool = Field(default=True, description="Suppress NetSuite warnings")
    timeout: int = Field(
        default=1200,
        description="Request timeout in seconds (20 minutes)",
        ge=1,  # Must be at least 1 second
        le=3600,  # Max 1 hour
    )

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

    @field_validator("account")
    @classmethod
    def validate_account(cls, v: str) -> str:
        """Validate account is provided when needed."""
        # Account can be empty in test environment or when not configured
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format if provided."""
        if v is not None and v != "" and not re.match(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v
        ):
            raise ValueError(f"Invalid email format: {v}")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """Validate password is not empty if provided."""
        if v is not None and v == "":
            raise ValueError("Password cannot be empty")
        return v

    @field_validator("role", "limited_role")
    @classmethod
    def validate_role_id(cls, v: str | None) -> str | None:
        """Validate role ID is numeric if provided."""
        if v is not None and v != "" and not v.isdigit():
            raise ValueError(f"Role ID must be numeric: {v}")
        return v

    @field_validator("wsdl_url")
    @classmethod
    def validate_wsdl_url(cls, v: str | None) -> str | None:
        """Validate WSDL URL format if provided."""
        if v is not None and v != "":
            if not v.startswith(("http://", "https://")):
                raise ValueError(f"WSDL URL must start with http:// or https://: {v}")
            if ".netsuite.com" not in v:
                raise ValueError(f"WSDL URL must be a NetSuite domain: {v}")
        return v

    @field_validator("consumer_key", "consumer_secret", "token_id", "token_secret")
    @classmethod
    def validate_oauth_fields(cls, v: str | None) -> str | None:
        """Validate OAuth fields are not empty if provided."""
        if v is not None and v == "":
            raise ValueError("OAuth fields cannot be empty if provided")
        return v

    @computed_field
    @property
    def has_password_auth(self) -> bool:
        """Check if password authentication is configured."""
        return bool(self.email and self.password)

    @computed_field
    @property
    def has_oauth_auth(self) -> bool:
        """Check if OAuth authentication is configured."""
        return bool(
            self.consumer_key and self.consumer_secret and self.token_id and self.token_secret
        )

    @computed_field
    @property
    def auth_type(self) -> Literal["password", "oauth", "none"]:
        """Determine the authentication type available."""
        if self.has_oauth_auth:
            return "oauth"
        if self.has_password_auth:
            return "password"
        return "none"

    @model_validator(mode="after")
    def validate_oauth_completeness(self) -> Self:
        """Ensure OAuth fields are provided together."""
        oauth_fields = [self.consumer_key, self.consumer_secret, self.token_id, self.token_secret]
        provided = [f for f in oauth_fields if f is not None]

        if provided and len(provided) != 4:
            raise ValueError(
                "OAuth authentication requires all four fields: "
                "consumer_key, consumer_secret, token_id, and token_secret"
            )
        return self

    @model_validator(mode="after")
    def validate_restlet_config(self) -> Self:
        """Ensure RESTlet configuration is complete if provided."""
        if (self.script_id is None) != (self.deploy_id is None):
            raise ValueError(
                "Both script_id and deploy_id must be provided for RESTlet configuration"
            )
        return self

    def get_wsdl_url(self) -> str:
        """Generate or return the WSDL URL."""
        if self.wsdl_url:
            return self.wsdl_url

        # Generate WSDL URL based on account and API version
        account_id = self.account.lower().replace("_", "-")
        return f"https://{account_id}.suitetalk.api.netsuite.com/wsdl/v{self.api}_0/netsuite.wsdl"

    model_config = SettingsConfigDict(
        env_prefix="NETSUITE_",
        env_file=".env" if os.getenv("ENVIRONMENT", "development") != "test" else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from env
    )


class Settings(BaseSettings):
    """Application-wide settings."""

    # Application metadata
    app_name: str = Field(default="NetSuite Proxy", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: Literal["development", "staging", "production", "test"] = Field(
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
    secret_key_base: str = Field(
        ...,
        description="Secret key for signing",
        min_length=32,  # Ensure sufficient entropy
    )
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
        env_file=".env" if os.getenv("ENVIRONMENT", "development") != "test" else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Allow NetSuite settings to be set at the top level
        env_nested_delimiter="__",
        extra="ignore",  # Ignore extra fields from env
    )

    @field_validator("endpoint_basic_auth_token")
    @classmethod
    def validate_auth_token(cls, v: str | None) -> str | None:
        """Validate auth token strength if provided."""
        if v is not None and v != "" and len(v) < 16:
            raise ValueError("Authentication token must be at least 16 characters")
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Validate CORS origins format."""
        if not v:
            raise ValueError("CORS origins cannot be empty")

        for origin in v:
            if origin == "*":
                continue  # Wildcard is allowed

            # Basic URL validation
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"CORS origin must be a valid URL or '*': {origin}")

        return v

    @field_validator("log_format")
    @classmethod
    def validate_log_format_env(cls, v: str) -> str:
        """Set log format based on environment if not explicitly set."""
        # This is handled in the default_factory pattern
        return v

    @model_validator(mode="after")
    def populate_netsuite(self) -> Self:
        """Populate NetSuite config from environment if not provided."""
        if self.netsuite is None:
            # Create NetSuiteConfig from environment
            self.netsuite = NetSuiteConfig()
        return self

    @model_validator(mode="after")
    def validate_production_settings(self) -> Self:
        """Validate production environment requirements."""
        if self.environment == "production":
            if self.debug:
                raise ValueError("Debug mode must be disabled in production")
            if "*" in self.cors_origins and len(self.cors_origins) == 1:
                raise ValueError("CORS wildcard (*) should not be used alone in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    This function returns a cached instance of the Settings object,
    ensuring that environment variables are only read once.
    """
    # Settings will be populated from environment variables
    # The env file is handled by the model_config in Settings class
    return Settings()


# Convenience function for getting NetSuite config directly
def get_netsuite_config() -> NetSuiteConfig:
    """Get NetSuite configuration."""
    settings = get_settings()
    if settings.netsuite is None:
        raise RuntimeError("NetSuite configuration not available")
    return settings.netsuite
