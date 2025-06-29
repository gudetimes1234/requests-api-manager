
"""
ConnectionManager - Main class that provides connection pooling, retries,
rate limiting, and circuit breaker functionality for HTTP requests.
"""

import time
import logging
from typing import Optional, Dict, Any, Callable, List, Tuple, Union
from urllib3.util.retry import Retry
import requests
from requests.adapters import HTTPAdapter
from ratelimit import limits, sleep_and_retry
import pybreaker
from concurrent.futures import ThreadPoolExecutor, as_completed

from .exceptions import (
    ConnectionManagerError,
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)
from .plugins import PluginManager, RequestContext, ResponseContext, ErrorContext, HookType
from .utils import safe_log_request, safe_log_response, safe_log_error

# Set up logging
logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Main connection manager class that provides enhanced HTTP functionality.
    """
    
    def __init__(
        self,
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
        # Advanced connection options
        verify: Union[bool, str] = True,
        cert: Optional[Union[str, tuple]] = None,
        connect_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
        ssl_context: Optional[Any] = None
    ):
        """
        Initialize ConnectionManager with configuration options.
        
        Args:
            pool_connections: Number of connection pools to cache
            pool_maxsize: Maximum number of connections in each pool
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
            rate_limit_requests: Number of requests allowed per period
            rate_limit_period: Time period for rate limiting (seconds)
            circuit_breaker_failure_threshold: Failures before opening circuit
            circuit_breaker_recovery_timeout: Recovery timeout for circuit breaker
            timeout: Default request timeout
            endpoint_configs: Dict mapping URL patterns to custom configurations
            api_key: Global API key for authentication
            api_key_header: Header name for API key (default: X-API-Key)
            bearer_token: Global Bearer token for authentication
            oauth2_token: Global OAuth2 token for authentication
            basic_auth: Tuple of (username, password) for basic authentication
            verify: SSL certificate verification. True (default), False, or path to CA bundle
            cert: Client certificate. Path to cert file or tuple of (cert, key)
            connect_timeout: Connection timeout in seconds (separate from read timeout)
            read_timeout: Read timeout in seconds (separate from connect timeout)
            ssl_context: Custom SSL context for advanced SSL configuration
        """
        # Store default configuration values
        self.default_timeout = timeout
        self.default_rate_limit_requests = rate_limit_requests
        self.default_rate_limit_period = rate_limit_period
        self.default_max_retries = max_retries
        self.default_backoff_factor = backoff_factor
        self.default_circuit_breaker_failure_threshold = circuit_breaker_failure_threshold
        self.default_circuit_breaker_recovery_timeout = circuit_breaker_recovery_timeout
        
        # Store endpoint-specific configurations
        self.endpoint_configs = endpoint_configs or {}
        
        # Store authentication options
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.bearer_token = bearer_token
        self.oauth2_token = oauth2_token
        self.basic_auth = basic_auth
        
        # Store advanced connection options
        self.verify = verify
        self.cert = cert
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.ssl_context = ssl_context
        
        # Keep these for backward compatibility
        self.timeout = timeout
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_period = rate_limit_period
        
        # Set up connection pooling with requests.Session
        self.session = requests.Session()
        
        # Configure retry strategy using urllib3.Retry
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            # Add read retries for connection issues
            read=max_retries,
            connect=max_retries,
            # Reduce redirect retries to improve performance
            redirect=2
        )
        
        # Create HTTP adapter with connection pooling and optimized settings
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy,
            # Enable connection pooling optimizations
            pool_block=False  # Don't block when pool is full
        )
        
        # Apply SSL context if provided
        if ssl_context is not None:
            # Import here to avoid issues if SSL is not available
            from urllib3.util.ssl_ import create_urllib3_context
            from urllib3.poolmanager import PoolManager
            
            # Create custom HTTPAdapter with SSL context
            class SSLContextAdapter(HTTPAdapter):
                def init_poolmanager(self, *args, **kwargs):
                    kwargs['ssl_context'] = ssl_context
                    return super().init_poolmanager(*args, **kwargs)
            
            adapter = SSLContextAdapter(
                pool_connections=pool_connections,
                pool_maxsize=pool_maxsize,
                max_retries=retry_strategy,
                pool_block=False
            )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set up circuit breaker using pybreaker
        self.circuit_breaker = pybreaker.CircuitBreaker(
            fail_max=circuit_breaker_failure_threshold,
            reset_timeout=circuit_breaker_recovery_timeout,
            exclude=[RateLimitExceeded]  # Don't count rate limit as circuit breaker failure
        )
        
        # Pre-configure rate limited function to avoid dynamic creation
        @sleep_and_retry
        @limits(calls=rate_limit_requests, period=rate_limit_period)
        def _rate_limited_wrapper(func: Callable, *args, **kwargs):
            return func(*args, **kwargs)
        
        self._rate_limited_wrapper = _rate_limited_wrapper
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager()
        
        logger.info("ConnectionManager initialized with pooling, retries, rate limiting, circuit breaker, and plugin system")
    
    def _get_endpoint_config(self, url: str) -> Dict[str, Any]:
        """
        Get configuration for a specific endpoint URL.
        
        Args:
            url: The request URL
            
        Returns:
            Dictionary with configuration values for this endpoint
        """
        # Default configuration
        config = {
            'timeout': self.default_timeout,
            'rate_limit_requests': self.default_rate_limit_requests,
            'rate_limit_period': self.default_rate_limit_period,
            'max_retries': self.default_max_retries,
            'backoff_factor': self.default_backoff_factor,
            'circuit_breaker_failure_threshold': self.default_circuit_breaker_failure_threshold,
            'circuit_breaker_recovery_timeout': self.default_circuit_breaker_recovery_timeout
        }
        
        # Check if URL matches any endpoint patterns
        for pattern, endpoint_config in self.endpoint_configs.items():
            if pattern in url:
                # Update config with endpoint-specific values
                config.update(endpoint_config)
                break
        
        return config
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Internal method to make HTTP request with optimized parameter handling.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object
        """
        # Handle timeout efficiently without modifying kwargs
        request_timeout = kwargs.get('timeout', self.timeout)
        if 'timeout' not in kwargs:
            # Apply fine-grained timeouts if specified
            if self.connect_timeout is not None and self.read_timeout is not None:
                kwargs['timeout'] = (self.connect_timeout, self.read_timeout)
            else:
                kwargs['timeout'] = request_timeout
        
        # Apply SSL verification settings
        if 'verify' not in kwargs:
            kwargs['verify'] = self.verify
        
        # Apply client certificate settings
        if 'cert' not in kwargs and self.cert is not None:
            kwargs['cert'] = self.cert
        
        # Safe logging of request details
        safe_log_request(
            method=method,
            url=url,
            headers=kwargs.get('headers'),
            payload=kwargs.get('json') or kwargs.get('data')
        )
        
        try:
            response = self.session.request(method=method, url=url, **kwargs)
            
            # Safe logging of response details
            safe_log_response(response)
            
            return response
        except Exception as e:
            safe_log_error(e, method, url)
            raise
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with all enhancements (pooling, retries, rate limiting, circuit breaker, plugins).
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object
            
        Raises:
            RateLimitExceeded: When rate limit is exceeded
            CircuitBreakerOpen: When circuit breaker is open
            ConnectionManagerError: For other connection manager errors
        """
        # Get endpoint-specific configuration
        endpoint_config = self._get_endpoint_config(url)
        
        # Create request context and execute pre-request hooks
        request_context = RequestContext(method, url, **kwargs)
        self.plugin_manager.execute_pre_request_hooks(request_context)
        
        # Update method, url, and kwargs from context (may have been modified by hooks)
        method = request_context.method
        url = request_context.url
        kwargs = request_context.kwargs
        
        # Apply endpoint-specific timeout if not already specified
        if 'timeout' not in kwargs:
            kwargs['timeout'] = endpoint_config['timeout']
        
        # Apply authentication
        self._apply_authentication(kwargs, url)
        
        try:
            # Create endpoint-specific rate limiter if needed
            rate_limiter = self._get_rate_limiter_for_endpoint(endpoint_config)
            
            # Create endpoint-specific circuit breaker if needed
            circuit_breaker = self._get_circuit_breaker_for_endpoint(url, endpoint_config)
            
            # Use endpoint-specific rate limiter with circuit breaker
            response = rate_limiter(
                circuit_breaker(self._make_request),
                method,
                url,
                **kwargs
            )
            
            # Execute post-response hooks
            response_context = ResponseContext(response, request_context)
            self.plugin_manager.execute_post_response_hooks(response_context)
            
            logger.debug(f"Successful {method} request completed")
            return response_context.response
            
        except pybreaker.CircuitBreakerError:
            safe_log_error(CircuitBreakerOpen("Circuit breaker is open"), method, url)
            error = CircuitBreakerOpen("Circuit breaker is open")
            return self._handle_error(error, request_context)
        except Exception as e:
            safe_log_error(e, method, url)
            return self._handle_error(e, request_context)
    
    def _get_rate_limiter_for_endpoint(self, endpoint_config: Dict[str, Any]) -> Callable:
        """
        Get or create a rate limiter for the endpoint configuration.
        
        Args:
            endpoint_config: Configuration dictionary for the endpoint
            
        Returns:
            Rate limiter function
        """
        # Use default rate limiter if endpoint config matches defaults
        if (endpoint_config['rate_limit_requests'] == self.default_rate_limit_requests and 
            endpoint_config['rate_limit_period'] == self.default_rate_limit_period):
            return self._rate_limited_wrapper
        
        # Create custom rate limiter for this endpoint
        @sleep_and_retry
        @limits(calls=endpoint_config['rate_limit_requests'], period=endpoint_config['rate_limit_period'])
        def _endpoint_rate_limited_wrapper(func: Callable, *args, **kwargs):
            return func(*args, **kwargs)
        
        return _endpoint_rate_limited_wrapper
    
    def _get_circuit_breaker_for_endpoint(self, url: str, endpoint_config: Dict[str, Any]) -> pybreaker.CircuitBreaker:
        """
        Get or create a circuit breaker for the endpoint configuration.
        
        Args:
            url: The request URL
            endpoint_config: Configuration dictionary for the endpoint
            
        Returns:
            Circuit breaker instance
        """
        # Use default circuit breaker if endpoint config matches defaults
        if (endpoint_config['circuit_breaker_failure_threshold'] == self.default_circuit_breaker_failure_threshold and 
            endpoint_config['circuit_breaker_recovery_timeout'] == self.default_circuit_breaker_recovery_timeout):
            return self.circuit_breaker
        
        # Create or get cached circuit breaker for this endpoint
        if not hasattr(self, '_endpoint_circuit_breakers'):
            self._endpoint_circuit_breakers = {}
        
        # Use URL domain as key for circuit breaker caching
        from urllib.parse import urlparse
        domain = urlparse(url).netloc or url
        
        circuit_breaker_key = f"{domain}_{endpoint_config['circuit_breaker_failure_threshold']}_{endpoint_config['circuit_breaker_recovery_timeout']}"
        
        if circuit_breaker_key not in self._endpoint_circuit_breakers:
            self._endpoint_circuit_breakers[circuit_breaker_key] = pybreaker.CircuitBreaker(
                fail_max=endpoint_config['circuit_breaker_failure_threshold'],
                reset_timeout=endpoint_config['circuit_breaker_recovery_timeout'],
                exclude=[RateLimitExceeded]
            )
        
        return self._endpoint_circuit_breakers[circuit_breaker_key]
    
    def _apply_authentication(self, kwargs: Dict[str, Any], url: str):
        """
        Apply authentication headers to the request.
        
        Args:
            kwargs: Request parameters dictionary
            url: Request URL for endpoint-specific auth
        """
        # Initialize headers if not present
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        # Check for endpoint-specific authentication first
        endpoint_config = self._get_endpoint_config(url)
        
        # Apply API key authentication
        api_key = endpoint_config.get('api_key', self.api_key)
        api_key_header = endpoint_config.get('api_key_header', self.api_key_header)
        if api_key:
            kwargs['headers'][api_key_header] = api_key
        
        # Apply Bearer token authentication
        bearer_token = endpoint_config.get('bearer_token', self.bearer_token)
        if bearer_token:
            kwargs['headers']['Authorization'] = f'Bearer {bearer_token}'
        
        # Apply OAuth2 token authentication
        oauth2_token = endpoint_config.get('oauth2_token', self.oauth2_token)
        if oauth2_token:
            kwargs['headers']['Authorization'] = f'Bearer {oauth2_token}'
        
        # Apply basic authentication
        basic_auth = endpoint_config.get('basic_auth', self.basic_auth)
        if basic_auth and 'auth' not in kwargs:
            kwargs['auth'] = basic_auth

    def _handle_error(self, exception: Exception, request_context: RequestContext):
        """Handle errors through the plugin system."""
        error_context = ErrorContext(exception, request_context)
        self.plugin_manager.execute_error_hooks(error_context)
        
        if error_context.handled and error_context.fallback_response:
            logger.info(f"Error handled by plugin, returning fallback response")
            return error_context.fallback_response
        
        # Re-raise the original exception if not handled
        raise exception
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request."""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request."""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """Make PUT request."""
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """Make DELETE request."""
        return self.request('DELETE', url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> requests.Response:
        """Make PATCH request."""
        return self.request('PATCH', url, **kwargs)
    
    def head(self, url: str, **kwargs) -> requests.Response:
        """Make HEAD request."""
        return self.request('HEAD', url, **kwargs)
    
    def options(self, url: str, **kwargs) -> requests.Response:
        """Make OPTIONS request."""
        return self.request('OPTIONS', url, **kwargs)
    
    def close(self):
        """Close the session and clean up resources."""
        if self.session:
            self.session.close()
            logger.info("ConnectionManager session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def register_pre_request_hook(self, hook_func: Callable[[RequestContext], None]):
        """
        Register a pre-request hook.
        
        Args:
            hook_func: Function that takes RequestContext and modifies it
        """
        self.plugin_manager.register_hook(HookType.PRE_REQUEST, hook_func)
    
    def register_post_response_hook(self, hook_func: Callable[[ResponseContext], None]):
        """
        Register a post-response hook.
        
        Args:
            hook_func: Function that takes ResponseContext and can inspect/modify response
        """
        self.plugin_manager.register_hook(HookType.POST_RESPONSE, hook_func)
    
    def register_error_hook(self, hook_func: Callable[[ErrorContext], None]):
        """
        Register an error handling hook.
        
        Args:
            hook_func: Function that takes ErrorContext and can handle errors
        """
        self.plugin_manager.register_hook(HookType.ERROR_HANDLER, hook_func)
    
    def unregister_hook(self, hook_type: HookType, hook_func: Callable):
        """
        Unregister a specific hook.
        
        Args:
            hook_type: Type of hook to unregister
            hook_func: Function to remove
        """
        self.plugin_manager.unregister_hook(hook_type, hook_func)
    
    def list_hooks(self) -> Dict[str, List[str]]:
        """List all registered hooks."""
        return self.plugin_manager.list_hooks()
    
    def add_endpoint_config(self, pattern: str, config: Dict[str, Any]):
        """
        Add or update configuration for a specific endpoint pattern.
        
        Args:
            pattern: URL pattern to match (substring match)
            config: Configuration dictionary with custom settings
        """
        self.endpoint_configs[pattern] = config
        logger.info(f"Added endpoint configuration for pattern: {pattern}")
    
    def remove_endpoint_config(self, pattern: str):
        """
        Remove configuration for a specific endpoint pattern.
        
        Args:
            pattern: URL pattern to remove
        """
        if pattern in self.endpoint_configs:
            del self.endpoint_configs[pattern]
            logger.info(f"Removed endpoint configuration for pattern: {pattern}")
    
    def get_endpoint_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all endpoint configurations.
        
        Returns:
            Dictionary of endpoint patterns and their configurations
        """
        return self.endpoint_configs.copy()
    
    def set_api_key(self, api_key: str, header_name: str = "X-API-Key"):
        """
        Set global API key authentication.
        
        Args:
            api_key: The API key value
            header_name: The header name for the API key (default: X-API-Key)
        """
        self.api_key = api_key
        self.api_key_header = header_name
        logger.info(f"Set global API key authentication with header: {header_name}")
    
    def set_bearer_token(self, token: str):
        """
        Set global Bearer token authentication.
        
        Args:
            token: The Bearer token value
        """
        self.bearer_token = token
        logger.info("Set global Bearer token authentication")
    
    def set_oauth2_token(self, token: str):
        """
        Set global OAuth2 token authentication.
        
        Args:
            token: The OAuth2 token value
        """
        self.oauth2_token = token
        logger.info("Set global OAuth2 token authentication")
    
    def set_basic_auth(self, username: str, password: str):
        """
        Set global basic authentication.
        
        Args:
            username: Username for basic auth
            password: Password for basic auth
        """
        self.basic_auth = (username, password)
        logger.info("Set global basic authentication")
    
    def set_endpoint_auth(self, pattern: str, auth_type: str, **auth_kwargs):
        """
        Set authentication for a specific endpoint pattern.
        
        Args:
            pattern: URL pattern to match
            auth_type: Type of authentication ('api_key', 'bearer', 'oauth2', 'basic')
            **auth_kwargs: Authentication parameters based on auth_type
        """
        if pattern not in self.endpoint_configs:
            self.endpoint_configs[pattern] = {}
        
        if auth_type == 'api_key':
            self.endpoint_configs[pattern]['api_key'] = auth_kwargs['api_key']
            self.endpoint_configs[pattern]['api_key_header'] = auth_kwargs.get('header_name', 'X-API-Key')
        elif auth_type == 'bearer':
            self.endpoint_configs[pattern]['bearer_token'] = auth_kwargs['token']
        elif auth_type == 'oauth2':
            self.endpoint_configs[pattern]['oauth2_token'] = auth_kwargs['token']
        elif auth_type == 'basic':
            self.endpoint_configs[pattern]['basic_auth'] = (auth_kwargs['username'], auth_kwargs['password'])
        else:
            raise ValueError(f"Unsupported auth_type: {auth_type}")
        
        logger.info(f"Set {auth_type} authentication for endpoint pattern: {pattern}")
    
    def clear_auth(self, pattern: Optional[str] = None):
        """
        Clear authentication for a specific endpoint or globally.
        
        Args:
            pattern: URL pattern to clear auth for, or None for global auth
        """
        if pattern:
            if pattern in self.endpoint_configs:
                auth_keys = ['api_key', 'api_key_header', 'bearer_token', 'oauth2_token', 'basic_auth']
                for key in auth_keys:
                    self.endpoint_configs[pattern].pop(key, None)
                logger.info(f"Cleared authentication for endpoint pattern: {pattern}")
        else:
            self.api_key = None
            self.api_key_header = "X-API-Key"
            self.bearer_token = None
            self.oauth2_token = None
            self.basic_auth = None
            logger.info("Cleared global authentication")

    def batch_request(
        self, 
        requests_data: List[Tuple[str, str, Dict[str, Any]]], 
        max_workers: int = 5,
        return_exceptions: bool = True
    ) -> List[Union[requests.Response, Exception]]:
        """
        Perform multiple HTTP requests concurrently with controlled parallelism.
        
        Args:
            requests_data: List of tuples (method, url, kwargs) for each request
            max_workers: Maximum number of concurrent requests (default: 5)
            return_exceptions: If True, exceptions are returned in results instead of raised
            
        Returns:
            List of Response objects or exceptions in the same order as input requests
            
        Example:
            requests_data = [
                ('GET', 'https://api.example.com/users', {}),
                ('POST', 'https://api.example.com/data', {'json': {'key': 'value'}}),
                ('GET', 'https://api.example.com/status', {'timeout': 10})
            ]
            results = manager.batch_request(requests_data, max_workers=3)
        """
        if not requests_data:
            return []
        
        # Validate input data
        for i, request_tuple in enumerate(requests_data):
            if not isinstance(request_tuple, (tuple, list)) or len(request_tuple) != 3:
                raise ValueError(f"Request {i} must be a tuple/list of (method, url, kwargs)")
            method, url, kwargs = request_tuple
            if not isinstance(method, str) or not isinstance(url, str):
                raise ValueError(f"Request {i}: method and url must be strings")
            if not isinstance(kwargs, dict):
                raise ValueError(f"Request {i}: kwargs must be a dictionary")
        
        results = [None] * len(requests_data)
        
        def _execute_single_request(index: int, method: str, url: str, kwargs: Dict[str, Any]):
            """Execute a single request and return (index, result)."""
            try:
                response = self.request(method, url, **kwargs)
                return index, response
            except Exception as e:
                safe_log_error(e, method, url, level=logging.WARNING)
                logger.warning(f"Batch request {index} failed")
                return index, e
        
        # Execute requests concurrently using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            future_to_index = {
                executor.submit(_execute_single_request, i, method, url, kwargs): i 
                for i, (method, url, kwargs) in enumerate(requests_data)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    # This should not happen as exceptions are caught in _execute_single_request
                    index = future_to_index[future]
                    logger.error(f"Unexpected error in batch request {index}: {str(e)}")
                    results[index] = e
        
        # Handle exceptions based on return_exceptions flag
        if not return_exceptions:
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    raise result
        
        logger.info(f"Completed batch request with {len(requests_data)} requests using {max_workers} workers")
        return results

    def set_ssl_verification(self, verify: Union[bool, str]):
        """
        Set SSL certificate verification.
        
        Args:
            verify: True to use default CA bundle, False to disable, or path to CA bundle
        """
        self.verify = verify
        logger.info(f"SSL verification set to: {verify}")
    
    def set_client_certificate(self, cert: Union[str, tuple]):
        """
        Set client certificate for mutual TLS.
        
        Args:
            cert: Path to certificate file or tuple of (cert_file, key_file)
        """
        self.cert = cert
        logger.info("Client certificate configured")
    
    def set_timeouts(self, connect_timeout: Optional[float] = None, read_timeout: Optional[float] = None):
        """
        Set fine-grained connection and read timeouts.
        
        Args:
            connect_timeout: Connection timeout in seconds
            read_timeout: Read timeout in seconds
        """
        if connect_timeout is not None:
            self.connect_timeout = connect_timeout
        if read_timeout is not None:
            self.read_timeout = read_timeout
        logger.info(f"Timeouts set - Connect: {self.connect_timeout}s, Read: {self.read_timeout}s")
    
    def set_ssl_context(self, ssl_context: Any):
        """
        Set custom SSL context for advanced SSL configuration.
        
        Args:
            ssl_context: SSL context object
        """
        self.ssl_context = ssl_context
        logger.info("Custom SSL context configured")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics about the connection manager.
        
        Returns:
            Dictionary with current stats
        """
        try:
            circuit_breaker_state = getattr(self.circuit_breaker, 'current_state', 'unknown')
            circuit_breaker_failure_count = getattr(self.circuit_breaker, 'fail_counter', 0)
        except:
            circuit_breaker_state = 'unknown'
            circuit_breaker_failure_count = 0
            
        stats = {
            'circuit_breaker_state': circuit_breaker_state,
            'circuit_breaker_failure_count': circuit_breaker_failure_count,
            'rate_limit_requests': self.rate_limit_requests,
            'rate_limit_period': self.rate_limit_period,
            'timeout': self.timeout,
            'requests_made': 0,  # Simple counter for compatibility
            'ssl_verification': getattr(self, 'verify', True),
            'client_certificate_configured': getattr(self, 'cert', None) is not None,
            'connect_timeout': getattr(self, 'connect_timeout', None),
            'read_timeout': getattr(self, 'read_timeout', None),
            'ssl_context_configured': getattr(self, 'ssl_context', None) is not None
        }
        return stats
