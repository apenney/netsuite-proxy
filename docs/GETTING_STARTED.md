# Getting Started Guide

## Prerequisites

- Python 3.11 or higher
- Git
- Flox (optional but recommended for environment management)

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd netsuite-proxy
```

### 2. Set Up Development Environment

#### Option A: Using Flox (Recommended)
```bash
# Flox automatically manages the virtual environment
flox activate

# All dependencies are already available
```

#### Option B: Using Python venv
```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -e ".[dev]"
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required
SECRET_KEY_BASE=your-secret-key-here

# NetSuite Configuration
NETSUITE__ACCOUNT=TSTDRV123456
NETSUITE__API=2024_2

# For OAuth authentication
NETSUITE__CONSUMER_KEY=your-consumer-key
NETSUITE__CONSUMER_SECRET=your-consumer-secret
NETSUITE__TOKEN_ID=your-token-id
NETSUITE__TOKEN_SECRET=your-token-secret

# Optional
DEBUG=true
ENVIRONMENT=development
```

### 4. Verify Installation

```bash
# Run tests
pytest

# Run the application
python -m app.main

# Or with uvicorn
uvicorn app.main:app --reload
```

## Project Structure Overview

```
netsuite-proxy/
├── app/                 # Application code
│   ├── api/            # API endpoints
│   ├── core/           # Core utilities
│   ├── models/         # Pydantic models
│   └── services/       # Business logic
├── tests/              # Test suite
├── docs/               # Documentation
└── CLAUDE.md           # Project context for AI
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the patterns established in the codebase:

#### Adding a New Endpoint

1. Create a Pydantic model for request/response:
```python
# app/models/customer.py
from pydantic import BaseModel

class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
```

2. Create the endpoint:
```python
# app/api/customers.py
from fastapi import APIRouter
from app.models.customer import CustomerResponse

router = APIRouter()

@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str) -> CustomerResponse:
    # Implementation here
    return CustomerResponse(...)
```

3. Add router to main app:
```python
# app/main.py
from app.api.customers import router as customers_router

app.include_router(customers_router, prefix="/api", tags=["customers"])
```

### 3. Write Tests

```python
# tests/unit/test_customers.py
def test_get_customer(client: TestClient):
    response = client.get("/api/customers/123")
    assert response.status_code == 200
    assert response.json()["id"] == "123"
```

### 4. Run Quality Checks

```bash
# Format code
flox activate -- ruff format

# Run linter
flox activate -- ruff check --fix

# Run type checker
flox activate -- basedpyright

# Run tests
flox activate -- pytest
```

### 5. Commit Changes

```bash
git add -p  # Stage changes selectively
git commit -m "feat: add customer endpoint"
```

## Common Tasks

### Running the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Access the API docs
open http://localhost:8000/api/docs
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_health.py

# With coverage
pytest --cov=app --cov-report=html
```

### Adding Dependencies

```bash
# Add to pyproject.toml
# Then install in development mode
pip install -e ".[dev]"
```

### Debugging

1. Use breakpoints in VS Code or PyCharm
2. Use structured logging for debugging:
```python
from app.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing request", customer_id=customer_id, status="started")
```

3. Import constants from core:
```python
from app.core import NETSUITE_ACCOUNT_HEADER, DEFAULT_PAGE_SIZE
# Or import all NetSuite headers
from app.core.constants import (
    NETSUITE_ACCOUNT_HEADER,
    NETSUITE_EMAIL_HEADER,
    NETSUITE_PASSWORD_HEADER,
)
```

4. Use pytest debugging:
```bash
pytest -vv --pdb  # Drop into debugger on failure
```

## Environment Variables

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY_BASE` | Secret key for signing | Required |
| `DEBUG` | Debug mode | `false` |
| `ENVIRONMENT` | Deployment environment | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `NETSUITE__ACCOUNT` | NetSuite account ID | Required |
| `NETSUITE__API` | API version (e.g., 2024_2) | `2024_2` |

See [Configuration](../app/core/config.py) for full list.

## Making Authenticated API Calls

When calling endpoints that require NetSuite authentication, provide credentials via headers:

### Using cURL
```bash
# Password authentication
curl -H "X-NetSuite-Account: TEST123" \
     -H "X-NetSuite-Email: user@example.com" \
     -H "X-NetSuite-Password: password" \
     http://localhost:8000/api/auth/info

# OAuth authentication  
curl -H "X-NetSuite-Account: TEST123" \
     -H "X-NetSuite-Consumer-Key: key" \
     -H "X-NetSuite-Consumer-Secret: secret" \
     -H "X-NetSuite-Token-Id: token" \
     -H "X-NetSuite-Token-Secret: tokensecret" \
     http://localhost:8000/api/auth/info
```

### Using Python requests
```python
import requests

headers = {
    "X-NetSuite-Account": "TEST123",
    "X-NetSuite-Email": "user@example.com",
    "X-NetSuite-Password": "password"
}

response = requests.get("http://localhost:8000/api/auth/info", headers=headers)
```

## API Documentation

Once running, access interactive API documentation at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Best Practices

### Code Style
- Use type hints everywhere
- Follow PEP 8 (enforced by ruff)
- Write descriptive function/class names
- Add docstrings to public functions

### Testing
- Write tests for all new features
- Aim for >90% coverage
- Use fixtures for reusable test data
- Test edge cases and error scenarios

### Git Workflow
- Make small, focused commits
- Write clear commit messages
- Keep PR scope manageable
- Update documentation with code changes

## Troubleshooting

### Import Errors
```bash
# Ensure you're in the virtual environment
flox activate
# or
source .venv/bin/activate
```

### Test Failures
```bash
# Run specific test with verbose output
pytest -vv tests/unit/test_health.py::test_health_check

# Clear test cache
pytest --cache-clear
```

### Type Checking Issues
```bash
# Run basedpyright on specific file
flox activate -- basedpyright app/api/health.py
```

## Next Steps

1. Read the [Architecture Guide](./ARCHITECTURE.md)
2. Review [Testing Guidelines](./TESTING.md)
3. Understand [Pydantic Usage](./PYDANTIC_GUIDE.md)
4. Check existing code examples in `app/`
5. Start with a small feature or bug fix

## Getting Help

1. Check documentation in `docs/`
2. Look at existing tests for examples
3. Review similar implementations in codebase
4. Check `CLAUDE.md` for project context

## Useful Commands Reference

```bash
# Development
flox activate              # Activate environment
uvicorn app.main:app --reload  # Run with auto-reload
pytest -vv                 # Run tests verbosely

# Code Quality
ruff format               # Format code
ruff check --fix         # Fix linting issues
basedpyright             # Type check

# Git
git add -p              # Stage selectively
git commit -m "type: message"  # Commit with conventional format
pre-commit run          # Run pre-commit hooks
```