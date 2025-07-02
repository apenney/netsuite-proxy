# netsuite-proxy

This service will be a python project to replace a legacy rails service.

## 🚨 Critical Rules

1. **ALWAYS make atomic commits** - One feature/fix per commit, never combine
2. **Run tests before committing** - Use `pyright`, `pytest` and `pre-commit run`
3. **Follow type hints strictly** - All code must pass pyright
4. **Document as you code** - Update docs with any API changes

# Important

- @PLAN.md is the overall plan that was created for this project
- @TODO.md is where TODO items and working state should be kept
- the RUBY/ directory is where the legacy code is for reference purposes

## Documentation

- @docs/README.md - Documentation overview and quick links
- @docs/ARCHITECTURE.md - System architecture, design principles, and patterns
- @docs/TESTING.md - Testing guidelines, patterns, and best practices
- @docs/PYDANTIC_GUIDE.md - Pydantic usage patterns and examples
- @docs/GETTING_STARTED.md - Quick start guide for new developers
- @docs/API_REFERENCE.md - API endpoint documentation

- Focus on writing good tests first, when possible, then the code.
- Tell me when you think you have useful context that should be added to this file, and ask to add it.

- When you finish making changes, always run the `ruff` commands.
- Before you git commit, run `pre-commit` to validate work.
- When committing multiple changes, ALWAYS break them into separate atomic commits (see Git section below)

# Build And Test Commands

- `pytest` to run the python tests
- `pre-commit run` to run the pre-commit tests
- `pre-commit run --all-files` to run on all files (not just staged)
- If pre-commit fails on pyright: use `--no-verify` flag when committing (pyright may fail outside venv)

# Code Style Guidelines

- Formatting: Use Ruff for consistent code formatting
- Imports: Group by stdlib, third-party, internal modules
- Type Hints: Required throughout, verified by pyright
- Naming:
  - Classes: PascalCase
  - Methods/functions/variables: snake_case
  - Constants: UPPER_SNAKE_CASE
  - Private items: \_prefixed_with_underscore
- Documentation: Docstrings for all public functions/classes
- Testing: Every feature needs associated tests in pytest format

# Permissions Guidelines

- Allowed without asking: Running tests, linting, code formatting, viewing files
- Ask before: Making destructive operations, installing packages
- Never allowed: Pushing directly to main branch, changing API keys/secrets

# Type Annotations

Write readable, domain-specific types instead of primitive type soup:

- **Use TypedDict/dataclasses/Pydantic** for structured data instead of `dict[str, Any]`
- **Create type aliases** for complex types: `UserId = str` or `AuthConfig = dict[str, str | None]`
- **Break down nested types** into named components
- **Prefer domain types** over primitives: `EmailAddress`, `UserId` vs raw `str`

❌ Bad: `dict[str, dict[str, str | None] | None]`
✅ Good: `AuthResponse` (defined as TypedDict or dataclass)

See @docs/TYPES.md for detailed examples and patterns.

# Technologies

## Flox

This project uses flox.dev to manage the packages and services required to run and test this service.

- `flox list` will show all installed packages
- `flox search $pkgname` will show all available packages
- `flox install $pkgname` will install a package
- `flox activate` activates the environment to make those packages available
- `flox activate -- $cmd` allows you to run any command within the flox environment

## Python

Our code should be written with types, and a type checker (pyright) will be run to validate these. Please think in
terms of types, and use modern python typing practices. This means things like dataclasses.

- Always use `ruff format` and `ruff check --fix` to lint and format code.
- If it makes sense, use `hypothesis` to write a property test instead of multiple unit tests.
- All tests should use pytest format, not unittest.

## Git

**CRITICAL: Always make small, atomic commits. NEVER combine multiple features/fixes in one commit.**

### Commit Strategy When Multiple Changes Exist

When you've made multiple types of changes, follow this process:

1. **First, review all changes**: `git status` and `git diff`
2. **Reset all staged files**: `git reset`
3. **Group related changes** and commit them separately:
   - New features/models: `git add <feature-files> && git commit -m "feat: ..."`
   - Bug fixes: `git add <fix-files> && git commit -m "fix: ..."`
   - Refactoring: `git add <refactor-files> && git commit -m "refactor: ..."`
   - Documentation: `git add <doc-files> && git commit -m "docs: ..."`
   - Test updates: `git add <test-files> && git commit -m "test: ..."`
   - Config/build changes: `git add <config-files> && git commit -m "chore: ..."`

### Example Commit Breakdown

If you've implemented a new endpoint with tests and docs:

```bash
# Commit 1: Add the model
git add app/models/customer.py
git commit -m "feat: add Customer response model"

# Commit 2: Add the endpoint
git add app/api/customers.py
git commit -m "feat: implement customer endpoint"

# Commit 3: Add tests
git add tests/unit/test_customers.py
git commit -m "test: add customer endpoint tests"

# Commit 4: Add documentation
git add docs/customers.md
git commit -m "docs: add customer API documentation"
```

### Commit Message Format

- Format: `<type>: <what changed>`
- Types: `feat|fix|docs|refactor|test|chore`
- Keep under 72 characters
- Use imperative mood ("add" not "added")
- No period at the end

### Git Commands Reference

- `git add -p` - Stage specific hunks interactively
- `git reset` - Unstage all files
- `git reset <file>` - Unstage specific file
- `git diff --staged` - Review what will be committed
- `git commit --amend` - Modify the last commit
- `git log --oneline -n 10` - View recent commits

## Datadog (Observability)

It's important for us to be able to observe this product. Within Datadog
we rely on APM (traces) to provide all the observability of this service,
with logs emitted as a secondary method. This means you must:

- Make sure that datadog is configured properly for any libraries we use
- Anything required for emitting APM traces must be done
