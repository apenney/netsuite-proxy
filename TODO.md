# TODO Items

This file is for tracking tasks related to building this service. Claude, when you are working on issues please put them into this file so we can manage them and not lose issues.

# TODO (next)

## Phase 1: Foundation Setup (High Priority)
- [ ] Set up basic FastAPI application with health check endpoint
- [ ] Create configuration module with environment variable management (app/core/config.py)
- [ ] Implement NetSuite-specific exception classes (app/core/exceptions.py)
- [ ] Set up structured logging with structlog
- [ ] Create authentication middleware to extract NetSuite credentials from headers

## Phase 2: NetSuite Integration Layer (High Priority)
- [ ] Implement NetSuiteSoapClient class with zeep integration
- [ ] Implement NetSuiteRestletClient class with OAuth1 support
- [ ] Create authentication service supporting both password and OAuth methods

## Infrastructure Setup (High Priority)
- [ ] Configure pyproject.toml with proper dependencies and tool configurations
- [ ] Set up ruff configuration for linting and formatting
- [ ] Configure pyright for type checking
- [ ] Set up pytest configuration with VCR.py for recording NetSuite interactions

# TODO (backlog) - Non-critical items

## Phase 3: Service Layer Migration (Medium Priority)
- [ ] Create BaseRecordService abstract class with common CRUD operations
- [ ] Implement BaseSerializer with Pydantic for field mapping
- [ ] Implement CustomerService with poll, count, and CRUD operations
- [ ] Create field mapping system for customer records

## Phase 4: API Endpoints (Medium Priority)
- [ ] Create customer API endpoints with FastAPI router
- [ ] Implement request/response logging middleware
- [ ] Add error handling middleware for NetSuite exceptions

## Testing (Medium Priority)
- [ ] Write unit tests for configuration module
- [ ] Write unit tests for authentication service
- [ ] Write integration tests for customer endpoints

## Additional Services (Low Priority)
- [ ] Implement InvoiceService
- [ ] Implement VendorBillService
- [ ] Implement PaymentService
- [ ] Implement JournalEntryService

## Other (Low Priority)
- [ ] Create performance benchmarks for API endpoints
- [ ] Create GitHub Actions workflow for CI/CD

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

## Phase 1: Foundation (Partial)
- [x] Create configuration module with environment variable management (app/core/config.py)
- [x] Implement NetSuite-specific exception classes (app/core/exceptions.py)
- [x] Write unit tests for configuration module (100% coverage)
- [x] Write unit tests for exceptions module (100% coverage)
- [x] Set up basic FastAPI application with health check endpoint
- [x] Write unit tests for health check endpoints
