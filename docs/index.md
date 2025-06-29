
# requests-connection-manager

**Enhanced HTTP connection management for Python applications**

[![PyPI version](https://badge.fury.io/py/requests-connection-manager.svg)](https://badge.fury.io/py/requests-connection-manager)
[![Python versions](https://img.shields.io/pypi/pyversions/requests-connection-manager.svg)](https://pypi.org/project/requests-connection-manager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`requests-connection-manager` is a Python package that extends the popular `requests` library with advanced connection management features including connection pooling, automatic retries, rate limiting, and circuit breaker functionality.

## Key Features

- **🔄 Connection Pooling**: Efficient connection reuse with configurable pool sizes
- **🔁 Automatic Retries**: Smart retry logic with exponential backoff for failed requests
- **⏱️ Rate Limiting**: Built-in request throttling to prevent API abuse
- **🔌 Circuit Breaker**: Fail-fast pattern to handle service failures gracefully
- **🔐 Authentication**: Support for API keys, Bearer tokens, OAuth2, and basic auth
- **🚀 Async Support**: Full async/await support with httpx backend
- **🧩 Plugin System**: Extensible hook system for custom functionality
- **🛡️ Thread Safety**: Safe for use in multi-threaded applications
- **🔄 Drop-in Replacement**: Compatible with existing `requests` code

## Quick Example

```python
from requests_connection_manager import ConnectionManager

# Create a connection manager with default settings
manager = ConnectionManager()

# Make requests just like with the requests library
response = manager.get('https://api.example.com/data')
print(response.json())

# Use as a context manager for automatic cleanup
with ConnectionManager() as manager:
    response = manager.get('https://httpbin.org/get')
    print(f"Status: {response.status_code}")
```

## Installation

Install using pip:

```bash
pip install requests-connection-manager
```

## Getting Started

- [Installation Guide](installation.md) - Detailed installation instructions
- [Quick Start](quick-start.md) - Get up and running in minutes
- [Basic Usage](usage/basic.md) - Learn the fundamentals
- [Examples](examples/basic.md) - See practical examples

## Advanced Features

- [Authentication](usage/authentication.md) - API keys, tokens, and more
- [Advanced Configuration](usage/advanced.md) - SSL, timeouts, and custom settings
- [Endpoint Configuration](usage/endpoints.md) - Per-service configurations
- [Batch Requests](usage/batch.md) - Concurrent request processing
- [Async Support](usage/async.md) - Full async/await functionality

## API Reference

Complete API documentation:

- [ConnectionManager](api/manager.md) - Main synchronous client
- [AsyncConnectionManager](api/async-manager.md) - Async client
- [Exceptions](api/exceptions.md) - Custom exceptions
- [Plugins](api/plugins.md) - Plugin system

## Contributing

We welcome contributions! See our [Contributing Guide](contributing.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/charlesgude/requests-connection-manager/blob/main/LICENSE) file for details.
