# API Reference

## Overview

The NetSuite Proxy API provides RESTful endpoints for interacting with NetSuite's SOAP and RESTlet APIs. All endpoints are prefixed with `/api` and return JSON responses.

## Base URL

```
http://localhost:8000/api
```

## Authentication

Currently, the API does not require authentication for health endpoints. NetSuite authentication is configured via environment variables.

Future endpoints will support:
- API Key authentication
- Bearer token authentication

## Common Response Formats

### Success Response

```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response

```json
{
  "error": "Error message",
  "error_type": "ErrorClassName",
  "details": {
    "field": "value",
    ...
  }
}
```

## Endpoints

### Health Check

#### Basic Health Check

Check if the service is running and healthy.

**Endpoint:** `GET /api/health`

**Response Model:** `HealthResponse`

**Example Request:**
```bash
curl http://localhost:8000/api/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "app_name": "NetSuite Proxy",
  "version": "0.1.0",
  "environment": "development"
}
```

**Response Fields:**
- `status` (string): Always "healthy" if service is running
- `app_name` (string): Application name from configuration
- `version` (string): Application version
- `environment` (string): Current environment (development/staging/production)

#### Detailed Health Check

Get detailed health information including NetSuite configuration status.

**Endpoint:** `GET /api/health/detailed`

**Response Model:** `DetailedHealthResponse`

**Example Request:**
```bash
curl http://localhost:8000/api/health/detailed
```

**Example Response:**
```json
{
  "status": "healthy",
  "app_name": "NetSuite Proxy",
  "version": "0.1.0",
  "environment": "development",
  "debug": false,
  "netsuite": {
    "account": "TSTDRV123456",
    "api_version": "2024_2",
    "auth_configured": true,
    "auth_type": "oauth",
    "restlet_configured": true
  }
}
```

**Response Fields:**
- All fields from basic health check, plus:
- `debug` (boolean): Whether debug mode is enabled
- `netsuite` (object): NetSuite configuration details
  - `account` (string): NetSuite account ID
  - `api_version` (string): NetSuite API version (e.g., "2024_2")
  - `auth_configured` (boolean): Whether authentication is configured
  - `auth_type` (string): Type of authentication ("password", "oauth", or "none")
  - `restlet_configured` (boolean): Whether RESTlet endpoints are configured

### NetSuite Operations (Coming Soon)

#### Customer Operations

##### List Customers
```
GET /api/customers
```

Query Parameters:
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20, max: 100)
- `search` (string): Search term
- `status` (string): Filter by status

##### Get Customer
```
GET /api/customers/{customer_id}
```

##### Create Customer
```
POST /api/customers
```

##### Update Customer
```
PUT /api/customers/{customer_id}
```

##### Delete Customer
```
DELETE /api/customers/{customer_id}
```

#### Invoice Operations

##### List Invoices
```
GET /api/invoices
```

##### Get Invoice
```
GET /api/invoices/{invoice_id}
```

##### Create Invoice
```
POST /api/invoices
```

## Error Codes

The API uses standard HTTP status codes:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Error Types

Custom exceptions that may be returned:

### NetSuiteError
Base error for all NetSuite-related issues.

### AuthenticationError
```json
{
  "error": "Authentication failed",
  "error_type": "AuthenticationError",
  "details": {
    "reason": "Invalid credentials"
  }
}
```

### PermissionError
```json
{
  "error": "Insufficient permissions",
  "error_type": "PermissionError",
  "details": {
    "required_permission": "view_customer"
  }
}
```

### RecordNotFoundError
```json
{
  "error": "Customer record not found: 12345",
  "error_type": "RecordNotFoundError",
  "details": {
    "record_type": "Customer",
    "record_id": "12345"
  }
}
```

### ValidationError
```json
{
  "error": "Validation failed",
  "error_type": "ValidationError",
  "details": {
    "field": "email",
    "value": "invalid-email",
    "reason": "Invalid email format"
  }
}
```

### RateLimitError
```json
{
  "error": "Rate limit exceeded",
  "error_type": "RateLimitError",
  "details": {
    "retry_after": 60
  }
}
```

## Rate Limiting

The API implements rate limiting to protect against abuse:

- Default: 100 requests per minute per IP
- Authenticated: 1000 requests per minute per API key
- Bulk operations: 10 requests per minute

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

## Pagination

List endpoints support pagination:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}
```

## Filtering and Searching

### Filter Syntax
```
GET /api/customers?status=active&created_after=2024-01-01
```

### Search Syntax
```
GET /api/customers?search=john+doe
```

### Sorting
```
GET /api/customers?sort=name&order=asc
```

## Batch Operations

Some endpoints support batch operations:

```json
POST /api/customers/batch
{
  "operations": [
    {
      "method": "create",
      "data": { ... }
    },
    {
      "method": "update",
      "id": "123",
      "data": { ... }
    }
  ]
}
```

## Webhooks (Future)

Configure webhooks for real-time updates:

```json
POST /api/webhooks
{
  "url": "https://your-domain.com/webhook",
  "events": ["customer.created", "invoice.paid"],
  "secret": "your-webhook-secret"
}
```

## API Versioning

The API uses URL versioning. The current version is v1 (implicit in `/api` prefix).

Future versions will use: `/api/v2/...`

## SDK Examples

### Python
```python
import requests

# Basic health check
response = requests.get("http://localhost:8000/api/health")
health = response.json()
print(f"Status: {health['status']}")

# Get customer (future)
response = requests.get(
    "http://localhost:8000/api/customers/123",
    headers={"Authorization": "Bearer your-token"}
)
customer = response.json()
```

### JavaScript
```javascript
// Basic health check
fetch('http://localhost:8000/api/health')
  .then(response => response.json())
  .then(health => console.log(`Status: ${health.status}`));

// Get customer (future)
fetch('http://localhost:8000/api/customers/123', {
  headers: {
    'Authorization': 'Bearer your-token'
  }
})
  .then(response => response.json())
  .then(customer => console.log(customer));
```

### cURL
```bash
# Basic health check
curl http://localhost:8000/api/health

# With authentication (future)
curl -H "Authorization: Bearer your-token" \
     http://localhost:8000/api/customers/123

# POST request (future)
curl -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-token" \
     -d '{"name": "John Doe", "email": "john@example.com"}' \
     http://localhost:8000/api/customers
```

## OpenAPI Specification

The full OpenAPI specification is available at:
- JSON: `http://localhost:8000/api/openapi.json`
- Interactive docs: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Testing the API

Use the interactive documentation to test endpoints:

1. Navigate to `http://localhost:8000/api/docs`
2. Click on an endpoint to expand it
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"

## Best Practices

1. **Always check status codes**: Don't assume 200 means success
2. **Handle rate limits**: Implement exponential backoff
3. **Use pagination**: Don't request all records at once
4. **Cache responses**: Reduce unnecessary API calls
5. **Validate input**: Check data before sending
6. **Log requests**: Keep audit trail for debugging