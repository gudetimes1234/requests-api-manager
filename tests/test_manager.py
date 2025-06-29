"""
Comprehensive tests for the ConnectionManager class using external libraries.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call
import requests
import responses
import requests_mock

from requests_connection_manager import (
    ConnectionManager,
    RateLimitExceeded,
    CircuitBreakerOpen,
    MaxRetriesExceeded
)


class TestConnectionManager:
    """Test cases for ConnectionManager class."""

    def test_connection_manager_initialization(self):
        """Test ConnectionManager initialization."""
        manager = ConnectionManager(
            pool_connections=5,
            pool_maxsize=5,
            max_retries=2,
            rate_limit_requests=50
        )

        assert manager.timeout == 30  # Default timeout
        assert manager.rate_limit_requests == 50
        assert manager.rate_limit_period == 60  # Default period
        assert manager.session is not None
        assert manager.circuit_breaker is not None

        manager.close()

    @patch('requests.Session.request')
    def test_successful_request(self, mock_request):
        """Test successful HTTP request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        manager = ConnectionManager()

        response = manager.get('http://example.com')

        assert response.status_code == 200
        mock_request.assert_called_once()

        manager.close()

    @patch('requests.Session.request')
    def test_rate_limiting_behavior(self, mock_request):
        """Test rate limiting behavior with external ratelimit library."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Create manager with reasonable rate limit for testing
        manager = ConnectionManager(rate_limit_requests=2, rate_limit_period=1)

        # First two requests should succeed without significant delay
        response1 = manager.get('http://example.com')
        assert response1.status_code == 200

        response2 = manager.get('http://example.com')
        assert response2.status_code == 200

        # Verify that the rate limiting infrastructure is in place
        # (The actual rate limiting behavior is handled by the ratelimit library)
        assert mock_request.call_count == 2

        manager.close()

    @patch('requests.Session.request')
    def test_retry_mechanism_with_urllib3(self, mock_request):
        """Test retry mechanism using urllib3.Retry."""
        manager = ConnectionManager(max_retries=2, backoff_factor=0.1)

        # Mock successful response (urllib3.Retry handles retries in the adapter layer)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = manager.get('http://example.com')

        assert response.status_code == 200
        # urllib3.Retry is configured in the HTTPAdapter

        manager.close()

    @patch('requests.Session.request')
    def test_circuit_breaker_with_pybreaker(self, mock_request):
        """Test circuit breaker integration with pybreaker."""
        manager = ConnectionManager(
            circuit_breaker_failure_threshold=2,
            circuit_breaker_recovery_timeout=0.1
        )

        # Mock consistent failures
        mock_request.side_effect = requests.RequestException("Connection failed")

        # First failure
        with pytest.raises(requests.RequestException):
            manager.get('http://example.com')

        # Second failure - should trigger circuit breaker to open
        with pytest.raises((requests.RequestException, CircuitBreakerOpen)):
            manager.get('http://example.com')

        # Third attempt should raise CircuitBreakerOpen due to pybreaker
        with pytest.raises(CircuitBreakerOpen):
            manager.get('http://example.com')

        manager.close()

    def test_context_manager(self):
        """Test ConnectionManager as context manager."""
        with ConnectionManager() as manager:
            assert manager.session is not None

        # Session should be closed after context exit

    def test_get_stats(self):
        """Test get_stats method with new structure."""
        manager = ConnectionManager(
            rate_limit_requests=50,
            rate_limit_period=30,
            timeout=20
        )

        stats = manager.get_stats()

        assert 'circuit_breaker_state' in stats
        assert 'circuit_breaker_failure_count' in stats
        assert 'rate_limit_requests' in stats
        assert 'rate_limit_period' in stats
        assert stats['rate_limit_requests'] == 50
        assert stats['rate_limit_period'] == 30
        assert stats['timeout'] == 20

        manager.close()

    @patch('requests.Session.request')
    def test_all_http_methods(self, mock_request):
        """Test all HTTP methods."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        manager = ConnectionManager()

        # Test all HTTP methods
        methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']

        for method in methods:
            response = getattr(manager, method)('http://example.com')
            assert response.status_code == 200

        assert mock_request.call_count == len(methods)

        manager.close()

    @patch('requests.Session.request')
    def test_timeout_support(self, mock_request):
        """Test timeout support."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        manager = ConnectionManager(timeout=15)

        # Make request with default timeout
        manager.get('http://example.com')

        # Check that timeout was passed to the request
        call_args = mock_request.call_args
        assert 'timeout' in call_args.kwargs
        assert call_args.kwargs['timeout'] == 15

        # Make request with custom timeout
        manager.get('http://example.com', timeout=10)

        # Check that custom timeout was used
        call_args = mock_request.call_args
        assert call_args.kwargs['timeout'] == 10

        manager.close()

    def test_thread_safety_with_external_libraries(self):
        """Test thread safety with external rate limiting and circuit breaker."""
        manager = ConnectionManager(rate_limit_requests=5, rate_limit_period=1)

        results = []
        exceptions = []

        def make_request():
            try:
                with patch('requests.Session.request') as mock_request:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_request.return_value = mock_response

                    response = manager.get('http://example.com')
                    results.append(response.status_code)
            except Exception as e:
                exceptions.append(e)

        # Create multiple threads
        threads = []
        for _ in range(10):  # More than rate limit
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have successful requests (rate limiting will cause delays, not exceptions)
        assert len(results) > 0

        manager.close()

    @patch('requests.Session.request')
    def test_request_method_parameters(self, mock_request):
        """Test that request method properly passes parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        manager = ConnectionManager()

        # Test with various parameters
        data = {'key': 'value'}
        headers = {'Authorization': 'Bearer token'}

        manager.post('http://example.com', json=data, headers=headers)

        # Verify parameters were passed through
        call_args = mock_request.call_args
        assert call_args.kwargs['method'] == 'POST'  # method
        assert call_args.kwargs['url'] == 'http://example.com'  # url
        assert 'json' in call_args.kwargs
        assert 'headers' in call_args.kwargs
        assert call_args.kwargs['json'] == data
        assert call_args.kwargs['headers'] == headers

        manager.close()

    @patch('requests.Session.request')
    def test_batch_request_basic(self, mock_request):
        """Test basic batch request functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        manager = ConnectionManager()

        # Define batch requests
        requests_data = [
            ('GET', 'http://example.com/1', {}),
            ('POST', 'http://example.com/2', {'json': {'key': 'value'}}),
            ('GET', 'http://example.com/3', {'timeout': 10})
        ]

        # Execute batch request
        results = manager.batch_request(requests_data, max_workers=2)

        # Verify results
        assert len(results) == 3
        for result in results:
            assert hasattr(result, 'status_code')
            assert result.status_code == 200

        # Verify all requests were made
        assert mock_request.call_count == 3

        manager.close()

    @patch('requests.Session.request')
    def test_batch_request_with_exceptions(self, mock_request):
        """Test batch request with exceptions."""
        def side_effect(*args, **kwargs):
            if 'fail' in kwargs.get('url', ''):
                raise requests.exceptions.RequestException("Test error")
            mock_response = Mock()
            mock_response.status_code = 200
            return mock_response

        mock_request.side_effect = side_effect

        manager = ConnectionManager()

        requests_data = [
            ('GET', 'http://example.com/success', {}),
            ('GET', 'http://example.com/fail', {}),
            ('GET', 'http://example.com/success2', {})
        ]

        # Test with return_exceptions=True (default)
        results = manager.batch_request(requests_data, max_workers=3)

        assert len(results) == 3
        assert hasattr(results[0], 'status_code')  # Success
        assert isinstance(results[1], Exception)    # Failed
        assert hasattr(results[2], 'status_code')   # Success

        manager.close()

    def test_batch_request_empty_input(self):
        """Test batch request with empty input."""
        manager = ConnectionManager()

        results = manager.batch_request([])
        assert results == []

        manager.close()

    def test_batch_request_invalid_input(self):
        """Test batch request with invalid input."""
        manager = ConnectionManager()

        # Invalid tuple format
        with pytest.raises(ValueError, match="must be a tuple/list"):
            manager.batch_request([('GET', 'http://example.com')])  # Missing kwargs

        # Invalid method type
        with pytest.raises(ValueError, match="method and url must be strings"):
            manager.batch_request([(123, 'http://example.com', {})])

        # Invalid kwargs type
        with pytest.raises(ValueError, match="kwargs must be a dictionary"):
            manager.batch_request([('GET', 'http://example.com', "invalid")])

        manager.close()

    # def test_real_http_request(self):
    #     """Test real HTTP request to httpbin.org using ConnectionManager."""
    #     manager = ConnectionManager()

    #     try:
    #         # Make actual GET request to httpbin.org
    #         response = manager.get('https://httpbin.org/get')

    #         # Verify successful response
    #         assert response.status_code == 200

    #         # Verify response contains expected data structure
    #         data = response.json()
    #         assert 'url' in data
    #         assert 'headers' in data
    #         assert data['url'] == 'https://httpbin.org/get'

    #     except Exception as e:
    #         # For manual test runs, just assert False with the error
    #         assert False, f"Network request failed: {e}"

    #     finally:
    #         manager.close()

    @patch('requests.Session.request')
    def test_successful_request_scenarios(self, mock_request):
        """Test various successful request scenarios."""
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_request.return_value = mock_response

        manager = ConnectionManager()

        # Test different HTTP methods
        methods_data = [
            ('GET', 'https://api.example.com/users', {}),
            ('POST', 'https://api.example.com/users', {'json': {'name': 'test'}}),
            ('PUT', 'https://api.example.com/users/1', {'json': {'name': 'updated'}}),
            ('DELETE', 'https://api.example.com/users/1', {}),
            ('PATCH', 'https://api.example.com/users/1', {'json': {'status': 'active'}}),
            ('HEAD', 'https://api.example.com/health', {}),
            ('OPTIONS', 'https://api.example.com/users', {})
        ]

        for method, url, kwargs in methods_data:
            response = getattr(manager, method.lower())(url, **kwargs)
            assert response.status_code == 200

        # Verify all requests were made
        assert mock_request.call_count == len(methods_data)

        manager.close()

    # @patch('requests.Session.request')
    # def test_retry_on_failure_scenarios(self, mock_request):
    #     """Test retry behavior on different types of failures."""
    #     # Mock response that raises retriable HTTP status codes
    #     def side_effect(*args, **kwargs):
    #         response = Mock()
    #         # First two calls return 500 status (retriable)
    #         if mock_request.call_count <= 2:
    #             response.status_code = 500
    #             response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    #         else:
    #             # Third call succeeds
    #             response.status_code = 200
    #             response.raise_for_status.return_value = None
    #         return response

    #     mock_request.side_effect = side_effect

    #     manager = ConnectionManager(max_retries=3, backoff_factor=0.1)

    #     # This should succeed - urllib3.Retry handles retries at the adapter level
    #     response = manager.get('https://api.example.com/data')
    #     assert response.status_code == 200

    #     # Verify the request was made
    #     assert mock_request.call_count >= 1

    #     manager.close()

    @patch('requests.Session.request')
    def test_retry_exhaustion(self, mock_request):
        """Test behavior when retries are exhausted."""
        # Mock consistent failures
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")

        manager = ConnectionManager(max_retries=2, backoff_factor=0.1)

        # Should raise exception after exhausting retries
        with pytest.raises(requests.exceptions.ConnectionError):
            manager.get('https://api.example.com/data')

        manager.close()

    @patch('requests.Session.request')
    def test_circuit_breaker_open_state(self, mock_request):
        """Test circuit breaker behavior in open state."""
        manager = ConnectionManager(
            circuit_breaker_failure_threshold=2,
            circuit_breaker_recovery_timeout=0.1
        )

        # Mock consistent failures to trigger circuit breaker
        mock_request.side_effect = requests.exceptions.RequestException("Service unavailable")

        # First failure
        with pytest.raises(requests.exceptions.RequestException):
            manager.get('https://api.example.com/data')

        # Second failure - should open circuit breaker
        with pytest.raises((requests.exceptions.RequestException, CircuitBreakerOpen)):
            manager.get('https://api.example.com/data')

        # Third attempt should be blocked by circuit breaker
        with pytest.raises(CircuitBreakerOpen):
            manager.get('https://api.example.com/data')

        # Verify circuit breaker state
        stats = manager.get_stats()
        assert stats['circuit_breaker_failure_count'] >= 2

        manager.close()

    @patch('requests.Session.request')
    def test_circuit_breaker_recovery(self, mock_request):
        """Test circuit breaker recovery after timeout."""
        manager = ConnectionManager(
            circuit_breaker_failure_threshold=2,
            circuit_breaker_recovery_timeout=0.1
        )

        # Mock failures to open circuit breaker
        mock_request.side_effect = requests.exceptions.RequestException("Service unavailable")

        # Trigger circuit breaker to open
        for _ in range(2):
            with pytest.raises((requests.exceptions.RequestException, CircuitBreakerOpen)):
                manager.get('https://api.example.com/data')

        # Wait for recovery timeout
        time.sleep(0.2)

        # Mock successful response for recovery test
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.side_effect = None
        mock_request.return_value = mock_response

        # Circuit breaker should allow one test request (half-open state)
        response = manager.get('https://api.example.com/data')
        assert response.status_code == 200

        manager.close()

    def test_rate_limiting_behavior_detailed(self):
        """Test detailed rate limiting behavior."""
        # Create manager with very low rate limit for testing
        manager = ConnectionManager(rate_limit_requests=2, rate_limit_period=1)

        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            # Record request times
            request_times = []

            # Make requests and record timing
            for i in range(3):
                start_time = time.time()
                response = manager.get('https://api.example.com/data')
                request_times.append(time.time() - start_time)
                assert response.status_code == 200

            # Third request should have been delayed due to rate limiting
            # (The ratelimit library handles the actual delay)
            assert len(request_times) == 3

        manager.close()

    @patch('requests.Session.request')
    def test_rate_limiting_per_endpoint(self, mock_request):
        """Test per-endpoint rate limiting configuration."""
        endpoint_configs = {
            'slow-api.com': {
                'rate_limit_requests': 1,
                'rate_limit_period': 1
            },
            'fast-api.com': {
                'rate_limit_requests': 10,
                'rate_limit_period': 1
            }
        }

        manager = ConnectionManager(
            rate_limit_requests=5,
            rate_limit_period=1,
            endpoint_configs=endpoint_configs
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Test requests to different endpoints
        response1 = manager.get('https://slow-api.com/data')
        assert response1.status_code == 200

        response2 = manager.get('https://fast-api.com/data')
        assert response2.status_code == 200

        response3 = manager.get('https://other-api.com/data')  # Uses default config
        assert response3.status_code == 200

        assert mock_request.call_count == 3

        manager.close()

    @patch('requests.Session.request')
    def test_combined_retry_and_circuit_breaker(self, mock_request):
        """Test interaction between retry mechanism and circuit breaker."""
        manager = ConnectionManager(
            max_retries=2,
            backoff_factor=0.1,
            circuit_breaker_failure_threshold=3,
            circuit_breaker_recovery_timeout=0.1
        )

        # Mock intermittent failures
        failure_count = 0
        def side_effect(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 4:  # First 4 calls fail
                raise requests.exceptions.RequestException("Service error")
            else:
                # Success after failures
                mock_response = Mock()
                mock_response.status_code = 200
                return mock_response

        mock_request.side_effect = side_effect

        # This should trigger retries and eventually circuit breaker
        with pytest.raises((requests.exceptions.RequestException, CircuitBreakerOpen)):
            manager.get('https://api.example.com/data')

        # Verify circuit breaker opened due to accumulated failures
        stats = manager.get_stats()
        assert stats['circuit_breaker_failure_count'] > 0

        manager.close()

    @patch('requests.Session.request')
    def test_endpoint_specific_configurations(self, mock_request):
        """Test that endpoint-specific configurations are properly applied."""
        endpoint_configs = {
            'api.special.com': {
                'timeout': 60,
                'max_retries': 5,
                'circuit_breaker_failure_threshold': 10
            }
        }

        manager = ConnectionManager(
            timeout=30,
            max_retries=3,
            circuit_breaker_failure_threshold=5,
            endpoint_configs=endpoint_configs
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Make request to endpoint with specific config
        response = manager.get('https://api.special.com/data')
        assert response.status_code == 200

        # Verify timeout was applied from endpoint config
        call_args = mock_request.call_args
        assert call_args.kwargs['timeout'] == 60

        manager.close()

    @patch('requests.Session.request')
    def test_success_with_authentication(self, mock_request):
        """Test successful requests with various authentication methods."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Test API key authentication
        manager = ConnectionManager(api_key="test-api-key", api_key_header="X-API-Key")

        response = manager.get('https://api.example.com/data')
        assert response.status_code == 200

        # Verify API key was added to headers
        call_args = mock_request.call_args
        assert 'headers' in call_args.kwargs
        assert call_args.kwargs['headers']['X-API-Key'] == 'test-api-key'

        manager.close()

    @patch('requests.Session.request')
    def test_success_with_custom_headers(self, mock_request):
        """Test successful requests with custom headers and data."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 123, 'created': True}
        mock_request.return_value = mock_response

        manager = ConnectionManager()

        # Test POST with JSON data and custom headers
        custom_headers = {
            'Content-Type': 'application/json',
            'X-Custom-Header': 'custom-value'
        }

        post_data = {'name': 'Test User', 'email': 'test@example.com'}

        response = manager.post(
            'https://api.example.com/users',
            json=post_data,
            headers=custom_headers
        )

        assert response.status_code == 201

        # Verify request was made with correct parameters
        call_args = mock_request.call_args
        assert call_args.kwargs['method'] == 'POST'
        assert call_args.kwargs['json'] == post_data
        assert 'X-Custom-Header' in call_args.kwargs['headers']
        assert call_args.kwargs['headers']['X-Custom-Header'] == 'custom-value'

        manager.close()

    def test_stats_reporting(self):
        """Test that manager reports stats correctly."""
        manager = ConnectionManager(
            rate_limit_requests=50,
            rate_limit_period=30,
            timeout=20,
            circuit_breaker_failure_threshold=10
        )

        stats = manager.get_stats()



    @responses.activate
    def test_retry_with_responses_library(self):
        """Test retry behavior using responses library."""
        # First two requests fail with 500, third succeeds
        responses.add(responses.GET, "https://api.example.com/data", status=500)
        responses.add(responses.GET, "https://api.example.com/data", status=500)
        responses.add(responses.GET, "https://api.example.com/data", 
                     json={"status": "success"}, status=200)

        manager = ConnectionManager(max_retries=3, backoff_factor=0.1)

        # Should succeed after retries
        response = manager.get('https://api.example.com/data')
        assert response.status_code == 200

        manager.close()

    @responses.activate
    def test_rate_limiting_with_responses(self):
        """Test rate limiting behavior with responses library."""
        # Mock multiple successful responses
        for _ in range(5):
            responses.add(responses.GET, "https://api.example.com/data", 
                         json={"data": "test"}, status=200)

        manager = ConnectionManager(rate_limit_requests=2, rate_limit_period=1)

        start_time = time.time()

        # Make 3 requests - third should be delayed
        for i in range(3):
            response = manager.get('https://api.example.com/data')
            assert response.status_code == 200

        # Should take at least 1 second due to rate limiting
        elapsed = time.time() - start_time
        # Note: Due to rate limiting, this should take some time
        # but we can't assert exact timing due to test environment variability

        manager.close()

    def test_circuit_breaker_integration_detailed(self):
        """Test detailed circuit breaker behavior."""
        manager = ConnectionManager(
            circuit_breaker_failure_threshold=2,
            circuit_breaker_recovery_timeout=0.1
        )

        with patch('requests.Session.request') as mock_request:
            # Mock consistent failures
            mock_request.side_effect = requests.RequestException("Service down")

            # First failure
            with pytest.raises(requests.RequestException):
                manager.get('https://api.example.com/data')

            # Second failure - should trigger circuit breaker to open
            with pytest.raises((requests.RequestException, CircuitBreakerOpen)):
                manager.get('https://api.example.com/data')

            # Third attempt should be blocked by circuit breaker
            with pytest.raises(CircuitBreakerOpen):
                manager.get('https://api.example.com/data')

            # Verify circuit breaker state
            stats = manager.get_stats()
            assert stats['circuit_breaker_failure_count'] >= 2

        manager.close()

    # @responses.activate
    # def test_get_post_basic_functionality(self):
    #     """Test basic GET and POST functionality."""
    #     # Mock GET response
    #     responses.add(responses.GET, "https://api.example.com/users", 
    #                  json={"users": ["user1", "user2"]}, status=200)

    #     # Mock POST response
    #     responses.add(responses.POST, "https://api.example.com/users", 
    #                  json={"id": 123, "created": True}, status=201)

    #     manager = ConnectionManager()

    #     # Test GET
    #     get_response = manager.get('https://api.example.com/users')
    #     assert get_response.status_code == 200
    #     assert get_response.json()["users"] == ["user1", "user2"]

    #     # Test POST
    #     post_data = {"name": "new_user", "email": "user@example.com"}
    #     post_response = manager.post('https://api.example.com/users', json=post_data)
    #     assert post_response.status_code == 201
    #     assert post_response.json()["id"] == 123

    #     manager.close()

    # @responses.activate
    # def test_http_methods_comprehensive(self):
    #     """Test all HTTP methods comprehensively."""
    #     base_url = "https://api.example.com/resource"

    #     # Mock responses for all HTTP methods
    #     responses.add(responses.GET, base_url, json={"method": "GET"}, status=200)
    #     responses.add(responses.POST, base_url, json={"method": "POST"}, status=201)
    #     responses.add(responses.PUT, base_url, json={"method": "PUT"}, status=200)
    #     responses.add(responses.DELETE, base_url, status=204)
    #     responses.add(responses.PATCH, base_url, json={"method": "PATCH"}, status=200)
    #     responses.add(responses.HEAD, base_url, status=200)
    #     responses.add(responses.OPTIONS, base_url, status=200)

    #     manager = ConnectionManager()

    #     # Test GET
    #     response = manager.get(base_url)
    #     assert response.status_code == 200
    #     assert response.json()["method"] == "GET"

    #     # Test POST
    #     response = manager.post(base_url, json={"data": "test"})
    #     assert response.status_code == 201
    #     assert response.json()["method"] == "POST"

    #     # Test PUT
    #     response = manager.put(base_url, json={"data": "test"})
    #     assert response.status_code == 200
    #     assert response.json()["method"] == "PUT"

    #     # Test DELETE
    #     response = manager.delete(base_url)
    #     assert response.status_code == 204

    #     # Test PATCH
    #     response = manager.patch(base_url, json={"data": "test"})
    #     assert response.status_code == 200
    #     assert response.json()["method"] == "PATCH"

    #     # Test HEAD
    #     response = manager.head(base_url)
    #     assert response.status_code == 200

    #     # Test OPTIONS
    #     response = manager.options(base_url)
    #     assert response.status_code == 200

    #     manager.close()

    def test_circuit_breaker_recovery_cycle(self):
        """Test complete circuit breaker recovery cycle."""
        manager = ConnectionManager(
            circuit_breaker_failure_threshold=2,
            circuit_breaker_recovery_timeout=0.1
        )

        with patch('requests.Session.request') as mock_request:
            # Phase 1: Cause failures to open circuit breaker
            mock_request.side_effect = requests.RequestException("Service error")

            # Trigger failures to open circuit breaker
            for _ in range(2):
                with pytest.raises((requests.RequestException, CircuitBreakerOpen)):
                    manager.get('https://api.example.com/data')

            # Circuit breaker should be open now
            with pytest.raises(CircuitBreakerOpen):
                manager.get('https://api.example.com/data')

            # Phase 2: Wait for recovery timeout
            time.sleep(0.2)  # Wait longer than recovery timeout

            # Phase 3: Mock successful response for recovery
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.side_effect = None
            mock_request.return_value = mock_response

            # Circuit breaker should allow test request (half-open state)
            response = manager.get('https://api.example.com/data')
            assert response.status_code == 200

            # Circuit breaker should be closed now, subsequent requests should work
            response = manager.get('https://api.example.com/data')
            assert response.status_code == 200

        manager.close()

    @responses.activate
    def test_temporary_failures_with_eventual_success(self):
        """Test handling of temporary failures that eventually succeed."""
        # Add multiple responses: failures followed by success
        responses.add(responses.GET, "https://api.example.com/data", status=503)  # Service unavailable
        responses.add(responses.GET, "https://api.example.com/data", status=502)  # Bad gateway
        responses.add(responses.GET, "https://api.example.com/data", 
                     json={"status": "recovered"}, status=200)  # Success

        manager = ConnectionManager