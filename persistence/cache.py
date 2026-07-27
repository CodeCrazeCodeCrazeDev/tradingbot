"""
Cache management for AlphaAlgo 2.0
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
import pickle

logger = logging.getLogger(__name__)


class CacheManager:
    """
    In-memory cache manager with optional Redis backend.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # In-memory cache
        self.cache = {}
        self.expiry = {}
        
        # Default TTL
        self.default_ttl = self.config.get('default_ttl', 3600)  # 1 hour
        
        # Redis configuration
        self.redis_enabled = self.config.get('redis_enabled', False)
        self.redis_client = None
        
        if self.redis_enabled:
            self._initialize_redis()
        
        logger.info("✅ Cache Manager initialized")
    
    def _initialize_redis(self):
        """Initialize Redis connection."""
        try:
            import redis
            
            redis_config = self.config.get('redis', {})
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                decode_responses=False
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis initialization failed: {e}")
            self.redis_enabled = False
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True
    ):
        """Set cache value."""
        if ttl is None:
            ttl = self.default_ttl
        
        # Serialize value
        if serialize:
            value = pickle.dumps(value)
        
        # Set in memory cache
        self.cache[key] = value
        self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
        
        # Set in Redis if enabled
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.setex(key, ttl, value)
            except Exception as e:
                logger.warning(f"⚠️ Redis set error: {e}")
    
    def get(
        self,
        key: str,
        default: Any = None,
        deserialize: bool = True
    ) -> Any:
        """Get cache value."""
        # Check memory cache first
        if key in self.cache:
            # Check expiry
            if datetime.now() < self.expiry[key]:
                value = self.cache[key]
                
                # Deserialize value
                if deserialize and isinstance(value, bytes):
                    try:
                        value = pickle.loads(value)
                    except Exception as e:
                        logger.warning(f"⚠️ Deserialization error: {e}")
                
                return value
            else:
                # Expired - remove from cache
                del self.cache[key]
                del self.expiry[key]
        
        # Check Redis if enabled
        if self.redis_enabled and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value is not None:
                    # Update memory cache
                    self.cache[key] = value
                    self.expiry[key] = datetime.now() + timedelta(seconds=self.default_ttl)
                    
                    # Deserialize value
                    if deserialize:
                        try:
                            value = pickle.loads(value)
                        except Exception as e:
                            logger.warning(f"⚠️ Deserialization error: {e}")
                    
                    return value
            except Exception as e:
                logger.warning(f"⚠️ Redis get error: {e}")
        
        return default
    
    def delete(self, key: str):
        """Delete cache value."""
        # Delete from memory cache
        if key in self.cache:
            del self.cache[key]
            del self.expiry[key]
        
        # Delete from Redis if enabled
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"⚠️ Redis delete error: {e}")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        # Check memory cache
        if key in self.cache:
            if datetime.now() < self.expiry[key]:
                return True
            else:
                # Expired - remove from cache
                del self.cache[key]
                del self.expiry[key]
        
        # Check Redis if enabled
        if self.redis_enabled and self.redis_client:
            try:
                return self.redis_client.exists(key) > 0
            except Exception as e:
                logger.warning(f"⚠️ Redis exists error: {e}")
        
        return False
    
    def clear(self):
        """Clear all cache."""
        # Clear memory cache
        self.cache.clear()
        self.expiry.clear()
        
        # Clear Redis if enabled
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"⚠️ Redis clear error: {e}")
        
        logger.info("✅ Cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        # Count valid entries
        valid_entries = sum(
            1 for key in self.cache
            if datetime.now() < self.expiry[key]
        )
        
        stats = {
            'memory_entries': valid_entries,
            'total_entries': len(self.cache),
            'redis_enabled': self.redis_enabled
        }
        
        # Get Redis stats if enabled
        if self.redis_enabled and self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_keys'] = info.get('db0', {}).get('keys', 0)
                stats['redis_memory'] = info.get('used_memory_human', 'N/A')
            except Exception as e:
                logger.warning(f"⚠️ Redis stats error: {e}")
        
        return stats
    
    def cleanup_expired(self):
        """Remove expired entries from memory cache."""
        now = datetime.now()
        expired_keys = [
            key for key, expiry_time in self.expiry.items()
            if now >= expiry_time
        ]
        
        for key in expired_keys:
            del self.cache[key]
            del self.expiry[key]
        
        if expired_keys:
            logger.info(f"✅ Cleaned up {len(expired_keys)} expired cache entries")
