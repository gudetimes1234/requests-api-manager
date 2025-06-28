
"""
Examples demonstrating secure logging functionality that redacts sensitive information.
"""

import logging
from requests_connection_manager import (
    ConnectionManager, 
    AsyncConnectionManager,
    redact_sensitive_data,
    safe_log_request,
    safe_log_response,
    safe_log_error
)
import asyncio

# Configure logging to see the examples
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')


def secure_logging_example():
    """Example showing how sensitive data is automatically redacted in logs."""
    print("=== Secure Logging Example ===")
    
    manager = ConnectionManager()
    
    # Set up authentication that will be redacted in logs
    manager.set_api_key("secret-api-key-12345", "X-API-Key")
    manager.set_bearer_token("bearer-token-67890")
    
    try:
        # This request will log headers and payload with sensitive data redacted
        response = manager.post(
            "https://httpbin.org/post",
            headers={
                "X-Custom-Header": "safe-value",
                "Authorization": "Bearer another-secret-token",
                "X-API-Key": "another-api-key"
            },
            json={
                "username": "john_doe",
                "password": "secret123",  # This will be redacted
                "api_key": "hidden-key",  # This will be redacted
                "data": {
                    "message": "Hello World",
                    "auth_token": "nested-secret"  # This will be redacted
                }
            }
        )
        print(f"Request successful: {response.status_code}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    finally:
        manager.close()


async def async_secure_logging_example():
    """Example showing secure logging with async manager."""
    print("\n=== Async Secure Logging Example ===")
    
    async with AsyncConnectionManager() as manager:
        manager.set_oauth2_token("oauth2-secret-token")
        
        try:
            # Async request with sensitive data that will be redacted
            response = await manager.get(
                "https://httpbin.org/headers",
                headers={
                    "Authorization": "Bearer async-secret-token",
                    "X-Session-ID": "session123456",
                    "User-Agent": "TestClient/1.0"
                }
            )
            print(f"Async request successful: {response.status_code}")
            
        except Exception as e:
            print(f"Async request failed: {e}")


def manual_redaction_example():
    """Example showing manual use of redaction utilities."""
    print("\n=== Manual Redaction Example ===")
    
    # Example sensitive data structures
    sensitive_data = {
        "username": "john_doe",
        "password": "secret123",
        "api_key": "sk-1234567890abcdef",
        "user_data": {
            "email": "john@example.com",
            "auth_token": "nested-secret-token",
            "preferences": {
                "theme": "dark",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----"
            }
        },
        "session_data": {
            "session_id": "sess_abcdef123456",
            "csrf_token": "csrf_xyz789",
            "regular_field": "this is safe"
        }
    }
    
    print("Original data:")
    print(f"  password: {sensitive_data['password']}")
    print(f"  api_key: {sensitive_data['api_key']}")
    print(f"  auth_token: {sensitive_data['user_data']['auth_token']}")
    
    # Redact sensitive information
    safe_data = redact_sensitive_data(sensitive_data)
    
    print("\nRedacted data:")
    print(f"  password: {safe_data['password']}")
    print(f"  api_key: {safe_data['api_key']}")
    print(f"  auth_token: {safe_data['user_data']['auth_token']}")
    print(f"  regular_field: {safe_data['session_data']['regular_field']}")
    
    # Example with JSON string
    json_string = '{"Authorization": "Bearer secret123", "Content-Type": "application/json"}'
    print(f"\nOriginal JSON: {json_string}")
    
    safe_json = redact_sensitive_data(json_string)
    print(f"Redacted JSON: {safe_json}")


def custom_logging_hook_example():
    """Example showing how to use safe logging in custom hooks."""
    print("\n=== Custom Logging Hook Example ===")
    
    manager = ConnectionManager()
    
    def secure_request_hook(context):
        """Custom hook that safely logs request details."""
        safe_log_request(
            method=context.method,
            url=context.url,
            headers=context.kwargs.get('headers'),
            payload=context.kwargs.get('json'),
            level=logging.INFO
        )
        print("Custom hook: Request logged securely")
    
    def secure_response_hook(context):
        """Custom hook that safely logs response details."""
        safe_log_response(context.response, level=logging.INFO)
        print("Custom hook: Response logged securely")
    
    def secure_error_hook(context):
        """Custom hook that safely logs errors."""
        safe_log_error(
            context.exception,
            context.request_context.method,
            context.request_context.url,
            level=logging.INFO
        )
        print("Custom hook: Error logged securely")
    
    # Register hooks
    manager.register_pre_request_hook(secure_request_hook)
    manager.register_post_response_hook(secure_response_hook)
    manager.register_error_hook(secure_error_hook)
    
    try:
        # Make a request with sensitive headers
        response = manager.get(
            "https://httpbin.org/headers",
            headers={
                "Authorization": "Bearer hook-example-token",
                "X-API-Key": "hook-api-key-123"
            }
        )
        print(f"Request with hooks successful: {response.status_code}")
        
    except Exception as e:
        print(f"Request with hooks failed: {e}")
    
    finally:
        manager.close()


if __name__ == "__main__":
    secure_logging_example()
    
    # Run async example
    asyncio.run(async_secure_logging_example())
    
    manual_redaction_example()
    custom_logging_hook_example()
    
    print("\n=== Secure Logging Examples Complete ===")
    print("Check the logs above - sensitive data should be shown as [REDACTED]")
