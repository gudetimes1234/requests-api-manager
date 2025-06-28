
"""
Examples demonstrating authentication features for ConnectionManager.
"""

from requests_connection_manager import ConnectionManager


def api_key_authentication_example():
    """Example of using API key authentication."""
    print("=== API Key Authentication Example ===")
    
    # Method 1: Set API key in constructor
    manager = ConnectionManager(
        api_key="your-api-key-here",
        api_key_header="X-API-Key"  # This is the default
    )
    
    # Method 2: Set API key after initialization
    manager.set_api_key("your-api-key-here", "Authorization")
    
    try:
        # API key will be automatically added to headers
        response = manager.get('https://api.example.com/data')
        print(f"API response: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    manager.close()


def bearer_token_authentication_example():
    """Example of using Bearer token authentication."""
    print("=== Bearer Token Authentication Example ===")
    
    # Method 1: Set Bearer token in constructor
    manager = ConnectionManager(
        bearer_token="your-bearer-token-here"
    )
    
    # Method 2: Set Bearer token after initialization
    manager.set_bearer_token("your-bearer-token-here")
    
    try:
        # Bearer token will be automatically added as "Authorization: Bearer <token>"
        response = manager.get('https://api.example.com/protected')
        print(f"Protected API response: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    manager.close()


def oauth2_authentication_example():
    """Example of using OAuth2 token authentication."""
    print("=== OAuth2 Authentication Example ===")
    
    # Method 1: Set OAuth2 token in constructor
    manager = ConnectionManager(
        oauth2_token="your-oauth2-token-here"
    )
    
    # Method 2: Set OAuth2 token after initialization
    manager.set_oauth2_token("your-oauth2-token-here")
    
    try:
        # OAuth2 token will be automatically added as "Authorization: Bearer <token>"
        response = manager.get('https://api.example.com/oauth-protected')
        print(f"OAuth2 protected response: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    manager.close()


def basic_authentication_example():
    """Example of using basic authentication."""
    print("=== Basic Authentication Example ===")
    
    # Method 1: Set basic auth in constructor
    manager = ConnectionManager(
        basic_auth=("username", "password")
    )
    
    # Method 2: Set basic auth after initialization
    manager.set_basic_auth("username", "password")
    
    try:
        # Basic auth will be automatically handled by requests
        response = manager.get('https://api.example.com/basic-protected')
        print(f"Basic auth response: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    manager.close()


def endpoint_specific_authentication_example():
    """Example of endpoint-specific authentication configurations."""
    print("=== Endpoint-Specific Authentication Example ===")
    
    # Create manager with default authentication
    manager = ConnectionManager(
        api_key="default-api-key"
    )
    
    # Set different authentication for specific endpoints
    manager.set_endpoint_auth('api.service1.com', 'bearer', token='service1-bearer-token')
    manager.set_endpoint_auth('api.service2.com', 'api_key', api_key='service2-api-key', header_name='X-Service2-Key')
    manager.set_endpoint_auth('api.service3.com', 'basic', username='user', password='pass')
    manager.set_endpoint_auth('api.service4.com', 'oauth2', token='oauth2-token-for-service4')
    
    try:
        # Each request will use endpoint-specific authentication
        response1 = manager.get('https://api.service1.com/data')  # Uses Bearer token
        response2 = manager.get('https://api.service2.com/data')  # Uses custom API key
        response3 = manager.get('https://api.service3.com/data')  # Uses basic auth
        response4 = manager.get('https://api.service4.com/data')  # Uses OAuth2 token
        response5 = manager.get('https://api.other.com/data')     # Uses default API key
        
        print(f"Service 1 response: {response1.status_code}")
        print(f"Service 2 response: {response2.status_code}")
        print(f"Service 3 response: {response3.status_code}")
        print(f"Service 4 response: {response4.status_code}")
        print(f"Other service response: {response5.status_code}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    # View current configurations
    print("Current endpoint configurations:")
    for pattern, config in manager.get_endpoint_configs().items():
        print(f"  {pattern}: {config}")
    
    manager.close()


def mixed_configuration_example():
    """Example combining authentication with other endpoint configurations."""
    print("=== Mixed Configuration Example ===")
    
    # Define comprehensive endpoint configurations
    endpoint_configs = {
        'api.premium.com': {
            'timeout': 60,
            'rate_limit_requests': 50,
            'rate_limit_period': 60,
            'max_retries': 5,
            'bearer_token': 'premium-bearer-token'
        },
        'api.basic.com': {
            'timeout': 30,
            'rate_limit_requests': 10,
            'rate_limit_period': 60,
            'api_key': 'basic-api-key',
            'api_key_header': 'X-Basic-Key'
        }
    }
    
    manager = ConnectionManager(
        # Default settings
        timeout=30,
        api_key="default-key",
        # Endpoint-specific configurations
        endpoint_configs=endpoint_configs
    )
    
    try:
        # Premium endpoint uses Bearer token and custom timeouts/rate limits
        response1 = manager.get('https://api.premium.com/advanced')
        
        # Basic endpoint uses custom API key and settings
        response2 = manager.get('https://api.basic.com/simple')
        
        # Other endpoints use default settings
        response3 = manager.get('https://api.other.com/data')
        
        print(f"Premium API response: {response1.status_code}")
        print(f"Basic API response: {response2.status_code}")
        print(f"Other API response: {response3.status_code}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    manager.close()


def authentication_management_example():
    """Example of managing authentication dynamically."""
    print("=== Authentication Management Example ===")
    
    manager = ConnectionManager()
    
    # Initially no authentication
    print("No authentication set")
    
    # Set API key authentication
    manager.set_api_key("test-api-key")
    print("API key authentication set")
    
    # Switch to Bearer token
    manager.set_bearer_token("test-bearer-token")
    print("Bearer token authentication set")
    
    # Add endpoint-specific authentication
    manager.set_endpoint_auth('special.api.com', 'oauth2', token='special-oauth2-token')
    print("Endpoint-specific OAuth2 authentication added")
    
    # Clear global authentication (endpoint-specific remains)
    manager.clear_auth()
    print("Global authentication cleared")
    
    # Clear endpoint-specific authentication
    manager.clear_auth('special.api.com')
    print("Endpoint-specific authentication cleared")
    
    manager.close()


if __name__ == "__main__":
    api_key_authentication_example()
    print()
    bearer_token_authentication_example()
    print()
    oauth2_authentication_example()
    print()
    basic_authentication_example()
    print()
    endpoint_specific_authentication_example()
    print()
    mixed_configuration_example()
    print()
    authentication_management_example()
