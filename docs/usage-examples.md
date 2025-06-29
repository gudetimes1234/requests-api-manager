
# Usage Examples

This page provides practical examples of using `requests-connection-manager` in real-world scenarios.

## Basic Usage Examples

### Simple GET Request

```python
from requests_connection_manager import ConnectionManager

# Basic GET request with automatic features
with ConnectionManager() as manager:
    response = manager.get('https://httpbin.org/get')
    print(f"Status: {response.status_code}")
    print(f"Data: {response.json()}")
```

### POST Request with JSON Data

```python
with ConnectionManager() as manager:
    data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'age': 30
    }
    
    response = manager.post(
        'https://httpbin.org/post',
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Response: {response.json()}")
```

### File Upload

```python
with ConnectionManager() as manager:
    files = {'file': open('document.pdf', 'rb')}
    data = {'description': 'Important document'}
    
    response = manager.post(
        'https://httpbin.org/post',
        files=files,
        data=data
    )
    
    print(f"Upload status: {response.status_code}")
```

## Authentication Examples

### API Key Authentication

```python
# Global API key
manager = ConnectionManager(
    api_key="your-api-key-here",
    api_key_header="X-API-Key"
)

with manager:
    # API key automatically added to all requests
    response = manager.get('https://api.example.com/protected-data')
    print(response.json())
```

### Bearer Token Authentication

```python
# OAuth2/Bearer token
manager = ConnectionManager(bearer_token="your-oauth-token")

with manager:
    response = manager.get('https://api.example.com/user/profile')
    print(f"User data: {response.json()}")
```

### Basic Authentication

```python
# Username and password
manager = ConnectionManager(
    basic_auth=("username", "password")
)

with manager:
    response = manager.get('https://httpbin.org/basic-auth/username/password')
    print(f"Authenticated: {response.status_code == 200}")
```

### Multiple Authentication Methods

```python
# Different auth for different services
endpoint_configs = {
    'api.github.com': {
        'bearer_token': 'github-token'
    },
    'api.service.com': {
        'api_key': 'service-key',
        'api_key_header': 'X-Service-Key'
    },
    'secure.internal.com': {
        'basic_auth': ('admin', 'secret')
    }
}

manager = ConnectionManager(endpoint_configs=endpoint_configs)

with manager:
    # Each request uses appropriate authentication
    github_response = manager.get('https://api.github.com/user')
    service_response = manager.get('https://api.service.com/data')
    internal_response = manager.get('https://secure.internal.com/admin')
```

## Error Handling Examples

### Basic Error Handling

```python
from requests_connection_manager import ConnectionManager
from requests_connection_manager.exceptions import (
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)
import requests

with ConnectionManager() as manager:
    try:
        response = manager.get('https://api.example.com/data')
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        
    except RateLimitExceeded:
        print("Rate limit exceeded, please wait")
        
    except CircuitBreakerOpen:
        print("Service is currently unavailable")
        
    except MaxRetriesExceeded:
        print("Request failed after maximum retries")
        
    except requests.HTTPError as e:
        print(f"HTTP error: {e}")
        
    except requests.RequestException as e:
        print(f"Request error: {e}")
```

### Graceful Degradation

```python
def fetch_user_data(user_id):
    """Fetch user data with fallback strategies."""
    manager = ConnectionManager(
        max_retries=3,
        circuit_breaker_failure_threshold=5
    )
    
    with manager:
        try:
            # Try primary API
            response = manager.get(f'https://api.primary.com/users/{user_id}')
            return response.json()
            
        except CircuitBreakerOpen:
            # Try backup API if primary is down
            try:
                response = manager.get(f'https://api.backup.com/users/{user_id}')
                return response.json()
            except Exception:
                # Return cached data or default
                return get_cached_user_data(user_id)
                
        except Exception as e:
            print(f"Failed to fetch user data: {e}")
            return None
```

## Concurrent Requests Examples

### Batch Requests

```python
# Prepare multiple requests
requests_data = [
    ('GET', 'https://httpbin.org/get?id=1', {}),
    ('GET', 'https://httpbin.org/get?id=2', {}),
    ('GET', 'https://httpbin.org/get?id=3', {}),
    ('POST', 'https://httpbin.org/post', {'json': {'data': 'test'}}),
    ('GET', 'https://httpbin.org/delay/1', {'timeout': 5})
]

with ConnectionManager() as manager:
    # Execute all requests concurrently
    results = manager.batch_request(
        requests_data,
        max_workers=3,
        return_exceptions=True
    )
    
    # Process results
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Request {i} failed: {result}")
        else:
            print(f"Request {i} success: {result.status_code}")
```

### Data Aggregation

```python
def fetch_user_details(user_ids):
    """Fetch details for multiple users concurrently."""
    requests_data = [
        ('GET', f'https://api.example.com/users/{user_id}', {})
        for user_id in user_ids
    ]
    
    with ConnectionManager() as manager:
        results = manager.batch_request(
            requests_data,
            max_workers=10
        )
        
        users = []
        for result in results:
            if not isinstance(result, Exception):
                users.append(result.json())
        
        return users

# Usage
user_ids = [1, 2, 3, 4, 5]
users = fetch_user_details(user_ids)
print(f"Fetched {len(users)} users")
```

## Async Examples

### Basic Async Usage

```python
import asyncio
from requests_connection_manager import AsyncConnectionManager

async def fetch_data():
    async with AsyncConnectionManager() as manager:
        response = await manager.get('https://httpbin.org/get')
        return response.json()

# Run async function
data = asyncio.run(fetch_data())
print(data)
```

### Async Batch Requests

```python
async def async_batch_example():
    requests_data = [
        ('GET', 'https://httpbin.org/get?page=1', {}),
        ('GET', 'https://httpbin.org/get?page=2', {}),
        ('GET', 'https://httpbin.org/get?page=3', {})
    ]
    
    async with AsyncConnectionManager() as manager:
        results = await manager.batch_request(
            requests_data,
            max_workers=5
        )
        
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                print(f"Page {i+1}: {result.status_code}")

asyncio.run(async_batch_example())
```

## API Integration Examples

### REST API Client

```python
class APIClient:
    def __init__(self, base_url, api_key):
        self.manager = ConnectionManager(
            api_key=api_key,
            api_key_header="Authorization",
            timeout=30,
            max_retries=3
        )
        self.base_url = base_url.rstrip('/')
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.close()
    
    def get_user(self, user_id):
        with self.manager:
            response = self.manager.get(f'{self.base_url}/users/{user_id}')
            response.raise_for_status()
            return response.json()
    
    def create_user(self, user_data):
        with self.manager:
            response = self.manager.post(
                f'{self.base_url}/users',
                json=user_data
            )
            response.raise_for_status()
            return response.json()
    
    def update_user(self, user_id, user_data):
        with self.manager:
            response = self.manager.put(
                f'{self.base_url}/users/{user_id}',
                json=user_data
            )
            response.raise_for_status()
            return response.json()

# Usage
with APIClient('https://api.example.com', 'your-api-key') as client:
    user = client.get_user(123)
    print(f"User: {user['name']}")
```

### Microservices Communication

```python
class ServiceRegistry:
    def __init__(self):
        # Configure different settings for different services
        endpoint_configs = {
            'user-service': {
                'timeout': 10,
                'rate_limit_requests': 200,
                'circuit_breaker_failure_threshold': 5
            },
            'order-service': {
                'timeout': 30,
                'rate_limit_requests': 100,
                'circuit_breaker_failure_threshold': 3
            },
            'notification-service': {
                'timeout': 5,
                'rate_limit_requests': 500,
                'max_retries': 1  # Fire and forget
            }
        }
        
        self.manager = ConnectionManager(
            endpoint_configs=endpoint_configs,
            bearer_token=self._get_service_token()
        )
    
    def _get_service_token(self):
        # Get service-to-service authentication token
        return "service-token"
    
    def get_user_profile(self, user_id):
        with self.manager:
            response = self.manager.get(
                f'https://user-service/api/users/{user_id}'
            )
            return response.json()
    
    def create_order(self, order_data):
        with self.manager:
            response = self.manager.post(
                'https://order-service/api/orders',
                json=order_data
            )
            return response.json()
    
    def send_notification(self, notification_data):
        with self.manager:
            try:
                self.manager.post(
                    'https://notification-service/api/notify',
                    json=notification_data
                )
            except Exception as e:
                # Log but don't fail the main operation
                print(f"Notification failed: {e}")
```

## Real-World Scenarios

### Data Pipeline

```python
def process_data_pipeline():
    """Example data processing pipeline with external API calls."""
    
    # Configure for data processing workload
    manager = ConnectionManager(
        pool_connections=20,
        pool_maxsize=50,
        rate_limit_requests=200,
        rate_limit_period=60,
        timeout=120  # Longer timeout for data processing
    )
    
    with manager:
        # Step 1: Fetch source data
        response = manager.get('https://api.data-source.com/export')
        source_data = response.json()
        
        # Step 2: Process data in batches
        processed_items = []
        batch_size = 10
        
        for i in range(0, len(source_data['items']), batch_size):
            batch = source_data['items'][i:i+batch_size]
            
            # Prepare batch requests for enrichment
            enrichment_requests = [
                ('GET', f'https://api.enrichment.com/enhance/{item["id"]}', {})
                for item in batch
            ]
            
            # Execute batch enrichment
            enrichment_results = manager.batch_request(
                enrichment_requests,
                max_workers=5
            )
            
            # Combine original data with enrichment
            for item, enrichment in zip(batch, enrichment_results):
                if not isinstance(enrichment, Exception):
                    item.update(enrichment.json())
                processed_items.append(item)
        
        # Step 3: Save processed data
        response = manager.post(
            'https://api.storage.com/bulk-save',
            json={'items': processed_items}
        )
        
        return response.json()
```

### Monitoring and Health Checks

```python
def health_check_system():
    """Monitor multiple services with different requirements."""
    
    services = {
        'critical-api': {
            'url': 'https://critical-api.com/health',
            'timeout': 5,
            'max_retries': 1
        },
        'user-service': {
            'url': 'https://user-service.com/health',
            'timeout': 10,
            'max_retries': 2
        },
        'analytics-service': {
            'url': 'https://analytics.com/health',
            'timeout': 30,
            'max_retries': 1
        }
    }
    
    # Configure endpoint-specific settings
    endpoint_configs = {
        service_name: {
            'timeout': config['timeout'],
            'max_retries': config['max_retries'],
            'circuit_breaker_failure_threshold': 2
        }
        for service_name, config in services.items()
    }
    
    manager = ConnectionManager(endpoint_configs=endpoint_configs)
    
    with manager:
        health_status = {}
        
        # Prepare health check requests
        health_requests = [
            ('GET', config['url'], {})
            for service_name, config in services.items()
        ]
        
        # Execute all health checks concurrently
        results = manager.batch_request(
            health_requests,
            max_workers=len(services),
            return_exceptions=True
        )
        
        # Process results
        for (service_name, _), result in zip(services.items(), results):
            if isinstance(result, Exception):
                health_status[service_name] = {
                    'status': 'unhealthy',
                    'error': str(result)
                }
            else:
                health_status[service_name] = {
                    'status': 'healthy' if result.status_code == 200 else 'degraded',
                    'response_time': result.elapsed.total_seconds(),
                    'status_code': result.status_code
                }
        
        return health_status

# Run health checks
health = health_check_system()
for service, status in health.items():
    print(f"{service}: {status['status']}")
```

## Plugin Examples

### Custom Logging Plugin

```python
def request_logger(request_context):
    """Log all outgoing requests."""
    print(f"Making {request_context.method} request to {request_context.url}")

def response_logger(response_context):
    """Log all responses."""
    response = response_context.response
    duration = getattr(response, 'elapsed', None)
    duration_ms = duration.total_seconds() * 1000 if duration else 'unknown'
    
    print(f"Response: {response.status_code} in {duration_ms:.1f}ms")

# Register hooks
manager = ConnectionManager()
manager.register_pre_request_hook(request_logger)
manager.register_post_response_hook(response_logger)

with manager:
    response = manager.get('https://httpbin.org/get')
    # Logs: Making GET request to https://httpbin.org/get
    # Logs: Response: 200 in 245.3ms
```

### Metrics Collection Plugin

```python
import time
from collections import defaultdict

class MetricsCollector:
    def __init__(self):
        self.request_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
    
    def pre_request_hook(self, request_context):
        request_context.start_time = time.time()
    
    def post_response_hook(self, response_context):
        url = response_context.request_context.url
        duration = time.time() - response_context.request_context.start_time
        
        self.request_counts[url] += 1
        self.response_times[url].append(duration)
    
    def error_hook(self, error_context):
        url = error_context.request_context.url
        self.error_counts[url] += 1
    
    def get_metrics(self):
        metrics = {}
        for url in self.request_counts:
            avg_time = sum(self.response_times[url]) / len(self.response_times[url])
            metrics[url] = {
                'request_count': self.request_counts[url],
                'avg_response_time': avg_time,
                'error_count': self.error_counts[url]
            }
        return metrics

# Usage
metrics = MetricsCollector()
manager = ConnectionManager()

manager.register_pre_request_hook(metrics.pre_request_hook)
manager.register_post_response_hook(metrics.post_response_hook)
manager.register_error_hook(metrics.error_hook)

with manager:
    # Make some requests
    for i in range(5):
        manager.get(f'https://httpbin.org/get?id={i}')

# Get metrics
print(metrics.get_metrics())
```

## Next Steps

- [Advanced Features](advanced-features.md) - Explore powerful features
- [API Reference](api-reference.md) - Complete API documentation
- [Configuration](configuration.md) - Detailed configuration options
