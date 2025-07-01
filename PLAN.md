# NetSuite Rails to Python Migration Plan

## Executive Summary

This document outlines a comprehensive plan to migrate the existing NetSuite proxy service from Rails 5/Ruby 2.3 to a modern Python-based solution. The existing service acts as a REST-to-SOAP proxy, offering a RESTful API to clients while communicating with NetSuite via SOAP (SuiteTalk) and RESTlet scripts.

The old ruby code is located in `RUBY/` and should serve PURELY as a reference.

## Architecture Analysis

### Current Rails Architecture

1. **Dual API Strategy**

   - SOAP API (SuiteTalk) using the NetSuite Ruby gem
   - RESTlet API for efficient searching and custom operations

2. **Key Components**

   - Controllers: REST endpoints inheriting from `BaseRecordController` or `BaseRestletRecordController`
   - Services: Business logic with SOAP/REST translation
   - Serializers: Field mapping between REST API and NetSuite SOAP fields
   - Custom utilities in `lib/`: Error handling, search enhancements, authentication

3. **Authentication Methods**

   - Password-based (email, password, account, role) - Legacy
   - OAuth/Token-based (consumer key/secret, token ID/secret) - Recommended

4. **Performance Optimizations**
   - Batching service for bulk operations
   - RESTlet scripts for complex searches
   - Field selection to reduce payload size
   - Caching and connection pooling

## Python Technology Stack

### Recommended Libraries

1. **Web Framework**: FastAPI

   - Modern, fast, with automatic OpenAPI documentation
   - Native async support for better performance
   - Type hints and validation built-in

2. **SOAP Integration**: zeep

   - Actively maintained (unlike suds)
   - Handles NetSuite's complex WSDL
   - Support for large XML responses with `xml_huge_tree` option

3. **RESTlet Integration**: requests-oauthlib

   - OAuth 1.0a support with HMAC-SHA256
   - Simple integration with existing RESTlet scripts

4. **Testing**: pytest with vcrpy

   - Similar functionality to Ruby's VCR
   - Records HTTP interactions for testing

5. **Additional Libraries**
   - pydantic: Data validation and serialization
   - httpx: Async HTTP client
   - python-dotenv: Environment variable management
   - structlog: Structured logging

## Migration Strategy

### Phase 1: Foundation Setup (Week 1-2)

1. **Project Structure**

   ```
   netsuite-proxy/
   ├── app/
   │   ├── api/
   │   │   ├── endpoints/
   │   │   ├── dependencies/
   │   │   └── middleware/
   │   ├── core/
   │   │   ├── config.py
   │   │   ├── security.py
   │   │   └── exceptions.py
   │   ├── services/
   │   │   ├── netsuite/
   │   │   │   ├── soap/
   │   │   │   └── restlet/
   │   │   └── serializers/
   │   └── models/
   ├── tests/
   ├── requirements.txt
   └── .env
   ```

2. **Core Infrastructure**
   - FastAPI application setup
   - Authentication middleware
   - Error handling framework
   - Logging configuration
   - Environment configuration

### Phase 2: NetSuite Integration Layer (Week 3-4)

1. **SOAP Client Implementation**

   ```python
   # app/services/netsuite/soap/client.py
   from zeep import Client, Settings
   from zeep.transports import Transport

   class NetSuiteSoapClient:
       def __init__(self, config):
           settings = Settings(
               xml_huge_tree=True,  # Handle large responses
               strict=False
           )
           transport = Transport(timeout=1200)  # 20 minutes
           self.client = Client(
               wsdl=config.wsdl_path,
               settings=settings,
               transport=transport
           )
   ```

2. **RESTlet Client Implementation**

   ```python
   # app/services/netsuite/restlet/client.py
   from requests_oauthlib import OAuth1Session

   class NetSuiteRestletClient:
       def __init__(self, config):
           self.session = OAuth1Session(
               client_key=config.consumer_key,
               client_secret=config.consumer_secret,
               resource_owner_key=config.token_id,
               resource_owner_secret=config.token_secret,
               realm=config.account,
               signature_method='HMAC-SHA256'
           )
   ```

3. **Authentication Service**
   - Port authentication logic from Rails
   - Support both password and OAuth methods
   - Dynamic endpoint configuration

### Phase 3: Service Layer Migration (Week 5-8)

1. **Base Service Pattern**

   ```python
   # app/services/base_service.py
   from abc import ABC, abstractmethod

   class BaseRecordService(ABC):
       def __init__(self, client, serializer):
           self.client = client
           self.serializer = serializer

       @abstractmethod
       async def poll(self, params):
           pass

       @abstractmethod
       async def count(self, params):
           pass
   ```

2. **Priority Services to Migrate**

   - CustomerService
   - InvoiceService
   - VendorBillService
   - PaymentService
   - JournalEntryService

3. **Serializer Implementation**

   ```python
   # app/services/serializers/base.py
   from pydantic import BaseModel

   class BaseSerializer(BaseModel):
       @classmethod
       def from_netsuite(cls, ns_record):
           # Map NetSuite fields to REST API fields
           pass

       def to_netsuite(self):
           # Map REST API fields to NetSuite fields
           pass
   ```

### Phase 4: API Endpoints (Week 9-10)

1. **Controller to Router Migration**

   ```python
   # app/api/endpoints/customers.py
   from fastapi import APIRouter, Depends

   router = APIRouter()

   @router.get("/customers")
   async def list_customers(
       service: CustomerService = Depends(get_customer_service),
       params: QueryParams = Depends()
   ):
       return await service.poll(params)
   ```

2. **Middleware Implementation**
   - Authentication headers extraction
   - Request/response logging
   - Error handling
   - CORS configuration

### Phase 5: Testing Strategy (Week 11-12)

1. **Unit Tests**

   - Service layer tests with mocked NetSuite responses
   - Serializer transformation tests
   - Authentication logic tests

2. **Integration Tests**

   - API endpoint tests
   - VCR.py recordings for NetSuite interactions
   - Performance benchmarks

3. **VCR Cassette Migration**
   - Write conversion script for critical test cases
   - Re-record remaining interactions
   - Validate response compatibility

### Phase 6: Migration Execution (Week 13-16)

1. **Parallel Running**

   - Deploy Python service alongside Rails
   - Route percentage of traffic for testing
   - Monitor performance and errors

2. **Data Validation**

   - Compare responses between services
   - Log discrepancies for investigation
   - Build confidence metrics

3. **Cutover Strategy**
   - Gradual traffic migration
   - Feature flag control
   - Rollback plan

## Key Implementation Details

### 1. Field Mapping System

```python
# app/services/serializers/mappings.py
FIELD_MAPPINGS = {
    'customer': {
        'id': ('internal_id', None),
        'name': ('entity_id', None),
        'email': ('email', None),
        'balance': ('balance', lambda x: float(x or 0)),
        'subsidiary_id': ('subsidiary.internal_id', None),
        'custom_fields': ('custom_field_list', custom_field_transformer)
    }
}
```

### 2. Error Handling

```python
# app/core/exceptions.py
class NetSuiteError(Exception):
    pass

class PageBoundsError(NetSuiteError):
    pass

class AuthenticationError(NetSuiteError):
    pass

# app/api/middleware/error_handler.py
@app.exception_handler(NetSuiteError)
async def netsuite_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )
```

### 3. Search Enhancement

```python
# app/services/netsuite/search.py
class SearchService:
    def __init__(self, soap_client, restlet_client):
        self.soap = soap_client
        self.restlet = restlet_client

    async def search(self, record_type, criteria, use_restlet=False):
        if use_restlet or self._is_complex_search(criteria):
            return await self._restlet_search(record_type, criteria)
        return await self._soap_search(record_type, criteria)
```

### 4. Performance Optimizations

```python
# app/services/batching.py
class BatchingService:
    def __init__(self, client):
        self.client = client
        self._cache = {}

    async def fetch_columns(self, records, columns):
        # Collect IDs needing fetch
        needed_ids = [r.id for r in records if r.id not in self._cache]

        # Batch fetch
        if needed_ids:
            results = await self.client.get_multiple(needed_ids, columns)
            self._cache.update({r.id: r for r in results})

        # Apply to records
        for record in records:
            if record.id in self._cache:
                record.update(self._cache[record.id])
```

## Testing Approach

### 1. Functional Equivalence Testing

```python
# tests/compatibility/test_response_compatibility.py
import pytest
from deepdiff import DeepDiff

@pytest.mark.parametrize("endpoint,params", [
    ("/customers", {"ids": "75,76,77"}),
    ("/invoices", {"status": "open"}),
])
async def test_response_compatibility(endpoint, params, rails_client, python_client):
    rails_response = await rails_client.get(endpoint, params=params)
    python_response = await python_client.get(endpoint, params=params)

    diff = DeepDiff(rails_response.json(), python_response.json(),
                    ignore_order=True, exclude_paths=["root['updated_at']"])
    assert not diff, f"Response mismatch: {diff}"
```

### 2. Performance Testing

```python
# tests/performance/test_endpoints.py
import asyncio
import time

async def test_customer_list_performance(client):
    start = time.time()
    tasks = [client.get("/customers", params={"page": i}) for i in range(1, 11)]
    responses = await asyncio.gather(*tasks)
    duration = time.time() - start

    assert all(r.status_code == 200 for r in responses)
    assert duration < 10  # Should complete within 10 seconds
```

### 3. VCR Integration

```python
# tests/integration/test_netsuite_soap.py
import vcr

@vcr.use_cassette('tests/cassettes/customer_search.yaml')
async def test_customer_search(soap_client):
    results = await soap_client.search(
        record_type='Customer',
        criteria={'entityId': 'CUST123'}
    )
    assert len(results) == 1
    assert results[0].entity_id == 'CUST123'
```

## Risk Mitigation

### 1. Technical Risks

- **WSDL Complexity**: Zeep has proven NetSuite compatibility
- **Performance**: Python async capabilities match or exceed Ruby performance
- **Memory Usage**: Implement streaming for large datasets
- **Authentication**: Maintain exact authentication flow compatibility

### 2. Business Risks

- **Data Integrity**: Extensive validation testing
- **Downtime**: Zero-downtime deployment strategy
- **Rollback**: Maintain Rails service until fully migrated
- **Training**: Document differences for operations team

## Success Criteria

1. **Functional**

   - All endpoints produce identical responses
   - All authentication methods supported
   - Error handling maintains compatibility

2. **Performance**

   - Response times equal or better than Rails
   - Memory usage within acceptable limits
   - Concurrent request handling improved

3. **Operational**
   - Comprehensive monitoring and logging
   - Easy deployment and configuration
   - Clear documentation and runbooks

## Timeline Summary

- **Weeks 1-2**: Foundation and infrastructure
- **Weeks 3-4**: NetSuite integration layer
- **Weeks 5-8**: Service layer migration
- **Weeks 9-10**: API endpoints
- **Weeks 11-12**: Testing and validation
- **Weeks 13-16**: Migration and cutover

Total estimated time: 16 weeks for full migration with parallel running and validation.

## Conclusion

The migration from Rails to Python is technically feasible and offers several advantages:

1. **Modern Stack**: Python's ecosystem provides robust, maintained libraries
2. **Performance**: Async capabilities and better resource utilization
3. **Maintainability**: Type hints, better tooling, larger talent pool
4. **Compatibility**: Can maintain exact API compatibility with proper design

The key to success is maintaining functional equivalence while taking advantage of Python's strengths. The phased approach allows for risk mitigation and validation at each step.

# Learnings from attempting to upgrade the ruby project

Below is a list of assorted learnings from working on a big upgrade to the ruby code (that has failed) to take in account when designing and building the python version:

- avoid creating fragile tests - many of the original tests hardcoded very exact expectations from a test server that changes drastically over time.
- much has changed upstream in netsuite since the tests were written in 2016 - the credentials we're using don't always have the correct permissions and it is important to verify directly within netsuite that features are available and that the user is allowed to access those features when things break. do not assume the code is wrong, but verify that raw requests to netsuite work too.
- a lot of this project seems to be managing json and it gets pretty ugly, it's important to take care not to wrap and unwrap objects all over leading to confusing code.

I asked Claude (you!) to also give me a list of learnings it would want you to know if rewriting from scratch. I would take these lightly, but they may contain wisdom:

1. Design for API Evolution from Day One

The NetSuite API has changed significantly since 2016. Design your abstraction layer to handle version differences, namespace changes, and field deprecations. Consider using a plugin architecture where different API versions can be
swapped out.

2. Create a Robust Test Strategy with Multiple Layers

- Use recorded API responses (like VCR) but make them easily regeneratable
- Write tests that expect ranges rather than exact values (e.g., "count > 0" not "count == 66")
- Create integration tests that can run against live API with feature flags
- Maintain a separate test suite for validating NetSuite permissions and capabilities

3. Implement Clear Data Transformation Boundaries

The biggest complexity came from multiple serialization layers. In Python:

- Use dataclasses or Pydantic models with clear boundaries
- Avoid circular dependencies between serializers and models
- Have one clear transformation point between NetSuite objects and your API responses
- Don't mix business logic with serialization logic

4. Handle NetSuite's Namespace Complexity Explicitly

NetSuite uses different namespaces (tranSales, tranPurch, listAcct) inconsistently. Create a namespace mapping system that can be configured per record type rather than relying on the upstream library getting it right.

5. Build Permission and Capability Discovery

Don't assume API operations will work. Build tooling to:

- Discover what record types are accessible
- Check field-level permissions
- Validate search capabilities before using them
- Provide clear error messages when permissions are missing

6. Implement Efficient Batch Operations

The batching service pattern is good but needs careful implementation:

- Make batch operations optional/degradable
- Handle partial failures gracefully
- Consider using async operations for large batches
- Profile performance early - N+1 queries killed performance here

7. Create Strong Service Layer Abstractions

The service pattern worked well but could be improved:

- Use dependency injection rather than inheritance
- Make services stateless where possible
- Separate search/filter building from data fetching
- Consider using the Repository pattern for data access

8. Plan for Complex Authentication Scenarios

NetSuite's OAuth + token auth is complex:

- Build authentication as a pluggable component
- Support multiple authentication methods from the start
- Handle token refresh and expiration gracefully
- Consider per-tenant authentication configuration

9. Document NetSuite Quirks Extensively

Create a "quirks" documentation system:

- Document every workaround with NetSuite issue details
- Include examples of problematic API responses
- Version your workarounds so they can be removed later
- Build regression tests for each quirk

  10. Design for Maintainability Over Cleverness

The Ruby codebase suffered from too much metaprogramming:

- Prefer explicit over implicit
- Make the code grep-able - avoid dynamic method generation
- Use type hints extensively in Python
- Create clear upgrade paths for breaking changes
