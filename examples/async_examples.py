
"""
Examples demonstrating async functionality with AsyncConnectionManager.
"""

import asyncio
from requests_connection_manager import AsyncConnectionManager


async def basic_async_example():
    """Example of basic async request usage."""
    print("=== Basic Async Example ===")
    
    async with AsyncConnectionManager() as manager:
        try:
            # Make async GET request
            response = await manager.get('https://httpbin.org/get')
            print(f"Async GET response: {response.status_code}")
            
            # Make async POST request
            response = await manager.post('https://httpbin.org/post', json={'message': 'Hello Async!'})
            print(f"Async POST response: {response.status_code}")
            
        except Exception as e:
            print(f"Request failed: {e}")


async def concurrent_requests_example():
    """Example of making concurrent async requests."""
    print("=== Concurrent Requests Example ===")
    
    async with AsyncConnectionManager() as manager:
        try:
            # Create multiple async requests
            tasks = [
                manager.get('https://httpbin.org/delay/1'),
                manager.get('https://httpbin.org/delay/2'),
                manager.get('https://httpbin.org/delay/1'),
                manager.get('https://httpbin.org/status/200'),
                manager.get('https://httpbin.org/json')
            ]
            
            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks)
            
            for i, response in enumerate(responses):
                print(f"Request {i}: Status {response.status_code}")
                
        except Exception as e:
            print(f"Concurrent requests failed: {e}")


async def async_batch_request_example():
    """Example of using async batch request functionality."""
    print("=== Async Batch Request Example ===")
    
    async with AsyncConnectionManager() as manager:
        # Define batch requests
        requests_data = [
            ('GET', 'https://httpbin.org/get', {}),
            ('POST', 'https://httpbin.org/post', {'json': {'key': 'value'}}),
            ('GET', 'https://httpbin.org/delay/1', {}),
            ('GET', 'https://httpbin.org/status/201', {}),
            ('GET', 'https://httpbin.org/json', {})
        ]
        
        try:
            # Execute batch request with controlled parallelism
            results = await manager.batch_request(requests_data, max_workers=3)
            
            for i, result in enumerate(results):
                method, url, kwargs = requests_data[i]
                if hasattr(result, 'status_code'):
                    print(f"Batch request {i}: {method} -> {result.status_code}")
                else:
                    print(f"Batch request {i}: {method} -> Error: {result}")
                    
        except Exception as e:
            print(f"Batch request failed: {e}")


async def async_with_authentication_example():
    """Example of async requests with authentication."""
    print("=== Async Authentication Example ===")
    
    # Create manager with authentication
    async with AsyncConnectionManager(
        bearer_token="test-token",
        endpoint_configs={
            'httpbin.org': {
                'timeout': 60,
                'rate_limit_requests': 20,
                'rate_limit_period': 60
            }
        }
    ) as manager:
        try:
            # Request will include Bearer token
            response = await manager.get('https://httpbin.org/bearer')
            print(f"Authenticated request: {response.status_code}")
            
            # Check if token was included in request
            if response.status_code == 200:
                data = response.json()
                print(f"Token authenticated: {data.get('authenticated', False)}")
                
        except Exception as e:
            print(f"Authenticated request failed: {e}")


async def mixed_sync_async_example():
    """Example showing both sync and async managers can coexist."""
    print("=== Mixed Sync/Async Example ===")
    
    from requests_connection_manager import ConnectionManager
    
    # Sync manager
    sync_manager = ConnectionManager()
    
    # Async manager
    async with AsyncConnectionManager() as async_manager:
        try:
            # Make sync request
            sync_response = sync_manager.get('https://httpbin.org/get')
            print(f"Sync request: {sync_response.status_code}")
            
            # Make async request
            async_response = await async_manager.get('https://httpbin.org/get')
            print(f"Async request: {async_response.status_code}")
            
        except Exception as e:
            print(f"Mixed requests failed: {e}")
        finally:
            sync_manager.close()


async def async_error_handling_example():
    """Example of error handling in async requests."""
    print("=== Async Error Handling Example ===")
    
    from requests_connection_manager.exceptions import CircuitBreakerOpen
    
    async with AsyncConnectionManager(
        circuit_breaker_failure_threshold=2,
        circuit_breaker_recovery_timeout=5
    ) as manager:
        try:
            # This will likely fail and trigger circuit breaker
            for i in range(3):
                try:
                    response = await manager.get('https://httpbin.org/status/500')
                    print(f"Request {i}: {response.status_code}")
                except Exception as e:
                    print(f"Request {i} failed: {e}")
                    
        except CircuitBreakerOpen:
            print("Circuit breaker is open, requests are being blocked")
        except Exception as e:
            print(f"Error handling example failed: {e}")


async def performance_comparison_example():
    """Example comparing sync vs async performance."""
    print("=== Performance Comparison Example ===")
    
    import time
    from requests_connection_manager import ConnectionManager
    
    urls = [
        'https://httpbin.org/delay/1',
        'https://httpbin.org/delay/1',
        'https://httpbin.org/delay/1',
        'https://httpbin.org/delay/1',
        'https://httpbin.org/delay/1'
    ]
    
    # Test sync performance
    start_time = time.time()
    with ConnectionManager() as sync_manager:
        for url in urls:
            try:
                response = sync_manager.get(url)
                print(f"Sync request completed: {response.status_code}")
            except Exception as e:
                print(f"Sync request failed: {e}")
    sync_time = time.time() - start_time
    
    # Test async performance
    start_time = time.time()
    async with AsyncConnectionManager() as async_manager:
        tasks = [async_manager.get(url) for url in urls]
        try:
            responses = await asyncio.gather(*tasks)
            for response in responses:
                print(f"Async request completed: {response.status_code}")
        except Exception as e:
            print(f"Async requests failed: {e}")
    async_time = time.time() - start_time
    
    print(f"Sync time: {sync_time:.2f}s")
    print(f"Async time: {async_time:.2f}s")
    print(f"Async speedup: {sync_time/async_time:.2f}x")


async def main():
    """Run all async examples."""
    examples = [
        basic_async_example,
        concurrent_requests_example,
        async_batch_request_example,
        async_with_authentication_example,
        mixed_sync_async_example,
        async_error_handling_example,
        performance_comparison_example
    ]
    
    for example in examples:
        try:
            await example()
            print()
        except Exception as e:
            print(f"Example failed: {e}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
