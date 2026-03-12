"""
Redis-based real-time data streaming
High-performance in-memory data distribution
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50
    decode_responses: bool = True


class RedisStreamManager:
    """
    Redis-based streaming for ultra-low latency data distribution
    Uses Redis Streams and Pub/Sub
    """
    
    def __init__(self, config: RedisConfig):
        self.config = config
        self.redis_client = None
        self.pubsub = None
        self.running = False
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.stats = {
            'messages_published': 0,
            'messages_received': 0,
            'active_channels': 0
        }
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            import redis.asyncio as aioredis
            
            self.redis_client = await aioredis.from_url(
                f"redis://{self.config.host}:{self.config.port}/{self.config.db}",
                password=self.config.password,
                max_connections=self.config.max_connections,
                decode_responses=self.config.decode_responses
            )
            
            self.pubsub = self.redis_client.pubsub()
            logger.info("Redis stream manager initialized")
            
        except ImportError:
            logger.warning("redis not installed, using mock")
            self.redis_client = MockRedis()
            self.pubsub = MockPubSub()
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self.redis_client = MockRedis()
            self.pubsub = MockPubSub()
    
    async def start(self):
        """Start listening to subscribed channels"""
        if not self.redis_client:
            await self.initialize()
        
        self.running = True
        asyncio.create_task(self._listen_loop())
        logger.info("Redis stream started")
    
    async def stop(self):
        """Stop streaming"""
        self.running = False
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Redis stream stopped")
    
    async def _listen_loop(self):
        """Main listening loop"""
        while self.running:
            try:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                
                if message:
                    channel = message['channel']
                    data = json.loads(message['data'])
                    
                    await self._process_message(channel, data)
                    self.stats['messages_received'] += 1
                
                await asyncio.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, channel: str, data: Dict[str, Any]):
        """Process incoming message"""
        if channel in self.subscribers:
            for callback in self.subscribers[channel]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    async def publish(self, channel: str, data: Dict[str, Any]):
        """Publish to channel"""
        try:
            message = json.dumps(data)
            await self.redis_client.publish(channel, message)
            self.stats['messages_published'] += 1
        except Exception as e:
            logger.error(f"Publish failed: {e}")
    
    async def subscribe(self, channel: str, callback: Callable):
        """Subscribe to channel"""
        self.subscribers[channel].append(callback)
        await self.pubsub.subscribe(channel)
        self.stats['active_channels'] = len(self.subscribers)
        logger.info(f"Subscribed to: {channel}")
    
    async def set_cache(self, key: str, value: Any, expiry: int = 60):
        """Set cached value"""
        try:
            await self.redis_client.setex(key, expiry, json.dumps(value))
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            value = await self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return self.stats.copy()


class MockRedis:
    """Mock Redis for testing"""
    def __init__(self):
        self.data = {}
    
    
    async def setex(self, key, expiry, value):
        self.data[key] = value
    
    async def get(self, key):
        return self.data.get(key)
    
    async def close(self):
        pass

class MockPubSub:
    """Mock PubSub for testing"""
    async def subscribe(self, channel):
        pass
    
    async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
        await asyncio.sleep(timeout)
        return None
    
    async def close(self):
        pass
