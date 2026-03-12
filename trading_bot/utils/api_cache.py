"""
from typing import Callable, Dict, Optional, Set
API Response Caching System
Reduces API latency through intelligent caching with Redis and memory layers
"""

import json
import hashlib
import time
from typing import Any, Optional, Callable, Dict
from datetime import datetime, timedelta
from functools import wraps
import pickle

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: Redis not available. Using memory-only caching.")

class APICache:
    """
    Multi-layer API response caching system
    
    Features:
    - Memory cache (L1) - Ultra-fast, limited size
    - Redis cache (L2) - Fast, persistent, shared
    - Automatic TTL management
    - Cache invalidation
    - Hit/miss statistics
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379,
                 redis_db: int = 0, memory_size: int = 1000):
        """
        Initialize API cache
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            memory_size: Maximum memory cache entries
        """
        self.memory_cache: Dict[str, tuple] = {}  # key -> (value, expiry)
        self.memory_size = memory_size
        self.redis_client = None
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'memory_hits': 0,
            'redis_hits': 0,
            'sets': 0
        }
        
        # Initialize Redis if available
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=False,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                print(f"✅ Redis cache connected: {redis_host}:{redis_port}")
            except Exception as e:
                print(f"⚠️  Redis connection failed: {e}. Using memory-only cache.")
                self.redis_client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        # Create a unique key from arguments
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"api_cache:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        # Try memory cache first (L1)
        if key in self.memory_cache:
            value, expiry = self.memory_cache[key]
            if expiry > time.time():
                self.stats['hits'] += 1
                self.stats['memory_hits'] += 1
                return value
            else:
                # Expired, remove from memory
                del self.memory_cache[key]
        
        # Try Redis cache (L2)
        if self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    value = pickle.loads(cached)
                    # Promote to memory cache
                    ttl = self.redis_client.ttl(key)
                    if ttl > 0:
                        self.memory_cache[key] = (value, time.time() + ttl)
                        self._cleanup_memory_cache()
                    
                    self.stats['hits'] += 1
                    self.stats['redis_hits'] += 1
                    return value
            except Exception as e:
                print(f"Redis get error: {e}")
        
        self.stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 5 minutes)
        """
        expiry = time.time() + ttl
        
        # Set in memory cache (L1)
        self.memory_cache[key] = (value, expiry)
        self._cleanup_memory_cache()
        
        # Set in Redis cache (L2)
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    pickle.dumps(value)
                )
            except Exception as e:
                print(f"Redis set error: {e}")
        
        self.stats['sets'] += 1
    
    def delete(self, key: str):
        """Delete key from cache"""
        # Remove from memory
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Remove from Redis
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                print(f"Redis delete error: {e}")
    
    def clear(self, pattern: Optional[str] = None):
        """
        Clear cache
        
        Args:
            pattern: Optional pattern to match keys (e.g., "api_cache:market_data:*")
        """
        if pattern:
            # Clear matching keys from memory
            keys_to_delete = [k for k in self.memory_cache.keys() if self._match_pattern(k, pattern)]
            for key in keys_to_delete:
                del self.memory_cache[key]
            
            # Clear matching keys from Redis
            if self.redis_client:
                try:
                    for key in self.redis_client.scan_iter(pattern):
                        self.redis_client.delete(key)
                except Exception as e:
                    print(f"Redis clear error: {e}")
        else:
            # Clear all
            self.memory_cache.clear()
            if self.redis_client:
                try:
                    self.redis_client.flushdb()
                except Exception as e:
                    print(f"Redis flush error: {e}")
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for cache keys"""
        pattern = pattern.replace('*', '.*')
        import re
        return bool(re.match(pattern, key))
    
    def _cleanup_memory_cache(self):
        """Remove expired entries and enforce size limit"""
        current_time = time.time()
        
        # Remove expired entries
        expired_keys = [k for k, (v, exp) in self.memory_cache.items() if exp <= current_time]
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Enforce size limit (LRU-like: remove oldest)
        if len(self.memory_cache) > self.memory_size:
            # Sort by expiry time and remove oldest
            sorted_items = sorted(self.memory_cache.items(), key=lambda x: x[1][1])
            excess = len(self.memory_cache) - self.memory_size
            for key, _ in sorted_items[:excess]:
                del self.memory_cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'memory_hits': self.stats['memory_hits'],
            'redis_hits': self.stats['redis_hits'],
            'sets': self.stats['sets'],
            'memory_size': len(self.memory_cache),
            'memory_limit': self.memory_size,
            'redis_available': self.redis_client is not None
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'memory_hits': 0,
            'redis_hits': 0,
            'sets': 0
        }

# Global cache instance
_global_cache = None

def get_cache() -> APICache:
    """Get global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = APICache()
    return _global_cache

def cached(ttl: int = 300, prefix: str = "default"):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        prefix: Cache key prefix
        
    Example:
        @cached(ttl=600, prefix="market_data")
        def fetch_market_data(symbol, timeframe):
            # Expensive API call
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# Convenience decorators for common use cases
def cache_market_data(ttl: int = 60):
    """Cache market data for 1 minute by default"""
    return cached(ttl=ttl, prefix="market_data")

def cache_api_response(ttl: int = 300):
    """Cache API responses for 5 minutes by default"""
    return cached(ttl=ttl, prefix="api_response")

def cache_analysis(ttl: int = 120):
    """Cache analysis results for 2 minutes by default"""
    return cached(ttl=ttl, prefix="analysis")

# Export
__all__ = [
    'APICache',
    'get_cache',
    'cached',
    'cache_market_data',
    'cache_api_response',
    'cache_analysis'
]
