"""
requests_connection_manager - A Python package that extends requests with connection pooling,
retries, rate limiting, and circuit breaker functionality.
"""

from .manager import ConnectionManager
from .exceptions import (
    ConnectionManagerError,
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)
from .plugins import (
    PluginManager,
    RequestContext,
    ResponseContext,
    ErrorContext,
    HookType
)

__version__ = "1.0.0"
__author__ = "requests-connection-manager"
__email__ = "contact@requests-connection-manager.com"

__all__ = [
    "ConnectionManager",
    "ConnectionManagerError",
    "RateLimitExceeded",
    "CircuitBreakerOpen",
    "MaxRetriesExceeded",
    "PluginManager",
    "RequestContext",
    "ResponseContext", 
    "ErrorContext",
    "HookType"
]
