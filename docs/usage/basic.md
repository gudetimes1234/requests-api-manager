
# Basic Usage

This guide covers the fundamental usage patterns of `requests-connection-manager`.

## Creating a Connection Manager

### Default Configuration

```python
from requests_connection_manager import ConnectionManager

# Create with default settings
manager = ConnectionManager()
```

### Custom Configuration

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

## HTTP Methods

### GET Requests

```python
with ConnectionManager() as manager:
    # Simple GET
    response = manager.get('https://httpbin.org/get')
    
    # GET with query parameters
    params = {'key1': 'value1', 'key2': 'value2'}
    response = manager.get('https://httpbin.org/get', params=params)
    
    # GET with custom headers
    headers = {'User-Agent': 'MyApp/1.0'}
    response = manager.get('https://httpbin.org/get', headers=headers)
```

### POST Requests

```python
with ConnectionManager() as manager:
    # POST with JSON data
    data = {'name': 'John', 'age': 30}
    response = manager.post('https://httpbin.org/post', json=data)
    
    # POST with form data
    form_data = {'username': 'john', 'password': 'secret'}
    response = manager.post('https://httpbin.org/post', data=form_data)
    
    # POST with files
    files = {'file': open('document.pdf', 'rb')}
    response = manager.post('https://httpbin.org/post', files=files)
```

### Other HTTP Methods

```python
with ConnectionManager() as manager:
    # PUT request
    data = {'id': 1, 'name': 'Updated Name'}
    response = manager.put('https://httpbin.org/put', json=data)
    
    # PATCH request
    patch_data = {'name': 'New Name'}
    response = manager.patch('https://httpbin.org/patch', json=patch_data)
    
    # DELETE request
    response = manager.delete('https://httpbin.org/delete')
    
    # HEAD request
    response = manager.head('https://httpbin.org/get')
    
    # OPTIONS request
    response = manager.options('https://httpbin.org/get')
```

## Working with Responses

```python
with ConnectionManager() as manager:
    response = manager.get('https://httpbin.org/json')
    
    # Status code
    print(f"Status: {response.status_code}")
    
    # Headers
    print(f"Content-Type: {response.headers['content-type']}")
    
    # JSON response
    if response.headers['content-type'] == 'application/json':
        data = response.json()
        print(f"Data: {data}")
    
    # Text response
    print(f"Text: {response.text}")
    
    # Raw bytes
    print(f"Content length: {len(response.content)}")
```

## Request Configuration

### Timeouts

```python
with ConnectionManager() as manager:
    # Request-specific timeout
    response = manager.get('https://httpbin.org/delay/5', timeout=10)
    
    # Fine-grained timeouts (connect, read)
    response = manager.get(
        'https://httpbin.org/get',
        timeout=(5.0, 30.0)  # 5s connect, 30s read
    )
```

### Custom Headers

```python
with ConnectionManager() as manager:
    headers = {
        'User-Agent': 'MyApp/1.0',
        'Accept': 'application/json',
        'X-Custom-Header': 'custom-value'
    }
    response = manager.get('https://httpbin.org/headers', headers=headers)
```

### Cookies

```python
with ConnectionManager() as manager:
    # Send cookies
    cookies = {'session_id': 'abc123', 'user_pref': 'dark_mode'}
    response = manager.get('https://httpbin.org/cookies', cookies=cookies)
    
    # Cookies are automatically handled in the session
    response = manager.get('https://httpbin.org/cookies/set/session/value')
    response = manager.get('https://httpbin.org/cookies')  # Includes previous cookies
```

## Context Manager Usage

Always use the context manager for proper resource cleanup:

```python
# ✅ Recommended - automatic cleanup
with ConnectionManager() as manager:
    response = manager.get('https://httpbin.org/get')
    print(response.status_code)
# Session automatically closed

# ❌ Not recommended - manual cleanup required
manager = ConnectionManager()
try:
    response = manager.get('https://httpbin.org/get')
    print(response.status_code)
finally:
    manager.close()  # Must remember to close
```

## Built-in Features

### Automatic Retries

Retries are automatically handled for transient failures:

```python
with ConnectionManager(max_retries=3, backoff_factor=0.5) as manager:
    # Automatically retries on 5xx errors, timeouts, connection errors
    response = manager.get('https://unreliable-service.com/api')
```

### Rate Limiting

Rate limiting prevents overwhelming APIs:

```python
with ConnectionManager(rate_limit_requests=10, rate_limit_period=60) as manager:
    # Maximum 10 requests per minute
    for i in range(20):
        response = manager.get(f'https://api.example.com/item/{i}')
        # Automatically throttled after 10 requests
```

### Circuit Breaker

Circuit breaker protects against failing services:

```python
with ConnectionManager(
    circuit_breaker_failure_threshold=5,
    circuit_breaker_recovery_timeout=30
) as manager:
    # After 5 failures, circuit opens for 30 seconds
    for i in range(10):
        try:
            response = manager.get('https://failing-service.com/api')
        except CircuitBreakerOpen:
            print("Circuit breaker is open, service unavailable")
            break
```

## Error Handling

```python
from requests_connection_manager.exceptions import (
    ConnectionManagerError,
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)
import requests

with ConnectionManager() as manager:
    try:
        response = manager.get('https://api.example.com/data')
        response.raise_for_status()  # Raises HTTPError for bad status codes
        
    except RateLimitExceeded:
        print("Rate limit exceeded")
    except CircuitBreakerOpen:
        print("Circuit breaker is open")
    except MaxRetriesExceeded:
        print("Max retries exceeded")
    except requests.HTTPError as e:
        print(f"HTTP error: {e}")
    except requests.RequestException as e:
        print(f"Request error: {e}")
    except ConnectionManagerError as e:
        print(f"Connection manager error: {e}")
```

## Thread Safety

`ConnectionManager` is thread-safe and can be used across multiple threads:

```python
import threading
from requests_connection_manager import ConnectionManager

# Shared manager across threads
manager = ConnectionManager()

def worker(worker_id):
    for i in range(5):
        response = manager.get(f'https://httpbin.org/get?worker={worker_id}&req={i}')
        print(f"Worker {worker_id}, Request {i}: {response.status_code}")

# Create multiple threads
threads = []
for i in range(3):
    thread = threading.Thread(target=worker, args=(i,))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()

manager.close()
```

## Statistics and Monitoring

Get insights into your connection manager's performance:

```python
with ConnectionManager() as manager:
    # Make some requests
    for i in range(5):
        response = manager.get(f'https://httpbin.org/get?req={i}')
    
    # Get statistics
    stats = manager.get_stats()
    print(f"Circuit breaker state: {stats['circuit_breaker_state']}")
    print(f"Failure count: {stats['circuit_breaker_failure_count']}")
    print(f"Rate limit: {stats['rate_limit_requests']}/{stats['rate_limit_period']}s")
    print(f"Timeout: {stats['timeout']}s")
```

## Next Steps

- [Authentication](authentication.md) - Learn about authentication methods
- [Advanced Configuration](advanced.md) - SSL, timeouts, and custom settings
- [Endpoint Configuration](endpoints.md) - Per-service configurations
- [Examples](../examples/basic.md) - See more comprehensive examples
