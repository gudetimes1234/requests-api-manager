"""
Custom exceptions for the requests_connection_manager package.
"""


class ConnectionManagerError(Exception):
    """Base exception for all connection manager errors."""
    pass


class RateLimitExceeded(ConnectionManagerError):
    """Raised when rate limit is exceeded."""
    pass


class CircuitBreakerOpen(ConnectionManagerError):
    """Raised when circuit breaker is open."""
    pass


class MaxRetriesExceeded(ConnectionManagerError):
    """Raised when maximum retry attempts are exceeded."""
    pass
