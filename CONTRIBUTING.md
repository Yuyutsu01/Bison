# Contributing to Bison

Thank you for your interest in contributing to Bison! We welcome high-quality code contributions, bug reports, and quantitative strategy suggestions.

## Development Principles

1. **Correctness & Zero Look-Ahead Bias**: All financial simulations must maintain zero look-ahead bias and pass deterministic tests.
2. **Type Safety**: Python code must use explicit type hints and Pydantic schemas; TypeScript code must be strictly typed without `any`.
3. **Testing**: New domain features must be accompanied by comprehensive unit tests.

## Workflow

1. Fork and clone the repository.
2. Create a feature branch: `git checkout -b feat/your-feature-name`.
3. Run test suites locally: `make test`.
4. Ensure linting passes: `make lint`.
5. Submit a detailed Pull Request detailing the architecture and quantitative assumptions.
