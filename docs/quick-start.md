
# Quick Start

Get up and running with `requests-connection-manager` in just a few minutes!

## Basic Usage

### Simple GET Request

```python
from requests_connection_manager import ConnectionManager

# Create a connection manager
manager = ConnectionManager()

# Make a GET request
response = manager.get('https://httpbin.org/get')
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Clean up
manager.close()
```

### Using Context Manager

The recommended approach is to use a context manager for automatic cleanup:

```python
from requests_connection_manager import ConnectionManager

with ConnectionManager() as manager:
    response = manager.get('https://httpbin.org/get')
    print(f"Status: {response.status_code}")
# Automatically closed when exiting the context
```

### Configuration Example

Customize the connection manager with your preferred settings:

```python
from requests_connection_manager import ConnectionManager

manager = ConnectionManager(
    pool_connections=20,          # Number of connection pools
    pool_maxsize=20,             # Max connections per pool
    max_retries=5,               # Retry attempts
    backoff_factor=0.5,          # Retry delay multiplier
    rate_limit_requests=100,     # Requests per period
    rate_limit_period=60,        # Rate limit period (seconds)
    timeout=30                   # Default request timeout
)

with manager:
    # Rate limiting automatically prevents excessive requests
    for i in range(10):
        response = manager.get(f'https://httpbin.org/get?id={i}')
        print(f"Request {i}: {response.status_code}")
```

## HTTP Methods

All standard HTTP methods are supported:

```python
with ConnectionManager() as manager:
    # GET request
    response = manager.get('https://httpbin.org/get')
    
    # POST request with JSON data
    data = {'key': 'value', 'number': 42}
    response = manager.post('https://httpbin.org/post', json=data)
    
    # PUT request
    response = manager.put('https://httpbin.org/put', json=data)
    
    # DELETE request
    response = manager.delete('https://httpbin.org/delete')
    
    # Custom headers
    headers = {'Authorization': 'Bearer your-token'}
    response = manager.get('https://httpbin.org/headers', headers=headers)
```

## Authentication

### API Key Authentication

```python
manager = ConnectionManager(
    api_key="your-api-key",
    api_key_header="X-API-Key"
)

with manager:
    response = manager.get('https://api.example.com/data')
    # X-API-Key header automatically added
```

### Bearer Token

```python
manager = ConnectionManager(bearer_token="your-bearer-token")

with manager:
    response = manager.get('https://api.example.com/protected')
    # Authorization: Bearer header automatically added
```

## Error Handling

```python
from requests_connection_manager import ConnectionManager
from requests_connection_manager.exceptions import (
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)

with ConnectionManager() as manager:
    try:
        response = manager.get('https://api.example.com/data')
        print(f"Success: {response.status_code}")
    except RateLimitExceeded:
        print("Rate limit exceeded, please wait")
    except CircuitBreakerOpen:
        print("Service is currently unavailable")
    except MaxRetriesExceeded:
        print("Request failed after maximum retries")
```

## Async Usage

For async applications, use `AsyncConnectionManager`:

```python
import asyncio
from requests_connection_manager import AsyncConnectionManager

async def main():
    async with AsyncConnectionManager() as manager:
        response = await manager.get('https://httpbin.org/get')
        print(f"Status: {response.status_code}")

# Run the async function
asyncio.run(main())
```

## Next Steps

Now that you have the basics down, explore more advanced features:

- [Authentication](usage/authentication.md) - Learn about all authentication methods
- [Advanced Configuration](usage/advanced.md) - SSL, timeouts, and more
- [Endpoint Configuration](usage/endpoints.md) - Per-service configurations
- [Examples](examples/basic.md) - See more comprehensive examples
