# Type System Guide

## Overview

This guide explains the type system used in the NetSuite Proxy project. We prioritize readable, domain-specific types over primitive type soup to make the codebase more maintainable and self-documenting.

## Core Principles

1. **Use TypedDict for structured data** instead of generic `dict[str, Any]`
2. **Create type aliases** for complex or frequently used types
3. **Break down nested types** into named components
4. **Prefer domain types** over primitives where it adds clarity

## Type Definitions

All custom types are defined in `app/types.py`. This central location makes it easy to:
- Find and understand data structures
- Maintain consistency across the codebase
- Update types in one place

## Key Types

### Authentication Types

```python
# Base authentication data with all possible fields
NetSuiteAuthBase = TypedDict(...)  # All auth fields, total=False

# Authenticated context from middleware
NetSuiteAuth = TypedDict(...)  # Required fields with auth_type

# Optional auth for dependency injection
OptionalNetSuiteAuth = NetSuiteAuth | None
```

**Usage Example:**
```python
# In dependencies
async def extract_netsuite_auth(...) -> NetSuiteAuthBase:
    # Extract and validate auth from headers
    
# In endpoints
async def get_customer(auth: NetSuiteAuth) -> CustomerResponse:
    # auth is guaranteed to have account and auth_type
```

### Response Types

```python
class AuthInfoResponse(TypedDict):
    """Response model for auth info endpoint."""
    account: str
    auth_type: str
    api_version: str
    has_role: bool
```

**Why:** Instead of returning `dict[str, str | bool]`, we define exactly what fields are in the response.

### Error Details

Each exception type has its own TypedDict for details:

```python
class RecordNotFoundErrorDetails(TypedDict):
    record_type: str
    record_id: str | int

class RateLimitErrorDetails(TypedDict):
    retry_after: int | None
```

**Usage:**
```python
raise RecordNotFoundError(
    "Customer", 
    "12345"
)  # Automatically creates typed details
```

### Request Context

```python
class RequestContext(TypedDict):
    """HTTP request context for structured logging."""
    request_id: str
    method: str
    path: str
    client_ip: str | None
```

**Why:** Makes logging consistent and type-safe across the application.

## Type Aliases

For common patterns, we use type aliases:

```python
# Clear, semantic aliases
HeaderDict = dict[str, str]
ErrorDetails = dict[str, Any]
RecordData = dict[str, Any]
QueryParams = dict[str, str | list[str]]
```

## Best Practices

### 1. Avoid Type Soup

❌ **Bad:**
```python
def process_auth(auth: dict[str, str | None] | None) -> dict[str, dict[str, str | None] | None]:
    # What does this even mean?
```

✅ **Good:**
```python
def process_auth(auth: OptionalNetSuiteAuth) -> AuthInfoResponse:
    # Clear input and output types
```

### 2. Use TypedDict for API Responses

❌ **Bad:**
```python
@router.get("/info")
async def get_info() -> dict[str, Any]:
    return {"status": "ok", "data": {...}}
```

✅ **Good:**
```python
class InfoResponse(TypedDict):
    status: Literal["ok", "error"]
    data: UserData

@router.get("/info", response_model=InfoResponse)
async def get_info() -> InfoResponse:
    return InfoResponse(status="ok", data=user_data)
```

### 3. Progressive Type Refinement

Start with broader types and refine as you validate:

```python
# Headers come in as generic dict
headers: dict[str, str] = request.headers

# Extract and validate into typed structure
auth_data: NetSuiteAuthBase = extract_auth(headers)

# Middleware ensures auth is valid
auth: NetSuiteAuth = validate_auth(auth_data)
```

### 4. Document Type Meanings

Always include docstrings for TypedDict classes:

```python
class SearchResult(TypedDict):
    """NetSuite search result.
    
    Contains paginated search results with metadata
    about the total result set.
    """
    total_records: int
    page_index: int
    total_pages: int
    search_id: str | None  # Only present for saved searches
    records: list[RecordData]
```

## When to Create New Types

Create a new TypedDict or type alias when:

1. **The same structure appears 3+ times** in the codebase
2. **The type is complex** (nested dicts, unions, etc.)
3. **Domain meaning is important** (e.g., `CustomerId` vs `str`)
4. **API contracts need documentation** (request/response models)

## Migration Strategy

When refactoring existing code:

1. **Identify repeated patterns** of dict usage
2. **Create TypedDict** in `app/types.py`
3. **Update function signatures** to use the new type
4. **Add runtime validation** where needed (Pydantic models)

## Integration with FastAPI

FastAPI works seamlessly with TypedDict:

```python
# TypedDict for response
class CustomerResponse(TypedDict):
    id: str
    name: str
    email: str

# Use directly in endpoint
@router.get("/customers/{id}", response_model=CustomerResponse)
async def get_customer(id: str) -> CustomerResponse:
    # FastAPI handles serialization
    return CustomerResponse(
        id=id,
        name="John Doe",
        email="john@example.com"
    )
```

## Future Improvements

As the codebase grows:

1. **Consider NewType** for semantic primitives:
   ```python
   CustomerId = NewType('CustomerId', str)
   EmailAddress = NewType('EmailAddress', str)
   ```

2. **Use Pydantic models** for complex validation:
   ```python
   class Customer(BaseModel):
       id: CustomerId
       email: EmailStr
       created_at: datetime
   ```

3. **Generate types from OpenAPI** for external APIs

## Examples from Our Codebase

### Before: Type Soup
```python
async def test_auth(
    auth: dict[str, str | None] | None = Depends(get_netsuite_auth)
) -> dict[str, dict[str, str | None] | None]:
    return {"auth": auth}
```

### After: Clear Types
```python
async def test_auth(
    auth: OptionalNetSuiteAuth = Depends(get_netsuite_auth)
) -> AuthResponse:
    return AuthResponse(auth=auth)
```

The second version immediately tells you:
- Input: Optional NetSuite authentication data
- Output: A structured auth response
- No need to guess what fields are in the dicts

## Conclusion

Good types are documentation that can't go out of date. They make the code:
- **Easier to understand** - types explain intent
- **Safer to refactor** - compiler catches mistakes
- **Better documented** - IDEs show helpful hints
- **More maintainable** - changes are localized

Always prefer specific, named types over generic dictionaries and primitives.