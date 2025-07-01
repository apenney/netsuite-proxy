# netsuite-proxy

This service will be a python project to replace a legacy rails service.

# Important

- @PLAN.md is the overall plan that was created for this project
- @TODO.md is where TODO items and working state should be kept
- the RUBY/ directory is where the legacy code is for reference purposes

- Focus on writing good tests first, when possible, then the code.
- Tell me when you think you have useful context that should be added to this file, and ask to add it.

- When you finish making changes, always run the `ruff` commands.
- Before you git commit, run `pre-commit` to validate work.

# Build And Test Commands

- `pytest` to run the python tests
- `pre-commit run` to run the pre-commit tests

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
- Testing: Every feature needs associated tests

# Permissions Guidelines

- Allowed without asking: Running tests, linting, code formatting, viewing files
- Ask before: Making destructive operations, installing packages
- Never allowed: Pushing directly to main branch, changing API keys/secrets

# Architecture

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
