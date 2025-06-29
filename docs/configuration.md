
# Configuration

This guide covers all configuration options available in `requests-connection-manager`.

## Basic Configuration

### Default Settings

```python
from requests_connection_manager import ConnectionManager

# All default values shown
manager = ConnectionManager(
    pool_connections=10,                    # Connection pools to cache
    pool_maxsize=10,                       # Max connections per pool
    max_retries=3,                         # Retry attempts
    backoff_factor=0.3,                    # Retry delay multiplier
    rate_limit_requests=100,               # Requests per period
    rate_limit_period=60,                  # Rate limit period (seconds)
    circuit_breaker_failure_threshold=5,   # Failures before opening
    circuit_breaker_recovery_timeout=60,   # Recovery timeout (seconds)
    timeout=30                             # Default timeout
)
```

## Connection Pooling

### Pool Size Configuration

```python
# For high-throughput applications
manager = ConnectionManager(
    pool_connections=50,    # More pools for different hosts
    pool_maxsize=100       # More connections per pool
)

# For resource-constrained environments
manager = ConnectionManager(
    pool_connections=5,     # Fewer pools
    pool_maxsize=10        # Fewer connections
)
```

### Performance Optimization

```python
# Optimized for speed
manager = ConnectionManager(
    pool_connections=100,
    pool_maxsize=200,
    max_retries=2,          # Fewer retries
    backoff_factor=0.1      # Faster retries
)
```

## Retry Configuration

### Basic Retry Settings

```python
manager = ConnectionManager(
    max_retries=5,          # Maximum attempts
    backoff_factor=0.5      # Exponential backoff
)
# Retry delays: 0.5s, 1s, 2s, 4s, 8s
```

### Fine-tuned Retry Strategy

```python
# Conservative retries
manager = ConnectionManager(
    max_retries=2,
    backoff_factor=1.0      # Longer delays: 1s, 2s
)

# Aggressive retries
manager = ConnectionManager(
    max_retries=10,
    backoff_factor=0.1      # Quick retries: 0.1s, 0.2s, 0.4s...
)
```

## Rate Limiting

### Global Rate Limiting

```python
manager = ConnectionManager(
    rate_limit_requests=100,  # 100 requests
    rate_limit_period=60      # per minute
)
```

### Endpoint-Specific Rate Limiting

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

## Circuit Breaker

### Basic Circuit Breaker

```python
manager = ConnectionManager(
    circuit_breaker_failure_threshold=5,   # Open after 5 failures
    circuit_breaker_recovery_timeout=60    # Try recovery after 60s
)
```

### Service-Specific Circuit Breakers

```python
endpoint_configs = {
    'unstable-service.com': {
        'circuit_breaker_failure_threshold': 3,   # More sensitive
        'circuit_breaker_recovery_timeout': 30
    },
    'reliable-service.com': {
        'circuit_breaker_failure_threshold': 10,  # More tolerant
        'circuit_breaker_recovery_timeout': 120
    }
}

manager = ConnectionManager(endpoint_configs=endpoint_configs)
```

## Timeout Configuration

### Simple Timeouts

```python
# Global timeout
manager = ConnectionManager(timeout=30)

# Request-specific timeout
with manager:
    response = manager.get('https://api.example.com/data', timeout=60)
```

### Fine-Grained Timeouts

```python
manager = ConnectionManager(
    connect_timeout=5.0,    # Connection timeout
    read_timeout=30.0       # Read timeout
)

# Or specify per request
with manager:
    response = manager.get(
        'https://api.example.com/data',
        timeout=(5.0, 30.0)  # (connect, read)
    )
```

## SSL Configuration

### SSL Verification

```python
# Default: verify with system CA bundle
manager = ConnectionManager(verify=True)

# Use custom CA bundle
manager = ConnectionManager(verify="/path/to/ca-bundle.pem")

# Disable verification (not recommended for production)
manager = ConnectionManager(verify=False)
```

### Client Certificates (Mutual TLS)

```python
# Single file with cert and key
manager = ConnectionManager(cert="/path/to/client.pem")

# Separate cert and key files
manager = ConnectionManager(
    cert=("/path/to/client.crt", "/path/to/client.key")
)
```

### Custom SSL Context

```python
import ssl

# Create custom SSL context
ssl_context = ssl.create_default_context()
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

manager = ConnectionManager(ssl_context=ssl_context)
```

## Authentication

### API Key Authentication

```python
# Global API key
manager = ConnectionManager(
    api_key="your-api-key",
    api_key_header="X-API-Key"  # Custom header name
)

# Endpoint-specific API key
endpoint_configs = {
    'api.service1.com': {
        'api_key': 'service1-key',
        'api_key_header': 'X-Service1-Key'
    }
}
```

### Bearer Token Authentication

```python
# Global Bearer token
manager = ConnectionManager(bearer_token="your-token")

# Endpoint-specific token
endpoint_configs = {
    'api.service.com': {
        'bearer_token': 'service-specific-token'
    }
}
```

### Basic Authentication

```python
# Global basic auth
manager = ConnectionManager(
    basic_auth=("username", "password")
)

# Endpoint-specific basic auth
endpoint_configs = {
    'secure.api.com': {
        'basic_auth': ('user', 'pass')
    }
}
```

## Endpoint-Specific Configuration

### Complete Endpoint Configuration

```python
endpoint_configs = {
    'critical-service.com': {
        # Connection settings
        'timeout': 120,
        'max_retries': 5,
        'backoff_factor': 0.5,
        
        # Rate limiting
        'rate_limit_requests': 50,
        'rate_limit_period': 60,
        
        # Circuit breaker
        'circuit_breaker_failure_threshold': 3,
        'circuit_breaker_recovery_timeout': 300,
        
        # Authentication
        'bearer_token': 'critical-service-token',
        
        # SSL settings
        'verify': '/path/to/critical-service-ca.pem',
        'cert': ('/path/to/client.crt', '/path/to/client.key')
    },
    'analytics-service.com': {
        'timeout': 90,
        'rate_limit_requests': 20,
        'rate_limit_period': 60,
        'max_retries': 2
    }
}

manager = ConnectionManager(endpoint_configs=endpoint_configs)
```

## Environment-Based Configuration

### Development Configuration

```python
import os

def create_dev_manager():
    return ConnectionManager(
        verify=False,                    # Skip SSL in dev
        timeout=120,                     # Longer timeouts for debugging
        rate_limit_requests=1000,        # No real rate limiting
        circuit_breaker_failure_threshold=50  # More forgiving
    )
```

### Production Configuration

```python
def create_prod_manager():
    return ConnectionManager(
        verify=True,                     # Strict SSL
        timeout=30,                      # Reasonable timeouts
        max_retries=3,                   # Proper retry count
        rate_limit_requests=100,         # Proper rate limiting
        circuit_breaker_failure_threshold=5,
        connect_timeout=5.0,             # Quick connection timeout
        read_timeout=25.0                # Reasonable read timeout
    )
```

## Dynamic Configuration

### Runtime Updates

```python
manager = ConnectionManager()

# Update authentication
manager.set_bearer_token("new-token")
manager.set_api_key("new-key", "X-New-Header")

# Update SSL settings
manager.set_ssl_verification("/new/ca-bundle.pem")
manager.set_client_certificate(("/new/cert.crt", "/new/key.key"))

# Update timeouts
manager.set_timeouts(connect_timeout=3.0, read_timeout=20.0)

# Add endpoint configuration
manager.add_endpoint_config('new-api.com', {
    'timeout': 60,
    'rate_limit_requests': 25
})
```

## Configuration Validation

### Getting Current Configuration

```python
with manager:
    # Get comprehensive stats
    stats = manager.get_stats()
    
    print(f"Circuit breaker state: {stats['circuit_breaker_state']}")
    print(f"Rate limit: {stats['rate_limit_requests']}/{stats['rate_limit_period']}s")
    print(f"SSL verification: {stats['ssl_verification']}")
    print(f"Endpoint configs: {len(stats['endpoint_configs'])}")
```

## Best Practices

### Production Recommendations

```python
# Recommended production configuration
manager = ConnectionManager(
    # Conservative connection pooling
    pool_connections=20,
    pool_maxsize=50,
    
    # Reasonable retry strategy
    max_retries=3,
    backoff_factor=0.5,
    
    # Proper rate limiting
    rate_limit_requests=100,
    rate_limit_period=60,
    
    # Fail-fast circuit breaker
    circuit_breaker_failure_threshold=5,
    circuit_breaker_recovery_timeout=60,
    
    # Quick timeouts
    timeout=30,
    connect_timeout=5.0,
    read_timeout=25.0,
    
    # Secure defaults
    verify=True
)
```

### High-Performance Configuration

```python
# For high-throughput applications
manager = ConnectionManager(
    pool_connections=100,
    pool_maxsize=200,
    max_retries=2,
    backoff_factor=0.1,
    rate_limit_requests=1000,
    timeout=15,
    connect_timeout=2.0,
    read_timeout=10.0
)
```

### Resource-Constrained Configuration

```python
# For limited resources
manager = ConnectionManager(
    pool_connections=5,
    pool_maxsize=10,
    max_retries=1,
    rate_limit_requests=20,
    timeout=60
)
```

## Next Steps

- [Usage Examples](usage-examples.md) - See configuration in action
- [Advanced Features](advanced-features.md) - Explore advanced capabilities
- [API Reference](api-reference.md) - Complete API documentation
