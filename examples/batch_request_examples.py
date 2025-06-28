
"""
Examples demonstrating batch request functionality for ConnectionManager.
"""

from requests_connection_manager import ConnectionManager
import json


def basic_batch_request_example():
    """Example of basic batch request usage."""
    print("=== Basic Batch Request Example ===")
    
    manager = ConnectionManager()
    
    # Define multiple requests to execute concurrently
    requests_data = [
        ('GET', 'https://httpbin.org/get', {}),
        ('POST', 'https://httpbin.org/post', {'json': {'message': 'Hello'}}),
        ('GET', 'https://httpbin.org/delay/1', {}),
        ('GET', 'https://httpbin.org/status/200', {}),
        ('GET', 'https://httpbin.org/user-agent', {'headers': {'User-Agent': 'BatchRequestExample'}})
    ]
    
    try:
        # Execute all requests concurrently with max 3 workers
        results = manager.batch_request(requests_data, max_workers=3)
        
        # Process results
        for i, result in enumerate(results):
            method, url, kwargs = requests_data[i]
            if hasattr(result, 'status_code'):
                print(f"Request {i}: {method} {url} -> {result.status_code}")
            else:
                print(f"Request {i}: {method} {url} -> Error: {result}")
    
    except Exception as e:
        print(f"Batch request failed: {e}")
    
    finally:
        manager.close()


def batch_request_with_different_endpoints_example():
    """Example with different API endpoints and configurations."""
    print("=== Batch Request with Different Endpoints Example ===")
    
    # Set up manager with endpoint-specific configurations
    manager = ConnectionManager(
        endpoint_configs={
            'httpbin.org': {
                'timeout': 5,
                'rate_limit_requests': 10,
                'rate_limit_period': 10
            },
            'api.github.com': {
                'timeout': 10,
                'rate_limit_requests': 5,
                'rate_limit_period': 60
            }
        }
    )
    
    # Mix of different APIs and methods
    requests_data = [
        ('GET', 'https://httpbin.org/json', {}),
        ('GET', 'https://api.github.com/users/octocat', {}),
        ('POST', 'https://httpbin.org/post', {
            'json': {'data': 'test'},
            'headers': {'Content-Type': 'application/json'}
        }),
        ('GET', 'https://httpbin.org/headers', {
            'headers': {'X-Custom-Header': 'BatchTest'}
        })
    ]
    
    try:
        results = manager.batch_request(requests_data, max_workers=4)
        
        for i, result in enumerate(results):
            method, url, kwargs = requests_data[i]
            if hasattr(result, 'status_code'):
                print(f"✓ {method} {url} -> {result.status_code}")
                if hasattr(result, 'json'):
                    try:
                        # Show snippet of response data
                        data = result.json()
                        if isinstance(data, dict) and len(str(data)) > 100:
                            print(f"  Response: {str(data)[:100]}...")
                        else:
                            print(f"  Response: {data}")
                    except:
                        print(f"  Response length: {len(result.text)} chars")
            else:
                print(f"✗ {method} {url} -> {type(result).__name__}: {result}")
    
    except Exception as e:
        print(f"Batch request failed: {e}")
    
    finally:
        manager.close()


def batch_request_error_handling_example():
    """Example demonstrating error handling in batch requests."""
    print("=== Batch Request Error Handling Example ===")
    
    manager = ConnectionManager()
    
    # Include some requests that will fail
    requests_data = [
        ('GET', 'https://httpbin.org/status/200', {}),
        ('GET', 'https://httpbin.org/status/404', {}),
        ('GET', 'https://httpbin.org/status/500', {}),
        ('GET', 'https://invalid-domain-that-does-not-exist.com', {}),
        ('GET', 'https://httpbin.org/delay/2', {'timeout': 1})  # Will timeout
    ]
    
    try:
        # Execute with return_exceptions=True (default)
        print("With return_exceptions=True:")
        results = manager.batch_request(requests_data, max_workers=5, return_exceptions=True)
        
        for i, result in enumerate(results):
            method, url, kwargs = requests_data[i]
            if hasattr(result, 'status_code'):
                print(f"  ✓ Request {i}: {result.status_code}")
            else:
                print(f"  ✗ Request {i}: {type(result).__name__}")
        
        print(f"\nSuccessful requests: {sum(1 for r in results if hasattr(r, 'status_code'))}")
        print(f"Failed requests: {sum(1 for r in results if not hasattr(r, 'status_code'))}")
    
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    finally:
        manager.close()


def performance_comparison_example():
    """Example comparing sequential vs batch request performance."""
    print("=== Performance Comparison Example ===")
    
    import time
    
    manager = ConnectionManager()
    
    # Test URLs with artificial delays
    test_urls = [
        f'https://httpbin.org/delay/1?id={i}' for i in range(5)
    ]
    
    requests_data = [('GET', url, {}) for url in test_urls]
    
    # Sequential execution
    print("Sequential execution:")
    start_time = time.time()
    sequential_results = []
    for method, url, kwargs in requests_data:
        try:
            result = manager.request(method, url, **kwargs)
            sequential_results.append(result)
        except Exception as e:
            sequential_results.append(e)
    sequential_time = time.time() - start_time
    print(f"  Time taken: {sequential_time:.2f} seconds")
    
    # Batch execution
    print("\nBatch execution (max_workers=5):")
    start_time = time.time()
    batch_results = manager.batch_request(requests_data, max_workers=5)
    batch_time = time.time() - start_time
    print(f"  Time taken: {batch_time:.2f} seconds")
    
    print(f"\nSpeedup: {sequential_time/batch_time:.2f}x")
    
    manager.close()


if __name__ == "__main__":
    basic_batch_request_example()
    print("\n" + "="*50 + "\n")
    
    batch_request_with_different_endpoints_example()
    print("\n" + "="*50 + "\n")
    
    batch_request_error_handling_example()
    print("\n" + "="*50 + "\n")
    
    performance_comparison_example()
