
"""
ConnectionManager - Main class that provides connection pooling, retries,
rate limiting, and circuit breaker functionality for HTTP requests.
"""

import time
import logging
from typing import Optional, Dict, Any, Callable
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
        timeout: int = 30
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
        """
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
        # Create request context and execute pre-request hooks
        request_context = RequestContext(method, url, **kwargs)
        self.plugin_manager.execute_pre_request_hooks(request_context)
        
        # Update method, url, and kwargs from context (may have been modified by hooks)
        method = request_context.method
        url = request_context.url
        kwargs = request_context.kwargs
        
        try:
            # Use pre-configured rate limiter with circuit breaker
            response = self._rate_limited_wrapper(
                self.circuit_breaker(self._make_request),
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
            'registered_hooks': self.list_hooks()
        }
        return stats
