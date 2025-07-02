# TODO Items

This file is for tracking tasks related to building this service. Claude, when you are working on issues please put them into this file so we can manage them and not lose issues.

## Current Status & Priority Summary

After analyzing the Ruby service, we've identified that our Python foundation is missing several critical components needed for a complete replacement. **We should NOT proceed to Phase 3 (Service Layer) until we implement the Pre-Phase 3 foundation components.**

### Critical Missing Features:
1. **Query Parameter Infrastructure** - Complex filtering, date ranges, ID parsing
2. **Serializer Pattern** - Bi-directional field mapping with transformations
3. **Batching Service** - Performance optimization for fetching specific fields
4. **Search Continuation** - NetSuite's pagination via search IDs
5. **Complete RESTlet Support** - Dynamic script configuration and generic search
6. **Enhanced Error Handling** - NetSuite-specific error interpretation

### Implementation Order:
1. **Pre-Phase 3 Foundation** (HIGH PRIORITY) - Must be completed first
2. **Phase 3 Service Layer** - Depends on foundation components
3. **Phase 4 API Endpoints** - Depends on service layer
4. **Performance & Optimization** - Can be done in parallel
5. **Testing & Documentation** - Ongoing throughout development

# TODO (next)

## Pre-Phase 3: Foundation Components (High Priority)

### Query Parameter Infrastructure
- [ ] Create query parameter models with Pydantic for complex filtering
  - [ ] Date range parameters (updated_since, updated_before, created_since, created_before)
  - [ ] ID filtering with support for arrays, ranges, and comma-separated values
  - [ ] Field selection parameter (fields=id,name,email)
  - [ ] Pagination parameters (page, page_size, search_id)
  - [ ] Performance flags (fast, body_fields_only)
  - [ ] Sorting parameters (sort_by, order)
- [ ] Create query parameter parser utilities
  - [ ] Parse ID ranges (e.g., "1,100" -> range(1, 101))
  - [ ] Parse comma-separated lists
  - [ ] Validate and convert timestamps

### Serializer Base Pattern
- [ ] Create BaseSerializer abstract class with field mapping support
  - [ ] Implement netsuite_field_map pattern for bi-directional mapping
  - [ ] Support for lambda/callable transformations
  - [ ] Handle nested field access (e.g., 'subsidiary.internal_id')
  - [ ] Custom field handling (customFieldList)
  - [ ] Company-specific override system
- [ ] Create field transformation utilities
  - [ ] Type conversions (string to float, etc.)
  - [ ] Date/time formatting
  - [ ] Null/None handling

### Batching Service Pattern
- [ ] Implement BatchingService for efficient field fetching
  - [ ] Batch requests in groups of 1000
  - [ ] Support column selection
  - [ ] Handle joins (e.g., salesRepJoin)
  - [ ] Implement caching for fetched data
  - [ ] Support lambda transformations on fetched data

### Search Continuation & Pagination
- [ ] Implement search ID tracking system
  - [ ] Store search IDs from NetSuite responses
  - [ ] Support search continuation requests
  - [ ] Handle search expiration
- [ ] Add NetSuite-specific response headers
  - [ ] NETSUITE-SEARCH-ID for pagination
  - [ ] NETSUITE-TOTAL-RECORDS for total count
  - [ ] NETSUITE-TOTAL-PAGES for pagination info
- [ ] Create pagination utilities
  - [ ] Page calculation helpers
  - [ ] Search ID validation

### RESTlet Integration Enhancement
- [ ] Complete RESTlet client implementation
  - [ ] Support dynamic script/deploy ID from headers
  - [ ] Implement generic search service
  - [ ] Add saved search support
  - [ ] Handle RESTlet-specific authentication
- [ ] Create RESTlet request builders
  - [ ] Build search expressions
  - [ ] Handle field lists
  - [ ] Support complex filters

### Enhanced Error Handling
- [ ] Add NetSuite-specific error interpretation
  - [ ] SOAP fault parsing with user-friendly messages
  - [ ] Handle permission errors with specific details
  - [ ] Credential expiration detection
  - [ ] Rate limit error handling
- [ ] Create error message mapping
  - [ ] Map NetSuite error codes to user messages
  - [ ] Add context-specific error details

### Service Layer Foundation
- [ ] Create BaseRecordService with mixin-style modules
  - [ ] PollCountManager for pagination and counting
  - [ ] PollIdsFilterManager for ID-based filtering
  - [ ] Create/Update/Delete mixins
  - [ ] Search functionality mixin
- [ ] Create BaseRestletRecordService for RESTlet-based services
  - [ ] Generic search functionality
  - [ ] Saved search support
  - [ ] Dynamic field selection

## Phase 3: Service Layer Migration (Medium Priority)
*Note: These tasks depend on Pre-Phase 3 foundation components*

- [ ] Implement CustomerService with full functionality
  - [ ] Poll with all query parameters
  - [ ] Count with filtering
  - [ ] CRUD operations
  - [ ] Field selection support
  - [ ] Batching for performance
- [ ] Create Customer serializer with field mappings
- [ ] Implement other core services
  - [ ] InvoiceService
  - [ ] VendorBillService
  - [ ] PaymentService
  - [ ] JournalEntryService

## Phase 4: API Endpoints (Medium Priority)
- [ ] Create customer API endpoints with all query parameters
- [ ] Add response header management
- [ ] Implement field selection in API layer
- [ ] Add performance optimization flags

## Performance & Optimization Features
- [ ] Implement response caching strategy
  - [ ] Cache serialized responses
  - [ ] Cache NetSuite query results
  - [ ] Implement cache invalidation
- [ ] Add connection pooling for SOAP/REST clients
- [ ] Implement request queuing for rate limiting
- [ ] Add metrics collection (response times, cache hits)

## Missing Ruby Service Features
- [ ] Support for NetSuite's "Page" functionality (1000 item pages)
- [ ] Implement ServicePages enumerable pattern for iterating all pages
- [ ] Add support for NetSuite custom records
- [ ] Implement subsidiary filtering
- [ ] Add support for NetSuite's datetime formats
- [ ] Handle NetSuite's null vs empty string distinction
- [ ] Support for NetSuite record references
- [ ] Implement "expand" functionality for related records

## API Compatibility Features
- [ ] Add CSV/Excel export endpoints (like Ruby service)
- [ ] Implement webhook support for async operations
- [ ] Add bulk operation endpoints
- [ ] Support for partial updates (PATCH)
- [ ] Implement field validation before NetSuite submission

## Testing (Medium Priority)
- [ ] Write comprehensive unit tests for all foundation components
- [ ] Create integration tests with VCR.py recordings
- [ ] Add performance benchmark tests
- [ ] Create end-to-end tests for complete workflows
- [ ] Add contract tests to ensure API compatibility

## Documentation
- [ ] Create migration guide from Ruby to Python service
- [ ] Document all API endpoints with examples
- [ ] Add NetSuite field mapping documentation
- [ ] Create troubleshooting guide for common issues
- [ ] Document performance tuning options

## DevOps & Deployment
- [ ] Create Docker configuration
- [ ] Set up GitHub Actions CI/CD pipeline
- [ ] Add health check monitoring
- [ ] Create deployment scripts
- [ ] Set up log aggregation
- [ ] Configure alerts for errors/performance

## Other (Low Priority)
- [ ] Create CLI tools for testing NetSuite connections
- [ ] Add admin endpoints for cache management
- [ ] Implement request replay functionality
- [ ] Create data migration tools from Ruby service

# TODO (done) - For tracking what we finished if it's important

## Project Setup
- [x] Initialize project with uv init
- [x] Add core dependencies (FastAPI, zeep, etc.)
- [x] Add development dependencies (ruff, pyright, hypothesis)
- [x] Initialize git repository
- [x] Create .gitignore with RUBY directory excluded
- [x] Install and configure pre-commit hooks
- [x] Create project structure

## Infrastructure
- [x] Configure pyproject.toml with proper dependencies and tool configurations
- [x] Set up ruff configuration for linting and formatting
- [x] Configure pyright for type checking  
- [x] Set up pytest configuration with VCR.py
- [x] Configure flox environment for automatic venv activation

## Phase 1: Foundation (Completed)
- [x] Create configuration module with environment variable management (app/core/config.py)
- [x] Implement NetSuite-specific exception classes (app/core/exceptions.py)
- [x] Write unit tests for configuration module (100% coverage)
- [x] Write unit tests for exceptions module (100% coverage)
- [x] Set up basic FastAPI application with health check endpoint
- [x] Write unit tests for health check endpoints
- [x] Set up structured logging with structlog
- [x] Create authentication middleware to extract NetSuite credentials from headers
- [x] Write unit tests for logging configuration
- [x] Write unit tests for authentication middleware

## Phase 2: NetSuite Integration Layer (Completed)
- [x] Implement NetSuiteSoapClient class with zeep integration
- [x] Implement NetSuiteRestletClient class with OAuth1 support
- [x] Create authentication service supporting both password and OAuth methods
- [x] Implement environment-based configuration for test environment
- [x] Write unit tests for all NetSuite integration classes

## Codebase Refactoring (Completed)
- [x] Simplify pytest fixture by removing redundant environment variable clearing
- [x] Create constants module to centralize configuration values (DRY principle)
- [x] Add discriminated unions for authentication configuration
- [x] Create abstract base classes for NetSuite services
- [x] Add protocol definitions for type safety and testability
- [x] Update authentication middleware to use constants
- [x] Improve error handling with exception chaining
- [x] Fix all linting and formatting issues
- [x] Configure ruff to allow Any types for NetSuite integration code
