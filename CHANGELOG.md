
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Secure logging functionality that redacts sensitive information
- Advanced connection options (custom CA bundles, client certificates)
- Fine-grained timeout controls (connect/read timeouts)
- Authentication support (API keys, Bearer tokens, OAuth2, Basic auth)
- Batch request functionality with controlled parallelism
- Plugin system with pre/post request hooks
- Async support with AsyncConnectionManager
- Per-endpoint configuration capabilities
- Dynamic endpoint configuration management

### Changed
- Refactored to use external libraries (ratelimit, pybreaker) for better reliability
- Improved error handling and custom exceptions
- Enhanced thread safety for multi-threaded applications

### Fixed
- Connection pooling efficiency improvements
- Rate limiting accuracy enhancements

## [1.0.0] - 2024-12-28

### Added
- Initial release of requests-connection-manager
- Connection pooling with configurable pool sizes
- Automatic retries with exponential backoff
- Rate limiting with configurable thresholds
- Circuit breaker pattern for fail-fast behavior
- Thread-safe operations
- Drop-in replacement for requests library
- Comprehensive test suite
- Full documentation and examples

### Dependencies
- requests >= 2.25.0
- urllib3 >= 1.26.0
- ratelimit >= 2.2.1
- pybreaker >= 1.2.0
- httpx >= 0.28.1

[Unreleased]: https://github.com/charlesgude/requests-connection-manager/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/charlesgude/requests-connection-manager/releases/tag/v1.0.0
