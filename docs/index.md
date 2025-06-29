# requests-connection-manager

A Python package that extends the popular `requests` library with advanced connection management features including connection pooling, automatic retries, rate limiting, and circuit breaker functionality.

## Features

- **Connection Pooling**: Efficient HTTP connection reuse with urllib3
- **Automatic Retries**: Configurable retry logic with exponential backoff
- **Rate Limiting**: Built-in request throttling to prevent API abuse
- **Circuit Breaker**: Fail-fast pattern for handling service failures
- **Thread Safety**: Safe for use in multi-threaded applications
- **Drop-in Replacement**: Works as an enhanced replacement for requests.Session

## Quick Start

```python
from requests_connection_manager import ConnectionManager

# Create a connection manager with enhanced features
manager = ConnectionManager(
    max_retries=3,
    timeout=30,
    rate_limit_requests=100,
    rate_limit_period=60
)

# Use like requests.Session
response = manager.get('https://api.example.com/data')
print(response.json())

# Context manager support
with ConnectionManager() as manager:
    response = manager.post('https://api.example.com/users', json={'name': 'John'})
```

## Installation

```bash
pip install requests-connection-manager
```

## Navigation

- [Installation Guide](installation.md)
- [Quick Start Guide](quick-start.md)
- [API Reference](api/manager.md)
- [Examples](examples/basic.md)
- [Contributing](contributing.md)