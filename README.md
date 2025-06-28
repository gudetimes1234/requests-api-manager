# requests-connection-manager

A Python package that extends the popular `requests` library with advanced connection management features including connection pooling, automatic retries, rate limiting, and circuit breaker functionality.

## Features

- **Connection Pooling**: Efficient connection reuse with configurable pool sizes
- **Automatic Retries**: Smart retry logic with exponential backoff for failed requests
- **Rate Limiting**: Built-in request throttling to prevent API abuse
- **Circuit Breaker**: Fail-fast pattern to handle service failures gracefully
- **Thread Safety**: Safe for use in multi-threaded applications
- **Drop-in Replacement**: Compatible with existing `requests` code

## Installation

```bash
pip install requests-connection-manager
```

## Quick Start

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

## Configuration

Customize the connection manager with various options:

```python
manager = ConnectionManager(
    pool_connections=20,          # Number of connection pools
    pool_maxsize=20,             # Max connections per pool
    max_retries=5,               # Retry attempts
    backoff_factor=0.5,          # Retry delay multiplier
    rate_limit_requests=100,     # Requests per period
    rate_limit_period=60,        # Rate limit period (seconds)
    circuit_breaker_failure_threshold=10,  # Failures before opening circuit
    circuit_breaker_recovery_timeout=30,   # Recovery timeout (seconds)
    timeout=30                   # Default request timeout
)
```

### Per-Endpoint Configuration

Configure different settings for specific endpoints or URL patterns:

```python
# Define endpoint-specific configurations
endpoint_configs = {
    'api.example.com': {
        'timeout': 60,
        'rate_limit_requests': 50,
        'rate_limit_period': 60,
        'max_retries': 5,
        'circuit_breaker_failure_threshold': 10
    },
    'slow-service.com': {
        'timeout': 120,
        'rate_limit_requests': 10,
        'rate_limit_period': 60,
        'backoff_factor': 1.0
    }
}

manager = ConnectionManager(
    timeout=30,  # Default timeout
    endpoint_configs=endpoint_configs
)

# Requests to api.example.com will use 60s timeout and 50 req/min limit
response = manager.get('https://api.example.com/data')

# Requests to other URLs will use default 30s timeout
response = manager.get('https://other-service.com/data')
```

### Dynamic Endpoint Configuration

Add or modify endpoint configurations at runtime:

```python
manager = ConnectionManager()

# Add new endpoint configuration
manager.add_endpoint_config('new-api.com', {
    'timeout': 45,
    'rate_limit_requests': 75,
    'max_retries': 3
})

# Remove endpoint configuration
manager.remove_endpoint_config('old-api.com')

# View all endpoint configurations
configs = manager.get_endpoint_configs()
```

### Authentication

ConnectionManager supports various authentication methods that can be applied globally or per-endpoint:

```python
# API Key authentication
manager = ConnectionManager(
    api_key="your-api-key",
    api_key_header="X-API-Key"  # Custom header name
)

# Bearer token authentication
manager = ConnectionManager(bearer_token="your-bearer-token")

# OAuth2 token authentication
manager = ConnectionManager(oauth2_token="your-oauth2-token")

# Basic authentication
manager = ConnectionManager(basic_auth=("username", "password"))

# Set authentication after initialization
manager.set_api_key("new-api-key", "Authorization")
manager.set_bearer_token("new-bearer-token")
manager.set_oauth2_token("new-oauth2-token")
manager.set_basic_auth("user", "pass")

# Endpoint-specific authentication
manager.set_endpoint_auth('api.service1.com', 'bearer', token='service1-token')
manager.set_endpoint_auth('api.service2.com', 'api_key', api_key='service2-key', header_name='X-Service2-Key')

# Clear authentication
manager.clear_auth()  # Global
manager.clear_auth('api.service1.com')  # Endpoint-specific
```

## Usage Examples

### Basic HTTP Methods

```python
from requests_connection_manager import ConnectionManager

manager = ConnectionManager()

# GET request
response = manager.get('https://httpbin.org/get')

# POST request with JSON data
data = {'key': 'value'}
response = manager.post('https://httpbin.org/post', json=data)

# Custom headers
headers = {'Authorization': 'Bearer token'}
response = manager.get('https://api.example.com/protected', headers=headers)

manager.close()
```

### Advanced Features

```python
# Rate limiting automatically prevents excessive requests
manager = ConnectionManager(rate_limit_requests=10, rate_limit_period=60)

# Circuit breaker protects against failing services
manager = ConnectionManager(
    circuit_breaker_failure_threshold=5,
    circuit_breaker_recovery_timeout=60
)

# Automatic retries with exponential backoff
manager = ConnectionManager(max_retries=3, backoff_factor=0.3)
```

### Error Handling

```python
from requests_connection_manager import ConnectionManager
from requests_connection_manager.exceptions import (
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)

manager = ConnectionManager()

try:
    response = manager.get('https://api.example.com/data')
except RateLimitExceeded:
    print("Rate limit exceeded, please wait")
except CircuitBreakerOpen:
    print("Service is currently unavailable")
except MaxRetriesExceeded:
    print("Request failed after maximum retries")
```

### Thread Safety

```python
import threading
from requests_connection_manager import ConnectionManager

# Safe to use across multiple threads
manager = ConnectionManager()

def make_request(url):
    response = manager.get(url)
    return response.status_code

# Create multiple threads
threads = []
for i in range(10):
    thread = threading.Thread(target=make_request, args=(f'https://httpbin.org/get?id={i}',))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()

manager.close()
```

## API Reference

### ConnectionManager

The main class that provides enhanced HTTP functionality.

#### Methods

- `get(url, **kwargs)` - Make GET request
- `post(url, **kwargs)` - Make POST request  
- `put(url, **kwargs)` - Make PUT request
- `delete(url, **kwargs)` - Make DELETE request
- `patch(url, **kwargs)` - Make PATCH request
- `head(url, **kwargs)` - Make HEAD request
- `options(url, **kwargs)` - Make OPTIONS request
- `request(method, url, **kwargs)` - Make request with specified method
- `close()` - Close session and clean up resources
- `get_stats()` - Get current connection statistics

#### Configuration Parameters

- `pool_connections` (int): Number of connection pools to cache (default: 10)
- `pool_maxsize` (int): Maximum number of connections in each pool (default: 10)
- `max_retries` (int): Maximum number of retry attempts (default: 3)
- `backoff_factor` (float): Backoff factor for retries (default: 0.3)
- `rate_limit_requests` (int): Number of requests allowed per period (default: 100)
- `rate_limit_period` (int): Time period for rate limiting in seconds (default: 60)
- `circuit_breaker_failure_threshold` (int): Failures before opening circuit (default: 5)
- `circuit_breaker_recovery_timeout` (float): Recovery timeout for circuit breaker (default: 60)
- `timeout` (int): Default request timeout in seconds (default: 30)

## Dependencies

- `requests` >= 2.25.0
- `urllib3` >= 1.26.0
- `ratelimit` >= 2.2.1
- `pybreaker` >= 1.2.0

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

See the [GitHub releases](https://github.com/charlesgude/requests-connection-manager/releases) for version history and changes.