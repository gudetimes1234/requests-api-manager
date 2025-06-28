
"""
ConnectionManager - Main class that provides connection pooling, retries,
rate limiting, and circuit breaker functionality for HTTP requests.
"""

import time
import logging
from typing import Optional, Dict, Any, Callable, List
from urllib3.util.retry import Retry
import requests
from requests.adapters import HTTPAdapter
from ratelimit import limits, sleep_and_retry
import pybreaker

from .exceptions import (
    ConnectionManagerError,
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)
from .plugins import PluginManager, RequestContext, ResponseContext, ErrorContext, HookType

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
        endpoint_configs: Optional[Dict[str, Dict[str, Any]]] = None
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
            kwargs['timeout'] = request_timeout
        
        try:
            response = self.session.request(method=method, url=url, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Request failed: {method} {url} - {str(e)}")
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
            
            logger.debug(f"Successful {method} request to {url}")
            return response_context.response
            
        except pybreaker.CircuitBreakerError:
            logger.error(f"Circuit breaker is open for {method} {url}")
            error = CircuitBreakerOpen("Circuit breaker is open")
            return self._handle_error(error, request_context)
        except Exception as e:
            logger.error(f"Request failed: {method} {url} - {str(e)}")
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

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics about the connection manager.
        
        Returns:
            Dictionary with current stats
        """
        stats = {
            'circuit_breaker_state': self.circuit_breaker.current_state,
            'circuit_breaker_failure_count': self.circuit_breaker.fail_counter,
            'rate_limit_requests': self.rate_limit_requests,
            'rate_limit_period': self.rate_limit_period,
            'timeout': self.timeout,
            'registered_hooks': self.list_hooks(),
            'endpoint_configs': self.get_endpoint_configs()
        }
        return stats
