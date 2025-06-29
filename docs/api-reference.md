
# API Reference

Complete API documentation for `requests-connection-manager`.

## ConnectionManager

Main class for synchronous HTTP requests with enhanced features.

### Constructor

```python
ConnectionManager(
    pool_connections: int = 10,
    pool_maxsize: int = 10,
    max_retries: int = 3,
    backoff_factor: float = 0.3,
    rate_limit_requests: int = 100,
    rate_limit_period: int = 60,
    circuit_breaker_failure_threshold: int = 5,
    circuit_breaker_recovery_timeout: float = 60,
    timeout: int = 30,
    endpoint_configs: Optional[Dict[str, Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
    api_key_header: str = "X-API-Key",
    bearer_token: Optional[str] = None,
    oauth2_token: Optional[str] = None,
    basic_auth: Optional[tuple] = None,
    verify: Union[bool, str] = True,
    cert: Optional[Union[str, tuple]] = None,
    connect_timeout: Optional[float] = None,
    read_timeout: Optional[float] = None,
    ssl_context: Optional[Any] = None
)
```

#### Parameters

- **pool_connections** (int): Number of connection pools to cache. Default: 10
- **pool_maxsize** (int): Maximum number of connections in each pool. Default: 10
- **max_retries** (int): Maximum number of retry attempts. Default: 3
- **backoff_factor** (float): Exponential backoff multiplier for retries. Default: 0.3
- **rate_limit_requests** (int): Number of requests allowed per period. Default: 100
- **rate_limit_period** (int): Time period for rate limiting in seconds. Default: 60
- **circuit_breaker_failure_threshold** (int): Number of failures before opening circuit breaker. Default: 5
- **circuit_breaker_recovery_timeout** (float): Recovery timeout for circuit breaker in seconds. Default: 60
- **timeout** (int): Default request timeout in seconds. Default: 30
- **endpoint_configs** (Dict): Endpoint-specific configuration overrides
- **api_key** (str): Global API key for authentication
- **api_key_header** (str): Header name for API key. Default: "X-API-Key"
- **bearer_token** (str): Global Bearer token for authentication
- **oauth2_token** (str): Global OAuth2 token for authentication
- **basic_auth** (tuple): Tuple of (username, password) for basic authentication
- **verify** (bool|str): SSL certificate verification. True, False, or path to CA bundle
- **cert** (str|tuple): Client certificate file path or (cert_file, key_file) tuple
- **connect_timeout** (float): Connection timeout in seconds
- **read_timeout** (float): Read timeout in seconds
- **ssl_context**: Custom SSL context for advanced SSL configuration

### HTTP Methods

#### request()

```python
request(method: str, url: str, **kwargs) -> requests.Response
```

Make HTTP request with all enhancements.

**Parameters:**
- **method** (str): HTTP method (GET, POST, etc.)
- **url** (str): Request URL
- **kwargs**: Additional request parameters

**Returns:** `requests.Response` object

**Raises:**
- `RateLimitExceeded`: When rate limit is exceeded
- `CircuitBreakerOpen`: When circuit breaker is open
- `MaxRetriesExceeded`: When maximum retries are exceeded

#### get()

```python
get(url: str, **kwargs) -> requests.Response
```

Make GET request.

#### post()

```python
post(url: str, **kwargs) -> requests.Response
```

Make POST request.

#### put()

```python
put(url: str, **kwargs) -> requests.Response
```

Make PUT request.

#### delete()

```python
delete(url: str, **kwargs) -> requests.Response
```

Make DELETE request.

#### patch()

```python
patch(url: str, **kwargs) -> requests.Response
```

Make PATCH request.

#### head()

```python
head(url: str, **kwargs) -> requests.Response
```

Make HEAD request.

#### options()

```python
options(url: str, **kwargs) -> requests.Response
```

Make OPTIONS request.

### Batch Operations

#### batch_request()

```python
batch_request(
    requests_data: List[Tuple[str, str, Dict[str, Any]]], 
    max_workers: int = 5,
    return_exceptions: bool = True
) -> List[Union[requests.Response, Exception]]
```

Perform multiple HTTP requests concurrently.

**Parameters:**
- **requests_data**: List of (method, url, kwargs) tuples
- **max_workers**: Maximum number of concurrent requests
- **return_exceptions**: If True, exceptions are returned instead of raised

**Returns:** List of Response objects or exceptions

### Configuration Management

#### add_endpoint_config()

```python
add_endpoint_config(pattern: str, config: Dict[str, Any]) -> None
```

Add configuration for specific endpoint pattern.

#### remove_endpoint_config()

```python
remove_endpoint_config(pattern: str) -> None
```

Remove configuration for endpoint pattern.

#### get_endpoint_configs()

```python
get_endpoint_configs() -> Dict[str, Dict[str, Any]]
```

Get all endpoint configurations.

### Authentication Methods

#### set_api_key()

```python
set_api_key(api_key: str, header_name: str = "X-API-Key") -> None
```

Set global API key authentication.

#### set_bearer_token()

```python
set_bearer_token(token: str) -> None
```

Set global Bearer token authentication.

#### set_oauth2_token()

```python
set_oauth2_token(token: str) -> None
```

Set global OAuth2 token authentication.

#### set_basic_auth()

```python
set_basic_auth(username: str, password: str) -> None
```

Set global basic authentication.

#### set_endpoint_auth()

```python
set_endpoint_auth(pattern: str, auth_type: str, **auth_kwargs) -> None
```

Set authentication for specific endpoint pattern.

**Parameters:**
- **pattern**: URL pattern to match
- **auth_type**: Type of authentication ('api_key', 'bearer', 'oauth2', 'basic')
- **auth_kwargs**: Authentication parameters

#### clear_auth()

```python
clear_auth(pattern: Optional[str] = None) -> None
```

Clear authentication for endpoint or globally.

### SSL Configuration

#### set_ssl_verification()

```python
set_ssl_verification(verify: Union[bool, str]) -> None
```

Set SSL certificate verification.

#### set_client_certificate()

```python
set_client_certificate(cert: Union[str, tuple]) -> None
```

Set client certificate for mutual TLS.

#### set_timeouts()

```python
set_timeouts(connect_timeout: Optional[float] = None, read_timeout: Optional[float] = None) -> None
```

Set fine-grained connection and read timeouts.

#### set_ssl_context()

```python
set_ssl_context(ssl_context: Any) -> None
```

Set custom SSL context.

### Plugin System

#### register_pre_request_hook()

```python
register_pre_request_hook(hook_func: Callable[[RequestContext], None]) -> None
```

Register pre-request hook.

#### register_post_response_hook()

```python
register_post_response_hook(hook_func: Callable[[ResponseContext], None]) -> None
```

Register post-response hook.

#### register_error_hook()

```python
register_error_hook(hook_func: Callable[[ErrorContext], None]) -> None
```

Register error handling hook.

#### unregister_hook()

```python
unregister_hook(hook_type: HookType, hook_func: Callable) -> None
```

Unregister specific hook.

#### list_hooks()

```python
list_hooks() -> Dict[str, List[str]]
```

List all registered hooks.

### Monitoring

#### get_stats()

```python
get_stats() -> Dict[str, Any]
```

Get current statistics about the connection manager.

**Returns:** Dictionary with current stats including:
- `circuit_breaker_state`: Current circuit breaker state
- `circuit_breaker_failure_count`: Number of failures
- `rate_limit_requests`: Current rate limit
- `timeout`: Current timeout setting
- `registered_hooks`: List of registered hooks
- `endpoint_configs`: Endpoint configurations

### Context Manager

#### \_\_enter\_\_() / \_\_exit\_\_()

```python
with ConnectionManager() as manager:
    # Use manager
    pass
# Automatically cleaned up
```

#### close()

```python
close() -> None
```

Manually close session and clean up resources.

## AsyncConnectionManager

Async version of ConnectionManager using httpx backend.

### Constructor

Same parameters as `ConnectionManager`.

### Async HTTP Methods

All HTTP methods are async versions:

```python
async def request(method: str, url: str, **kwargs) -> httpx.Response
async def get(url: str, **kwargs) -> httpx.Response
async def post(url: str, **kwargs) -> httpx.Response
# ... etc
```

### Async Batch Operations

```python
async def batch_request(
    requests_data: List[Tuple[str, str, Dict[str, Any]]], 
    max_workers: int = 5,
    return_exceptions: bool = True
) -> List[Union[httpx.Response, Exception]]
```

### Async Context Manager

```python
async with AsyncConnectionManager() as manager:
    response = await manager.get('https://api.example.com/data')
```

## Exception Classes

### ConnectionManagerError

Base exception for all connection manager errors.

```python
class ConnectionManagerError(Exception):
    """Base exception for connection manager errors."""
    pass
```

### RateLimitExceeded

Raised when rate limit is exceeded.

```python
class RateLimitExceeded(ConnectionManagerError):
    """Raised when rate limit is exceeded."""
    pass
```

### CircuitBreakerOpen

Raised when circuit breaker is open.

```python
class CircuitBreakerOpen(ConnectionManagerError):
    """Raised when circuit breaker is open."""
    pass
```

### MaxRetriesExceeded

Raised when maximum retries are exceeded.

```python
class MaxRetriesExceeded(ConnectionManagerError):
    """Raised when maximum retries are exceeded."""
    pass
```

## Plugin System Classes

### RequestContext

Context object passed to pre-request hooks.

```python
class RequestContext:
    def __init__(self, method: str, url: str, **kwargs):
        self.method = method
        self.url = url
        self.kwargs = kwargs
```

**Attributes:**
- `method`: HTTP method
- `url`: Request URL
- `kwargs`: Request parameters dictionary

### ResponseContext

Context object passed to post-response hooks.

```python
class ResponseContext:
    def __init__(self, response, request_context: RequestContext):
        self.response = response
        self.request_context = request_context
```

**Attributes:**
- `response`: Response object
- `request_context`: Original request context

### ErrorContext

Context object passed to error hooks.

```python
class ErrorContext:
    def __init__(self, exception: Exception, request_context: RequestContext):
        self.exception = exception
        self.request_context = request_context
        self.handled = False
        self.fallback_response = None
```

**Attributes:**
- `exception`: The exception that occurred
- `request_context`: Original request context
- `handled`: Set to True to mark error as handled
- `fallback_response`: Optional fallback response

### HookType

Enumeration of hook types.

```python
class HookType(Enum):
    PRE_REQUEST = "pre_request"
    POST_RESPONSE = "post_response"
    ERROR_HANDLER = "error_handler"
```

### PluginManager

Manages plugin hooks.

```python
class PluginManager:
    def register_hook(self, hook_type: HookType, hook_func: Callable) -> None
    def unregister_hook(self, hook_type: HookType, hook_func: Callable) -> None
    def execute_pre_request_hooks(self, context: RequestContext) -> None
    def execute_post_response_hooks(self, context: ResponseContext) -> None
    def execute_error_hooks(self, context: ErrorContext) -> None
    def list_hooks(self) -> Dict[str, List[str]]
```

## Utility Functions

### safe_log_request()

```python
safe_log_request(method: str, url: str, headers: Optional[Dict] = None, payload: Optional[Any] = None) -> None
```

Safely log request details without exposing sensitive information.

### safe_log_response()

```python
safe_log_response(response) -> None
```

Safely log response details.

### safe_log_error()

```python
safe_log_error(exception: Exception, method: str, url: str, level: int = logging.ERROR) -> None
```

Safely log error details.

## Type Hints

Common type definitions used throughout the library:

```python
from typing import Dict, List, Optional, Union, Any, Callable, Tuple

EndpointConfig = Dict[str, Any]
RequestData = Tuple[str, str, Dict[str, Any]]
BatchResults = List[Union[requests.Response, Exception]]
```

## Constants

### Default Values

```python
DEFAULT_POOL_CONNECTIONS = 10
DEFAULT_POOL_MAXSIZE = 10
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.3
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_PERIOD = 60
DEFAULT_CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
DEFAULT_CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
DEFAULT_TIMEOUT = 30
DEFAULT_API_KEY_HEADER = "X-API-Key"
```

## Example Usage

### Basic Usage

```python
from requests_connection_manager import ConnectionManager

with ConnectionManager() as manager:
    response = manager.get('https://api.example.com/data')
    print(response.json())
```

### Advanced Configuration

```python
manager = ConnectionManager(
    pool_connections=20,
    max_retries=5,
    rate_limit_requests=200,
    bearer_token="your-token",
    timeout=45
)

with manager:
    response = manager.post(
        'https://api.example.com/data',
        json={'key': 'value'}
    )
```

### Async Usage

```python
import asyncio
from requests_connection_manager import AsyncConnectionManager

async def main():
    async with AsyncConnectionManager() as manager:
        response = await manager.get('https://api.example.com/data')
        return response.json()

data = asyncio.run(main())
```

### Plugin Usage

```python
def log_requests(request_context):
    print(f"Making {request_context.method} request to {request_context.url}")

manager = ConnectionManager()
manager.register_pre_request_hook(log_requests)

with manager:
    response = manager.get('https://api.example.com/data')
```

## Next Steps

- [Getting Started](getting-started.md) - Basic introduction
- [Configuration](configuration.md) - Detailed configuration options
- [Usage Examples](usage-examples.md) - Practical examples
- [Advanced Features](advanced-features.md) - Advanced capabilities
