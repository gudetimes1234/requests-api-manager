
# Installation

## Requirements

- Python 3.8 or higher
- Operating System: Windows, macOS, or Linux

## Install from PyPI

The easiest way to install `requests-connection-manager` is using pip:

```bash
pip install requests-connection-manager
```

## Install from Source

If you want to install from the source code:

```bash
git clone https://github.com/charlesgude/requests-connection-manager.git
cd requests-connection-manager
pip install -e .
```

## Development Installation

For development, install with development dependencies:

```bash
git clone https://github.com/charlesgude/requests-connection-manager.git
cd requests-connection-manager
pip install -e ".[dev]"
```

Or if you're using Poetry:

```bash
git clone https://github.com/charlesgude/requests-connection-manager.git
cd requests-connection-manager
poetry install
```

## Dependencies

The package automatically installs these dependencies:

- **requests** (>=2.25.0) - HTTP library for Python
- **urllib3** (>=1.26.0) - HTTP client library
- **ratelimit** (>=2.2.1) - Rate limiting decorator
- **pybreaker** (>=1.2.0) - Circuit breaker implementation
- **httpx** (>=0.28.1) - Modern async HTTP client

## Verify Installation

To verify the installation was successful:

```python
import requests_connection_manager
print(requests_connection_manager.__version__)
```

You should see the version number printed without any errors.

## Next Steps

- [Quick Start Guide](quick-start.md) - Get started with basic usage
- [Basic Usage](usage/basic.md) - Learn the fundamentals
- [Examples](examples/basic.md) - See practical examples
