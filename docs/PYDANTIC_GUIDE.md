# Pydantic Usage Guide

## Overview

Pydantic is a core dependency of this project, providing data validation, serialization, and type safety using Python type hints. This guide covers how we use Pydantic in the NetSuite Proxy service.

## Why Pydantic?

1. **Runtime Validation**: Validates data at runtime, catching errors early
2. **Type Safety**: Works with Python type hints and static type checkers
3. **Serialization**: Easy conversion between Python objects and JSON
4. **Documentation**: Automatic schema generation for API documentation
5. **Performance**: Fast validation using Rust-based pydantic-core

## Basic Concepts

### 1. BaseModel

All Pydantic models inherit from `BaseModel`:

```python
from pydantic import BaseModel

class Customer(BaseModel):
    id: str
    name: str
    email: str
    active: bool = True  # Default value
```

### 2. Field Validation

Use `Field` for additional validation and metadata:

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Product name")
    price: float = Field(gt=0, description="Price in USD")
    quantity: int = Field(ge=0, default=0, description="Stock quantity")
```

### 3. Optional Fields

Handle optional fields correctly:

```python
from typing import Optional

class User(BaseModel):
    name: str
    email: Optional[str] = None  # Optional with None default
    age: Optional[int]  # Required but can be None
    nickname: str | None = None  # Python 3.10+ union syntax
```

## Common Patterns in This Project

### 1. Configuration Models

We use Pydantic for configuration management:

```python
from pydantic import BaseSettings, Field
from typing import Literal

class Settings(BaseSettings):
    app_name: str = Field(default="NetSuite Proxy")
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"  # For NETSUITE__ACCOUNT=123
```

### 2. API Response Models

All API responses use Pydantic models:

```python
from pydantic import BaseModel
from typing import Literal

class HealthResponse(BaseModel):
    status: Literal["healthy"]
    app_name: str
    version: str
    environment: str
```

### 3. Request Validation

Validate incoming requests:

```python
from pydantic import BaseModel, validator
from datetime import datetime

class CreateInvoiceRequest(BaseModel):
    customer_id: str
    amount: float
    due_date: datetime
    
    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v
```

### 4. Nested Models

Handle complex data structures:

```python
class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str

class Customer(BaseModel):
    id: str
    name: str
    billing_address: Address
    shipping_address: Optional[Address] = None
```

## Validation Patterns

### 1. Field Validators

Use validators for complex validation logic:

```python
from pydantic import BaseModel, field_validator

class NetSuiteConfig(BaseModel):
    api: str
    
    @field_validator("api")
    @classmethod
    def validate_api_version(cls, v: str) -> str:
        """Validate API version format (YYYY_N)."""
        parts = v.split("_")
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValueError(f"Invalid API version: {v}")
        return v
```

### 2. Model Validators

Validate the entire model:

```python
from pydantic import BaseModel, model_validator
from typing import Self

class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime
    
    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
        return self
```

### 3. Computed Properties

Add computed fields using Pydantic v2's `computed_field` decorator:

```python
from pydantic import BaseModel, computed_field
from typing import Literal, Optional

class NetSuiteConfig(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    consumer_key: Optional[str] = None
    consumer_secret: Optional[str] = None
    
    @computed_field
    @property
    def auth_type(self) -> Literal["password", "oauth", "none"]:
        """Determine the authentication type available."""
        if self.consumer_key and self.consumer_secret:
            return "oauth"
        elif self.email and self.password:
            return "password"
        return "none"
```

Note: The `@computed_field` decorator is the Pydantic v2 way to handle computed properties. It ensures the field is included in model exports and schema generation.

### 4. Datetime Validation with Timezone Awareness

Always ensure datetimes are timezone-aware in your models:

```python
from datetime import datetime, UTC
import pendulum
from pydantic import BaseModel, field_validator

class QueryParams(BaseModel):
    created_since: datetime | None = None
    created_before: datetime | None = None
    
    @field_validator("created_since", "created_before", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime | str | None) -> datetime | None:
        """Ensure all datetime values are timezone-aware."""
        if v is None:
            return None
        if isinstance(v, str):
            # Use pendulum for robust timezone-aware parsing
            parsed = pendulum.parse(v, tz="UTC")
            # Convert to standard datetime
            return datetime(
                parsed.year, parsed.month, parsed.day,
                parsed.hour, parsed.minute, parsed.second,
                parsed.microsecond, tzinfo=UTC
            )
        if isinstance(v, datetime) and v.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware")
        return v
```

## Serialization and Deserialization

### 1. Model to Dict

```python
customer = Customer(id="123", name="John Doe", email="john@example.com")

# Convert to dictionary
data = customer.model_dump()
# {"id": "123", "name": "John Doe", "email": "john@example.com"}

# Exclude unset fields
data = customer.model_dump(exclude_unset=True)

# Exclude specific fields
data = customer.model_dump(exclude={"email"})
```

### 2. Model to JSON

```python
# Convert to JSON string
json_str = customer.model_dump_json()
# '{"id": "123", "name": "John Doe", "email": "john@example.com"}'

# Pretty print
json_str = customer.model_dump_json(indent=2)
```

### 3. Parsing Data

```python
# From dictionary
customer = Customer.model_validate({"id": "123", "name": "John"})

# From JSON string
customer = Customer.model_validate_json('{"id": "123", "name": "John"}')

# With error handling
from pydantic import ValidationError

try:
    customer = Customer.model_validate({"id": 123})  # Wrong type
except ValidationError as e:
    print(e.errors())
```

## Advanced Features

### 1. Discriminated Unions

Handle different types based on a discriminator field:

```python
from typing import Union, Literal
from pydantic import BaseModel, Field

class CreditCard(BaseModel):
    type: Literal["credit_card"] = "credit_card"
    number: str
    exp_month: int
    exp_year: int

class BankAccount(BaseModel):
    type: Literal["bank_account"] = "bank_account"
    account_number: str
    routing_number: str

class PaymentMethod(BaseModel):
    method: Union[CreditCard, BankAccount] = Field(discriminator="type")
```

### 2. Custom Types

Create reusable custom types:

```python
from pydantic import BaseModel, constr, conint
from typing import Annotated

# Constrained types
AccountId = constr(pattern=r"^[A-Z0-9]+$", min_length=3, max_length=20)
PositiveInt = conint(gt=0)

# Using Annotated for reusability
from pydantic import Field
Email = Annotated[str, Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")]

class Account(BaseModel):
    id: AccountId
    employee_count: PositiveInt
    contact_email: Email
```

### 3. Config Options

Customize model behavior:

```python
class StrictModel(BaseModel):
    name: str
    age: int
    
    model_config = ConfigDict(
        # Validate on assignment
        validate_assignment=True,
        # Use enum values instead of names
        use_enum_values=True,
        # Validate default values
        validate_default=True,
        # Extra fields cause error
        extra="forbid",
        # String strip whitespace
        str_strip_whitespace=True,
    )
```

## Integration with FastAPI

### 1. Request Body Validation

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class CreateCustomerRequest(BaseModel):
    name: str
    email: str
    company: Optional[str] = None

@router.post("/customers", response_model=CustomerResponse)
async def create_customer(customer: CreateCustomerRequest):
    # customer is automatically validated
    return CustomerResponse(...)
```

### 2. Query Parameter Validation

```python
from fastapi import Query
from pydantic import BaseModel

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

@router.get("/customers")
async def list_customers(
    pagination: PaginationParams = Depends()
):
    # Use pagination.page and pagination.page_size
    pass
```

### 3. Response Models

```python
class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime
    
    model_config = ConfigDict(
        # Serialize datetime as ISO string
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
```

## Best Practices

### 1. Use Type Hints Consistently

```python
# Good
def process_customer(customer: Customer) -> CustomerResponse:
    pass

# Bad
def process_customer(customer):
    pass
```

### 2. Provide Field Descriptions

```python
class Invoice(BaseModel):
    id: str = Field(description="Unique invoice identifier")
    amount: float = Field(description="Total amount in USD", gt=0)
    status: Literal["draft", "sent", "paid"] = Field(
        description="Current invoice status"
    )
```

### 3. Handle Validation Errors

```python
from fastapi import HTTPException
from pydantic import ValidationError

try:
    customer = Customer.model_validate(data)
except ValidationError as e:
    raise HTTPException(
        status_code=400,
        detail={"errors": e.errors()}
    )
```

### 4. Use Appropriate Field Types

```python
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID

class Transaction(BaseModel):
    id: UUID
    amount: Decimal  # For monetary values
    date: date  # Date without time
    timestamp: datetime  # Date with time
    metadata: dict[str, Any]  # Flexible structure
```

### 5. Avoid Mutable Defaults

```python
# Bad
class Model(BaseModel):
    items: list = []  # Shared between instances!

# Good
class Model(BaseModel):
    items: list = Field(default_factory=list)
```

## Testing Pydantic Models

### 1. Test Validation

```python
def test_customer_validation():
    # Valid data
    customer = Customer(id="123", name="John", email="john@example.com")
    assert customer.id == "123"
    
    # Invalid data
    with pytest.raises(ValidationError) as exc_info:
        Customer(id=123, name="John", email="invalid")
    
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("id",) for e in errors)
    assert any(e["loc"] == ("email",) for e in errors)
```

### 2. Test Serialization

```python
def test_customer_serialization():
    customer = Customer(id="123", name="John", email="john@example.com")
    
    # Test dict conversion
    data = customer.model_dump()
    assert data == {
        "id": "123",
        "name": "John",
        "email": "john@example.com"
    }
    
    # Test JSON conversion
    json_data = customer.model_dump_json()
    assert isinstance(json_data, str)
    
    # Test round trip
    parsed = Customer.model_validate_json(json_data)
    assert parsed == customer
```

## Common Pitfalls

### 1. Mutable Default Arguments
```python
# Wrong - default list is shared!
class Bad(BaseModel):
    items: list[str] = []

# Correct
class Good(BaseModel):
    items: list[str] = Field(default_factory=list)
```

### 2. Optional vs Default
```python
# Optional but required
field1: Optional[str]  # Must be provided, can be None

# Optional with default
field2: Optional[str] = None  # Not required, defaults to None

# Not optional but has default
field3: str = "default"  # Not required, cannot be None
```

### 3. Validator Order
Validators run in the order they're defined:
```python
class Model(BaseModel):
    value: str
    
    @field_validator("value")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip()
    
    @field_validator("value")
    @classmethod
    def check_not_empty(cls, v):
        # This runs after strip_whitespace
        if not v:
            raise ValueError("Cannot be empty")
        return v
```

## Performance Tips

1. **Reuse Models**: Create models once and reuse them
2. **Use TypeAdapter for Simple Validation**: For non-model validation
3. **Avoid Complex Validators**: Keep validation logic simple
4. **Use `model_construct()` Carefully**: Bypasses validation for performance
5. **Use `cached_property` for Expensive Computations**: Cache parsed results

```python
# Fast construction without validation (use carefully!)
customer = Customer.model_construct(
    id="123",
    name="John",
    email="john@example.com"
)

# Using cached_property for expensive parsing
from functools import cached_property

class QueryParams(BaseModel):
    ids: str | None = None
    
    @cached_property
    def id_list(self) -> list[int] | None:
        """Parse IDs into list - only computed once."""
        if not self.ids:
            return None
        # Expensive parsing logic here
        return parse_id_string(self.ids)
```

### Preventing DoS with Range Validation
When parsing ranges, always validate the size to prevent memory exhaustion:

```python
MAX_RANGE_SIZE = 10000

if end - start + 1 > MAX_RANGE_SIZE:
    raise ValueError(f"Range too large (max {MAX_RANGE_SIZE} items)")
```

## Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI + Pydantic Integration](https://fastapi.tiangolo.com/tutorial/body/)
- [Pydantic V2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- Project examples in `app/models/` and `app/core/config.py`