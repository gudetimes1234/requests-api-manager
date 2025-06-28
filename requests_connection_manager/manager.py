"""
ConnectionManager - Main class that provides connection pooling, retries,
rate limiting, and circuit breaker functionality for HTTP requests.
"""

import time
import logging
from typing import Optional, Dict, Any
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
        )
        
        # Create HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set up circuit breaker using pybreaker
        self.circuit_breaker = pybreaker.CircuitBreaker(
            fail_max=circuit_breaker_failure_threshold,
            reset_timeout=circuit_breaker_recovery_timeout,
            exclude=[RateLimitExceeded]  # Don't count rate limit as circuit breaker failure
        )
        
        logger.info("ConnectionManager initialized with pooling, retries, rate limiting, and circuit breaker")
    
    @sleep_and_retry
    @limits(calls=100, period=60)  # Default rate limit - will be overridden by instance method
    def _rate_limited_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with rate limiting using ratelimit decorator.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object
        """
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=kwargs.pop('timeout', self.timeout),
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"Request failed: {method} {url} - {str(e)}")
            raise
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with all enhancements (pooling, retries, rate limiting, circuit breaker).
        
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
        try:
            # Apply dynamic rate limiting by creating a new decorator with instance values
            rate_limited_func = sleep_and_retry(
                limits(calls=self.rate_limit_requests, period=self.rate_limit_period)(
                    self._rate_limited_request
                )
            )
            
            # Make request through circuit breaker and rate limiter
            response = self.circuit_breaker(rate_limited_func)(method, url, **kwargs)
            
            logger.debug(f"Successful {method} request to {url}")
            return response
            
        except pybreaker.CircuitBreakerError:
            logger.error(f"Circuit breaker is open for {method} {url}")
            raise CircuitBreakerOpen("Circuit breaker is open")
        except Exception as e:
            logger.error(f"Request failed: {method} {url} - {str(e)}")
            raise
    
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
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics about the connection manager.
        
        Returns:
            Dictionary with current stats
        """
        return {
            'circuit_breaker_state': self.circuit_breaker.current_state,
            'circuit_breaker_failure_count': self.circuit_breaker.fail_counter,
            'rate_limit_requests': self.rate_limit_requests,
            'rate_limit_period': self.rate_limit_period,
            'timeout': self.timeout
        }
