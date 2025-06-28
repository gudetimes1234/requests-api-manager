# requests-connection-manager

A Python package that extends the popular `requests` library with advanced connection management features including connection pooling, automatic retries, rate limiting, and circuit breaker functionality.

## Features

- **Connection Pooling**: Efficient connection reuse with configurable pool sizes
- **Automatic Retries**: Intelligent retry mechanism with exponential backoff
- **Rate Limiting**: Token bucket-based rate limiting to prevent API abuse
- **Circuit Breaker**: Fail-fast pattern to handle service failures gracefully
- **Thread-Safe**: All components are designed for concurrent usage
- **Easy Integration**: Drop-in enhancement for existing `requests` code

## Installation

```bash
pip install requests-connection-manager
