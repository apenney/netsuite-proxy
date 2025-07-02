# Testing Guidelines

## Overview

This document outlines the testing philosophy, patterns, and best practices for the NetSuite Proxy service. We use pytest as our testing framework with a focus on maintainability, clarity, and comprehensive coverage.

## Testing Philosophy

1. **Test Behavior, Not Implementation**: Focus on what the code does, not how it does it
2. **Isolation**: Each test should be independent and not rely on external state
3. **Clarity**: Test names should clearly describe what is being tested
4. **Fast Feedback**: Unit tests should run quickly to encourage frequent testing
5. **Realistic**: Use realistic test data that represents actual use cases

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/                # Unit tests for individual components
│   ├── test_config.py   # Configuration tests
│   ├── test_exceptions.py # Exception tests
│   └── test_health.py   # Health endpoint tests
├── integration/         # Integration tests (future)
└── e2e/                 # End-to-end tests (future)
```

## Writing Tests

### 1. Test File Naming
- Test files must start with `test_` prefix
- Match the module being tested: `app/core/config.py` → `tests/unit/test_config.py`

### 2. Test Class Organization
Group related tests using classes:

```python
class TestNetSuiteConfig:
    """Tests for NetSuite configuration."""
    
    def test_minimal_config(self):
        """Test configuration with minimal required fields."""
        pass
    
    def test_oauth_auth_detection(self):
        """Test OAuth authentication detection."""
        pass
```

### 3. Test Method Naming
Use descriptive names that explain the test scenario:

```python
def test_api_version_validation_invalid_format_raises_error(self):
    """Test that invalid API version format raises ValueError."""
    pass

def test_health_check_returns_200_with_valid_response(self):
    """Test health check endpoint returns 200 with valid response."""
    pass
```

### 4. Arrange-Act-Assert Pattern
Structure tests with clear sections:

```python
def test_record_not_found_error(self):
    # Arrange
    record_type = "Customer"
    record_id = "12345"
    
    # Act
    error = RecordNotFoundError(record_type, record_id)
    
    # Assert
    assert str(error) == "Customer record not found: 12345"
    assert error.details["record_type"] == record_type
    assert error.details["record_id"] == record_id
```

## Testing Patterns

### 1. Testing Pydantic Models

```python
def test_model_validation(self):
    """Test Pydantic model validation."""
    # Valid data
    model = MyModel(field1="value", field2=123)
    assert model.field1 == "value"
    assert model.field2 == 123
    
    # Invalid data
    with pytest.raises(ValidationError) as exc_info:
        MyModel(field1=123, field2="invalid")
    
    errors = exc_info.value.errors()
    assert len(errors) == 2
    assert errors[0]["loc"] == ("field1",)
    assert errors[0]["type"] == "string_type"
```

### 2. Testing FastAPI Endpoints

```python
def test_endpoint(client: TestClient):
    """Test API endpoint."""
    response = client.get("/api/endpoint")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "result" in data
```

### 3. Testing with Environment Variables

```python
def test_with_env_vars(monkeypatch: pytest.MonkeyPatch):
    """Test with environment variables."""
    # Set environment variables
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("DEBUG", "true")
    
    # Clear settings cache if using cached settings
    get_settings.cache_clear()
    
    # Test the behavior
    settings = get_settings()
    assert settings.app_name == "Test App"
    assert settings.debug is True
```

### 4. Testing Exceptions

```python
def test_custom_exception():
    """Test custom exception behavior."""
    error = CustomError("Something went wrong", details={"code": "ERR001"})
    
    assert str(error) == "Something went wrong"
    assert error.details["code"] == "ERR001"
    assert isinstance(error, BaseException)
```

### 5. Using Fixtures

```python
@pytest.fixture
def sample_config():
    """Provide sample configuration for tests."""
    return {
        "account": "TEST123",
        "api": "2024_2",
        "email": "test@example.com",
        "password": "secret"
    }

def test_with_fixture(sample_config):
    """Test using fixture data."""
    config = NetSuiteConfig(**sample_config)
    assert config.account == "TEST123"
```

## Test Fixtures (conftest.py)

### Global Fixtures

```python
@pytest.fixture
def client() -> TestClient:
    """Create test client for API testing."""
    from app.main import app
    return TestClient(app)

@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear settings cache before each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch):
    """Mock application settings."""
    monkeypatch.setenv("SECRET_KEY_BASE", "test-secret")
    monkeypatch.setenv("NETSUITE__ACCOUNT", "TEST123")
    # Add more as needed
```

## Best Practices

### 1. Avoid Hardcoded Test Data
Use fixtures or factory functions:

```python
@pytest.fixture
def customer_data():
    return {
        "id": "CUST123",
        "name": "Test Customer",
        "email": "customer@test.com"
    }
```

### 2. Test Edge Cases
Always test:
- Empty/None values
- Invalid data types
- Boundary conditions
- Error scenarios

### 3. Use Parametrized Tests
For testing multiple scenarios:

```python
@pytest.mark.parametrize("api_version,expected_valid", [
    ("2024_2", True),
    ("2023_1", True),
    ("invalid", False),
    ("2024", False),
    ("", False),
])
def test_api_version_formats(api_version, expected_valid):
    """Test various API version formats."""
    if expected_valid:
        config = NetSuiteConfig(account="TEST", api=api_version)
        assert config.api == api_version
    else:
        with pytest.raises(ValueError):
            NetSuiteConfig(account="TEST", api=api_version)
```

### 4. Mock External Dependencies
Use unittest.mock or pytest-mock:

```python
from unittest.mock import Mock, patch

@patch("app.services.netsuite.client.NetSuiteClient")
def test_with_mock(mock_client):
    """Test with mocked NetSuite client."""
    mock_client.return_value.search.return_value = [{"id": "123"}]
    
    result = search_customers("test")
    assert len(result) == 1
    mock_client.return_value.search.assert_called_once()
```

### 5. Test Async Code

```python
@pytest.mark.asyncio
async def test_async_endpoint(client: TestClient):
    """Test async endpoint."""
    response = await client.get("/api/async-endpoint")
    assert response.status_code == 200
```

## Coverage Guidelines

### Target Coverage
- Aim for >90% code coverage
- Focus on critical business logic
- Don't test obvious code (e.g., simple getters/setters)

### Running Coverage

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

### Coverage Configuration (pyproject.toml)

```toml
[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

## Integration Testing (Future)

### Database Tests
- Use test database or transactions
- Clean up after each test
- Test actual SQL queries

### External Service Tests
- Use VCR.py to record/replay HTTP interactions
- Mock time-sensitive operations
- Test error scenarios

## Performance Testing

### Basic Performance Tests

```python
import time

def test_endpoint_performance(client: TestClient):
    """Test endpoint responds within acceptable time."""
    start = time.time()
    response = client.get("/api/endpoint")
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 0.1  # 100ms threshold
```

## Test Data Management

### 1. Use Factories
Create factory functions for complex test data:

```python
def create_test_invoice(*, customer_id="CUST123", amount=100.0):
    """Create test invoice data."""
    return {
        "customer_id": customer_id,
        "amount": amount,
        "date": "2024-01-01",
        "items": [{"description": "Test Item", "amount": amount}]
    }
```

### 2. Realistic Test Data
- Use production-like data formats
- Test with various character sets
- Include edge cases from real scenarios

## Continuous Integration

### Pre-commit Hooks
Tests should pass before committing:

```yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest
      language: system
      types: [python]
      pass_filenames: false
```

### CI Pipeline
- Run tests on every pull request
- Fail builds if coverage drops
- Run different test suites in parallel

## Debugging Tests

### 1. Use pytest -v for Verbose Output
```bash
pytest -v tests/unit/test_config.py::TestNetSuiteConfig::test_oauth_auth_detection
```

### 2. Use pytest.set_trace() for Debugging
```python
def test_complex_logic():
    result = complex_function()
    pytest.set_trace()  # Debugger breakpoint
    assert result == expected
```

### 3. Print Debugging
```python
def test_with_print(capsys):
    print("Debug info")
    result = function_under_test()
    
    captured = capsys.readouterr()
    assert "Debug info" in captured.out
```

## Common Pitfalls to Avoid

1. **Don't test implementation details**: Test public interfaces, not private methods
2. **Avoid test interdependencies**: Each test should run independently
3. **Don't over-mock**: Too much mocking can hide real issues
4. **Avoid time-dependent tests**: Use time mocking for consistent results
5. **Don't ignore flaky tests**: Fix them or mark them appropriately

## Test Documentation

### Docstrings
Every test should have a clear docstring:

```python
def test_feature():
    """
    Test that feature X works correctly.
    
    This test verifies that when condition Y is met,
    the system responds with behavior Z.
    """
    pass
```

### Comments
Add comments for complex test logic:

```python
def test_complex_scenario():
    # Setup: Create user with specific permissions
    user = create_test_user(role="admin")
    
    # This simulates a race condition
    with concurrent_requests():
        response1 = client.post("/api/resource", user=user)
        response2 = client.post("/api/resource", user=user)
    
    # Only one should succeed
    assert (response1.status_code == 200) != (response2.status_code == 200)
```