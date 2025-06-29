
# Advanced Features

This guide covers the advanced capabilities of `requests-connection-manager` for power users and complex scenarios.

## Plugin System

The plugin system allows you to extend functionality with custom hooks that execute at different stages of the request lifecycle.

### Hook Types

- **Pre-Request Hooks**: Execute before sending requests
- **Post-Response Hooks**: Execute after receiving responses  
- **Error Hooks**: Execute when errors occur

### Creating Custom Plugins

```python
from requests_connection_manager import ConnectionManager

def add_request_id_hook(request_context):
    """Add unique request ID to all requests."""
    import uuid
    if 'headers' not in request_context.kwargs:
        request_context.kwargs['headers'] = {}
    request_context.kwargs['headers']['X-Request-ID'] = str(uuid.uuid4())

def log_response_time_hook(response_context):
    """Log response times for monitoring."""
    duration = response_context.response.elapsed.total_seconds()
    url = response_context.request_context.url
    print(f"Request to {url} took {duration:.3f}s")

def retry_on_rate_limit_hook(error_context):
    """Custom retry logic for rate limits."""
    if hasattr(error_context.exception, 'response'):
        if error_context.exception.response.status_code == 429:
            # Extract retry-after header and implement custom backoff
            retry_after = error_context.exception.response.headers.get('Retry-After')
            if retry_after:
                import time
                time.sleep(int(retry_after))
                # Mark as handled to trigger retry
                error_context.handled = True

# Register hooks
manager = ConnectionManager()
manager.register_pre_request_hook(add_request_id_hook)
manager.register_post_response_hook(log_response_time_hook)
manager.register_error_hook(retry_on_rate_limit_hook)
```

### Advanced Plugin Example: Request Caching

```python
import hashlib
import json
import time
from typing import Dict, Any

class RequestCache:
    def __init__(self, ttl: int = 300):  # 5 minutes default TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
    
    def _get_cache_key(self, request_context):
        """Generate cache key from request details."""
        key_data = {
            'method': request_context.method,
            'url': request_context.url,
            'headers': request_context.kwargs.get('headers', {}),
            'params': request_context.kwargs.get('params', {}),
            'data': request_context.kwargs.get('data', ''),
            'json': request_context.kwargs.get('json', {})
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def pre_request_hook(self, request_context):
        """Check cache before making request."""
        # Only cache GET requests
        if request_context.method.upper() != 'GET':
            return
        
        cache_key = self._get_cache_key(request_context)
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            
            # Check if cache entry is still valid
            if time.time() - cached_data['timestamp'] < self.ttl:
                # Create a mock response from cached data
                import requests
                response = requests.Response()
                response._content = cached_data['content']
                response.status_code = cached_data['status_code']
                response.headers.update(cached_data['headers'])
                
                # Store in request context to use in post_response
                request_context._cached_response = response
                print(f"Cache HIT for {request_context.url}")
                return
        
        print(f"Cache MISS for {request_context.url}")
    
    def post_response_hook(self, response_context):
        """Cache successful responses."""
        request_context = response_context.request_context
        
        # Use cached response if available
        if hasattr(request_context, '_cached_response'):
            response_context.response = request_context._cached_response
            return
        
        # Only cache GET requests with successful responses
        if (request_context.method.upper() == 'GET' and 
            200 <= response_context.response.status_code < 300):
            
            cache_key = self._get_cache_key(request_context)
            
            self.cache[cache_key] = {
                'content': response_context.response.content,
                'status_code': response_context.response.status_code,
                'headers': dict(response_context.response.headers),
                'timestamp': time.time()
            }
    
    def clear_cache(self):
        """Clear all cached responses."""
        self.cache.clear()

# Usage
cache = RequestCache(ttl=600)  # 10 minutes
manager = ConnectionManager()

manager.register_pre_request_hook(cache.pre_request_hook)
manager.register_post_response_hook(cache.post_response_hook)

with manager:
    # First request - cache miss
    response1 = manager.get('https://httpbin.org/get?param=value')
    
    # Second request - cache hit
    response2 = manager.get('https://httpbin.org/get?param=value')
```

## SSL/TLS Advanced Configuration

### Custom SSL Context

```python
import ssl
from requests_connection_manager import ConnectionManager

# Create advanced SSL context
ssl_context = ssl.create_default_context()

# Configure specific TLS version
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3

# Configure cipher suites
ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')

# Configure certificate verification
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED

# Load custom CA certificates
ssl_context.load_verify_locations('/path/to/custom-ca-bundle.pem')

# Use with connection manager
manager = ConnectionManager(ssl_context=ssl_context)
```

### Mutual TLS (mTLS) Configuration

```python
# Client certificate authentication
manager = ConnectionManager(
    cert=('/path/to/client.crt', '/path/to/client.key'),
    verify='/path/to/ca-bundle.pem'
)

# Or with password-protected key
cert_config = ('/path/to/client.crt', '/path/to/client.key', 'key-password')
manager = ConnectionManager(cert=cert_config)

with manager:
    # All requests use client certificate
    response = manager.get('https://secure-api.example.com/data')
```

### SSL Pinning

```python
import ssl
import hashlib
from requests_connection_manager import ConnectionManager

class SSLPinningManager(ConnectionManager):
    def __init__(self, expected_cert_hash: str, **kwargs):
        super().__init__(**kwargs)
        self.expected_cert_hash = expected_cert_hash
        self.register_pre_request_hook(self._validate_certificate)
    
    def _validate_certificate(self, request_context):
        """Validate certificate hash matches expected value."""
        # This is a simplified example - real implementation would
        # need to intercept the SSL handshake
        pass

# Usage with expected certificate hash
manager = SSLPinningManager(
    expected_cert_hash="sha256:ABC123...",
    verify=True
)
```

## Advanced Circuit Breaker Patterns

### Custom Circuit Breaker States

```python
import pybreaker
from requests_connection_manager import ConnectionManager

class AdvancedCircuitBreaker:
    def __init__(self):
        # Create circuit breaker with custom state monitoring
        self.circuit_breaker = pybreaker.CircuitBreaker(
            fail_max=5,
            reset_timeout=60,
            exclude=[Exception]  # Custom exclusion logic
        )
        
        # Track state changes
        self.circuit_breaker.add_listener(self._on_state_change)
    
    def _on_state_change(self, old_state, new_state, exception=None):
        """Handle circuit breaker state changes."""
        print(f"Circuit breaker state changed: {old_state} -> {new_state}")
        
        if new_state == pybreaker.CircuitBreakerState.OPEN:
            # Alert monitoring system
            self._send_alert("Circuit breaker opened", exception)
        elif new_state == pybreaker.CircuitBreakerState.CLOSED:
            # Recovery notification
            self._send_notification("Service recovered")
    
    def _send_alert(self, message, exception):
        """Send alert to monitoring system."""
        print(f"ALERT: {message} - {exception}")
    
    def _send_notification(self, message):
        """Send notification about recovery."""
        print(f"INFO: {message}")

# Create manager with advanced circuit breaker
breaker = AdvancedCircuitBreaker()
manager = ConnectionManager()

# Replace default circuit breaker
manager.circuit_breaker = breaker.circuit_breaker
```

### Circuit Breaker with Fallback

```python
def create_fallback_manager():
    """Create manager with fallback service configuration."""
    
    primary_config = {
        'api.primary.com': {
            'circuit_breaker_failure_threshold': 3,
            'circuit_breaker_recovery_timeout': 30,
            'timeout': 10
        }
    }
    
    fallback_config = {
        'api.fallback.com': {
            'circuit_breaker_failure_threshold': 10,  # More tolerant
            'circuit_breaker_recovery_timeout': 60,
            'timeout': 20
        }
    }
    
    return ConnectionManager(endpoint_configs={**primary_config, **fallback_config})

def fetch_with_fallback(resource_path):
    """Fetch data with automatic fallback."""
    manager = create_fallback_manager()
    
    with manager:
        try:
            # Try primary service
            response = manager.get(f'https://api.primary.com{resource_path}')
            return response.json()
        
        except Exception as e:
            print(f"Primary service failed: {e}")
            
            try:
                # Try fallback service
                response = manager.get(f'https://api.fallback.com{resource_path}')
                return response.json()
            
            except Exception as fallback_error:
                print(f"Fallback service also failed: {fallback_error}")
                return None
```

## Advanced Rate Limiting

### Adaptive Rate Limiting

```python
import time
from typing import Dict
from requests_connection_manager import ConnectionManager

class AdaptiveRateLimiter:
    def __init__(self):
        self.response_times: Dict[str, list] = {}
        self.rate_limits: Dict[str, int] = {}
        self.base_rate_limit = 100
    
    def pre_request_hook(self, request_context):
        """Adjust rate limit based on response times."""
        url_pattern = self._get_url_pattern(request_context.url)
        
        if url_pattern in self.response_times:
            avg_response_time = sum(self.response_times[url_pattern]) / len(self.response_times[url_pattern])
            
            # Reduce rate limit if responses are slow
            if avg_response_time > 2.0:  # 2 seconds
                new_rate = max(10, self.base_rate_limit // 2)
            elif avg_response_time > 1.0:  # 1 second
                new_rate = max(20, self.base_rate_limit // 1.5)
            else:
                new_rate = self.base_rate_limit
            
            self.rate_limits[url_pattern] = new_rate
        
        request_context.start_time = time.time()
    
    def post_response_hook(self, response_context):
        """Track response times for adaptation."""
        url_pattern = self._get_url_pattern(response_context.request_context.url)
        response_time = time.time() - response_context.request_context.start_time
        
        if url_pattern not in self.response_times:
            self.response_times[url_pattern] = []
        
        self.response_times[url_pattern].append(response_time)
        
        # Keep only recent measurements
        if len(self.response_times[url_pattern]) > 10:
            self.response_times[url_pattern] = self.response_times[url_pattern][-10:]
    
    def _get_url_pattern(self, url):
        """Extract URL pattern for grouping."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

# Usage
adaptive_limiter = AdaptiveRateLimiter()
manager = ConnectionManager()

manager.register_pre_request_hook(adaptive_limiter.pre_request_hook)
manager.register_post_response_hook(adaptive_limiter.post_response_hook)
```

### Per-User Rate Limiting

```python
import time
from collections import defaultdict
from threading import Lock

class PerUserRateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.user_requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def pre_request_hook(self, request_context):
        """Check rate limit per user."""
        # Extract user ID from headers or URL
        user_id = self._extract_user_id(request_context)
        
        if user_id:
            with self.lock:
                current_time = time.time()
                user_requests = self.user_requests[user_id]
                
                # Remove requests older than 1 minute
                cutoff_time = current_time - 60
                user_requests[:] = [req_time for req_time in user_requests if req_time > cutoff_time]
                
                # Check if user has exceeded rate limit
                if len(user_requests) >= self.requests_per_minute:
                    from requests_connection_manager.exceptions import RateLimitExceeded
                    raise RateLimitExceeded(f"Rate limit exceeded for user {user_id}")
                
                # Add current request
                user_requests.append(current_time)
    
    def _extract_user_id(self, request_context):
        """Extract user ID from request context."""
        headers = request_context.kwargs.get('headers', {})
        
        # Check for user ID in headers
        return headers.get('X-User-ID') or headers.get('User-ID')

# Usage
user_limiter = PerUserRateLimiter(requests_per_minute=30)
manager = ConnectionManager()
manager.register_pre_request_hook(user_limiter.pre_request_hook)
```

## Advanced Monitoring and Observability

### Distributed Tracing Integration

```python
import uuid
import time
from typing import Optional

class DistributedTracing:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.active_traces = {}
    
    def pre_request_hook(self, request_context):
        """Start distributed trace."""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        # Add tracing headers
        if 'headers' not in request_context.kwargs:
            request_context.kwargs['headers'] = {}
        
        request_context.kwargs['headers'].update({
            'X-Trace-ID': trace_id,
            'X-Span-ID': span_id,
            'X-Parent-Span': getattr(request_context, 'parent_span', ''),
            'X-Service-Name': self.service_name
        })
        
        # Store trace information
        request_context.trace_id = trace_id
        request_context.span_id = span_id
        request_context.start_time = time.time()
        
        self.active_traces[span_id] = {
            'trace_id': trace_id,
            'span_id': span_id,
            'method': request_context.method,
            'url': request_context.url,
            'start_time': request_context.start_time
        }
    
    def post_response_hook(self, response_context):
        """Complete distributed trace."""
        request_context = response_context.request_context
        
        if hasattr(request_context, 'span_id'):
            span_id = request_context.span_id
            
            if span_id in self.active_traces:
                trace_data = self.active_traces[span_id]
                trace_data.update({
                    'duration': time.time() - request_context.start_time,
                    'status_code': response_context.response.status_code,
                    'success': 200 <= response_context.response.status_code < 400
                })
                
                # Send to tracing backend (Jaeger, Zipkin, etc.)
                self._send_trace(trace_data)
                del self.active_traces[span_id]
    
    def error_hook(self, error_context):
        """Handle trace for errors."""
        request_context = error_context.request_context
        
        if hasattr(request_context, 'span_id'):
            span_id = request_context.span_id
            
            if span_id in self.active_traces:
                trace_data = self.active_traces[span_id]
                trace_data.update({
                    'duration': time.time() - request_context.start_time,
                    'error': str(error_context.exception),
                    'success': False
                })
                
                self._send_trace(trace_data)
                del self.active_traces[span_id]
    
    def _send_trace(self, trace_data):
        """Send trace data to monitoring backend."""
        # In real implementation, send to Jaeger, Zipkin, or other tracing system
        print(f"Trace: {trace_data['trace_id']} - {trace_data['method']} {trace_data['url']} - "
              f"{trace_data['duration']:.3f}s - Success: {trace_data.get('success', False)}")

# Usage
tracer = DistributedTracing("my-service")
manager = ConnectionManager()

manager.register_pre_request_hook(tracer.pre_request_hook)
manager.register_post_response_hook(tracer.post_response_hook)
manager.register_error_hook(tracer.error_hook)
```

### Performance Metrics Collection

```python
import time
import statistics
from collections import defaultdict
from threading import Lock

class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            'request_count': 0,
            'error_count': 0,
            'response_times': [],
            'status_codes': defaultdict(int)
        })
        self.lock = Lock()
    
    def pre_request_hook(self, request_context):
        """Mark request start time."""
        request_context.perf_start_time = time.perf_counter()
    
    def post_response_hook(self, response_context):
        """Collect performance metrics."""
        request_context = response_context.request_context
        
        if hasattr(request_context, 'perf_start_time'):
            duration = time.perf_counter() - request_context.perf_start_time
            
            # Extract service name from URL
            service_name = self._extract_service_name(request_context.url)
            
            with self.lock:
                metrics = self.metrics[service_name]
                metrics['request_count'] += 1
                metrics['response_times'].append(duration)
                metrics['status_codes'][response_context.response.status_code] += 1
                
                # Keep only recent response times (last 1000 requests)
                if len(metrics['response_times']) > 1000:
                    metrics['response_times'] = metrics['response_times'][-1000:]
    
    def error_hook(self, error_context):
        """Track errors."""
        service_name = self._extract_service_name(error_context.request_context.url)
        
        with self.lock:
            self.metrics[service_name]['error_count'] += 1
    
    def _extract_service_name(self, url):
        """Extract service name from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def get_metrics_summary(self):
        """Get performance metrics summary."""
        summary = {}
        
        with self.lock:
            for service, metrics in self.metrics.items():
                response_times = metrics['response_times']
                
                if response_times:
                    summary[service] = {
                        'request_count': metrics['request_count'],
                        'error_count': metrics['error_count'],
                        'error_rate': metrics['error_count'] / metrics['request_count'],
                        'avg_response_time': statistics.mean(response_times),
                        'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times),
                        'p99_response_time': statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else max(response_times),
                        'status_codes': dict(metrics['status_codes'])
                    }
        
        return summary

# Usage
monitor = PerformanceMonitor()
manager = ConnectionManager()

manager.register_pre_request_hook(monitor.pre_request_hook)
manager.register_post_response_hook(monitor.post_response_hook)
manager.register_error_hook(monitor.error_hook)

with manager:
    # Make some requests
    for i in range(10):
        manager.get(f'https://httpbin.org/delay/{i%3}')

# Get performance summary
print(monitor.get_metrics_summary())
```

## Load Balancing and Service Discovery

### Round-Robin Load Balancer

```python
import itertools
from typing import List
from requests_connection_manager import ConnectionManager

class LoadBalancedManager:
    def __init__(self, service_endpoints: List[str], **kwargs):
        self.endpoints = itertools.cycle(service_endpoints)
        self.base_manager = ConnectionManager(**kwargs)
    
    def _get_next_endpoint(self):
        """Get next endpoint in round-robin fashion."""
        return next(self.endpoints)
    
    def request(self, method: str, path: str, **kwargs):
        """Make request to next available endpoint."""
        endpoint = self._get_next_endpoint()
        url = f"{endpoint.rstrip('/')}/{path.lstrip('/')}"
        
        return self.base_manager.request(method, url, **kwargs)
    
    def get(self, path: str, **kwargs):
        return self.request('GET', path, **kwargs)
    
    def post(self, path: str, **kwargs):
        return self.request('POST', path, **kwargs)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.base_manager.close()

# Usage
endpoints = [
    'https://api1.example.com',
    'https://api2.example.com',
    'https://api3.example.com'
]

with LoadBalancedManager(endpoints) as lb_manager:
    # Requests are distributed across endpoints
    for i in range(6):
        response = lb_manager.get(f'/data/{i}')
        print(f"Request {i}: {response.status_code}")
```

### Health-Aware Load Balancer

```python
import time
import random
from typing import List, Dict
from threading import Lock

class HealthAwareLoadBalancer:
    def __init__(self, service_endpoints: List[str], health_check_interval: int = 30):
        self.endpoints = service_endpoints
        self.healthy_endpoints = set(service_endpoints)
        self.endpoint_health = {ep: True for ep in service_endpoints}
        self.last_health_check = 0
        self.health_check_interval = health_check_interval
        self.lock = Lock()
        self.manager = ConnectionManager(timeout=5)
    
    def _check_endpoint_health(self, endpoint: str) -> bool:
        """Check if endpoint is healthy."""
        try:
            response = self.manager.get(f"{endpoint}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _update_health_status(self):
        """Update health status of all endpoints."""
        current_time = time.time()
        
        if current_time - self.last_health_check < self.health_check_interval:
            return
        
        with self.lock:
            for endpoint in self.endpoints:
                is_healthy = self._check_endpoint_health(endpoint)
                self.endpoint_health[endpoint] = is_healthy
                
                if is_healthy:
                    self.healthy_endpoints.add(endpoint)
                else:
                    self.healthy_endpoints.discard(endpoint)
            
            self.last_health_check = current_time
    
    def get_healthy_endpoint(self) -> str:
        """Get a healthy endpoint."""
        self._update_health_status()
        
        with self.lock:
            if not self.healthy_endpoints:
                # If no healthy endpoints, try any endpoint
                return random.choice(self.endpoints)
            
            return random.choice(list(self.healthy_endpoints))
    
    def request(self, method: str, path: str, **kwargs):
        """Make request to a healthy endpoint."""
        endpoint = self.get_healthy_endpoint()
        url = f"{endpoint.rstrip('/')}/{path.lstrip('/')}"
        
        try:
            return self.manager.request(method, url, **kwargs)
        except Exception as e:
            # Mark endpoint as unhealthy on error
            with self.lock:
                self.healthy_endpoints.discard(endpoint)
                self.endpoint_health[endpoint] = False
            raise

# Usage
endpoints = [
    'https://api1.example.com',
    'https://api2.example.com',
    'https://api3.example.com'
]

lb = HealthAwareLoadBalancer(endpoints)
response = lb.request('GET', '/data')
```

## Next Steps

- [API Reference](api-reference.md) - Complete API documentation
- [Usage Examples](usage-examples.md) - More practical examples
- [Configuration](configuration.md) - Detailed configuration options
