
"""
Utility functions for ConnectionManager.
"""

import logging
import re
import json
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

# Sensitive field patterns (case-insensitive)
SENSITIVE_PATTERNS = [
    r'authorization',
    r'api[_-]?key',
    r'auth[_-]?token',
    r'bearer[_-]?token',
    r'oauth[_-]?token',
    r'x-api-key',
    r'x-auth-token',
    r'access[_-]?token',
    r'refresh[_-]?token',
    r'secret',
    r'password',
    r'passwd',
    r'pwd',
    r'private[_-]?key',
    r'session[_-]?id',
    r'csrf[_-]?token',
    r'jwt'
]

def is_sensitive_field(field_name: str) -> bool:
    """
    Check if a field name contains sensitive information.
    
    Args:
        field_name: The field name to check
        
    Returns:
        True if the field is sensitive, False otherwise
    """
    field_lower = field_name.lower()
    return any(re.search(pattern, field_lower) for pattern in SENSITIVE_PATTERNS)

def redact_sensitive_data(data: Union[Dict[str, Any], str], redaction_text: str = "[REDACTED]") -> Union[Dict[str, Any], str]:
    """
    Redact sensitive information from data structures.
    
    Args:
        data: Dictionary or string to redact sensitive information from
        redaction_text: Text to replace sensitive values with
        
    Returns:
        Data with sensitive fields redacted
    """
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            if is_sensitive_field(key):
                redacted[key] = redaction_text
            elif isinstance(value, dict):
                redacted[key] = redact_sensitive_data(value, redaction_text)
            elif isinstance(value, list):
                redacted[key] = [
                    redact_sensitive_data(item, redaction_text) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted[key] = value
        return redacted
    elif isinstance(data, str):
        # Try to parse as JSON and redact if possible
        try:
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                redacted_dict = redact_sensitive_data(parsed, redaction_text)
                return json.dumps(redacted_dict)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # For non-JSON strings, redact common patterns
        redacted_str = data
        for pattern in SENSITIVE_PATTERNS:
            # Match patterns like "Authorization: Bearer token123"
            auth_pattern = fr'({pattern})\s*[:=]\s*["\']?([^"\'\s,}}]+)["\']?'
            redacted_str = re.sub(auth_pattern, fr'\1: {redaction_text}', redacted_str, flags=re.IGNORECASE)
        
        return redacted_str
    
    return data

def safe_log_request(method: str, url: str, headers: Dict[str, str] = None, payload: Any = None, level: int = logging.DEBUG):
    """
    Safely log request information with sensitive data redacted.
    
    Args:
        method: HTTP method
        url: Request URL
        headers: Request headers
        payload: Request payload
        level: Logging level
    """
    # Redact sensitive information from headers
    safe_headers = redact_sensitive_data(headers or {})
    
    # Log basic request info
    logger.log(level, f"Making {method} request to {url}")
    
    if safe_headers:
        logger.log(level, f"Request headers: {safe_headers}")
    
    if payload:
        # Redact sensitive information from payload
        safe_payload = redact_sensitive_data(payload)
        if isinstance(safe_payload, dict):
            logger.log(level, f"Request payload: {json.dumps(safe_payload, indent=2)}")
        else:
            logger.log(level, f"Request payload: {safe_payload}")

def safe_log_response(response, level: int = logging.DEBUG):
    """
    Safely log response information with sensitive data redacted.
    
    Args:
        response: Response object
        level: Logging level
    """
    try:
        # Log basic response info
        logger.log(level, f"Response status: {response.status_code}")
        
        # Redact sensitive headers
        if hasattr(response, 'headers'):
            safe_headers = redact_sensitive_data(dict(response.headers))
            logger.log(level, f"Response headers: {safe_headers}")
        
        # Try to log response body if it's JSON and not too large
        if hasattr(response, 'text') and response.text:
            try:
                if len(response.text) < 1000:  # Only log small responses
                    response_data = response.json() if hasattr(response, 'json') else response.text
                    safe_response = redact_sensitive_data(response_data)
                    if isinstance(safe_response, dict):
                        logger.log(level, f"Response body: {json.dumps(safe_response, indent=2)}")
                    else:
                        logger.log(level, f"Response body: {safe_response}")
                else:
                    logger.log(level, f"Response body length: {len(response.text)} characters (too large to log)")
            except (json.JSONDecodeError, AttributeError):
                # If not JSON, log first 200 characters
                preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
                safe_preview = redact_sensitive_data(preview)
                logger.log(level, f"Response body preview: {safe_preview}")
                
    except Exception as e:
        logger.warning(f"Error logging response safely: {e}")

def safe_log_error(exception: Exception, method: str, url: str, level: int = logging.ERROR):
    """
    Safely log error information with sensitive data redacted.
    
    Args:
        exception: Exception that occurred
        method: HTTP method
        url: Request URL (will be checked for sensitive info)
        level: Logging level
    """
    # Redact sensitive info from URL (like API keys in query params)
    safe_url = redact_sensitive_data(url) if isinstance(url, str) else url
    
    logger.log(level, f"Request failed: {method} {safe_url} - {type(exception).__name__}: {str(exception)}")
