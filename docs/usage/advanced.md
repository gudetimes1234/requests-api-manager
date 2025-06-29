
# Advanced Configuration

This guide covers advanced configuration options for SSL, timeouts, connection settings, and more.

## SSL and Certificate Configuration

### SSL Verification

```python
from requests_connection_manager import ConnectionManager

# Disable SSL verification (not recommended for production)
manager = ConnectionManager(verify=False)

# Use custom CA bundle
manager = ConnectionManager(verify="/path/to/ca-bundle.pem")

# Use system default CA bundle (default)
manager = ConnectionManager(verify=True)
```

### Client Certificates (Mutual TLS)

```python
# Single file containing both cert and key
manager = ConnectionManager(cert="/path/to/client.pem")

# Separate cert and key files
manager = ConnectionManager(cert=("/path/to/client.crt", "/path/to/client.key"))

# Update after initialization
manager = ConnectionManager()
manager.set_client_certificate(("/path/to/cert.crt", "/path/to/key.key"))
```

### Custom SSL Context

```python
import ssl
from requests_connection_manager import ConnectionManager

# Create custom SSL context
ssl_context = ssl.create_default_context()
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_context.check_hostname = False

manager = ConnectionManager(ssl_context=ssl_context)

# Update after initialization
manager.set_ssl_context(ssl_context)
```

## Timeout Configuration

### Basic Timeouts

```python
# Global timeout for all requests
manager = ConnectionManager(timeout=30)

# Request-specific timeout
with manager:
    response = manager.get('https://api.example.com/data', timeout=60)
```

### Fine-Grained Timeouts

```python
# Separate connection and read timeouts
manager = ConnectionManager(
    connect_timeout=5.0,  # 5 seconds to establish connection
    read_timeout=30.0     # 30 seconds to read response
)

# Update timeouts after initialization
manager.set_timeouts(connect_timeout=3.0, read_timeout=25.0)

# Tuple format for request-specific timeouts
with manager:
    response = manager.get(
        'https://api.example.com/data',
        timeout=(5.0, 30.0)  # (connect, read)
    )
```

## Connection Pool Configuration

### Pool Settings

```python
manager = ConnectionManager(
    pool_connections=20,    # Number of connection pools to cache
    pool_maxsize=50,       # Maximum connections per pool
    max_retries=5          # Retry attempts per connection
)
```

### Advanced Pool Configuration

```python
# For high-throughput applications
manager = ConnectionManager(
    pool_connections=100,   # More pools for different hosts
    pool_maxsize=100,      # More connections per pool
    max_retries=3,
    backoff_factor=0.1     # Faster retries
)

# For resource-constrained environments
manager = ConnectionManager(
    pool_connections=5,     # Fewer pools
    pool_maxsize=10,       # Fewer connections
    max_retries=2
)
```

## Retry Configuration

### Retry Strategy

```python
manager = ConnectionManager(
    max_retries=5,          # Maximum retry attempts
    backoff_factor=0.5      # Exponential backoff multiplier
)

# Retry delays: 0.5s, 1s, 2s, 4s, 8s
```

### Custom Retry Logic

```python
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Create custom retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1.0,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS", "POST"]
)

# Apply to manager's session (advanced usage)
manager = ConnectionManager()
adapter = HTTPAdapter(max_retries=retry_strategy)
manager.session.mount("https://", adapter)
manager.session.mount("http://", adapter)
```

## Rate Limiting Configuration

### Global Rate Limiting

```python
manager = ConnectionManager(
    rate_limit_requests=100,  # Requests allowed
    rate_limit_period=60      # Time period in seconds
)
```

### Per-Endpoint Rate Limiting

```python
endpoint_configs = {
    'api.github.com': {
        'rate_limit_requests': 60,
        'rate_limit_period': 3600  # 60 requests per hour
    },
    'api.twitter.com': {
        'rate_limit_requests': 300,
        'rate_limit_period': 900   # 300 requests per 15 minutes
    }
}

manager = ConnectionManager(endpoint_configs=endpoint_configs)
```

## Circuit Breaker Configuration

### Basic Circuit Breaker

```python
manager = ConnectionManager(
    circuit_breaker_failure_threshold=5,   # Open after 5 failures
    circuit_breaker_recovery_timeout=60    # Try to recover after 60 seconds
)
```

### Per-Endpoint Circuit Breakers

```python
endpoint_configs = {
    'unreliable-service.com': {
        'circuit_breaker_failure_threshold': 3,
        'circuit_breaker_recovery_timeout': 30
    },
    'stable-service.com': {
        'circuit_breaker_failure_threshold': 10,
        'circuit_breaker_recovery_timeout': 120
    }
}

manager = ConnectionManager(endpoint_configs=endpoint_configs)
```

## Comprehensive Configuration Example

```python
import ssl
from requests_connection_manager import ConnectionManager

# Create custom SSL context
ssl_context = ssl.create_default_context()
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

# Endpoint-specific configurations
endpoint_configs = {
    'secure-bank-api.com': {
        'timeout': 120,
        'rate_limit_requests': 10,
        'rate_limit_period': 60,
        'circuit_breaker_failure_threshold': 3,
        'circuit_breaker_recovery_timeout': 300,
        'bearer_token': 'bank-api-token'
    },
    'partner-api.example.com': {
        'timeout': 45,
        'rate_limit_requests': 50,
        'rate_limit_period': 60,
        'api_key': 'partner-api-key',
        'api_key_header': 'X-Partner-Key'
    },
    'internal-service.company.com': {
        'timeout': 30,
        'rate_limit_requests': 200,
        'rate_limit_period': 60,
        'verify': '/path/to/internal-ca.pem',
        'cert': ('/path/to/client.crt', '/path/to/client.key')
    }
}

# Create manager with comprehensive configuration
manager = ConnectionManager(
    # Connection pooling
    pool_connections=50,
    pool_maxsize=100,
    
    # Retry configuration
    max_retries=3,
    backoff_factor=0.5,
    
    # Default rate limiting
    rate_limit_requests=100,
    rate_limit_period=60,
    
    # Default circuit breaker
    circuit_breaker_failure_threshold=5,
    circuit_breaker_recovery_timeout=60,
    
    # Default timeout
    timeout=30,
    
    # SSL configuration
    verify=True,
    cert=None,
    connect_timeout=5.0,
    read_timeout=30.0,
    ssl_context=ssl_context,
    
    # Global authentication
    bearer_token="global-default-token",
    
    # Endpoint-specific configurations
    endpoint_configs=endpoint_configs
)

with manager:
    # Bank API - uses secure config with long timeout
    bank_response = manager.get('https://secure-bank-api.com/account/balance')
    
    # Partner API - uses partner-specific API key
    partner_response = manager.get('https://partner-api.example.com/data')
    
    # Internal service - uses mutual TLS
    internal_response = manager.get('https://internal-service.company.com/metrics')
    
    # Other services use global defaults
    public_response = manager.get('https://api.publicservice.com/data')
```

## Dynamic Configuration Updates

### Runtime Configuration Changes

```python
manager = ConnectionManager()

# Update authentication
manager.set_bearer_token("new-token")

# Update SSL settings
manager.set_ssl_verification("/new/path/to/ca-bundle.pem")
manager.set_client_certificate(("/new/cert.crt", "/new/key.key"))

# Update timeouts
manager.set_timeouts(connect_timeout=2.0, read_timeout=15.0)

# Add new endpoint configuration
manager.add_endpoint_config('new-api.com', {
    'timeout': 60,
    'rate_limit_requests': 25,
    'api_key': 'new-api-key'
})

# Remove endpoint configuration
manager.remove_endpoint_config('old-api.com')
```

## Performance Optimization

### High-Throughput Configuration

```python
# Optimized for high request volume
manager = ConnectionManager(
    pool_connections=100,      # Many pools for different hosts
    pool_maxsize=200,         # Large pool size
    max_retries=2,            # Fewer retries for speed
    backoff_factor=0.1,       # Quick retries
    rate_limit_requests=1000, # High rate limit
    rate_limit_period=60,
    circuit_breaker_failure_threshold=10,
    timeout=15,               # Shorter timeout
    connect_timeout=2.0,      # Quick connection timeout
    read_timeout=10.0         # Reasonable read timeout
)
```

### Resource-Constrained Configuration

```python
# Optimized for low resource usage
manager = ConnectionManager(
    pool_connections=5,        # Few pools
    pool_maxsize=10,          # Small pool size
    max_retries=1,            # Minimal retries
    rate_limit_requests=20,   # Conservative rate limit
    rate_limit_period=60,
    circuit_breaker_failure_threshold=3,
    timeout=60,               # Longer timeout tolerance
    connect_timeout=10.0,
    read_timeout=30.0
)
```

## Monitoring and Statistics

### Getting Performance Statistics

```python
with manager:
    # Make some requests
    for i in range(10):
        response = manager.get(f'https://api.example.com/item/{i}')
    
    # Get detailed statistics
    stats = manager.get_stats()
    
    print(f"Circuit breaker state: {stats['circuit_breaker_state']}")
    print(f"Failure count: {stats['circuit_breaker_failure_count']}")
    print(f"Rate limit: {stats['rate_limit_requests']}/{stats['rate_limit_period']}s")
    print(f"SSL verification: {stats['ssl_verification']}")
    print(f"Client cert configured: {stats['client_certificate_configured']}")
    print(f"Connect timeout: {stats['connect_timeout']}s")
    print(f"Read timeout: {stats['read_timeout']}s")
    print(f"Registered hooks: {stats['registered_hooks']}")
    print(f"Endpoint configs: {len(stats['endpoint_configs'])}")
```

## Environment-Specific Configurations

### Development Environment

```python
# Development configuration
dev_manager = ConnectionManager(
    verify=False,             # Skip SSL verification for local testing
    timeout=120,              # Longer timeouts for debugging
    max_retries=1,           # Fewer retries to fail fast
    rate_limit_requests=1000, # No real rate limiting
    circuit_breaker_failure_threshold=50  # More forgiving
)
```

### Production Environment

```python
# Production configuration
prod_manager = ConnectionManager(
    verify=True,              # Strict SSL verification
    timeout=30,               # Reasonable timeouts
    max_retries=3,           # Sensible retry count
    rate_limit_requests=100, # Proper rate limiting
    rate_limit_period=60,
    circuit_breaker_failure_threshold=5,
    circuit_breaker_recovery_timeout=60,
    connect_timeout=5.0,     # Quick connection timeout
    read_timeout=25.0        # Reasonable read timeout
)
```

## Next Steps

- [Endpoint Configuration](endpoints.md) - Per-service configurations
- [Batch Requests](batch.md) - Concurrent request processing
- [Examples](../examples/advanced.md) - Advanced usage examples
