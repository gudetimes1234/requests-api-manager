
# Authentication

`requests-connection-manager` supports multiple authentication methods that can be applied globally or per-endpoint.

## API Key Authentication

### Global API Key

```python
from requests_connection_manager import ConnectionManager

# Default header (X-API-Key)
manager = ConnectionManager(api_key="your-api-key")

# Custom header
manager = ConnectionManager(
    api_key="your-api-key",
    api_key_header="Authorization"
)

with manager:
    response = manager.get('https://api.example.com/data')
    # X-API-Key: your-api-key header automatically added
```

### Setting API Key After Initialization

```python
manager = ConnectionManager()
manager.set_api_key("new-api-key", "X-Custom-Key")

with manager:
    response = manager.get('https://api.example.com/data')
```

## Bearer Token Authentication

### Global Bearer Token

```python
manager = ConnectionManager(bearer_token="your-bearer-token")

with manager:
    response = manager.get('https://api.example.com/protected')
    # Authorization: Bearer your-bearer-token header automatically added
```

### Setting Bearer Token After Initialization

```python
manager = ConnectionManager()
manager.set_bearer_token("new-bearer-token")

with manager:
    response = manager.get('https://api.example.com/data')
```

## OAuth2 Token Authentication

OAuth2 tokens are handled the same way as Bearer tokens:

```python
# Global OAuth2 token
manager = ConnectionManager(oauth2_token="your-oauth2-token")

# Set after initialization
manager = ConnectionManager()
manager.set_oauth2_token("new-oauth2-token")

with manager:
    response = manager.get('https://api.example.com/oauth-protected')
    # Authorization: Bearer your-oauth2-token header automatically added
```

## Basic Authentication

### Global Basic Auth

```python
manager = ConnectionManager(basic_auth=("username", "password"))

with manager:
    response = manager.get('https://api.example.com/basic-protected')
    # Authorization: Basic <base64-encoded-credentials> header automatically added
```

### Setting Basic Auth After Initialization

```python
manager = ConnectionManager()
manager.set_basic_auth("username", "password")

with manager:
    response = manager.get('https://api.example.com/data')
```

## Per-Endpoint Authentication

Configure different authentication for different services:

### Setting Up Endpoint-Specific Auth

```python
manager = ConnectionManager()

# API key for service 1
manager.set_endpoint_auth(
    'api.service1.com', 
    'api_key', 
    api_key='service1-key',
    header_name='X-Service1-Key'
)

# Bearer token for service 2
manager.set_endpoint_auth(
    'api.service2.com',
    'bearer',
    token='service2-bearer-token'
)

# Basic auth for service 3
manager.set_endpoint_auth(
    'api.service3.com',
    'basic',
    username='user',
    password='pass'
)

with manager:
    # Each request uses the appropriate authentication
    response1 = manager.get('https://api.service1.com/data')  # Uses API key
    response2 = manager.get('https://api.service2.com/data')  # Uses Bearer token
    response3 = manager.get('https://api.service3.com/data')  # Uses Basic auth
```

### Endpoint Configuration with Authentication

```python
endpoint_configs = {
    'api.github.com': {
        'bearer_token': 'github-token',
        'timeout': 30,
        'rate_limit_requests': 60,
        'rate_limit_period': 3600  # GitHub allows 60 requests per hour for auth'd users
    },
    'api.twitter.com': {
        'bearer_token': 'twitter-token',
        'timeout': 15,
        'rate_limit_requests': 300,
        'rate_limit_period': 900  # Twitter allows 300 requests per 15 minutes
    },
    'internal-api.company.com': {
        'api_key': 'internal-api-key',
        'api_key_header': 'X-Internal-Key',
        'timeout': 60
    }
}

manager = ConnectionManager(endpoint_configs=endpoint_configs)

with manager:
    # GitHub API request
    response = manager.get('https://api.github.com/user')
    
    # Twitter API request  
    response = manager.get('https://api.twitter.com/2/tweets/search/recent')
    
    # Internal API request
    response = manager.get('https://internal-api.company.com/data')
```

## Manual Authentication

For custom authentication schemes, you can manually add headers:

```python
with ConnectionManager() as manager:
    # Custom authentication header
    headers = {
        'X-Custom-Auth': 'custom-auth-token',
        'X-Client-Version': '2.0'
    }
    response = manager.get('https://api.example.com/data', headers=headers)
    
    # JWT token
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    headers = {'Authorization': f'JWT {jwt_token}'}
    response = manager.get('https://api.example.com/jwt-protected', headers=headers)
```

## Authentication Priority

When multiple authentication methods are configured, the priority is:

1. **Request-level headers** (highest priority)
2. **Endpoint-specific authentication**
3. **Global authentication** (lowest priority)

```python
manager = ConnectionManager(
    bearer_token="global-token"  # Global auth
)

# Endpoint-specific auth overrides global
manager.set_endpoint_auth('api.service.com', 'api_key', api_key='endpoint-key')

with manager:
    # Uses endpoint-specific API key
    response1 = manager.get('https://api.service.com/data')
    
    # Request-level auth overrides everything
    headers = {'Authorization': 'Bearer request-level-token'}
    response2 = manager.get('https://api.service.com/data', headers=headers)
    
    # Uses global bearer token
    response3 = manager.get('https://other-api.com/data')
```

## Clearing Authentication

### Clear Global Authentication

```python
manager = ConnectionManager(bearer_token="some-token")
manager.clear_auth()  # Removes global authentication

with manager:
    # No authentication headers added
    response = manager.get('https://api.example.com/data')
```

### Clear Endpoint-Specific Authentication

```python
manager = ConnectionManager()
manager.set_endpoint_auth('api.service.com', 'bearer', token='service-token')

# Clear auth for specific endpoint
manager.clear_auth('api.service.com')

with manager:
    # No authentication for this endpoint
    response = manager.get('https://api.service.com/data')
```

## Authentication with Async

All authentication methods work the same with `AsyncConnectionManager`:

```python
import asyncio
from requests_connection_manager import AsyncConnectionManager

async def main():
    manager = AsyncConnectionManager(
        bearer_token="async-bearer-token"
    )
    
    async with manager:
        response = await manager.get('https://api.example.com/async-data')
        print(f"Status: {response.status_code}")

asyncio.run(main())
```

## Real-World Examples

### GitHub API

```python
manager = ConnectionManager(
    bearer_token="ghp_your_github_token",
    rate_limit_requests=60,
    rate_limit_period=3600  # GitHub rate limit
)

with manager:
    # Get user info
    response = manager.get('https://api.github.com/user')
    user = response.json()
    print(f"Hello, {user['name']}")
    
    # Get repositories
    response = manager.get('https://api.github.com/user/repos')
    repos = response.json()
    print(f"You have {len(repos)} repositories")
```

### Multiple APIs with Different Auth

```python
manager = ConnectionManager()

# Set up authentication for different services
configs = {
    'api.github.com': {
        'bearer_token': 'github_token',
        'rate_limit_requests': 60,
        'rate_limit_period': 3600
    },
    'api.openai.com': {
        'bearer_token': 'openai_api_key',
        'rate_limit_requests': 20,
        'rate_limit_period': 60
    },
    'internal.company.com': {
        'api_key': 'internal_key',
        'api_key_header': 'X-Company-Key'
    }
}

manager = ConnectionManager(endpoint_configs=configs)

with manager:
    # GitHub API
    github_response = manager.get('https://api.github.com/user')
    
    # OpenAI API
    openai_response = manager.post(
        'https://api.openai.com/v1/chat/completions',
        json={
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': 'Hello!'}]
        }
    )
    
    # Internal API
    internal_response = manager.get('https://internal.company.com/data')
```

## Security Best Practices

### Environment Variables

Store sensitive credentials in environment variables:

```python
import os
from requests_connection_manager import ConnectionManager

manager = ConnectionManager(
    api_key=os.getenv('API_KEY'),
    bearer_token=os.getenv('BEARER_TOKEN')
)
```

### Credential Rotation

Update credentials without recreating the manager:

```python
manager = ConnectionManager()

def update_credentials():
    new_token = fetch_new_token()  # Your token refresh logic
    manager.set_bearer_token(new_token)

# Periodically update credentials
update_credentials()
```

### Secure Logging

The library automatically redacts sensitive information from logs:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

manager = ConnectionManager(api_key="secret-key")

with manager:
    # API key will be shown as [REDACTED] in logs
    response = manager.get('https://api.example.com/data')
```

## Next Steps

- [Advanced Configuration](advanced.md) - SSL, timeouts, and custom settings
- [Endpoint Configuration](endpoints.md) - Per-service configurations
- [Examples](../examples/authentication.md) - More authentication examples
