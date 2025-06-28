"""
Comprehensive tests for the ConnectionManager class using external libraries.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import requests

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
        
        # Create manager with very low rate limit for testing
        manager = ConnectionManager(rate_limit_requests=2, rate_limit_period=1)
        
        # First request should succeed
        response1 = manager.get('http://example.com')
        assert response1.status_code == 200
        
        # Second request should succeed
        response2 = manager.get('http://example.com')
        assert response2.status_code == 200
        
        # Third request should be rate limited (handled by ratelimit library)
        # The ratelimit library will sleep rather than raise an exception
        start_time = time.time()
        response3 = manager.get('http://example.com')
        end_time = time.time()
        
        # Should have been delayed by rate limiting
        assert end_time - start_time >= 0.5  # Some delay expected
        assert response3.status_code == 200
        
        manager.close()
    
    @patch('requests.Session.request')
    def test_retry_mechanism_with_urllib3(self, mock_request):
        """Test retry mechanism using urllib3.Retry."""
        manager = ConnectionManager(max_retries=2, backoff_factor=0.1)
        
        # Mock server error responses for first two attempts, then success
        mock_request.side_effect = [
            requests.HTTPError("Server error: 500"),
            requests.HTTPError("Server error: 500"),
            Mock(status_code=200)
        ]
        
        response = manager.get('http://example.com')
        
        assert response.status_code == 200
        # urllib3.Retry handles retries automatically in the adapter
        
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
        
        # Second failure - should trigger circuit breaker
        with pytest.raises(requests.RequestException):
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
        assert call_args.args[0] == 'POST'  # method
        assert call_args.args[1] == 'http://example.com'  # url
        assert 'json' in call_args.kwargs
        assert 'headers' in call_args.kwargs
        
        manager.close()