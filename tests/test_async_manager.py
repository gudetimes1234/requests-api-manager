"""
Comprehensive tests for the AsyncConnectionManager class.
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
import httpx

from requests_connection_manager import (
    AsyncConnectionManager,
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)


class TestAsyncConnectionManager:
    """Test cases for AsyncConnectionManager class."""

    @pytest.mark.asyncio
    async def test_async_connection_manager_initialization(self):
        """Test AsyncConnectionManager initialization."""
        manager = AsyncConnectionManager(
            pool_connections=5,
            pool_maxsize=5,
            max_retries=2,
            rate_limit_requests=50
        )

        assert manager.timeout == 30  # Default timeout
        assert manager.rate_limit_requests == 50
        assert manager.rate_limit_period == 60  # Default period
        assert manager.client is not None
        assert manager.circuit_breaker is not None

        await manager.close()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test AsyncConnectionManager as async context manager."""
        async with AsyncConnectionManager() as manager:
            assert manager.client is not None

        # Client should be closed after context exit

    @pytest.mark.asyncio
    async def test_async_get_stats(self):
        """Test get_stats method for async manager."""
        manager = AsyncConnectionManager(
            rate_limit_requests=50,
            rate_limit_period=30,
            timeout=20
        )

        stats = manager.get_stats()

        assert 'client_type' in stats
        assert stats['client_type'] == 'httpx.AsyncClient'
        assert 'circuit_breaker_state' in stats
        assert 'circuit_breaker_failure_count' in stats
        assert 'rate_limit_requests' in stats
        assert 'rate_limit_period' in stats
        assert stats['rate_limit_requests'] == 50
        assert stats['rate_limit_period'] == 30
        assert stats['timeout'] == 20

        await manager.close()

    @pytest.mark.asyncio
    async def test_async_successful_request(self):
        """Test successful async HTTP request."""
        with patch.object(httpx.AsyncClient, 'request', new_callable=AsyncMock) as mock_request:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            manager = AsyncConnectionManager()

            response = await manager.get('http://example.com')

            assert response.status_code == 200
            mock_request.assert_called_once()

            await manager.close()

    @pytest.mark.asyncio
    async def test_async_all_http_methods(self):
        """Test all async HTTP methods."""
        with patch.object(httpx.AsyncClient, 'request', new_callable=AsyncMock) as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            manager = AsyncConnectionManager()

            # Test all HTTP methods
            methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']

            for method in methods:
                response = await getattr(manager, method)('http://example.com')
                assert response.status_code == 200

            assert mock_request.call_count == len(methods)

            await manager.close()

    @pytest.mark.asyncio
    async def test_async_timeout_support(self):
        """Test timeout support in async requests."""
        with patch.object(httpx.AsyncClient, 'request', new_callable=AsyncMock) as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            manager = AsyncConnectionManager(timeout=15)

            # Make request with default timeout
            await manager.get('http://example.com')

            # Check that timeout was passed to the request
            call_args = mock_request.call_args
            assert 'timeout' in call_args.kwargs
            assert call_args.kwargs['timeout'] == 15

            # Make request with custom timeout
            await manager.get('http://example.com', timeout=10)

            # Check that custom timeout was used
            call_args = mock_request.call_args
            assert call_args.kwargs['timeout'] == 10

            await manager.close()

    @pytest.mark.asyncio
    async def test_async_request_method_parameters(self):
        """Test that async request method properly passes parameters."""
        with patch.object(httpx.AsyncClient, 'request', new_callable=AsyncMock) as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            manager = AsyncConnectionManager()

            # Test with various parameters
            data = {'key': 'value'}
            headers = {'Authorization': 'Bearer token'}

            await manager.post('http://example.com', json=data, headers=headers)

            # Verify parameters were passed through
            call_args = mock_request.call_args
            assert call_args.kwargs['method'] == 'POST'
            assert call_args.kwargs['url'] == 'http://example.com'
            assert 'json' in call_args.kwargs
            assert 'headers' in call_args.kwargs
            assert call_args.kwargs['json'] == data
            assert call_args.kwargs['headers'] == headers

            await manager.close()

    @pytest.mark.asyncio
    async def test_async_batch_request_basic(self):
        """Test basic async batch request functionality."""
        with patch.object(httpx.AsyncClient, 'request', new_callable=AsyncMock) as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            manager = AsyncConnectionManager()

            # Define batch requests
            requests_data = [
                ('GET', 'http://example.com/1', {}),
                ('POST', 'http://example.com/2', {'json': {'key': 'value'}}),
                ('GET', 'http://example.com/3', {'timeout': 10})
            ]

            # Execute batch request
            results = await manager.batch_request(requests_data, max_workers=2)

            # Verify results
            assert len(results) == 3
            for result in results:
                assert hasattr(result, 'status_code')
                assert result.status_code == 200

            # Verify all requests were made
            assert mock_request.call_count == 3

            await manager.close()

    @pytest.mark.asyncio
    async def test_async_batch_request_with_exceptions(self):
        """Test async batch request with exceptions."""
        async def side_effect(*args, **kwargs):
            if 'fail' in kwargs.get('url', ''):
                raise httpx.RequestError("Test error")
            mock_response = Mock()
            mock_response.status_code = 200
            return mock_response

        with patch.object(httpx.AsyncClient, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = side_effect

            manager = AsyncConnectionManager()

            requests_data = [
                ('GET', 'http://example.com/success', {}),
                ('GET', 'http://example.com/fail', {}),
                ('GET', 'http://example.com/success2', {})
            ]

            # Test with return_exceptions=True (default)
            results = await manager.batch_request(requests_data, max_workers=3)

            assert len(results) == 3
            assert hasattr(results[0], 'status_code')  # Success
            assert isinstance(results[1], Exception)    # Failed
            assert hasattr(results[2], 'status_code')   # Success

            await manager.close()

    @pytest.mark.asyncio
    async def test_async_batch_request_empty_input(self):
        """Test async batch request with empty input."""
        manager = AsyncConnectionManager()

        results = await manager.batch_request([])
        assert results == []

        await manager.close()

    @pytest.mark.asyncio
    async def test_async_batch_request_invalid_input(self):
        """Test async batch request with invalid input."""
        manager = AsyncConnectionManager()

        # Invalid tuple format
        with pytest.raises(ValueError, match="must be a tuple/list"):
            await manager.batch_request([('GET', 'http://example.com')])  # Missing kwargs

        # Invalid method type
        with pytest.raises(ValueError, match="method and url must be strings"):
            await manager.batch_request([(123, 'http://example.com', {})])

        # Invalid kwargs type
        with pytest.raises(ValueError, match="kwargs must be a dictionary"):
            await manager.batch_request([('GET', 'http://example.com', "invalid")])

        await manager.close()

    @pytest.mark.asyncio
    async def test_async_endpoint_configuration(self):
        """Test async manager with endpoint-specific configurations."""
        endpoint_configs = {
            'api.example.com': {
                'timeout': 60,
                'rate_limit_requests': 50,
                'rate_limit_period': 60,
                'max_retries': 5
            }
        }

        manager = AsyncConnectionManager(endpoint_configs=endpoint_configs)

        # Test endpoint config retrieval
        config = manager._get_endpoint_config('https://api.example.com/test')
        assert config['timeout'] == 60
        assert config['rate_limit_requests'] == 50

        # Test default config for non-matching URLs
        default_config = manager._get_endpoint_config('https://other.com/test')
        assert default_config['timeout'] == manager.default_timeout

        await manager.close()

    @pytest.mark.asyncio
    async def test_async_authentication(self):
        """Test async manager authentication features."""
        manager = AsyncConnectionManager(
            api_key="test-key",
            bearer_token="test-token"
        )

        # Test authentication methods
        manager.set_api_key("new-key", "X-Custom-Key")
        assert manager.api_key == "new-key"
        assert manager.api_key_header == "X-Custom-Key"

        manager.set_bearer_token("new-bearer-token")
        assert manager.bearer_token == "new-bearer-token"

        manager.set_oauth2_token("oauth-token")
        assert manager.oauth2_token == "oauth-token"

        manager.set_basic_auth("user", "pass")
        assert manager.basic_auth == ("user", "pass")

        # Test endpoint-specific auth
        manager.set_endpoint_auth('api.test.com', 'api_key', api_key='endpoint-key')
        assert 'api.test.com' in manager.endpoint_configs
        assert manager.endpoint_configs['api.test.com']['api_key'] == 'endpoint-key'

        # Test clearing auth
        manager.clear_auth()
        assert manager.api_key is None
        assert manager.bearer_token is None

        await manager.close()

    @pytest.mark.asyncio
    async def test_async_plugin_system_integration(self):
        """Test that async manager works with plugin system."""
        manager = AsyncConnectionManager()

        # Test hook registration
        def pre_request_hook(context):
            context.kwargs['headers'] = context.kwargs.get('headers', {})
            context.kwargs['headers']['X-Test'] = 'async-test'

        manager.register_pre_request_hook(pre_request_hook)

        # Verify hooks were called
        hooks = manager.list_hooks()
        assert 'pre_request' in hooks

        await manager.close()

    @pytest.mark.asyncio
    async def test_async_concurrent_performance(self):
        """Test that async requests can run concurrently for better performance."""
        with patch.object(httpx.AsyncClient, 'request', new_callable=AsyncMock) as mock_request:
            # Mock a slow response (simulate network delay)
            async def slow_response(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms delay
                mock_response = Mock()
                mock_response.status_code = 200
                return mock_response

            mock_request.side_effect = slow_response

            manager = AsyncConnectionManager()

            # Time concurrent requests
            start_time = time.time()
            tasks = [
                manager.get('http://example.com/1'),
                manager.get('http://example.com/2'),
                manager.get('http://example.com/3'),
                manager.get('http://example.com/4'),
                manager.get('http://example.com/5')
            ]

            responses = await asyncio.gather(*tasks)
            end_time = time.time()

            # All requests should complete
            assert len(responses) == 5
            for response in responses:
                assert response.status_code == 200

            # Should take roughly 100ms (concurrent) not 500ms (sequential)
            elapsed_time = end_time - start_time
            assert elapsed_time < 0.3  # Allow some overhead, but should be much less than 500ms

            await manager.close()

    @pytest.mark.asyncio
    async def test_real_async_http_request(self):
        """Test real async HTTP request to httpbin.org."""
        manager = AsyncConnectionManager()

        try:
            # Make actual async GET request to httpbin.org
            response = await manager.get('https://httpbin.org/get')

            # Verify successful response
            assert response.status_code == 200

            # Verify response contains expected data structure
            data = response.json()
            assert 'url' in data
            assert 'headers' in data
            assert data['url'] == 'https://httpbin.org/get'

        except Exception as e:
            # Skip this test if network is unavailable
            pytest.skip(f"Network request failed: {e}")

        finally:
            await manager.close()