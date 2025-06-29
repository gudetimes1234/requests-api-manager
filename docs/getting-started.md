
# Getting Started

Welcome to `requests-connection-manager`! This guide will help you get up and running quickly with enhanced HTTP connection management.

## What is requests-connection-manager?

`requests-connection-manager` is a Python package that extends the popular `requests` library with advanced features:

- **Connection Pooling**: Efficient reuse of HTTP connections
- **Automatic Retries**: Smart retry logic with exponential backoff
- **Rate Limiting**: Prevent API abuse with built-in throttling
- **Circuit Breaker**: Fail-fast pattern for handling service failures
- **Authentication**: Support for multiple auth methods
- **Async Support**: Full async/await compatibility
- **Plugin System**: Extensible hooks for custom functionality

## Prerequisites

- Python 3.8 or higher
- Basic familiarity with HTTP requests and the `requests` library

## Installation

Install the package using pip:

```bash
pip install requests-connection-manager
```

For development installation:

```bash
git clone https://github.com/charlesgude/requests-connection-manager.git
cd requests-connection-manager
pip install -e .
```

## Your First Request

Let's start with a simple example:

```python
from requests_connection_manager import ConnectionManager

# Create a connection manager with default settings
with ConnectionManager() as manager:
    response = manager.get('https://httpbin.org/get')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
```

That's it! You've just made your first request with automatic connection pooling, retries, and rate limiting.

## Key Concepts

### Connection Manager
The `ConnectionManager` is your main interface for making HTTP requests. It handles all the advanced features transparently.

### Context Manager Pattern
Always use the `with` statement to ensure proper resource cleanup:

```python
with ConnectionManager() as manager:
    # Make your requests here
    response = manager.get('https://api.example.com/data')
# Resources are automatically cleaned up
```

### Built-in Features
All requests automatically benefit from:
- Connection pooling for better performance
- Retry logic for transient failures
- Rate limiting to prevent overwhelming APIs
- Circuit breaker pattern for service protection

## Configuration Overview

You can customize the behavior during initialization:

```python
manager = ConnectionManager(
    pool_connections=20,      # Number of connection pools
    max_retries=5,           # Retry attempts
    rate_limit_requests=100, # Requests per minute
    timeout=30               # Default timeout
)
```

## What's Next?

- [Configuration](configuration.md) - Learn about all configuration options
- [Usage Examples](usage-examples.md) - See practical examples
- [Advanced Features](advanced-features.md) - Explore powerful features
- [API Reference](api-reference.md) - Complete API documentation

## Common Use Cases

### API Integration
Perfect for integrating with external APIs with built-in resilience:

```python
with ConnectionManager(
    rate_limit_requests=60,  # Respect API limits
    max_retries=3           # Handle transient failures
) as manager:
    response = manager.get('https://api.service.com/data')
```

### Microservices Communication
Ideal for service-to-service communication:

```python
manager = ConnectionManager(
    circuit_breaker_failure_threshold=5,  # Fail fast
    timeout=10                            # Quick timeouts
)
```

### Bulk Data Processing
Efficient for processing multiple requests:

```python
requests_data = [
    ('GET', 'https://api.example.com/item/1', {}),
    ('GET', 'https://api.example.com/item/2', {}),
    ('GET', 'https://api.example.com/item/3', {})
]

with ConnectionManager() as manager:
    results = manager.batch_request(requests_data, max_workers=5)
```

Ready to dive deeper? Check out our [Usage Examples](usage-examples.md) for more comprehensive scenarios!
