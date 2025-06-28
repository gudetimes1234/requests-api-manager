
"""
Examples demonstrating advanced connection options for ConnectionManager.
"""

import ssl
from requests_connection_manager import ConnectionManager, AsyncConnectionManager


def ssl_verification_examples():
    """Examples of SSL certificate verification options."""
    print("=== SSL Verification Examples ===")
    
    # Default SSL verification (uses system CA bundle)
    manager1 = ConnectionManager()
    
    # Disable SSL verification (not recommended for production)
    manager2 = ConnectionManager(verify=False)
    
    # Use custom CA bundle
    manager3 = ConnectionManager(verify="/path/to/custom/ca-bundle.pem")
    
    # Update SSL verification after initialization
    manager4 = ConnectionManager()
    manager4.set_ssl_verification("/path/to/company-ca-bundle.pem")
    
    try:
        # These would use different SSL verification settings
        response1 = manager1.get('https://httpbin.org/get')  # Default verification
        response2 = manager2.get('https://httpbin.org/get')  # No verification
        response3 = manager3.get('https://internal-api.company.com/data')  # Custom CA
        
        print(f"Default SSL: {response1.status_code}")
        print(f"No SSL verification: {response2.status_code}")
        print(f"Custom CA: {response3.status_code}")
        
    except Exception as e:
        print(f"SSL verification example failed: {e}")
    
    finally:
        manager1.close()
        manager2.close()
        manager3.close()
        manager4.close()


def client_certificate_examples():
    """Examples of client certificate authentication."""
    print("\n=== Client Certificate Examples ===")
    
    # Client certificate from single file (contains both cert and key)
    manager1 = ConnectionManager(cert="/path/to/client.pem")
    
    # Client certificate with separate cert and key files
    manager2 = ConnectionManager(cert=("/path/to/client.crt", "/path/to/client.key"))
    
    # Set client certificate after initialization
    manager3 = ConnectionManager()
    manager3.set_client_certificate(("/path/to/client.crt", "/path/to/client.key"))
    
    try:
        # These would use client certificate authentication
        response1 = manager1.get('https://secure-api.example.com/protected')
        response2 = manager2.get('https://mutual-tls.example.com/data')
        
        print(f"Client cert (single file): {response1.status_code}")
        print(f"Client cert (separate files): {response2.status_code}")
        
    except Exception as e:
        print(f"Client certificate example failed: {e}")
    
    finally:
        manager1.close()
        manager2.close()
        manager3.close()


def fine_grained_timeout_examples():
    """Examples of fine-grained timeout configuration."""
    print("\n=== Fine-Grained Timeout Examples ===")
    
    # Separate connect and read timeouts
    manager1 = ConnectionManager(
        connect_timeout=5.0,  # 5 seconds to establish connection
        read_timeout=30.0     # 30 seconds to read response
    )
    
    # Default timeout with custom connect timeout
    manager2 = ConnectionManager(
        timeout=15,
        connect_timeout=3.0
    )
    
    # Update timeouts after initialization
    manager3 = ConnectionManager()
    manager3.set_timeouts(connect_timeout=2.0, read_timeout=10.0)
    
    try:
        # These requests use different timeout configurations
        response1 = manager1.get('https://httpbin.org/delay/2')
        response2 = manager2.get('https://httpbin.org/delay/1')
        response3 = manager3.get('https://httpbin.org/delay/1')
        
        print(f"Fine-grained timeouts: {response1.status_code}")
        print(f"Mixed timeout config: {response2.status_code}")
        print(f"Updated timeouts: {response3.status_code}")
        
    except Exception as e:
        print(f"Timeout examples failed: {e}")
    
    finally:
        manager1.close()
        manager2.close()
        manager3.close()


def ssl_context_examples():
    """Examples of custom SSL context configuration."""
    print("\n=== SSL Context Examples ===")
    
    # Create custom SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Use custom SSL context
    manager1 = ConnectionManager(ssl_context=ssl_context)
    
    # Create SSL context with specific protocol version
    ssl_context_tls12 = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context_tls12.verify_mode = ssl.CERT_REQUIRED
    ssl_context_tls12.check_hostname = True
    ssl_context_tls12.load_default_certs()
    
    manager2 = ConnectionManager()
    manager2.set_ssl_context(ssl_context_tls12)
    
    try:
        # These requests use custom SSL contexts
        response1 = manager1.get('https://httpbin.org/get')
        response2 = manager2.get('https://httpbin.org/get')
        
        print(f"Custom SSL context: {response1.status_code}")
        print(f"TLS 1.2 context: {response2.status_code}")
        
    except Exception as e:
        print(f"SSL context examples failed: {e}")
    
    finally:
        manager1.close()
        manager2.close()


def comprehensive_advanced_config_example():
    """Example combining all advanced connection options."""
    print("\n=== Comprehensive Advanced Configuration Example ===")
    
    # Create SSL context with custom settings
    ssl_context = ssl.create_default_context()
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    
    manager = ConnectionManager(
        # Basic settings
        timeout=30,
        max_retries=3,
        
        # Advanced connection options
        verify="/path/to/custom-ca-bundle.pem",  # Custom CA bundle
        cert=("/path/to/client.crt", "/path/to/client.key"),  # Client certificate
        connect_timeout=5.0,  # 5 second connection timeout
        read_timeout=25.0,    # 25 second read timeout
        ssl_context=ssl_context,  # Custom SSL context
        
        # Authentication
        api_key="your-api-key",
        
        # Endpoint-specific configurations
        endpoint_configs={
            'secure-api.example.com': {
                'verify': '/path/to/secure-api-ca.pem',
                'cert': ('/path/to/secure-api-client.crt', '/path/to/secure-api-client.key'),
                'connect_timeout': 3.0,
                'read_timeout': 60.0
            }
        }
    )
    
    try:
        # Make requests that will use the advanced configuration
        response1 = manager.get('https://httpbin.org/get')
        response2 = manager.get('https://secure-api.example.com/protected-endpoint')
        
        print(f"Advanced config request 1: {response1.status_code}")
        print(f"Advanced config request 2: {response2.status_code}")
        
        # Show configuration stats
        stats = manager.get_stats()
        print(f"SSL verification: {stats['ssl_verification']}")
        print(f"Client cert configured: {stats['client_certificate_configured']}")
        print(f"Connect timeout: {stats['connect_timeout']}s")
        print(f"Read timeout: {stats['read_timeout']}s")
        print(f"SSL context configured: {stats['ssl_context_configured']}")
        
    except Exception as e:
        print(f"Comprehensive example failed: {e}")
    
    finally:
        manager.close()


async def async_advanced_connection_examples():
    """Examples of advanced connection options with AsyncConnectionManager."""
    print("\n=== Async Advanced Connection Examples ===")
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    async with AsyncConnectionManager(
        verify=True,
        cert=("/path/to/client.crt", "/path/to/client.key"),
        connect_timeout=5.0,
        read_timeout=30.0,
        ssl_context=ssl_context
    ) as manager:
        try:
            # Make async requests with advanced configuration
            response1 = await manager.get('https://httpbin.org/get')
            response2 = await manager.get('https://httpbin.org/delay/2')
            
            print(f"Async advanced request 1: {response1.status_code}")
            print(f"Async advanced request 2: {response2.status_code}")
            
            # Show async configuration stats
            stats = manager.get_stats()
            print(f"Async client type: {stats['client_type']}")
            print(f"SSL verification: {stats['ssl_verification']}")
            print(f"Connect timeout: {stats['connect_timeout']}s")
            
        except Exception as e:
            print(f"Async advanced examples failed: {e}")


def endpoint_specific_advanced_config_example():
    """Example of endpoint-specific advanced connection configurations."""
    print("\n=== Endpoint-Specific Advanced Configuration Example ===")
    
    endpoint_configs = {
        'api.bank.com': {
            'verify': '/path/to/bank-ca-bundle.pem',
            'cert': ('/path/to/bank-client.crt', '/path/to/bank-client.key'),
            'connect_timeout': 2.0,
            'read_timeout': 10.0,
            'timeout': 15
        },
        'api.partner.com': {
            'verify': True,  # Use system CA bundle
            'connect_timeout': 5.0,
            'read_timeout': 30.0,
            'bearer_token': 'partner-specific-token'
        },
        'internal.company.com': {
            'verify': False,  # Internal network, skip SSL verification
            'connect_timeout': 1.0,
            'read_timeout': 5.0
        }
    }
    
    manager = ConnectionManager(
        # Default settings
        verify=True,
        connect_timeout=3.0,
        read_timeout=15.0,
        # Endpoint-specific configurations
        endpoint_configs=endpoint_configs
    )
    
    try:
        # Each request will use its endpoint-specific configuration
        response1 = manager.get('https://api.bank.com/accounts')      # Bank-specific SSL config
        response2 = manager.get('https://api.partner.com/data')       # Partner-specific timeouts
        response3 = manager.get('https://internal.company.com/info')  # Internal network config
        response4 = manager.get('https://public-api.example.com/data') # Default config
        
        print(f"Bank API: {response1.status_code}")
        print(f"Partner API: {response2.status_code}")
        print(f"Internal API: {response3.status_code}")
        print(f"Public API: {response4.status_code}")
        
    except Exception as e:
        print(f"Endpoint-specific config example failed: {e}")
    
    finally:
        manager.close()


if __name__ == "__main__":
    ssl_verification_examples()
    client_certificate_examples()
    fine_grained_timeout_examples()
    ssl_context_examples()
    comprehensive_advanced_config_example()
    endpoint_specific_advanced_config_example()
    
    # Run async examples
    import asyncio
    asyncio.run(async_advanced_connection_examples())
