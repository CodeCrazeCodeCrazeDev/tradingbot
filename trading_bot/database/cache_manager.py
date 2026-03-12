"""
Cache Manager - In-memory caching with TTL support
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    value: Any
    expires_at: datetime
    created_at: datetime = None
    
    def __post_init__(self):
        try:
            if self.created_at is None:
                self.created_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class CacheManager:
    """In-memory cache with TTL"""
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.cache: Dict[str, CacheEntry] = {}
            self.default_ttl = timedelta(minutes=5)
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            if config:
                self.config.update(config)
                if 'default_ttl_seconds' in config:
                    self.default_ttl = timedelta(seconds=config['default_ttl_seconds'])
            logger.info("CacheManager initialized")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def start(self) -> bool:
        try:
            self._running = True
            logger.info("CacheManager started")
            return True
        except Exception as e:
            logger.error(f"Error in start: {e}")
            raise
    
    async def stop(self) -> bool:
        try:
            self._running = False
            self.cache.clear()
            logger.info("CacheManager stopped")
            return True
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            raise
    
    def set(self, key: str, value: Any, ttl: timedelta = None):
        try:
            ttl = ttl or self.default_ttl
            self.cache[key] = CacheEntry(value=value, expires_at=datetime.utcnow() + ttl)
        except Exception as e:
            logger.error(f"Error in set: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        try:
            if key not in self.cache:
                return None
            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                return None
            return entry.value
        except Exception as e:
            logger.error(f"Error in get: {e}")
            raise
    
    def delete(self, key: str):
        try:
            if key in self.cache:
                del self.cache[key]
        except Exception as e:
            logger.error(f"Error in delete: {e}")
            raise
    
    def clear(self):
        try:
            self.cache.clear()
        except Exception as e:
            logger.error(f"Error in clear: {e}")
            raise
    
    def cleanup_expired(self):
        try:
            expired = [k for k, v in self.cache.items() if v.is_expired()]
            for key in expired:
                del self.cache[key]
        except Exception as e:
            logger.error(f"Error in cleanup_expired: {e}")
            raise


_cache: Optional[CacheManager] = None

def get_cache() -> CacheManager:
    try:
        global _cache
        if _cache is None:
            _cache = CacheManager()
        return _cache
    except Exception as e:
        logger.error(f"Error in get_cache: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_cache().initialize(config)

async def start() -> bool:
    return await get_cache().start()

async def stop() -> bool:
    return await get_cache().stop()
