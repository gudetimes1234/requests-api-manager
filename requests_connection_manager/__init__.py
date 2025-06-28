"""
requests-connection-manager - Enhanced HTTP connection management for Python
"""

from .manager import ConnectionManager
from .async_manager import AsyncConnectionManager
from .exceptions import (
    ConnectionManagerError,
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)
from .plugins import PluginManager, HookType

__version__ = "1.0.0"
__all__ = [
    "ConnectionManager",
    "AsyncConnectionManager",
    "ConnectionManagerError", 
    "RateLimitExceeded",
    "CircuitBreakerOpen",
    "MaxRetriesExceeded",
    "PluginManager",
    "HookType"
]