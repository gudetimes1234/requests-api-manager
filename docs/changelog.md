
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-28

### Added

#### Core Features
- **ConnectionManager class** with connection pooling, retries, rate limiting, and circuit breaker functionality
- **AsyncConnectionManager class** for async/await support using httpx
- **Automatic retries** with exponential backoff for failed requests
- **Rate limiting** with configurable requests per time period
- **Circuit breaker** pattern to handle service failures gracefully
- **Connection pooling** for efficient connection reuse

#### Authentication Support
- **API key authentication** with configurable header names
- **Bearer token authentication** for OAuth2 and similar schemes
- **Basic authentication** with username/password
- **Per-endpoint authentication** configuration
- **Global and endpoint-specific** authentication methods

#### Advanced Configuration
- **SSL certificate verification** with custom CA bundles
- **Client certificates** for mutual TLS authentication
- **Fine-grained timeouts** (separate connect and read timeouts)
- **Custom SSL contexts** for advanced SSL configuration
- **Per-endpoint configuration** for different services

#### Request Features
- **Batch requests** with controlled parallelism
- **Thread-safe** operations for multi-threaded applications
- **Context manager** support for automatic resource cleanup
- **All HTTP methods** supported (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)

#### Plugin System
- **Extensible plugin architecture** with pre-request, post-response, and error hooks
- **Request/response modification** capabilities
- **Error handling and fallback** mechanisms
- **Hook registration and management**

#### Monitoring and Utilities
- **Statistics and monitoring** with get_stats() method
- **Secure logging** with automatic redaction of sensitive data
- **Comprehensive error handling** with custom exceptions
- **Performance optimizations** for high-throughput scenarios

#### Developer Experience
- **Comprehensive documentation** with examples
- **Type hints** throughout the codebase
- **Full test coverage** with pytest
- **GitHub Actions** for CI/CD
- **Semantic versioning** and changelog management

### Dependencies
- requests (>=2.25.0) - HTTP library for Python
- urllib3 (>=1.26.0) - HTTP client library
- ratelimit (>=2.2.1) - Rate limiting decorator
- pybreaker (>=1.2.0) - Circuit breaker implementation
- httpx (>=0.28.1) - Modern async HTTP client

### Documentation
- Complete API documentation
- Usage examples for all features
- Authentication guides
- Advanced configuration tutorials
- Contributing guidelines
- Installation instructions

## [Unreleased]

### Planned Features
- Metrics collection and export
- Request/response caching
- Advanced load balancing
- Distributed rate limiting
- Request replay functionality
- WebSocket support
- gRPC support

---

For the complete history of changes, see the [GitHub releases page](https://github.com/charlesgude/requests-connection-manager/releases).
