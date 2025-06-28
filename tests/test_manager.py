"""
Comprehensive tests for the ConnectionManager class.
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
from requests_connection_manager.manager import TokenBucket, CircuitBreaker


class TestTokenBucket:
    """Test cases for TokenBucket class."""
    
    def test_token_bucket_initialization(self):
        """Test token bucket initialization."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.capacity == 10
        assert bucket.tokens == 10
        assert bucket.refill_rate == 1.0
    
    def test_token_consumption(self):
        """Test token consumption."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        
        # Should be able to consume tokens
        assert bucket.consume(5) is True
        assert bucket.tokens == 5
        
        # Should not be able to consume more than available
        assert bucket.consume(6) is False
        assert bucket.tokens == 5
    
    def test_token_refill(self):
        """Test token refill over time."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)  # 2 tokens per second
        bucket.tokens = 0
        
        # Sleep for 1 second to allow refill
        time.sleep(1.1)
        
        # Should have refilled approximately 2 tokens
        assert bucket.consume(2) is True


class TestCircuitBreaker:
    """Test cases for CircuitBreaker class."""
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
        assert cb.state == 'CLOSED'
        assert cb.failure_count == 0
    
    def test_successful_calls(self):
        """Test successful function calls."""
        cb = CircuitBreaker()
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == 'CLOSED'
        assert cb.failure_count == 0
    
    def test_circuit_breaker_opens_on_failures(self):
        """Test that circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        def failing_func():
            raise Exception("Test failure")
        
        # First failure
        with pytest.raises(Exception):
            cb.call(failing_func)
        assert cb.state == 'CLOSED'
        assert cb.failure_count == 1
        
        # Second failure - should open circuit
        with pytest.raises(Exception):
            cb.call(failing_func)
        assert cb.state == 'OPEN'
        assert cb.failure_count == 2
        
        # Should now raise CircuitBreakerOpen
        with pytest.raises(CircuitBreakerOpen):
            cb.call(failing_func)
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        def failing_func():
            raise Exception("Test failure")
        
        def success_func():
            return "success"
        
        # Trigger failure to open circuit
        with pytest.raises(Exception):
            cb.call(failing_func)
        assert cb.state == 'OPEN'
        
        # Wait for recovery timeout
        time.sleep(0.2)
        
        # Should move to HALF_OPEN and then CLOSED on success
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == 'CLOSED'
        assert cb.failure_count == 0


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
        
        assert manager.max_retries == 2
        assert manager.rate_limiter.capacity == 50
        assert manager.circuit_breaker.failure_threshold == 5
        
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
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Create manager with very low rate limit
        manager = ConnectionManager(rate_limit_requests=1, rate_limit_period=10)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            # First request should succeed
            response = manager.get('http://example.com')
            assert response.status_code == 200
            
            # Second request should fail due to rate limit
            with pytest.raises(RateLimitExceeded):
                manager.get('http://example.com')
        
        manager.close()
    
    @patch('requests.Session.request')
    def test_retry_mechanism(self, mock_request):
        """Test retry mechanism on failures."""
        manager = ConnectionManager(max_retries=2, backoff_factor=0.1)
        
        # Mock server error responses for first two attempts, then success
        responses = [
            Mock(status_code=500),
            Mock(status_code=500),
            Mock(status_code=200)
        ]
        
        # First two calls raise HTTPError due to 500 status
        mock_request.side_effect = [
            requests.HTTPError("Server error: 500"),
            requests.HTTPError("Server error: 500"),
            responses[2]
        ]
        
        response = manager.get('http://example.com')
        
        assert response.status_code == 200
        assert mock_request.call_count == 3
        
        manager.close()
    
    @patch('requests.Session.request')
    def test_max_retries_exceeded(self, mock_request):
        """Test MaxRetriesExceeded exception."""
        manager = ConnectionManager(max_retries=1, backoff_factor=0.1)
        
        # Mock consistent failures
        mock_request.side_effect = requests.HTTPError("Server error")
        
        with pytest.raises(MaxRetriesExceeded):
            manager.get('http://example.com')
        
        assert mock_request.call_count == 2  # Initial attempt + 1 retry
        
        manager.close()
    
    @patch('requests.Session.request')
    def test_circuit_breaker_integration(self, mock_request):
        """Test circuit breaker integration."""
        manager = ConnectionManager(
            circuit_breaker_failure_threshold=2,
            circuit_breaker_recovery_timeout=0.1,
            max_retries=0  # Disable retries for this test
        )
        
        # Mock consistent failures
        mock_request.side_effect = requests.RequestException("Connection failed")
        
        # First failure
        with pytest.raises(requests.RequestException):
            manager.get('http://example.com')
        
        # Second failure - should open circuit
        with pytest.raises(requests.RequestException):
            manager.get('http://example.com')
        
        # Third attempt should raise CircuitBreakerOpen
        with pytest.raises(CircuitBreakerOpen):
            manager.get('http://example.com')
        
        manager.close()
    
    def test_context_manager(self):
        """Test ConnectionManager as context manager."""
        with ConnectionManager() as manager:
            assert manager.session is not None
        
        # Session should be closed after context exit
        # Note: We can't easily test if session is closed without accessing private attributes
    
    def test_get_stats(self):
        """Test get_stats method."""
        manager = ConnectionManager(
            max_retries=5,
            backoff_factor=0.5,
            timeout=20
        )
        
        stats = manager.get_stats()
        
        assert 'circuit_breaker_state' in stats
        assert 'rate_limiter_tokens' in stats
        assert stats['max_retries'] == 5
        assert stats['backoff_factor'] == 0.5
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
    
    def test_thread_safety(self):
        """Test thread safety of rate limiter and circuit breaker."""
        manager = ConnectionManager(rate_limit_requests=10, rate_limit_period=1)
        
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
        for _ in range(15):  # More than rate limit
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have some successful requests and some rate limit exceptions
        assert len(results) > 0
        assert len(exceptions) > 0
        assert any(isinstance(e, RateLimitExceeded) for e in exceptions)
        
        manager.close()
