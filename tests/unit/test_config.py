"""
Tests for configuration management.
"""

import os
from typing import Any

import pytest
from pydantic import ValidationError

from app.core.config import NetSuiteConfig, Settings, get_netsuite_config, get_settings


def create_netsuite_config(**kwargs: Any) -> NetSuiteConfig:
    """Create NetSuiteConfig without reading from env or .env file."""
    # Provide defaults for required fields
    defaults = {"account": "TEST123"}
    defaults.update(kwargs)
    
    # Create config without env file loading
    # We use model_construct to bypass validation and env loading
    return NetSuiteConfig.model_construct(**defaults)


def create_settings(**kwargs: Any) -> Settings:
    """Create Settings without reading from env or .env file."""
    # Provide defaults for required fields
    defaults = {
        "secret_key_base": "test-secret-key",
        "netsuite": create_netsuite_config(account="TEST123"),
    }
    
    # Handle nested netsuite config
    if "netsuite" in kwargs:
        netsuite_data = kwargs.pop("netsuite")
        defaults["netsuite"] = create_netsuite_config(**netsuite_data)
    
    defaults.update(kwargs)
    
    # Create settings without env file loading
    return Settings.model_construct(**defaults)


class TestNetSuiteConfig:
    """Tests for NetSuite configuration."""

    def test_minimal_config(self) -> None:
        """Test creating config with minimal required fields."""
        config = create_netsuite_config(account="TEST123")
        assert config.account == "TEST123"
        assert config.api == "2024_2"  # default
        assert config.timeout == 1200  # default

    def test_api_version_validation(self) -> None:
        """Test API version format validation."""
        # Valid formats
        config = create_netsuite_config(api="2024_2")
        assert config.api == "2024_2"

        config = create_netsuite_config(api="2023_1")
        assert config.api == "2023_1"

        # Invalid formats - test validation directly
        config = create_netsuite_config()
        with pytest.raises(ValueError) as exc_info:
            config.validate_api_version("2024.2")
        assert "Invalid API version format" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            config.validate_api_version("2024")
        assert "Invalid API version format" in str(exc_info.value)

    def test_password_auth_detection(self) -> None:
        """Test password authentication detection."""
        # No auth
        config = create_netsuite_config()
        assert not config.has_password_auth
        assert config.auth_type == "none"

        # Partial password auth
        config = create_netsuite_config(email="test@example.com")
        assert not config.has_password_auth

        # Full password auth
        config = create_netsuite_config(email="test@example.com", password="secret")
        assert config.has_password_auth
        assert config.auth_type == "password"

    def test_oauth_auth_detection(self) -> None:
        """Test OAuth authentication detection."""
        # No auth
        config = create_netsuite_config()
        assert not config.has_oauth_auth
        assert config.auth_type == "none"

        # Partial OAuth auth
        config = create_netsuite_config(consumer_key="key")
        assert not config.has_oauth_auth

        # Full OAuth auth
        config = create_netsuite_config(
            consumer_key="key",
            consumer_secret="secret",
            token_id="token",
            token_secret="token_secret",
        )
        assert config.has_oauth_auth
        assert config.auth_type == "oauth"

    def test_auth_type_priority(self) -> None:
        """Test that OAuth takes priority over password auth."""
        config = create_netsuite_config(
            # Password auth
            email="test@example.com",
            password="secret",
            # OAuth auth
            consumer_key="key",
            consumer_secret="secret",
            token_id="token",
            token_secret="token_secret",
        )
        assert config.auth_type == "oauth"  # OAuth takes priority

    def test_wsdl_url_generation(self) -> None:
        """Test WSDL URL generation."""
        # Auto-generated URL
        config = create_netsuite_config(account="TSTDRV1234567", api="2024_2")
        expected = "https://tstdrv1234567.suitetalk.api.netsuite.com/wsdl/v2024_2_0/netsuite.wsdl"
        assert config.get_wsdl_url() == expected

        # Custom URL
        custom_url = "https://custom.netsuite.com/wsdl"
        config = create_netsuite_config(wsdl_url=custom_url)
        assert config.get_wsdl_url() == custom_url

    def test_env_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that NETSUITE_ prefix is used for env vars."""
        monkeypatch.setenv("NETSUITE_ACCOUNT", "ENV_ACCOUNT")
        monkeypatch.setenv("NETSUITE_API", "2023_1")
        monkeypatch.setenv("NETSUITE_TIMEOUT", "3600")

        # This will read from env vars
        config = NetSuiteConfig()
        assert config.account == "ENV_ACCOUNT"
        assert config.api == "2023_1"
        assert config.timeout == 3600


class TestSettings:
    """Tests for application settings."""

    def test_minimal_settings(self) -> None:
        """Test creating settings with minimal required fields."""
        settings = create_settings()
        assert settings.app_name == "NetSuite Proxy"
        assert settings.version == "0.1.0"
        assert settings.secret_key_base == "test-secret-key"
        assert settings.netsuite.account == "TEST123"

    def test_environment_settings(self) -> None:
        """Test environment-specific settings."""
        settings = create_settings(
            environment="production",
            debug=True,
            log_level="DEBUG",
        )
        assert settings.environment == "production"
        assert settings.debug is True
        assert settings.log_level == "DEBUG"

    def test_nested_netsuite_config(self) -> None:
        """Test that NetSuite config can be set."""
        settings = create_settings(
            netsuite={
                "account": "PROD123",
                "email": "admin@example.com",
                "password": "secure-pass",
            }
        )
        assert settings.netsuite.account == "PROD123"
        assert settings.netsuite.email == "admin@example.com"
        assert settings.netsuite.password == "secure-pass"
        assert settings.netsuite.has_password_auth

    def test_cors_origins_default(self) -> None:
        """Test CORS origins default value."""
        settings = create_settings()
        assert settings.cors_origins == ["*"]

    def test_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test reading from environment variables."""
        monkeypatch.setenv("SECRET_KEY_BASE", "env-secret")
        monkeypatch.setenv("NETSUITE_ACCOUNT", "ENV123")
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("DEBUG", "true")

        settings = Settings()
        assert settings.secret_key_base == "env-secret"
        assert settings.netsuite.account == "ENV123"
        assert settings.environment == "staging"
        assert settings.debug is True


class TestConfigFunctions:
    """Tests for configuration helper functions."""

    def test_get_settings_caching(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_settings returns cached instance."""
        monkeypatch.setenv("SECRET_KEY_BASE", "secret")
        monkeypatch.setenv("NETSUITE_ACCOUNT", "TEST")

        # Clear cache first
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # Same instance

    def test_get_netsuite_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_netsuite_config helper."""
        monkeypatch.setenv("SECRET_KEY_BASE", "secret")
        monkeypatch.setenv("NETSUITE_ACCOUNT", "TEST123")

        # Clear cache first
        get_settings.cache_clear()

        config = get_netsuite_config()
        assert config.account == "TEST123"
        assert isinstance(config, NetSuiteConfig)