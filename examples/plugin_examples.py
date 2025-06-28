
"""
Examples demonstrating the plugin system for ConnectionManager.
"""

import json
import time
from requests_connection_manager import ConnectionManager, RequestContext, ResponseContext, ErrorContext


def authentication_hook(context: RequestContext):
    """Pre-request hook that adds authentication."""
    # Add API key to headers
    context.update_headers({"X-API-Key": "your-api-key-here"})
    
    # Add authentication to URL params for certain endpoints
    if "api.example.com" in context.url:
        if 'params' not in context.kwargs:
            context.kwargs['params'] = {}
        context.kwargs['params']['auth_token'] = "token123"


def request_logging_hook(context: RequestContext):
    """Pre-request hook that logs requests."""
    print(f"[REQUEST] {context.method} {context.url}")
    if context.kwargs.get('json'):
        print(f"[REQUEST] Payload: {json.dumps(context.kwargs['json'], indent=2)}")


def response_timing_hook(context: ResponseContext):
    """Post-response hook that logs response timing."""
    # Add timestamp to track when response was received
    if not hasattr(context.response, '_received_at'):
        context.response._received_at = time.time()
    
    print(f"[RESPONSE] {context.response.status_code} from {context.request_context.url}")
    print(f"[RESPONSE] Response time: {context.response.elapsed.total_seconds():.3f}s")


def response_validation_hook(context: ResponseContext):
    """Post-response hook that validates responses."""
    if context.response.status_code >= 400:
        print(f"[WARNING] HTTP {context.response.status_code} from {context.request_context.url}")
        
        # Mark as modified to indicate processing
        context.mark_modified()


def retry_error_hook(context: ErrorContext):
    """Error hook that provides intelligent retry logic."""
    error_msg = str(context.exception).lower()
    
    if "timeout" in error_msg or "connection" in error_msg:
        print(f"[ERROR] Connection issue detected: {context.exception}")
        print(f"[ERROR] URL: {context.request_context.url}")
        
        # Could implement custom retry logic here
        # For this example, we'll just log
        print("[ERROR] Consider implementing retry logic")


def fallback_error_hook(context: ErrorContext):
    """Error hook that provides fallback responses for certain errors."""
    if "404" in str(context.exception) and "api.example.com" in context.request_context.url:
        # Create a fallback response for 404s from our API
        from unittest.mock import Mock
        
        fallback_response = Mock()
        fallback_response.status_code = 200
        fallback_response.json.return_value = {
            "message": "Resource not found, using cached data",
            "data": {},
            "fallback": True
        }
        fallback_response.text = json.dumps(fallback_response.json())
        
        context.set_fallback_response(fallback_response)
        print("[FALLBACK] Using cached data for 404 response")


def comprehensive_error_hook(context: ErrorContext):
    """Comprehensive error handling hook."""
    error_info = {
        "error": str(context.exception),
        "error_type": type(context.exception).__name__,
        "url": context.request_context.url,
        "method": context.request_context.method,
        "timestamp": time.time()
    }
    
    # Log to file, send to monitoring service, etc.
    print(f"[ERROR LOG] {json.dumps(error_info, indent=2)}")
    
    # Could send alerts, write to database, etc.


def demo_plugin_system():
    """Demonstrate the plugin system with various hooks."""
    print("=== ConnectionManager Plugin System Demo ===\n")
    
    # Create connection manager
    manager = ConnectionManager()
    
    # Register pre-request hooks
    print("Registering pre-request hooks...")
    manager.register_pre_request_hook(authentication_hook)
    manager.register_pre_request_hook(request_logging_hook)
    
    # Register post-response hooks
    print("Registering post-response hooks...")
    manager.register_post_response_hook(response_timing_hook)
    manager.register_post_response_hook(response_validation_hook)
    
    # Register error hooks
    print("Registering error hooks...")
    manager.register_error_hook(retry_error_hook)
    manager.register_error_hook(fallback_error_hook)
    manager.register_error_hook(comprehensive_error_hook)
    
    print(f"\nRegistered hooks: {manager.list_hooks()}\n")
    
    try:
        # Make a test request
        print("Making test request...")
        response = manager.get("https://httpbin.org/get", params={"test": "value"})
        print(f"Response status: {response.status_code}\n")
        
        # Make a request that will trigger error handling
        print("Making request that will fail...")
        try:
            response = manager.get("https://httpbin.org/status/404")
        except Exception as e:
            print(f"Request failed as expected: {e}\n")
        
        # Test POST request with JSON
        print("Making POST request with JSON...")
        response = manager.post(
            "https://httpbin.org/post",
            json={"message": "Hello from plugin system!"}
        )
        print(f"POST response status: {response.status_code}\n")
        
    finally:
        manager.close()
        print("Demo completed!")


if __name__ == "__main__":
    demo_plugin_system()
