"""
ConnectionManager - Main class that provides connection pooling, retries,
rate limiting, and circuit breaker functionality for HTTP requests.
"""

import time
import threading
import logging
from typing import Optional, Dict, Any, Union, Callable, Tuple, Type
from urllib3 import PoolManager
from urllib3.util.retry import Retry
import requests
from requests.adapters import HTTPAdapter

from .exceptions import (
    ConnectionManagerError,
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)

# Set up logging
logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Rate at which tokens are added (tokens per second)
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        with self.lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class CircuitBreaker:
    """Circuit breaker implementation to handle service failures."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60, expected_exception: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying to close circuit
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpen: When circuit is open
        """
        with self.lock:
            if self.state == 'OPEN':
                if self.last_failure_time and time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                    logger.info("Circuit breaker moving to HALF_OPEN state")
                else:
                    raise CircuitBreakerOpen("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if isinstance(e, self.expected_exception):
                self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        with self.lock:
            self.failure_count = 0
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                logger.info("Circuit breaker CLOSED")
    
    def _on_failure(self):
        """Handle failed call."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
                logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")


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
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        
        # Set up connection pooling
        self.session = requests.Session()
        
        # Configure retry strategy
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
        
        # Set up rate limiting
        self.rate_limiter = TokenBucket(
            capacity=rate_limit_requests,
            refill_rate=rate_limit_requests / rate_limit_period
        )
        
        # Set up circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_failure_threshold,
            recovery_timeout=circuit_breaker_recovery_timeout,
            expected_exception=(requests.RequestException, ConnectionManagerError)
        )
        
        logger.info("ConnectionManager initialized with pooling, retries, rate limiting, and circuit breaker")
    
    def _check_rate_limit(self):
        """Check if request is within rate limit."""
        if not self.rate_limiter.consume():
            raise RateLimitExceeded("Rate limit exceeded")
    
    def _make_request_with_retries(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object
            
        Raises:
            MaxRetriesExceeded: When all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=kwargs.pop('timeout', self.timeout),
                    **kwargs
                )
                
                # Check if response indicates a server error that should be retried
                if response.status_code >= 500:
                    raise requests.HTTPError(f"Server error: {response.status_code}")
                
                return response
                
            except (requests.RequestException, requests.HTTPError) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate backoff delay
                    delay = self.backoff_factor * (2 ** attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                                 f"retrying in {delay:.2f} seconds: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for {method} {url}")
        
        raise MaxRetriesExceeded(f"Maximum retries exceeded. Last error: {str(last_exception)}")
    
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
            MaxRetriesExceeded: When all retries fail
            ConnectionManagerError: For other connection manager errors
        """
        try:
            # Check rate limit
            self._check_rate_limit()
            
            # Make request through circuit breaker
            response = self.circuit_breaker.call(
                self._make_request_with_retries,
                method,
                url,
                **kwargs
            )
            
            logger.debug(f"Successful {method} request to {url}")
            return response
            
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
            'circuit_breaker_state': self.circuit_breaker.state,
            'circuit_breaker_failure_count': self.circuit_breaker.failure_count,
            'rate_limiter_tokens': self.rate_limiter.tokens,
            'rate_limiter_capacity': self.rate_limiter.capacity,
            'max_retries': self.max_retries,
            'backoff_factor': self.backoff_factor,
            'timeout': self.timeout
        }
