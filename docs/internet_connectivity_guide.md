# Elite Trading Bot - Internet Connectivity Guide

This guide provides comprehensive documentation for the internet connectivity features of the Elite Trading Bot, enabling real-time market data access, news sentiment analysis, and external API integration.

## Table of Contents

1. [Overview](#overview)
2. [Components](#components)
3. [Command-Line Usage](#command-line-usage)
4. [Configuration](#configuration)
5. [API Integration](#api-integration)
6. [WebSocket Streaming](#websocket-streaming)
7. [News and Sentiment Analysis](#news-and-sentiment-analysis)
8. [Caching and Performance](#caching-and-performance)
9. [Security Considerations](#security-considerations)
10. [Advanced Usage](#advanced-usage)
11. [Troubleshooting](#troubleshooting)

## Overview

The internet connectivity module enables the Elite Trading Bot to access real-time market data, financial news, and external APIs, enhancing its decision-making capabilities with up-to-date information. The system is designed with security, performance, and reliability in mind, featuring robust error handling, rate limiting, and caching mechanisms.

Key features include:
- Real-time market data from multiple providers (Alpha Vantage, Yahoo Finance, Binance)
- WebSocket connections for live price updates
- Financial news scraping and sentiment analysis
- Secure API key management
- Rate limiting to comply with API restrictions
- Proxy support with IP rotation
- Efficient data caching to minimize requests

## Components

The internet connectivity module consists of the following components:

### 1. Web Client (`web_client.py`)
- Core HTTP client with synchronous and asynchronous request support
- Robust error handling and retry mechanisms
- SSL/TLS security with certificate verification

### 2. API Client (`api_client.py`)
- Specialized clients for financial data providers
- Implementations for Alpha Vantage, Yahoo Finance, and cryptocurrency exchanges
- Standardized interface for market data retrieval

### 3. WebSocket Client (`websocket_client.py`)
- Real-time data streaming via WebSockets
- Automatic reconnection with exponential backoff
- Subscription management for multiple data feeds

### 4. Authentication Manager (`auth_manager.py`)
- Secure storage and management of API keys
- Support for various authentication methods
- Encryption of sensitive credentials

### 5. Rate Limiter (`rate_limiter.py`)
- Token bucket and sliding window rate limiting algorithms
- Preconfigured limits for common financial APIs
- Automatic waiting for rate limit compliance

### 6. Proxy Manager (`proxy_manager.py`)
- Proxy server management with health monitoring
- Automatic IP rotation to avoid rate limits and bans
- Support for authenticated proxies

### 7. Cache Manager (`cache_manager.py`)
- Multi-level caching (memory and disk)
- Automatic expiration of cached data
- Function result caching with decorators

### 8. Web Scraper (`web_scraper.py`)
- Financial news scraping with sentiment analysis
- Respect for robots.txt and ethical scraping practices
- NLTK integration for sentiment scoring

## Command-Line Usage

The internet connectivity features can be enabled and configured via command-line arguments:

```bash
# Enable internet access with Yahoo Finance as the data source
python main.py --symbol AAPL --internet-access --api-source yahoo

# Enable WebSocket feed for real-time data
python main.py --symbol BTCUSDT --internet-access --api-source binance --websocket-feed

# Enable news scraping for sentiment analysis
python main.py --symbol AAPL --internet-access --news-scraping

# Enable caching to improve performance
python main.py --symbol AAPL --internet-access --cache-dir ./cache

# Use API keys from a configuration file
python main.py --symbol AAPL --internet-access --api-keys-file ./config/api_keys.json

# Full example with all features
python main.py --symbol AAPL --timeframe H1 --bars 500 --mode paper --use-ml \
  --internet-access --api-source all --websocket-feed --news-scraping \
  --cache-dir ./cache --api-keys-file ./config/api_keys.json
```

## Configuration

### API Keys Configuration

Create a JSON file to store your API keys securely:

```json
{
  "alpha_vantage": {
    "api_key": "YOUR_ALPHA_VANTAGE_API_KEY"
  },
  "binance": {
    "api_key": "YOUR_BINANCE_API_KEY",
    "api_secret": "YOUR_BINANCE_API_SECRET"
  }
}
```

Alternatively, you can set environment variables:

```bash
export ETB_ALPHA_VANTAGE_API_KEY=YOUR_ALPHA_VANTAGE_API_KEY
export ETB_BINANCE_API_KEY=YOUR_BINANCE_API_KEY
export ETB_BINANCE_API_SECRET=YOUR_BINANCE_API_SECRET
```

### Adaptive System Configuration

To enable internet connectivity in the adaptive trading system, add the following to your `adaptive_config.yaml`:

```yaml
connectivity:
  enabled: true
  components:
    api_client: true
    websocket_client: true
    web_scraper: true
    cache_manager: true
  settings:
    cache_dir: "./cache"
    rate_limiting: true
    proxy_enabled: false
```

## API Integration

### Available Data Providers

The Elite Trading Bot supports the following data providers:

1. **Alpha Vantage**
   - Stock, forex, and cryptocurrency data
   - Economic indicators and technical indicators
   - Requires API key (free tier available)

2. **Yahoo Finance**
   - Stock, ETF, and index data
   - Historical OHLCV data
   - No API key required

3. **Binance**
   - Cryptocurrency market data
   - Order book and trade data
   - API key required for private endpoints

### Example: Retrieving Market Data

```python
from trading_bot.connectivity.api_client import AlphaVantageClient

async def get_stock_data():
    # Create Alpha Vantage client
    client = AlphaVantageClient(api_key="YOUR_API_KEY")
    
    # Get daily stock data
    data = await client.get_market_data("AAPL", timeframe="daily")
    
    # Close client
    await client.close()
    
    return data
```

## WebSocket Streaming

### Available WebSocket Feeds

The Elite Trading Bot supports WebSocket streaming from:

1. **Binance**
   - Real-time ticker updates
   - Candlestick (kline) updates
   - Order book updates
   - Trade updates

### Example: Subscribing to WebSocket Feed

```python
from trading_bot.connectivity.websocket_client import BinanceWebsocketClient

async def stream_crypto_data():
    # Create message handler
    def message_handler(message):
        print(f"Received: {message}")
    
    # Create Binance WebSocket client
    client = BinanceWebsocketClient()
    
    # Add message handler
    client.add_default_handler(message_handler)
    
    # Connect to WebSocket
    await client.connect()
    
    # Subscribe to ticker updates
    await client.subscribe_ticker("btcusdt")
    
    # Keep connection open
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await client.disconnect()
```

## News and Sentiment Analysis

The web scraper component enables the bot to gather financial news and perform sentiment analysis to inform trading decisions.

### Example: Analyzing Market Sentiment

```python
from trading_bot.connectivity.web_scraper import FinancialNewsScraper

async def analyze_sentiment():
    # Create financial news scraper
    scraper = FinancialNewsScraper()
    
    # Analyze sentiment for a symbol
    sentiment = await scraper.analyze_market_sentiment(
        symbols=["AAPL"],
        sources=["https://www.cnbc.com/markets"]
    )
    
    return sentiment
```

## Caching and Performance

The cache manager provides efficient data caching to minimize API requests and improve performance.

### Example: Using the Cache Decorator

```python
from trading_bot.connectivity.cache_manager import CacheManager

# Create cache manager
cache_manager = CacheManager(
    memory_cache_size=1000,
    disk_cache_dir="./cache",
    disk_cache_size_mb=100
)

# Cache function results
@cache_manager.cached(ttl=3600)  # Cache for 1 hour
async def get_market_data(symbol):
    # This function will only execute once per hour per symbol
    # Results will be cached and returned for subsequent calls
    # ...
    return data
```

## Security Considerations

### API Key Security

- API keys are stored securely using encryption
- Keys can be stored in environment variables or a secure configuration file
- The authentication manager never logs or exposes sensitive credentials

### Network Security

- All HTTP requests use SSL/TLS encryption
- Certificate verification is enabled by default
- Proxy support for additional security and anonymity

### Best Practices

1. Use environment variables for API keys in production
2. Regularly rotate API keys
3. Use the rate limiter to avoid API bans
4. Enable caching to minimize API requests
5. Monitor API usage and costs

## Advanced Usage

### Custom API Client Implementation

You can create custom API clients for additional data providers:

```python
from trading_bot.connectivity.api_client import APIClient

class CustomDataProviderClient(APIClient):
    def __init__(self, api_key, **kwargs):
        super().__init__(
            base_url="https://api.customprovider.com",
            api_name="custom_provider",
            **kwargs
        )
        self.api_key = api_key
    
    async def get_market_data(self, symbol, timeframe="daily"):
        # Implement custom logic for this provider
        params = {
            "symbol": symbol,
            "interval": timeframe,
            "apikey": self.api_key
        }
        
        return await self.request("market_data", params=params)
```

### Proxy Rotation

For intensive data collection, you can use proxy rotation:

```python
from trading_bot.connectivity.proxy_manager import ProxyManager
from trading_bot.connectivity.web_client import WebClient

# Initialize proxy manager with a list of proxies
proxy_manager = ProxyManager(proxies=[
    {"host": "proxy1.example.com", "port": 8080},
    {"host": "proxy2.example.com", "port": 8080}
])

# Create web client with proxy support
client = WebClient(proxies=proxy_manager.get_proxy_for_requests())

# If a request fails, rotate to a new proxy
try:
    response = client.get("https://api.example.com/data")
except Exception:
    proxy_manager.mark_current_proxy_failed()
    client.proxies = proxy_manager.get_proxy_for_requests()
    response = client.get("https://api.example.com/data")
```

## Troubleshooting

### Common Issues

1. **API Rate Limits**
   - Error: "Rate limit exceeded"
   - Solution: Use the rate limiter and increase wait times between requests

2. **Authentication Failures**
   - Error: "Invalid API key" or "Unauthorized"
   - Solution: Verify API keys and check if they have expired or been revoked

3. **Network Connectivity**
   - Error: "Connection timeout" or "Network error"
   - Solution: Check internet connection and proxy settings

4. **WebSocket Disconnections**
   - Issue: Frequent disconnections from WebSocket feeds
   - Solution: The WebSocket client automatically reconnects with exponential backoff

### Logging

The internet connectivity module uses the `loguru` logger for comprehensive logging. To enable debug logging:

```python
from loguru import logger

# Set debug level for connectivity components
logger.add("connectivity.log", filter=lambda record: "trading_bot.connectivity" in record["name"], level="DEBUG")
```

### Support

For additional support or to report issues, please refer to the project's GitHub repository or contact the development team.

---

This documentation provides a comprehensive guide to the internet connectivity features of the Elite Trading Bot. For more information on other aspects of the bot, please refer to the main documentation.
