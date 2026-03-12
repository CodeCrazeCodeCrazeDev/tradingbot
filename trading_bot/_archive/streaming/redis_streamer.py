"""
Redis-based real-time data streaming.
High-performance pub/sub for market data distribution.
"""

import json
import asyncio
from typing import Callable, Dict, List, Optional
from loguru import logger

try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Install with: pip install redis[asyncio]")


class RedisStreamer:
    """Redis-based market data streamer."""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, 
                 db: int = 0, password: Optional[str] = None):
        """
        Initialize Redis streamer.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis not available")
        
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.redis = None
        self.pubsub = None
        self.subscribers = {}
        
        logger.info(f"Redis streamer initialized ({host}:{port})")
    
    async def connect(self):
        """Connect to Redis."""
        self.redis = await aioredis.from_url(
            f"redis://{self.host}:{self.port}/{self.db}",
            password=self.password,
            encoding="utf-8",
            decode_responses=True
        )
        
        self.pubsub = self.redis.pubsub()
        logger.success("Connected to Redis")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        
        logger.info("Disconnected from Redis")
    
    async def publish_market_data(self, symbol: str, data: Dict):
        """
        Publish market data to Redis channel.
        
        Args:
            symbol: Trading symbol
            data: Market data dictionary
        """
        if not self.redis:
            await self.connect()
        
        channel = f"market:{symbol}"
        message = json.dumps(data)
        
        await self.redis.publish(channel, message)
    
    async def subscribe_market_data(self, symbols: List[str], 
                                   callback: Callable):
        """
        Subscribe to market data for symbols.
        
        Args:
            symbols: List of symbols to subscribe
            callback: Async callback function for data
        """
        if not self.redis:
            await self.connect()
        
        # Subscribe to channels
        channels = [f"market:{symbol}" for symbol in symbols]
        await self.pubsub.subscribe(*channels)
        
        logger.info(f"Subscribed to {len(symbols)} symbols")
        
        # Listen for messages
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                channel = message['channel']
                symbol = channel.split(':')[1]
                data = json.loads(message['data'])
                
                await callback(symbol, data)
    
    async def publish_signal(self, symbol: str, signal: Dict):
        """Publish trading signal."""
        channel = f"signals:{symbol}"
        message = json.dumps(signal)
        await self.redis.publish(channel, message)
    
    async def cache_data(self, key: str, data: Dict, ttl: int = 300):
        """
        Cache data in Redis with TTL.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
        """
        if not self.redis:
            await self.connect()
        
        await self.redis.setex(key, ttl, json.dumps(data))
    
    async def get_cached_data(self, key: str) -> Optional[Dict]:
        """Get cached data from Redis."""
        if not self.redis:
            await self.connect()
        
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def stream_add(self, stream_name: str, data: Dict) -> str:
        """
        Add entry to Redis stream.
        
        Args:
            stream_name: Name of the stream
            data: Data to add
            
        Returns:
            Entry ID
        """
        if not self.redis:
            await self.connect()
        
        entry_id = await self.redis.xadd(stream_name, data)
        return entry_id
    
    async def stream_read(self, stream_name: str, count: int = 10,
                         block: int = 1000) -> List[Dict]:
        """
        Read from Redis stream.
        
        Args:
            stream_name: Name of the stream
            count: Number of entries to read
            block: Block time in milliseconds
            
        Returns:
            List of entries
        """
        if not self.redis:
            await self.connect()
        
        entries = await self.redis.xread(
            {stream_name: '$'},
            count=count,
            block=block
        )
        
        return entries


class MarketDataDistributor:
    """Distribute market data to multiple consumers via Redis."""
    
    def __init__(self, redis_streamer: RedisStreamer):
        """Initialize distributor."""
        self.streamer = redis_streamer
        self.active_symbols = set()
        
        logger.info("Market data distributor initialized")
    
    async def start_distribution(self, symbols: List[str]):
        """Start distributing data for symbols."""
        self.active_symbols.update(symbols)
        logger.info(f"Started distribution for {len(symbols)} symbols")
    
    async def distribute_tick(self, symbol: str, tick_data: Dict):
        """Distribute tick data."""
        await self.streamer.publish_market_data(symbol, tick_data)
    
    async def distribute_bar(self, symbol: str, bar_data: Dict):
        """Distribute bar data."""
        channel_data = {
            'type': 'bar',
            'symbol': symbol,
            **bar_data
        }
        await self.streamer.publish_market_data(symbol, channel_data)


# Fallback implementation without Redis
class MockRedisStreamer:
    """Mock Redis streamer for when Redis is not available."""
    
    def __init__(self, *args, **kwargs):
        self.subscribers = {}
        logger.warning("Using mock Redis streamer (Redis not available)")
    
    
    async def disconnect(self):
        pass
    
    async def publish_market_data(self, symbol: str, data: Dict):
        logger.debug(f"Mock publish: {symbol}")
    async def subscribe_market_data(self, symbols: List[str], callback: Callable):
        logger.debug(f"Mock subscribe: {symbols}")
    
    async def cache_data(self, key: str, data: Dict, ttl: int = 300):
        pass
    
    async def get_cached_data(self, key: str) -> Optional[Dict]:
        return None


def create_redis_streamer(**kwargs) -> RedisStreamer:
    """Create Redis streamer with fallback."""
    if REDIS_AVAILABLE:
        return RedisStreamer(**kwargs)
    else:
        return MockRedisStreamer(**kwargs)
