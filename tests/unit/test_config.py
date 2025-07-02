"""
Tests for configuration management.
"""

from typing import Any

import pytest

from app.core.config import NetSuiteConfig, Settings, get_netsuite_config, get_settings


def create_netsuite_config(**kwargs: Any) -> NetSuiteConfig:
    """Create NetSuiteConfig without reading from env or .env file."""
    # Provide defaults for required fields
    defaults = {"account": "TEST123"}
    defaults.update(kwargs)

    # Create config without env file loading
    # We use type: ignore because model_construct signature is complex
    return NetSuiteConfig.model_construct(**defaults)  # type: ignore[misc]


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
    # We use type: ignore because model_construct signature is complex
    return Settings.model_construct(**defaults)  # type: ignore[misc]


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
        monkeypatch.setenv("NETSUITE_TIMEOUT", "600")

        # This will read from env vars
        config = NetSuiteConfig()  # type: ignore[call-arg]
        assert config.account == "ENV_ACCOUNT"
        assert config.api == "2023_1"
        assert config.timeout == 600

    def test_email_validation(self) -> None:
        """Test email format validation."""
        # Valid email
        config = create_netsuite_config(email="test@example.com")
        assert config.email == "test@example.com"

        # Invalid email - test validation directly
        config = create_netsuite_config()
        with pytest.raises(ValueError) as exc_info:
            config.validate_email("invalid-email")
        assert "Invalid email format" in str(exc_info.value)

        # None is valid
        assert config.validate_email(None) is None
        assert config.validate_email("") == ""

    def test_password_validation(self) -> None:
        """Test password validation."""
        # Valid password
        config = create_netsuite_config(password="secret123")
        assert config.password == "secret123"

        # Empty password should fail validation
        config = create_netsuite_config()
        with pytest.raises(ValueError) as exc_info:
            config.validate_password("")
        assert "Password cannot be empty" in str(exc_info.value)

        # None is valid
        assert config.validate_password(None) is None

    def test_role_validation(self) -> None:
        """Test role ID validation."""
        # Valid role ID
        config = create_netsuite_config(role="123")
        assert config.role == "123"

        # Invalid role ID - test validation directly
        config = create_netsuite_config()
        with pytest.raises(ValueError) as exc_info:
            config.validate_role_id("admin")
        assert "Role ID must be numeric" in str(exc_info.value)

        # None and empty string are valid
        assert config.validate_role_id(None) is None
        assert config.validate_role_id("") == ""

    def test_wsdl_url_validation(self) -> None:
        """Test WSDL URL validation."""
        # Valid WSDL URL
        config = create_netsuite_config(
            wsdl_url="https://account.suitetalk.api.netsuite.com/wsdl/v2024_2/netsuite.wsdl"
        )
        assert config.wsdl_url is not None and "netsuite.com" in config.wsdl_url

        # Invalid WSDL URL - test validation directly
        config = create_netsuite_config()

        with pytest.raises(ValueError) as exc_info:
            config.validate_wsdl_url("ftp://invalid.com")
        assert "must start with http://" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            config.validate_wsdl_url("https://example.com/wsdl")
        assert "must be a NetSuite domain" in str(exc_info.value)

    def test_oauth_fields_validation(self) -> None:
        """Test OAuth fields validation."""
        # Valid OAuth config
        config = create_netsuite_config(
            consumer_key="key123",
            consumer_secret="secret123",
            token_id="token123",
            token_secret="tokensecret123",
        )
        assert config.consumer_key == "key123"

        # Empty OAuth field should fail validation
        config = create_netsuite_config()
        with pytest.raises(ValueError) as exc_info:
            config.validate_oauth_fields("")
        assert "OAuth fields cannot be empty" in str(exc_info.value)

    def test_timeout_validation(self) -> None:
        """Test timeout bounds validation."""
        # Valid timeout
        config = create_netsuite_config(timeout=300)
        assert config.timeout == 300

        # Test bounds with Pydantic validation
        with pytest.raises(ValueError):
            NetSuiteConfig(account="TEST", timeout=0)  # Too small

        with pytest.raises(ValueError):
            NetSuiteConfig(account="TEST", timeout=3601)  # Too large

    def test_oauth_completeness_validation(self) -> None:
        """Test OAuth fields must be provided together."""
        # Partial OAuth config should fail
        with pytest.raises(ValueError) as exc_info:
            NetSuiteConfig(
                account="TEST",
                consumer_key="key",
                consumer_secret="secret",
                # Missing token_id and token_secret
            )
        assert "OAuth authentication requires all four fields" in str(exc_info.value)

        # All fields provided should work
        config = NetSuiteConfig(
            account="TEST",
            consumer_key="key",
            consumer_secret="secret",
            token_id="token",
            token_secret="tokensecret",
        )
        assert config.has_oauth_auth

    def test_restlet_config_validation(self) -> None:
        """Test RESTlet configuration completeness."""
        # Partial RESTlet config should fail
        with pytest.raises(ValueError) as exc_info:
            NetSuiteConfig(
                account="TEST",
                script_id="123",
                # Missing deploy_id
            )
        assert "Both script_id and deploy_id must be provided" in str(exc_info.value)

        # Both fields provided should work
        config = NetSuiteConfig(account="TEST", script_id="123", deploy_id="1")
        assert config.script_id == "123"
        assert config.deploy_id == "1"


class TestSettings:
    """Tests for application settings."""

    def test_minimal_settings(self) -> None:
        """Test creating settings with minimal required fields."""
        settings = create_settings()
        assert settings.app_name == "NetSuite Proxy"
        assert settings.version == "0.1.0"
        assert settings.secret_key_base == "test-secret-key"
        assert settings.netsuite is not None
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
        assert settings.netsuite is not None
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
        monkeypatch.setenv("SECRET_KEY_BASE", "env-secret-key-that-is-32-chars-long-test")
        monkeypatch.setenv("NETSUITE__ACCOUNT", "ENV123")  # Using nested delimiter
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("DEBUG", "true")

        # Clear cache to pick up new env vars
        get_settings.cache_clear()

        settings = Settings()  # type: ignore[call-arg]
        assert settings.secret_key_base == "env-secret-key-that-is-32-chars-long-test"
        assert settings.netsuite is not None
        assert settings.netsuite.account == "ENV123"
        assert settings.environment == "staging"
        assert settings.debug is True


class TestConfigFunctions:
    """Tests for configuration helper functions."""

    def test_get_settings_caching(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_settings returns cached instance."""
        monkeypatch.setenv("SECRET_KEY_BASE", "test-secret-key-that-is-long-enough-32chars")
        monkeypatch.setenv("NETSUITE_ACCOUNT", "TEST")

        # Clear cache first
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # Same instance

    def test_get_netsuite_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_netsuite_config helper."""
        monkeypatch.setenv("SECRET_KEY_BASE", "test-secret-key-that-is-long-enough-32chars")
        monkeypatch.setenv("NETSUITE_ACCOUNT", "TEST123")

        # Clear cache first
        get_settings.cache_clear()

        config = get_netsuite_config()
        assert config.account == "TEST123"
        assert isinstance(config, NetSuiteConfig)

    def test_secret_key_validation(self) -> None:
        """Test secret key length validation."""
        # Too short secret key should fail
        with pytest.raises(ValueError) as exc_info:
            Settings(secret_key_base="short")
        errors = exc_info.value.errors() if hasattr(exc_info.value, "errors") else []
        assert len(errors) > 0 and "at least 32 characters" in str(errors[0].get("msg", ""))

        # Valid length secret key
        settings = Settings(secret_key_base="a" * 32)
        assert len(settings.secret_key_base) == 32

    def test_auth_token_validation(self) -> None:
        """Test endpoint auth token validation."""
        # Valid auth token
        settings = create_settings(endpoint_basic_auth_token="secure-token-16+")
        assert settings.endpoint_basic_auth_token == "secure-token-16+"

        # Too short auth token - test validator directly
        settings = create_settings()
        with pytest.raises(ValueError) as exc_info:
            settings.validate_auth_token("short")
        assert "at least 16 characters" in str(exc_info.value)

    def test_cors_origins_validation(self) -> None:
        """Test CORS origins validation."""
        # Valid CORS origins
        settings = create_settings(cors_origins=["https://example.com", "http://localhost:3000"])
        assert len(settings.cors_origins) == 2

        # Invalid CORS origin - test validator directly
        settings = create_settings()
        with pytest.raises(ValueError) as exc_info:
            settings.validate_cors_origins(["invalid-url"])
        assert "must be a valid URL" in str(exc_info.value)

        # Empty list should fail
        with pytest.raises(ValueError) as exc_info:
            settings.validate_cors_origins([])
        assert "cannot be empty" in str(exc_info.value)

    def test_production_settings_validation(self) -> None:
        """Test production environment validation."""
        # Debug mode in production should fail
        with pytest.raises(ValueError) as exc_info:
            Settings(secret_key_base="a" * 32, environment="production", debug=True)
        assert "Debug mode must be disabled in production" in str(exc_info.value)

        # Wildcard CORS in production should fail
        with pytest.raises(ValueError) as exc_info:
            Settings(secret_key_base="a" * 32, environment="production", cors_origins=["*"])
        assert "CORS wildcard (*) should not be used alone in production" in str(exc_info.value)

        # Valid production settings
        settings = Settings(
            secret_key_base="a" * 32,
            environment="production",
            debug=False,
            cors_origins=["https://app.example.com", "*"],  # Wildcard with specific origins is OK
        )
        assert settings.environment == "production"
