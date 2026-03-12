"""
Elite Trading Bot - Cache Manager

This module provides data caching capabilities to minimize API requests
and improve performance for the Elite Trading Bot.
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import threading
from typing import Set

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class CacheItem:
    """A cached item with metadata."""
    
    def __init__(self, 
                 key: str, 
                 value: Any, 
                 expires_at: Optional[float] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a cache item.
        
        Args:
            key: Cache key
            value: Cached value
            expires_at: Expiration timestamp (None for no expiration)
            metadata: Optional metadata
        """
        self.key = key
        self.value = value
        self.expires_at = expires_at
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
    
    def is_expired(self) -> bool:
        """
        Check if the item is expired.
        
        Returns:
            True if expired, False otherwise
        """
        if self.expires_at is None:
            return False
        
        return time.time() > self.expires_at
    
    def access(self):
        """Record an access to this item."""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "key": self.key,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "expires_at": self.expires_at,
            "expired": self.is_expired(),
            "metadata": self.metadata
        }


class MemoryCache:
    """In-memory cache implementation."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize memory cache.
        
        Args:
            max_size: Maximum number of items in cache
        """
        self.cache: Dict[str, CacheItem] = {}
        self.max_size = max_size
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            item = self.cache[key]
            
            # Check expiration
            if item.is_expired():
                del self.cache[key]
                return None
            
            # Record access
            item.access()
            
            return item.value
    
    def set(self, 
            key: str, 
            value: Any, 
            ttl: Optional[int] = None, 
            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None for no expiration)
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            # Check if we need to evict items
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_items()
            
            # Calculate expiration
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            
            # Create cache item
            item = CacheItem(key, value, expires_at, metadata)
            
            # Store in cache
            self.cache[key] = item
            
            return True
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if key not in self.cache:
                return False
            
            del self.cache[key]
            return True
    
    def clear(self):
        """Clear all items from cache."""
        with self.lock:
            self.cache.clear()
    
    def _evict_items(self):
        """Evict items from cache when full."""
        with self.lock:
            # First remove expired items
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.cache[key]
            
            # If still need to evict, remove least recently used
            if len(self.cache) >= self.max_size:
                # Sort by last accessed time
                sorted_items = sorted(
                    self.cache.items(),
                    key=lambda x: x[1].last_accessed
                )
                
                # Remove 10% of items or at least one
                to_remove = max(1, len(self.cache) // 10)
                for i in range(to_remove):
                    if i < len(sorted_items):
                        del self.cache[sorted_items[i][0]]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        with self.lock:
            # Count expired items
            expired_count = sum(1 for item in self.cache.values() if item.is_expired())
            
            # Calculate hit rate (if we had tracking)
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "expired_count": expired_count,
                "utilization": len(self.cache) / self.max_size if self.max_size > 0 else 0
            }


class DiskCache:
    """Disk-based cache implementation."""
    
    def __init__(self, 
                 cache_dir: str, 
                 max_size_mb: int = 100,
                 cleanup_interval: int = 3600):
        """
        Initialize disk cache.
        
        Args:
            cache_dir: Cache directory
            max_size_mb: Maximum cache size in MB
            cleanup_interval: Cleanup interval in seconds
        """
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = 0
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Index file for metadata
        self.index_file = os.path.join(cache_dir, "cache_index.json")
        self.index: Dict[str, Dict[str, Any]] = {}
        
        # Load index
        self._load_index()
        
        logger.info(f"DiskCache initialized at {cache_dir}")
    
    def _load_index(self):
        """Load cache index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache index: {str(e)}")
                self.index = {}
    
    def _save_index(self):
        """Save cache index to disk."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f)
        except Exception as e:
            logger.error(f"Error saving cache index: {str(e)}")
    
    def _get_cache_path(self, key: str) -> str:
        """
        Get file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            File path
        """
        # Create a safe filename from the key
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.cache")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        # Check if key exists in index
        if key not in self.index:
            return None
        
        # Check expiration
        item_info = self.index[key]
        if 'expires_at' in item_info and item_info['expires_at'] is not None:
            if time.time() > item_info['expires_at']:
                # Remove expired item
                self.delete(key)
                return None
        
        # Get file path
        file_path = self._get_cache_path(key)
        
        # Check if file exists
        if not os.path.exists(file_path):
            try:
                # Remove from index
                if key in self.index:
                    del self.index[key]
                    self._save_index()
                return None

                # Load from file
                with open(file_path, 'rb') as f:
                    value = pickle.load(f)

                # Update access info
                self.index[key]['last_accessed'] = time.time()
                self.index[key]['access_count'] += 1
                self._save_index()

                return value

            except Exception as e:
                logger.error(f"Error loading cache item {key}: {str(e)}")
                return None

    def set(self, 
            key: str, 
            value: Any, 
            ttl: Optional[int] = None, 
            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None for no expiration)
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        # Check if we need to clean up
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
        
        # Calculate expiration
        expires_at = None
        if ttl is not None:
            expires_at = current_time + ttl
        
        # Get file path
        file_path = self._get_cache_path(key)
        
        try:
            # Save to file
            with open(file_path, 'wb') as f:
                pickle.dump(value, f)
            
            # Update index
            self.index[key] = {
                'created_at': current_time,
                'last_accessed': current_time,
                'access_count': 0,
                'expires_at': expires_at,
                'metadata': metadata or {}
            }
            
            self._save_index()
            return True
            
        except Exception as e:
            logger.error(f"Error saving cache item {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        # Check if key exists in index
        if key not in self.index:
            return False
        
        # Get file path
        file_path = self._get_cache_path(key)
        
        # Delete file if it exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error deleting cache file {file_path}: {str(e)}")
        
        # Remove from index
        del self.index[key]
        self._save_index()
        
        return True
    
    def clear(self):
        """Clear all items from cache."""
        # Delete all cache files
        for key in list(self.index.keys()):
            self.delete(key)
        
        # Clear index
        self.index = {}
        self._save_index()
    
    def _cleanup(self):
        """Clean up expired and excess items."""
        self.last_cleanup = time.time()
        
        # Remove expired items
        expired_keys = []
        for key, info in self.index.items():
            if 'expires_at' in info and info['expires_at'] is not None:
                if time.time() > info['expires_at']:
                    expired_keys.append(key)
        
        for key in expired_keys:
            self.delete(key)
        
        # Check cache size
        cache_size = self._get_cache_size()
        
        if cache_size > self.max_size_bytes:
            # Sort items by last accessed time
            sorted_items = sorted(
                self.index.items(),
                key=lambda x: x[1]['last_accessed']
            )
            
            # Remove items until under size limit
            for key, _ in sorted_items:
                self.delete(key)
                
                # Recalculate size
                cache_size = self._get_cache_size()
                if cache_size <= self.max_size_bytes:
                    break
    
    def _get_cache_size(self) -> int:
        """
        Get total cache size in bytes.
        
        Returns:
            Cache size in bytes
        """
        total_size = 0
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
        
        return total_size
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        # Count expired items
        expired_count = 0
        for key, info in self.index.items():
            if 'expires_at' in info and info['expires_at'] is not None:
                if time.time() > info['expires_at']:
                    expired_count += 1
        
        # Calculate cache size
        cache_size = self._get_cache_size()
        
        return {
            "size": len(self.index),
            "expired_count": expired_count,
            "disk_usage_bytes": cache_size,
            "disk_usage_mb": cache_size / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "utilization": cache_size / self.max_size_bytes if self.max_size_bytes > 0 else 0
        }


class CacheManager:
    """
    Manager for multiple cache implementations.
    
    Features:
    - Multiple cache levels (memory, disk)
    - Automatic expiration
    - Cache statistics
    - Async support
    """
    
    def __init__(self, 
                 memory_cache_size: int = 1000,
                 disk_cache_dir: Optional[str] = None,
                 disk_cache_size_mb: int = 100):
        """
        Initialize the cache manager.
        
        Args:
            memory_cache_size: Maximum number of items in memory cache
            disk_cache_dir: Directory for disk cache (None to disable)
            disk_cache_size_mb: Maximum disk cache size in MB
        """
        # Initialize memory cache
        self.memory_cache = MemoryCache(max_size=memory_cache_size)
        
        # Initialize disk cache if directory provided
        self.disk_cache = None
        if disk_cache_dir:
            self.disk_cache = DiskCache(
                cache_dir=disk_cache_dir,
                max_size_mb=disk_cache_size_mb
            )
        
        # Cache hit/miss statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "disk_hits": 0
        }
        
        logger.info("CacheManager initialized")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        # Try memory cache first
        value = self.memory_cache.get(key)
        
        if value is not None:
            # Memory cache hit
            self.stats["hits"] += 1
            self.stats["memory_hits"] += 1
            return value
        
        # Try disk cache if available
        if self.disk_cache:
            value = self.disk_cache.get(key)
            
            if value is not None:
                # Disk cache hit, store in memory for faster access next time
                self.memory_cache.set(key, value)
                
                self.stats["hits"] += 1
                self.stats["disk_hits"] += 1
                return value
        
        # Cache miss
        self.stats["misses"] += 1
        return None
    
    def set(self, 
            key: str, 
            value: Any, 
            ttl: Optional[int] = None, 
            metadata: Optional[Dict[str, Any]] = None,
            memory_only: bool = False) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None for no expiration)
            metadata: Optional metadata
            memory_only: Whether to store only in memory cache
            
        Returns:
            True if successful, False otherwise
        """
        # Always set in memory cache
        memory_result = self.memory_cache.set(key, value, ttl, metadata)
        
        # Set in disk cache if available and not memory_only
        disk_result = True
        if self.disk_cache and not memory_only:
            disk_result = self.disk_cache.set(key, value, ttl, metadata)
        
        return memory_result and disk_result
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted from any cache, False if not found
        """
        memory_result = self.memory_cache.delete(key)
        
        disk_result = False
        if self.disk_cache:
            disk_result = self.disk_cache.delete(key)
        
        return memory_result or disk_result
    
    def clear(self):
        """Clear all caches."""
        self.memory_cache.clear()
        
        if self.disk_cache:
            self.disk_cache.clear()
        
        # Reset statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "disk_hits": 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        stats = {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "memory_hits": self.stats["memory_hits"],
            "disk_hits": self.stats["disk_hits"],
            "hit_rate": self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) if (self.stats["hits"] + self.stats["misses"]) > 0 else 0,
            "memory_cache": self.memory_cache.get_stats()
        }
        
        if self.disk_cache:
            stats["disk_cache"] = self.disk_cache.get_stats()
        
        return stats
    
    async def get_async(self, key: str) -> Optional[Any]:
        """
        Get a value from cache asynchronously.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        # For disk cache, run in thread pool
        if self.disk_cache:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.get, key)
        else:
            return self.get(key)
    
    async def set_async(self, 
                       key: str, 
                       value: Any, 
                       ttl: Optional[int] = None, 
                       metadata: Optional[Dict[str, Any]] = None,
                       memory_only: bool = False) -> bool:
        """
        Set a value in cache asynchronously.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None for no expiration)
            metadata: Optional metadata
            memory_only: Whether to store only in memory cache
            
        Returns:
            True if successful, False otherwise
        """
        # For disk cache, run in thread pool
        if self.disk_cache and not memory_only:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.set, key, value, ttl, metadata, memory_only)
        else:
            return self.set(key, value, ttl, metadata, memory_only)
    
    def cached(self, ttl: Optional[int] = 3600, key_prefix: str = ""):
        """
        Decorator for caching function results.
        
        Args:
            ttl: Time-to-live in seconds (None for no expiration)
            key_prefix: Prefix for cache keys
            
        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                key = self._generate_cache_key(func, key_prefix, args, kwargs)
                
                # Try to get from cache
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value
                
                # Call function
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(key, result, ttl)
                
                return result
            
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                key = self._generate_cache_key(func, key_prefix, args, kwargs)
                
                # Try to get from cache
                cached_value = await self.get_async(key)
                if cached_value is not None:
                    return cached_value
                
                # Call function
                result = await func(*args, **kwargs)
                
                # Store in cache
                await self.set_async(key, result, ttl)
                
                return result
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return wrapper
        
        return decorator
    
    def _generate_cache_key(self, func: Callable, prefix: str, args: Tuple, kwargs: Dict) -> str:
        """
        Generate a cache key for a function call.
        
        Args:
            func: Function
            prefix: Key prefix
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Cache key
        """
        # Create key components
        key_parts = [
            prefix if prefix else "",
            func.__module__,
            func.__name__,
            str(args),
            str(sorted(kwargs.items()))
        ]
        
        # Join and hash
        key = "_".join(key_parts)
        
        # Use hash for shorter keys
        if len(key) > 250:
            key = hashlib.md5(key.encode()).hexdigest()
        
        return key
