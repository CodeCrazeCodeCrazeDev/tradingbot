"""
Elite Trading Bot - Connectivity Module Demo

This example demonstrates how to use the connectivity module to access financial data,
perform web scraping, and use real-time websocket connections.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import trading_bot modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trading_bot.connectivity.web_client import WebClient, RequestMethod
from trading_bot.connectivity.api_client import APIClient, AlphaVantageClient, YahooFinanceClient
from trading_bot.connectivity.websocket_client import WebsocketClient, BinanceWebsocketClient
from trading_bot.connectivity.auth_manager import AuthManager
from trading_bot.connectivity.rate_limiter import RateLimiter, create_common_rate_limiter
from trading_bot.connectivity.proxy_manager import ProxyManager
from trading_bot.connectivity.cache_manager import CacheManager
from trading_bot.connectivity.web_scraper import WebScraper, FinancialNewsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_web_client():
    pass
    """Demonstrate WebClient functionality."""
    logger.info("=== WebClient Demo ===")
    
    # Create web client
    client = WebClient()
    
    # Make a simple GET request
    response = await client.async_get("https://httpbin.org/get")
    data = await response.json()
    logger.info(f"GET response: {json.dumps(data, indent=2)[:200]}...")
    
    # Make a POST request with JSON data
    response = await client.async_post(
        "https://httpbin.org/post",
        json_data={"message": "Hello from Elite Trading Bot!"}
    )
    data = await response.json()
    logger.info(f"POST response: {json.dumps(data, indent=2)[:200]}...")
    
    # Close client
    await client.async_close()


async def demo_api_client():
    pass
    """Demonstrate APIClient functionality."""
    logger.info("=== APIClient Demo ===")
    
    # Create API client
    api_client = APIClient(
        base_url="https://httpbin.org",
        api_name="httpbin"
    )
    
    # Make a request
    data = await api_client.request("get", RequestMethod.GET)
    logger.info(f"API response: {json.dumps(data, indent=2)[:200]}...")
    
    # Close client
    await api_client.close()
    
    # Demo with Alpha Vantage (if API key available)
    alpha_vantage_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if alpha_vantage_key:
    pass
        logger.info("=== Alpha Vantage Demo ===")
        
        # Create Alpha Vantage client
        alpha_client = AlphaVantageClient(api_key=alpha_vantage_key)
        
        # Get stock data
        stock_data = await alpha_client.get_market_data("AAPL")
        logger.info(f"AAPL data: {json.dumps(stock_data, indent=2)[:200]}...")
        
        # Close client
        await alpha_client.close()
    else:
    pass
        logger.info("Skipping Alpha Vantage demo (no API key)")


async def demo_websocket_client():
    pass
    """Demonstrate WebsocketClient functionality."""
    logger.info("=== WebsocketClient Demo ===")
    
    # Create a simple message handler
    def message_handler(message):
    pass
        logger.info(f"Received message: {json.dumps(message, indent=2)[:200]}...")
    
    # Create Binance websocket client
    binance_client = BinanceWebsocketClient()
    
    # Add message handler
    binance_client.add_default_handler(message_handler)
    
    # Connect to websocket
    connected = await binance_client.connect()
    
    if connected:
    pass
        logger.info("Connected to Binance websocket")
        
        # Subscribe to BTC/USDT ticker
        await binance_client.subscribe_ticker("btcusdt")
        
        # Wait for some messages
        logger.info("Waiting for messages (10 seconds)...")
        await asyncio.sleep(10)
        
        # Disconnect
        await binance_client.disconnect()
        logger.info("Disconnected from Binance websocket")
    else:
    pass
        logger.error("Failed to connect to Binance websocket")


async def demo_auth_manager():
    pass
    """Demonstrate AuthManager functionality."""
    logger.info("=== AuthManager Demo ===")
    
    # Create temporary directory for credentials
    import tempfile
    temp_dir = tempfile.mkdtemp()
    creds_path = os.path.join(temp_dir, "credentials.json")
    
    # Create auth manager
    auth_manager = AuthManager(config_path=creds_path)
    
    # Add API key
    auth_manager.add_api_key("demo_service", "demo_api_key", "demo_api_secret")
    logger.info("Added API key for demo_service")
    
    # Get API key
    api_key = auth_manager.get_api_key("demo_service")
    logger.info(f"Retrieved API key: {api_key}")
    
    # Get auth headers
    headers = await auth_manager.get_auth_headers("demo_service")
    logger.info(f"Auth headers: {headers}")
    
    # Generate signature
    signature = auth_manager.generate_signature("demo_service", "test_payload")
    logger.info(f"Generated signature: {signature}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir)


async def demo_rate_limiter():
    pass
    """Demonstrate RateLimiter functionality."""
    logger.info("=== RateLimiter Demo ===")
    
    # Create rate limiter
    rate_limiter = create_common_rate_limiter()
    
    # Add custom rate limit
    rate_limiter.add_service_limit("custom_api", 2, 5)  # 2 req/s, burst of 5
    
    # Demonstrate rate limiting
    logger.info("Making 10 requests with rate limiting...")
    
    for i in range(10):
    pass
        start_time = asyncio.get_event_loop().time()
        
        # Acquire permission
        wait_time = await rate_limiter.acquire("custom_api")
        
        end_time = asyncio.get_event_loop().time()
        actual_wait = end_time - start_time
        
        logger.info(f"Request {i+1}: waited {actual_wait:.2f}s")
    
    # Get stats
    stats = rate_limiter.get_stats()
    logger.info(f"Rate limiter stats: {stats}")


async def demo_cache_manager():
    pass
    """Demonstrate CacheManager functionality."""
    logger.info("=== CacheManager Demo ===")
    
    # Create temporary directory for disk cache
    temp_dir = tempfile.mkdtemp()
    
    # Create cache manager
    cache_manager = CacheManager(
        memory_cache_size=100,
        disk_cache_dir=temp_dir,
        disk_cache_size_mb=10
    )
    
    # Store some values
    cache_manager.set("key1", "value1", ttl=60)
    cache_manager.set("key2", {"complex": "value", "with": ["nested", "data"]}, ttl=120)
    logger.info("Stored values in cache")
    
    # Retrieve values
    value1 = cache_manager.get("key1")
    value2 = cache_manager.get("key2")
    logger.info(f"Retrieved values: {value1}, {value2}")
    
    # Demonstrate cache decorator
    @cache_manager.cached(ttl=60)
    def expensive_calculation(x, y):
    pass
        logger.info(f"Performing expensive calculation for {x} + {y}")
        return x + y
    
    # Call function twice, should only calculate once
    result1 = expensive_calculation(5, 10)
    result2 = expensive_calculation(5, 10)
    logger.info(f"Calculation results: {result1}, {result2}")
    
    # Get cache stats
    stats = cache_manager.get_stats()
    logger.info(f"Cache stats: {stats}")
    
    # Clean up
    shutil.rmtree(temp_dir)


async def demo_web_scraper():
    pass
    """Demonstrate WebScraper functionality."""
    logger.info("=== WebScraper Demo ===")
    
    # Create web scraper
    scraper = WebScraper()
    
    # Scrape a simple page
    result = await scraper.scrape_url("https://httpbin.org/html")
    logger.info(f"Scraped content title: {result.get('title', 'No title')}")
    
    # Create financial news scraper
    financial_scraper = FinancialNewsScraper()
    
    # Analyze market sentiment (limited to avoid overloading websites)
    logger.info("Analyzing market sentiment for BTC (limited scope)...")
    sentiment = await financial_scraper.analyze_market_sentiment(
        symbols=["BTC"],
        sources=["https://www.coindesk.com"]
    )
    
    if "BTC" in sentiment:
    pass
        logger.info(f"BTC sentiment: {sentiment['BTC']['sentiment']}")
        logger.info(f"Found {sentiment['BTC']['article_count']} articles")


async def demo_integrated_usage():
    pass
    """Demonstrate integrated usage of all components."""
    logger.info("=== Integrated Usage Demo ===")
    
    # Create components
    auth_manager = AuthManager()
    rate_limiter = create_common_rate_limiter()
    cache_manager = CacheManager()
    
    # Add demo API key
    auth_manager.add_api_key("demo_api", "demo_key", "demo_secret")
    
    # Create API client with all components
    api_client = APIClient(
        base_url="https://httpbin.org",
        api_name="demo_api",
        auth_manager=auth_manager,
        rate_limiter=rate_limiter
    )
    
    # Create a cached API request function
    @cache_manager.cached(ttl=60, key_prefix="demo_api")
    async def get_api_data(endpoint):
    pass
        return await api_client.request(endpoint)
    
    # Make cached API requests
    logger.info("Making first API request (will be a cache miss)...")
    data1 = await get_api_data("get")
    
    logger.info("Making second API request (should be a cache hit)...")
    data2 = await get_api_data("get")
    
    # Check cache stats
    stats = cache_manager.get_stats()
    logger.info(f"Cache stats after requests: {stats}")
    
    # Close client
    await api_client.close()


async def main():
    pass
    """Run all demos."""
    logger.info("Starting Elite Trading Bot Connectivity Module Demo")
    
    try:
    pass
        # Run individual demos
        await demo_web_client()
        await demo_api_client()
        await demo_websocket_client()
        await demo_auth_manager()
        await demo_rate_limiter()
        await demo_cache_manager()
        await demo_web_scraper()
        
        # Run integrated demo
        await demo_integrated_usage()
        
    except Exception as e:
    pass
        logger.error(f"Error in demo: {str(e)}", exc_info=True)
    
    logger.info("Demo completed")


if __name__ == "__main__":
    pass
    # Run the async main function
    asyncio.run(main())
