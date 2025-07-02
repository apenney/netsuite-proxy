"""Authentication configuration models using discriminated unions."""

from typing import Literal

from pydantic import BaseModel, Field


class PasswordAuth(BaseModel):
    """Password-based authentication configuration."""

    type: Literal["password"] = "password"
    email: str = Field(..., description="NetSuite user email")
    password: str = Field(..., description="NetSuite user password")
    role: str | None = Field(default=None, description="Optional role ID")


class OAuthAuth(BaseModel):
    """OAuth authentication configuration."""

    type: Literal["oauth"] = "oauth"
    consumer_key: str = Field(..., description="OAuth consumer key")
    consumer_secret: str = Field(..., description="OAuth consumer secret")
    token_id: str = Field(..., description="OAuth token ID")
    token_secret: str = Field(..., description="OAuth token secret")


class NoAuth(BaseModel):
    """No authentication configured."""

    type: Literal["none"] = "none"


# Union type for all authentication methods
AuthConfig = PasswordAuth | OAuthAuth | NoAuth
