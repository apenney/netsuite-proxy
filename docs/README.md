# NetSuite Proxy Documentation

Welcome to the NetSuite Proxy service documentation. This directory contains comprehensive guides for understanding, developing, and maintaining the service.

## Documentation Overview

### 📐 [Architecture Guide](./ARCHITECTURE.md)
Comprehensive overview of the system architecture, design principles, and implementation patterns.
- Layer architecture (API, Core, Models, Services)
- Configuration management
- Exception handling
- Dependency injection patterns
- Future considerations

### 🧪 [Testing Guidelines](./TESTING.md)
Complete guide to writing and maintaining tests.
- Testing philosophy and patterns
- pytest best practices
- Fixture usage
- Coverage guidelines
- Common pitfalls to avoid

### 📊 [Pydantic Usage Guide](./PYDANTIC_GUIDE.md)
How to effectively use Pydantic for data validation and serialization.
- Basic concepts and patterns
- Validation techniques
- FastAPI integration
- Performance tips
- Common pitfalls

### 🚀 [Getting Started Guide](./GETTING_STARTED.md)
Quick start guide for new developers.
- Environment setup
- Running the application
- Making your first contribution
- Development workflow

### 🔌 [API Reference](./API_REFERENCE.md)
API endpoint documentation and examples.
- Health endpoints
- NetSuite operations (coming soon)
- Request/response formats
- Error handling

## Quick Links

### Development
- [Project Root](../)
- [Main Application](../app/)
- [Tests](../tests/)
- [Configuration](../app/core/config.py)

### Key Concepts
- **Type Safety**: We use type hints everywhere with Pydantic validation
- **Dependency Injection**: FastAPI's DI system for clean, testable code
- **Configuration**: Environment-based settings with validation
- **Testing**: Comprehensive test coverage with pytest
- **Structured Logging**: Request correlation and detailed debugging with structlog
- **Authentication**: Header-based NetSuite credential extraction

## Contributing to Documentation

When adding new features or making significant changes:

1. Update relevant documentation
2. Add code examples where appropriate
3. Keep documentation close to code
4. Use clear, concise language
5. Include practical examples

## Documentation Standards

### Code Examples
```python
# Always include imports
from pydantic import BaseModel

# Add comments for clarity
class Example(BaseModel):
    """Document the purpose."""
    field: str  # Explain non-obvious fields
```

### Diagrams
Use ASCII art or Mermaid for diagrams:
```
┌─────────┐     ┌─────────┐     ┌─────────┐
│   API   │────▶│ Service │────▶│NetSuite │
└─────────┘     └─────────┘     └─────────┘
```

### Sections
- Use clear headings
- Include table of contents for long documents
- Cross-reference related documentation
- Keep examples realistic and tested

## Getting Help

- Check existing documentation first
- Look at test examples in `tests/`
- Review similar implementations in the codebase
- Ask questions with context

## Maintenance

Documentation should be:
- Reviewed with code changes
- Updated when APIs change
- Tested (code examples should work)
- Versioned with the code

---

*Last updated: 2024*