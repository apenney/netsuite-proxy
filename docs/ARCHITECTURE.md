# NetSuite Proxy Architecture

## Overview

The NetSuite Proxy service is a modern Python-based REST API that acts as an intermediary between client applications and NetSuite's SOAP (SuiteTalk) and RESTlet APIs. It's built using FastAPI, Pydantic, and follows clean architecture principles.

## Core Design Principles

1. **Type Safety**: Extensive use of Python type hints and Pydantic models for runtime validation
2. **Dependency Injection**: FastAPI's dependency system for clean, testable code
3. **Configuration Management**: Environment-based configuration using pydantic-settings
4. **Error Handling**: Comprehensive exception hierarchy with detailed error information
5. **API Documentation**: Automatic OpenAPI/Swagger documentation generation
6. **Testing**: Comprehensive unit tests with fixtures and mocking

## Project Structure

```
netsuite-proxy/
├── app/                    # Main application code
│   ├── api/               # API layer (endpoints, dependencies)
│   │   ├── endpoints/     # API endpoint modules
│   │   ├── auth_dependencies.py # Authentication dependency injections
│   │   ├── exception_handlers.py # Exception to HTTP response mapping
│   │   ├── health.py      # Health check endpoints
│   │   └── middleware/    # API middleware
│   │       ├── auth.py    # NetSuite authentication extraction
│   │       └── logging.py # Request/response logging
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration management
│   │   ├── constants.py   # Module-level constants (headers, defaults)
│   │   ├── exceptions.py  # Custom exception classes
│   │   ├── logging.py     # Structured logging configuration
│   │   └── security.py    # Security utilities (future)
│   ├── models/            # Pydantic models
│   │   ├── health.py      # Health check response models
│   │   └── ...            # Domain models
│   ├── services/          # Business logic layer
│   │   ├── netsuite/      # NetSuite integration services
│   │   │   ├── soap/      # SOAP/SuiteTalk client
│   │   │   └── restlet/   # RESTlet client
│   │   └── serializers/   # Data transformation
│   ├── main.py            # FastAPI application factory
│   └── asgi.py            # ASGI entry point
├── tests/                 # Test suite
├── docs/                  # Documentation
└── RUBY/                  # Legacy Ruby code (reference only)
```

## Layer Architecture

### 1. API Layer (`app/api/`)
- **Purpose**: Handle HTTP requests/responses, authentication, and validation
- **Components**:
  - **Endpoints**: FastAPI routers defining API routes
  - **Dependencies**: Reusable dependency injection functions
  - **Middleware**: Cross-cutting concerns (CORS, error handling, request logging, authentication)
- **Key Patterns**:
  - Use Pydantic models for request/response validation
  - Leverage FastAPI's dependency injection system
  - Apply OpenAPI documentation decorators

### 2. Core Layer (`app/core/`)
- **Purpose**: Application-wide utilities and configurations
- **Components**:
  - **Config**: Environment-based settings using pydantic-settings
  - **Exceptions**: Custom exception hierarchy
  - **Logging**: Structured logging with contextual information
  - **Security**: Authentication and authorization utilities
- **Key Patterns**:
  - Single source of truth for configuration
  - Rich exception information with structured details
  - Cached configuration instances

### 3. Models Layer (`app/models/`)
- **Purpose**: Define data structures and validation rules
- **Components**:
  - **Request Models**: Validate incoming API requests
  - **Response Models**: Structure API responses
  - **Domain Models**: Business entities
- **Key Patterns**:
  - Use Pydantic BaseModel for all models
  - Apply field validation and constraints
  - Document fields with descriptions

### 4. Services Layer (`app/services/`)
- **Purpose**: Business logic and external integrations
- **Components**:
  - **NetSuite Services**: SOAP and RESTlet clients
  - **Serializers**: Transform between API and NetSuite formats
  - **Business Services**: Domain-specific operations
- **Key Patterns**:
  - Separate business logic from API concerns
  - Handle NetSuite-specific transformations
  - Implement retry and error handling strategies

## Middleware Architecture

The application uses a layered middleware approach with careful ordering:

### Middleware Stack (in execution order)
1. **CORS Middleware** - Handles preflight requests and CORS headers
2. **RequestLoggingMiddleware** - Sets up request context and logging
   - Generates unique request IDs
   - Measures request duration
   - Logs request/response details
   - Sets up contextvar for automatic log context injection
3. **NetSuiteAuthMiddleware** - Extracts and validates NetSuite credentials
   - Checks exempt paths (health, docs, etc.)
   - Validates required headers
   - Sets auth context on request state

### Middleware Registration
```python
# In FastAPI, middleware executes in the order registered
app.add_middleware(NetSuiteAuthMiddleware)     # Executes third
app.add_middleware(RequestLoggingMiddleware)   # Executes second  
app.add_middleware(CORSMiddleware, ...)        # Executes first
```

### Path Exemption
The auth middleware exempts certain paths from authentication:
- `/api` (root path only, not sub-paths)
- `/api/health`, `/api/health/detailed`
- `/api/docs`, `/api/redoc`, `/api/openapi.json`

## Configuration Architecture

The application uses a hierarchical configuration system:

```python
Settings (root configuration)
├── app_name: str
├── version: str
├── environment: Literal["development", "staging", "production"]
├── debug: bool
├── api_prefix: str
├── cors_origins: list[str]
├── secret_key_base: str
└── netsuite: NetSuiteConfig
    ├── account: str
    ├── api: str (version)
    ├── email: str | None (password auth)
    ├── password: str | None (password auth)
    ├── consumer_key: str | None (OAuth)
    ├── consumer_secret: str | None (OAuth)
    ├── token_id: str | None (OAuth)
    ├── token_secret: str | None (OAuth)
    ├── script_id: str | None (RESTlet)
    └── deploy_id: str | None (RESTlet)
```

Environment variables use double underscore for nested configuration:
- `NETSUITE__ACCOUNT=TEST123`
- `NETSUITE__API=2024_2`

## Exception Handling Architecture

```
NetSuiteError (base exception)
├── AuthenticationError
├── NetSuitePermissionError  
├── PageBoundsError
├── RecordNotFoundError
├── RateLimitError
├── SOAPFaultError
├── ConcurrencyError
├── ValidationError
├── TimeoutError
└── RESTletError
```

Each exception includes:
- Human-readable message
- Structured details dictionary
- Specific error context (e.g., record ID, field name)

### HTTP Status Code Mapping
The exception handler automatically maps exception types to appropriate HTTP status codes:
- `AuthenticationError` → 401 Unauthorized
- `NetSuitePermissionError` → 403 Forbidden
- `RecordNotFoundError` → 404 Not Found
- `PageBoundsError` → 400 Bad Request
- `ValidationError` → 400 Bad Request
- `RateLimitError` → 429 Too Many Requests
- Other `NetSuiteError` subclasses → 500 Internal Server Error

## Dependency Injection Pattern

FastAPI's dependency injection is used extensively:

```python
# Define reusable dependencies
SettingsDep = Annotated[Settings, Depends(get_settings)]
NetSuiteConfigDep = Annotated[NetSuiteConfig, Depends(get_netsuite_config)]

# Use in endpoints
@router.get("/endpoint")
async def endpoint(settings: SettingsDep):
    # settings is automatically injected
    return {"app": settings.app_name}
```

## API Design Patterns

### 1. Response Models
All endpoints return Pydantic models for type safety and automatic documentation:

```python
class HealthResponse(BaseModel):
    status: Literal["healthy"]
    app_name: str
    version: str
    environment: str
```

### 2. Error Responses
Consistent error response format via exception handlers:

```json
{
    "error": "Record not found",
    "error_type": "RecordNotFoundError",
    "details": {
        "record_type": "Customer",
        "record_id": "12345"
    }
}
```

### 3. OpenAPI Documentation
Rich endpoint documentation with examples:

```python
@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Returns application health status",
    responses={
        200: {"description": "Application is healthy"}
    }
)
```

## Future Architecture Considerations

### 1. Service Layer Patterns
When implementing NetSuite services:
- Use abstract base classes for common operations
- Implement retry logic with exponential backoff
- Add circuit breakers for external service calls
- Cache frequently accessed data

### 2. Authentication & Authorization
- Implement API key authentication for clients
- Add role-based access control (RBAC)
- Support multiple authentication methods
- Implement request signing/verification

### 3. Performance Optimizations
- Connection pooling for NetSuite clients
- Request/response caching strategies
- Batch operation support
- Async processing for long-running operations

### 4. Monitoring & Observability
- ✅ Structured logging with correlation IDs (implemented with structlog)
  - JSON format in production, human-readable in development
  - Request IDs automatically generated and included in all logs
  - Request/response logging with duration tracking
  - ✅ **Automatic request context injection** using contextvars
    - All log messages within a request automatically include request_id, method, path, and client_ip
    - No need to manually pass request context to loggers
    - Context is properly isolated between concurrent requests
- Metrics collection (Prometheus) - future
- Distributed tracing (OpenTelemetry) - future
- ✅ Health check endpoints with detailed status (implemented)

## Development Workflow

1. **Define Models**: Start with Pydantic models for requests/responses
2. **Create Services**: Implement business logic in service layer
3. **Add Endpoints**: Create FastAPI endpoints using models and services
4. **Write Tests**: Unit tests for each component
5. **Document**: Update OpenAPI documentation and this guide