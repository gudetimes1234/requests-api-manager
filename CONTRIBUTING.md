
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

# Lint code
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
poetry run pytest --cov=requests_connection_manager --cov-report=html

# Run specific test file
poetry run pytest tests/test_manager.py -v
```

### Writing Tests

- Write tests for all new functionality
- Maintain or improve code coverage
- Use descriptive test names
- Follow the AAA pattern (Arrange, Act, Assert)

Example test structure:
```python
def test_feature_name():
    # Arrange
    manager = ConnectionManager()
    
    # Act
    result = manager.some_method()
    
    # Assert
    assert result.status_code == 200
```

## Submitting Changes

### Pull Request Process

1. Ensure all tests pass and code quality checks are successful
2. Update documentation if your changes affect the public API
3. Add a description of your changes to CHANGELOG.md
4. Push your branch to your fork
5. Create a pull request with a clear title and description

### Pull Request Guidelines

- **Title**: Use a clear, descriptive title
- **Description**: Explain what changes were made and why
- **Link Issues**: Reference any related issues
- **Tests**: Ensure all tests pass
- **Documentation**: Update docs for API changes

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

## Release Process

1. Update version using the bump script
2. Update CHANGELOG.md with release notes
3. Commit changes: `git commit -m "Bump version to X.Y.Z"`
4. Create tag: `git tag vX.Y.Z`
5. Push: `git push && git push --tags`
6. GitHub Actions will automatically publish to PyPI

## Getting Help

- **Issues**: Open an issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers directly for private matters

## Code of Conduct

Please be respectful and professional in all interactions. We're committed to providing a welcoming environment for all contributors.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
