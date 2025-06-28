
"""
Plugin system for ConnectionManager.
Provides hooks for pre-request, post-response, and error handling.
"""

from typing import Dict, Any, List, Callable, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HookType(Enum):
    """Types of hooks available in the plugin system."""
    PRE_REQUEST = "pre_request"
    POST_RESPONSE = "post_response" 
    ERROR_HANDLER = "error_handler"


class RequestContext:
    """Context object passed to pre-request hooks."""
    
    def __init__(self, method: str, url: str, **kwargs):
        self.method = method
        self.url = url
        self.kwargs = kwargs
    
    def update_url(self, new_url: str):
        """Update the request URL."""
        self.url = new_url
    
    def update_headers(self, headers: Dict[str, str]):
        """Update or add headers."""
        if 'headers' not in self.kwargs:
            self.kwargs['headers'] = {}
        self.kwargs['headers'].update(headers)
    
    def update_payload(self, **payload_kwargs):
        """Update request payload (json, data, etc.)."""
        self.kwargs.update(payload_kwargs)


class ResponseContext:
    """Context object passed to post-response hooks."""
    
    def __init__(self, response, request_context: RequestContext):
        self.response = response
        self.request_context = request_context
        self.modified = False
    
    def mark_modified(self):
        """Mark response as modified."""
        self.modified = True


class ErrorContext:
    """Context object passed to error handler hooks."""
    
    def __init__(self, exception: Exception, request_context: RequestContext):
        self.exception = exception
        self.request_context = request_context
        self.handled = False
        self.fallback_response = None
    
    def set_fallback_response(self, response):
        """Set a fallback response instead of raising the exception."""
        self.fallback_response = response
        self.handled = True


class PluginManager:
    """Manages plugins and hooks for ConnectionManager."""
    
    def __init__(self):
        self.hooks: Dict[HookType, List[Callable]] = {
            HookType.PRE_REQUEST: [],
            HookType.POST_RESPONSE: [],
            HookType.ERROR_HANDLER: []
        }
    
    def register_hook(self, hook_type: HookType, hook_func: Callable):
        """
        Register a hook function.
        
        Args:
            hook_type: Type of hook to register
            hook_func: Function to call for this hook
        """
        if hook_type not in self.hooks:
            raise ValueError(f"Invalid hook type: {hook_type}")
        
        self.hooks[hook_type].append(hook_func)
        logger.info(f"Registered {hook_type.value} hook: {hook_func.__name__}")
    
    def unregister_hook(self, hook_type: HookType, hook_func: Callable):
        """
        Unregister a specific hook function.
        
        Args:
            hook_type: Type of hook to unregister
            hook_func: Function to remove
        """
        if hook_type in self.hooks and hook_func in self.hooks[hook_type]:
            self.hooks[hook_type].remove(hook_func)
            logger.info(f"Unregistered {hook_type.value} hook: {hook_func.__name__}")
    
    def clear_hooks(self, hook_type: Optional[HookType] = None):
        """
        Clear hooks for a specific type or all hooks.
        
        Args:
            hook_type: Specific hook type to clear, or None for all
        """
        if hook_type:
            self.hooks[hook_type].clear()
            logger.info(f"Cleared all {hook_type.value} hooks")
        else:
            for hooks in self.hooks.values():
                hooks.clear()
            logger.info("Cleared all hooks")
    
    def execute_pre_request_hooks(self, request_context: RequestContext):
        """Execute all pre-request hooks."""
        for hook in self.hooks[HookType.PRE_REQUEST]:
            try:
                hook(request_context)
            except Exception as e:
                logger.error(f"Error in pre-request hook {hook.__name__}: {e}")
    
    def execute_post_response_hooks(self, response_context: ResponseContext):
        """Execute all post-response hooks."""
        for hook in self.hooks[HookType.POST_RESPONSE]:
            try:
                hook(response_context)
            except Exception as e:
                logger.error(f"Error in post-response hook {hook.__name__}: {e}")
    
    def execute_error_hooks(self, error_context: ErrorContext):
        """Execute all error handler hooks."""
        for hook in self.hooks[HookType.ERROR_HANDLER]:
            try:
                hook(error_context)
                if error_context.handled:
                    break  # Stop if error was handled
            except Exception as e:
                logger.error(f"Error in error handler hook {hook.__name__}: {e}")
    
    def list_hooks(self) -> Dict[str, List[str]]:
        """Return a summary of registered hooks."""
        return {
            hook_type.value: [func.__name__ for func in funcs]
            for hook_type, funcs in self.hooks.items()
        }
