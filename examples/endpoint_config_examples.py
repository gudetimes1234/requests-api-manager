
"""
Examples demonstrating per-endpoint configurations for ConnectionManager.
"""

from requests_connection_manager import ConnectionManager


def basic_endpoint_config_example():
    """Example of basic endpoint-specific configuration."""
    # Define endpoint-specific configurations
    endpoint_configs = {
        # Configuration for API endpoints
        'api.example.com': {
            'timeout': 60,
            'rate_limit_requests': 50,
            'rate_limit_period': 60,
            'max_retries': 5,
            'circuit_breaker_failure_threshold': 10
        },
        # Configuration for external service
        'external-service.com': {
            'timeout': 30,
            'rate_limit_requests': 10,
            'rate_limit_period': 60,
            'max_retries': 2,
            'circuit_breaker_failure_threshold': 3
        },
        # Configuration for slow third-party API
        'slow-api.com': {
            'timeout': 120,
            'rate_limit_requests': 5,
            'rate_limit_period': 60,
            'backoff_factor': 1.0
        }
    }
    
    # Create manager with endpoint configurations
    manager = ConnectionManager(
        # Default configuration
        timeout=30,
        rate_limit_requests=100,
        rate_limit_period=60,
        # Per-endpoint configurations
        endpoint_configs=endpoint_configs
    )
    
    # These requests will use endpoint-specific configurations
    try:
        # Will use api.example.com config (60s timeout, 50 req/min)
        response1 = manager.get('https://api.example.com/users')
        print(f"API response: {response1.status_code}")
        
        # Will use external-service.com config (30s timeout, 10 req/min)
        response2 = manager.get('https://external-service.com/data')
        print(f"External service response: {response2.status_code}")
        
        # Will use slow-api.com config (120s timeout, 5 req/min)
        response3 = manager.get('https://slow-api.com/heavy-computation')
        print(f"Slow API response: {response3.status_code}")
        
        # Will use default config (30s timeout, 100 req/min)
        response4 = manager.get('https://other-service.com/quick')
        print(f"Other service response: {response4.status_code}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    finally:
        manager.close()


def dynamic_endpoint_config_example():
    """Example of dynamically adding endpoint configurations."""
    # Create manager with default settings
    manager = ConnectionManager(
        timeout=30,
        rate_limit_requests=100,
        rate_limit_period=60
    )
    
    # Add endpoint configuration dynamically
    manager.add_endpoint_config('premium-api.com', {
        'timeout': 90,
        'rate_limit_requests': 200,
        'rate_limit_period': 60,
        'max_retries': 3,
        'circuit_breaker_failure_threshold': 15
    })
    
    # Add configuration for development endpoints
    manager.add_endpoint_config('dev.internal.com', {
        'timeout': 15,
        'rate_limit_requests': 1000,
        'rate_limit_period': 60,
        'max_retries': 1
    })
    
    try:
        # Will use premium-api.com config
        response1 = manager.get('https://premium-api.com/advanced-features')
        print(f"Premium API response: {response1.status_code}")
        
        # Will use dev.internal.com config
        response2 = manager.get('https://dev.internal.com/test-endpoint')
        print(f"Dev API response: {response2.status_code}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    # View current endpoint configurations
    print("Current endpoint configurations:")
    for pattern, config in manager.get_endpoint_configs().items():
        print(f"  {pattern}: {config}")
    
    # Remove a configuration
    manager.remove_endpoint_config('dev.internal.com')
    
    manager.close()


def microservices_config_example():
    """Example configuration for microservices architecture."""
    # Different configurations for different microservices
    microservice_configs = {
        # User service - critical, needs high availability
        'user-service': {
            'timeout': 45,
            'rate_limit_requests': 200,
            'rate_limit_period': 60,
            'max_retries': 5,
            'circuit_breaker_failure_threshold': 20,
            'circuit_breaker_recovery_timeout': 30
        },
        # Order service - important, moderate limits
        'order-service': {
            'timeout': 30,
            'rate_limit_requests': 100,
            'rate_limit_period': 60,
            'max_retries': 3,
            'circuit_breaker_failure_threshold': 10,
            'circuit_breaker_recovery_timeout': 60
        },
        # Analytics service - can be slower, lower priority
        'analytics-service': {
            'timeout': 90,
            'rate_limit_requests': 20,
            'rate_limit_period': 60,
            'max_retries': 2,
            'circuit_breaker_failure_threshold': 5,
            'circuit_breaker_recovery_timeout': 120
        },
        # Notification service - fire and forget style
        'notification-service': {
            'timeout': 10,
            'rate_limit_requests': 500,
            'rate_limit_period': 60,
            'max_retries': 1,
            'circuit_breaker_failure_threshold': 50
        }
    }
    
    manager = ConnectionManager(endpoint_configs=microservice_configs)
    
    try:
        # Each service call uses its specific configuration
        user_data = manager.get('https://user-service.internal/profile/123')
        order_data = manager.get('https://order-service.internal/orders/456')
        analytics_data = manager.get('https://analytics-service.internal/reports/daily')
        
        # Send notification (will use fast, low-retry config)
        manager.post('https://notification-service.internal/send', 
                    json={'message': 'Order processed', 'user_id': 123})
        
        print("All microservice calls completed successfully")
        
    except Exception as e:
        print(f"Microservice call failed: {e}")
    finally:
        manager.close()


if __name__ == "__main__":
    print("=== Basic Endpoint Configuration Example ===")
    basic_endpoint_config_example()
    
    print("\n=== Dynamic Endpoint Configuration Example ===")
    dynamic_endpoint_config_example()
    
    print("\n=== Microservices Configuration Example ===")
    microservices_config_example()
