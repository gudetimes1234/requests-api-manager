"""
requests-connection-manager - Enhanced HTTP connection management with pooling, retries, rate limiting, and circuit breaker functionality.
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
from .utils import (
    redact_sensitive_data,
    safe_log_request,
    safe_log_response,
    safe_log_error,
    is_sensitive_field
)

from .version import __version__
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
    "HookType",
    "redact_sensitive_data",
    "safe_log_request",
    "safe_log_response",
    "safe_log_error",
    "is_sensitive_field"
]