
"""
Tests for the plugin system functionality.
"""

import pytest
from unittest.mock import Mock, patch
import requests

from requests_connection_manager import (
    ConnectionManager,
    RequestContext,
    ResponseContext,
    ErrorContext,
    HookType
)


class TestPluginSystem:
    """Test cases for the plugin system."""
    
    def test_pre_request_hook_modify_url(self):
        """Test pre-request hook that modifies URL."""
        manager = ConnectionManager()
        
        def modify_url_hook(context: RequestContext):
            if context.url == "http://example.com":
                context.update_url("http://modified.example.com")
        
        manager.register_pre_request_hook(modify_url_hook)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            manager.get("http://example.com")
            
            # Verify the URL was modified
            call_args = mock_request.call_args
            assert call_args.kwargs['url'] == "http://modified.example.com"
        
        manager.close()
    
    def test_pre_request_hook_modify_headers(self):
        """Test pre-request hook that modifies headers."""
        manager = ConnectionManager()
        
        def add_auth_header(context: RequestContext):
            context.update_headers({"Authorization": "Bearer token123"})
        
        manager.register_pre_request_hook(add_auth_header)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            manager.get("http://example.com")
            
            # Verify headers were added
            call_args = mock_request.call_args
            assert "Authorization" in call_args.kwargs.get('headers', {})
            assert call_args.kwargs['headers']['Authorization'] == "Bearer token123"
        
        manager.close()
    
    def test_pre_request_hook_modify_payload(self):
        """Test pre-request hook that modifies payload."""
        manager = ConnectionManager()
        
        def add_timestamp_hook(context: RequestContext):
            context.update_payload(params={"timestamp": "2023-01-01"})
        
        manager.register_pre_request_hook(add_timestamp_hook)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            manager.get("http://example.com")
            
            # Verify payload was modified
            call_args = mock_request.call_args
            assert "params" in call_args.kwargs
            assert call_args.kwargs['params']['timestamp'] == "2023-01-01"
        
        manager.close()
    
    def test_post_response_hook_inspect_response(self):
        """Test post-response hook that inspects response."""
        manager = ConnectionManager()
        inspected_responses = []
        
        def inspect_response_hook(context: ResponseContext):
            inspected_responses.append({
                'status_code': context.response.status_code,
                'url': context.request_context.url
            })
        
        manager.register_post_response_hook(inspect_response_hook)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            manager.get("http://example.com")
            
            # Verify response was inspected
            assert len(inspected_responses) == 1
            assert inspected_responses[0]['status_code'] == 200
            assert inspected_responses[0]['url'] == "http://example.com"
        
        manager.close()
    
    def test_error_hook_logging(self):
        """Test error hook that logs errors."""
        manager = ConnectionManager()
        logged_errors = []
        
        def error_logging_hook(context: ErrorContext):
            logged_errors.append({
                'error': str(context.exception),
                'url': context.request_context.url
            })
        
        manager.register_error_hook(error_logging_hook)
        
        with patch('requests.Session.request') as mock_request:
            mock_request.side_effect = requests.RequestException("Connection failed")
            
            with pytest.raises(requests.RequestException):
                manager.get("http://example.com")
            
            # Verify error was logged
            assert len(logged_errors) == 1
            assert "Connection failed" in logged_errors[0]['error']
            assert logged_errors[0]['url'] == "http://example.com"
        
        manager.close()
    
    def test_error_hook_fallback_response(self):
        """Test error hook that provides fallback response."""
        manager = ConnectionManager()
        
        def fallback_response_hook(context: ErrorContext):
            if "timeout" in str(context.exception).lower():
                # Create a mock fallback response
                fallback = Mock()
                fallback.status_code = 408
                fallback.text = "Request timeout - fallback response"
                context.set_fallback_response(fallback)
        
        manager.register_error_hook(fallback_response_hook)
        
        with patch('requests.Session.request') as mock_request:
            mock_request.side_effect = requests.Timeout("Request timeout")
            
            # Should not raise exception, should return fallback
            response = manager.get("http://example.com")
            
            assert response.status_code == 408
            assert "fallback response" in response.text
        
        manager.close()
    
    def test_multiple_hooks_execution_order(self):
        """Test that multiple hooks execute in registration order."""
        manager = ConnectionManager()
        execution_order = []
        
        def hook1(context: RequestContext):
            execution_order.append("hook1")
        
        def hook2(context: RequestContext):
            execution_order.append("hook2")
        
        def hook3(context: RequestContext):
            execution_order.append("hook3")
        
        manager.register_pre_request_hook(hook1)
        manager.register_pre_request_hook(hook2)
        manager.register_pre_request_hook(hook3)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            manager.get("http://example.com")
            
            assert execution_order == ["hook1", "hook2", "hook3"]
        
        manager.close()
    
    def test_hook_unregistration(self):
        """Test unregistering hooks."""
        manager = ConnectionManager()
        executed_hooks = []
        
        def hook1(context: RequestContext):
            executed_hooks.append("hook1")
        
        def hook2(context: RequestContext):
            executed_hooks.append("hook2")
        
        manager.register_pre_request_hook(hook1)
        manager.register_pre_request_hook(hook2)
        
        # Unregister hook1
        manager.unregister_hook(HookType.PRE_REQUEST, hook1)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            manager.get("http://example.com")
            
            # Only hook2 should have executed
            assert executed_hooks == ["hook2"]
        
        manager.close()
    
    def test_list_hooks(self):
        """Test listing registered hooks."""
        manager = ConnectionManager()
        
        def pre_hook(context: RequestContext):
            pass
        
        def post_hook(context: ResponseContext):
            pass
        
        def error_hook(context: ErrorContext):
            pass
        
        manager.register_pre_request_hook(pre_hook)
        manager.register_post_response_hook(post_hook)
        manager.register_error_hook(error_hook)
        
        hooks = manager.list_hooks()
        
        assert "pre_request" in hooks
        assert "post_response" in hooks
        assert "error_handler" in hooks
        assert "pre_hook" in hooks["pre_request"]
        assert "post_hook" in hooks["post_response"]
        assert "error_hook" in hooks["error_handler"]
        
        manager.close()
    
    def test_hook_exception_handling(self):
        """Test that exceptions in hooks don't break the request flow."""
        manager = ConnectionManager()
        
        def failing_hook(context: RequestContext):
            raise ValueError("Hook failed")
        
        def working_hook(context: RequestContext):
            context.update_headers({"X-Hook": "working"})
        
        manager.register_pre_request_hook(failing_hook)
        manager.register_pre_request_hook(working_hook)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            # Request should still succeed despite failing hook
            response = manager.get("http://example.com")
            
            assert response.status_code == 200
            
            # Working hook should still have executed
            call_args = mock_request.call_args
            assert call_args.kwargs.get('headers', {}).get('X-Hook') == 'working'
        
        manager.close()
    
    # def test_get_stats_includes_hooks(self):
    #     """Test that get_stats includes hook information."""
    #     manager = ConnectionManager()
    #     
    #     def test_hook(context):
    #         pass
    #     
    #     manager.register_pre_request_hook(test_hook)
    #     
    #     stats = manager.get_stats()
    #     
    #     assert 'registered_hooks' in stats
    #     assert 'pre_request' in stats['registered_hooks']
    #     assert 'test_hook' in stats['registered_hooks']['pre_request']
    #     
    #     manager.close()
