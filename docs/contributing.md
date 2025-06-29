
# Contributing to requests-connection-manager

Thank you for your interest in contributing to requests-connection-manager! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Poetry for dependency management
- Git

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/requests-connection-manager.git
   cd requests-connection-manager
   ```

3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

4. Install pre-commit hooks (optional but recommended):
   ```bash
   poetry run pre-commit install
   ```

## Development Workflow

### Making Changes

1. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the coding standards below

3. Add or update tests as necessary

4. Update documentation if needed

5. Update CHANGELOG.md following the [Keep a Changelog](https://keepachangelog.com/) format

### Code Standards

- **Code Formatting**: Use `black` for code formatting
- **Import Sorting**: Use `isort` for import organization
- **Linting**: Code must pass `flake8` checks
- **Type Hints**: Use type hints for all public functions
- **Docstrings**: Follow Google-style docstrings

Run code quality checks:
```bash
# Format code
poetry run black requests_connection_manager/ tests/

# Sort imports
poetry run isort requests_connection_manager/ tests/

# Run linting
poetry run flake8 requests_connection_manager/ tests/

# Type checking
poetry run mypy requests_connection_manager/
```

### Testing

Run the test suite:
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=requests_connection_manager

# Run specific test file
poetry run pytest tests/test_manager.py

# Run with verbose output
poetry run pytest -v
```

### Documentation

Build and serve documentation locally:
```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve documentation
mkdocs serve --dev-addr=0.0.0.0:5000

# Build documentation
mkdocs build
```

### Commit Message Guidelines

Use clear, descriptive commit messages:

```
feat: add rate limiting configuration per endpoint

- Allow different rate limits for different endpoints
- Add endpoint_configs parameter to ConnectionManager
- Update documentation with examples

Closes #123
```

Commit message types:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Test additions or modifications
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

Use the version bumping script:
```bash
python scripts/bump_version.py patch  # or minor, major
```

## Pull Request Process

1. Ensure your code follows the style guidelines
2. Add tests for new functionality
3. Update documentation as needed
4. Update CHANGELOG.md
5. Ensure all tests pass
6. Create a pull request with a clear description

### Pull Request Template

When creating a pull request, please include:

- **Description**: What does this PR do?
- **Motivation**: Why is this change needed?
- **Testing**: How was this tested?
- **Documentation**: What documentation was updated?
- **Breaking Changes**: Any breaking changes?

## Release Process

1. Update version using the bump script
2. Update CHANGELOG.md with release notes
3. Commit changes: `git commit -m "Bump version to X.Y.Z"`
4. Create tag: `git tag vX.Y.Z`
5. Push: `git push && git push --tags`
6. GitHub Actions will automatically publish to PyPI

## Code of Conduct

Please be respectful and professional in all interactions. We're committed to providing a welcoming environment for all contributors.

## Getting Help

- **Issues**: Open an issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers directly for private matters

## Areas for Contribution

We welcome contributions in these areas:

### Features
- New authentication methods
- Additional retry strategies
- Enhanced monitoring and metrics
- Performance optimizations

### Documentation
- Usage examples
- API documentation improvements
- Tutorial content
- Video guides

### Testing
- Additional test cases
- Performance benchmarks
- Integration tests
- Load testing

### Bug Fixes
- Performance issues
- Edge case handling
- Memory leaks
- Thread safety issues

## Development Tips

### Running Examples

Test your changes with the provided examples:
```bash
python examples/basic_examples.py
python examples/authentication_examples.py
python examples/advanced_connection_examples.py
```

### Debugging

Enable debug logging to troubleshoot issues:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from requests_connection_manager import ConnectionManager
manager = ConnectionManager()
```

### Performance Testing

Use the batch request examples to test performance:
```bash
python examples/batch_request_examples.py
```

## License

By contributing to requests-connection-manager, you agree that your contributions will be licensed under the MIT License.

## Thank You

Thank you for contributing to requests-connection-manager! Your efforts help make this project better for everyone.
