"""
from typing import Callable, Dict, List, Optional, Set
Memory Management System
=========================
Production-grade memory management with limits, monitoring,
garbage collection, and memory-efficient data structures.
"""

import asyncio
import gc
import logging
import os
import sys
import threading
import time
import weakref
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union
import functools

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class MemoryConfig:
    """Memory management configuration."""
    max_memory_mb: int = 1024
    warning_threshold: float = 0.8  # 80%
    critical_threshold: float = 0.95  # 95%
    gc_interval_seconds: int = 300
    gc_threshold_mb: int = 100
    cache_max_size_mb: int = 256
    enable_monitoring: bool = True
    enable_auto_gc: bool = True
    enable_memory_limits: bool = True


@dataclass
class MemoryStats:
    """Memory statistics."""
    total_mb: float
    used_mb: float
    available_mb: float
    percent_used: float
    gc_count: int
    cache_size_mb: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MemoryPressure(Enum):
    """Memory pressure levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# LRU CACHE WITH SIZE LIMIT
# ============================================================================

class SizeLimitedLRUCache(Generic[T]):
    """
    LRU cache with memory size limit.
    Automatically evicts items when size limit is reached.
    """
    
    def __init__(
        self,
        max_size_mb: float = 100,
        max_items: int = 10000,
        ttl_seconds: Optional[int] = None,
    ):
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.max_items = max_items
        self.ttl_seconds = ttl_seconds
        
        self._cache: OrderedDict = OrderedDict()
        self._sizes: Dict[str, int] = {}
        self._timestamps: Dict[str, float] = {}
        self._current_size = 0
        self._lock = threading.Lock()
        
        self._hits = 0
        self._misses = 0
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value."""
        try:
            return sys.getsizeof(value)
        except TypeError:
            return 1000  # Default estimate
    
    def _is_expired(self, key: str) -> bool:
        """Check if item is expired."""
        if self.ttl_seconds is None:
            return False
        timestamp = self._timestamps.get(key, 0)
        return time.time() - timestamp > self.ttl_seconds
    
    def _evict_if_needed(self, needed_size: int = 0):
        """Evict items if needed."""
        # Evict expired items first
        expired = [k for k in self._cache if self._is_expired(k)]
        for key in expired:
            self._remove(key)
        
        # Evict LRU items if still over limit
        while (self._current_size + needed_size > self.max_size_bytes or 
               len(self._cache) >= self.max_items) and self._cache:
            oldest_key = next(iter(self._cache))
            self._remove(oldest_key)
    
    def _remove(self, key: str):
        """Remove item from cache."""
        if key in self._cache:
            del self._cache[key]
            self._current_size -= self._sizes.pop(key, 0)
            self._timestamps.pop(key, None)
    
    def get(self, key: str, default: T = None) -> Optional[T]:
        """Get item from cache."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
            
            if self._is_expired(key):
                self._remove(key)
                self._misses += 1
                return default
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
    
    def set(self, key: str, value: T):
        """Set item in cache."""
        with self._lock:
            size = self._estimate_size(value)
            
            # Remove existing if present
            if key in self._cache:
                self._remove(key)
            
            # Evict if needed
            self._evict_if_needed(size)
            
            # Add new item
            self._cache[key] = value
            self._sizes[key] = size
            self._timestamps[key] = time.time()
            self._current_size += size
    
    def delete(self, key: str) -> bool:
        """Delete item from cache."""
        with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False
    
    def clear(self):
        """Clear cache."""
        with self._lock:
            self._cache.clear()
            self._sizes.clear()
            self._timestamps.clear()
            self._current_size = 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                'items': len(self._cache),
                'size_mb': self._current_size / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
            }


# ============================================================================
# RING BUFFER
# ============================================================================

class RingBuffer(Generic[T]):
    """
    Memory-efficient ring buffer for streaming data.
    Fixed size, overwrites oldest data when full.
    """
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._buffer: List[Optional[T]] = [None] * capacity
        self._head = 0
        self._tail = 0
        self._size = 0
        self._lock = threading.Lock()
    
    def append(self, item: T):
        """Append item to buffer."""
        with self._lock:
            self._buffer[self._tail] = item
            self._tail = (self._tail + 1) % self.capacity
            
            if self._size < self.capacity:
                self._size += 1
            else:
                self._head = (self._head + 1) % self.capacity
    
    def get_all(self) -> List[T]:
        """Get all items in order."""
        with self._lock:
            if self._size == 0:
                return []
            
            result = []
            idx = self._head
            for _ in range(self._size):
                result.append(self._buffer[idx])
                idx = (idx + 1) % self.capacity
            
            return result
    
    def get_latest(self, n: int) -> List[T]:
        """Get latest n items."""
        with self._lock:
            if self._size == 0:
                return []
            
            n = min(n, self._size)
            result = []
            idx = (self._tail - n) % self.capacity
            
            for _ in range(n):
                result.append(self._buffer[idx])
                idx = (idx + 1) % self.capacity
            
            return result
    
    def __len__(self) -> int:
        return self._size
    
    def clear(self):
        """Clear buffer."""
        with self._lock:
            self._buffer = [None] * self.capacity
            self._head = 0
            self._tail = 0
            self._size = 0


# ============================================================================
# WEAK REFERENCE CACHE
# ============================================================================

class WeakRefCache(Generic[T]):
    """
    Cache using weak references.
    Items are automatically removed when no longer referenced elsewhere.
    """
    
    def __init__(self):
        self._cache: Dict[str, weakref.ref] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[T]:
        """Get item from cache."""
        with self._lock:
            ref = self._cache.get(key)
            if ref is None:
                return None
            
            value = ref()
            if value is None:
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: T):
        """Set item in cache."""
        with self._lock:
            self._cache[key] = weakref.ref(value)
    
    def delete(self, key: str) -> bool:
        """Delete item from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def cleanup(self):
        """Remove dead references."""
        with self._lock:
            dead_keys = [k for k, v in self._cache.items() if v() is None]
            for key in dead_keys:
                del self._cache[key]
    
    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)


# ============================================================================
# MEMORY MONITOR
# ============================================================================

class MemoryMonitor:
    """
    Monitors memory usage and triggers actions when thresholds are exceeded.
    """
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self._callbacks: Dict[MemoryPressure, List[Callable]] = {
            MemoryPressure.LOW: [],
            MemoryPressure.NORMAL: [],
            MemoryPressure.HIGH: [],
            MemoryPressure.CRITICAL: [],
        }
        self._last_pressure = MemoryPressure.NORMAL
        self._history: deque = deque(maxlen=100)
        self._gc_count = 0
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            used_mb = memory_info.rss / (1024 * 1024)
            total_mb = self.config.max_memory_mb
            available_mb = total_mb - used_mb
            percent_used = used_mb / total_mb if total_mb > 0 else 0
            
            return MemoryStats(
                total_mb=total_mb,
                used_mb=used_mb,
                available_mb=max(0, available_mb),
                percent_used=percent_used,
                gc_count=self._gc_count,
                cache_size_mb=0,  # Would need to track caches
            )
        except ImportError:
            # Fallback without psutil
            return MemoryStats(
                total_mb=self.config.max_memory_mb,
                used_mb=0,
                available_mb=self.config.max_memory_mb,
                percent_used=0,
                gc_count=self._gc_count,
                cache_size_mb=0,
            )
    
    def get_pressure_level(self) -> MemoryPressure:
        """Get current memory pressure level."""
        stats = self.get_memory_stats()
        
        if stats.percent_used >= self.config.critical_threshold:
            return MemoryPressure.CRITICAL
        elif stats.percent_used >= self.config.warning_threshold:
            return MemoryPressure.HIGH
        elif stats.percent_used >= 0.5:
            return MemoryPressure.NORMAL
        else:
            return MemoryPressure.LOW
    
    def on_pressure(self, level: MemoryPressure, callback: Callable):
        """Register callback for memory pressure level."""
        self._callbacks[level].append(callback)
    
    def _trigger_callbacks(self, level: MemoryPressure):
        """Trigger callbacks for pressure level."""
        for callback in self._callbacks[level]:
            try:
                callback(self.get_memory_stats())
            except Exception as e:
                logger.error(f"Memory callback error: {e}")
    
    def force_gc(self) -> int:
        """Force garbage collection."""
        with self._lock:
            collected = gc.collect()
            self._gc_count += 1
            logger.info(f"Garbage collection: {collected} objects collected")
            return collected
    
    async def start_monitoring(self):
        """Start background monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
    
    async def _monitor_loop(self):
        """Background monitoring loop."""
        while self._monitoring:
            try:
                stats = self.get_memory_stats()
                self._history.append(stats)
                
                pressure = self.get_pressure_level()
                
                # Check for pressure change
                if pressure != self._last_pressure:
                    logger.info(f"Memory pressure changed: {self._last_pressure.value} -> {pressure.value}")
                    self._trigger_callbacks(pressure)
                    self._last_pressure = pressure
                
                # Auto GC on high pressure
                if self.config.enable_auto_gc and pressure in [MemoryPressure.HIGH, MemoryPressure.CRITICAL]:
                    self.force_gc()
                
                await asyncio.sleep(self.config.gc_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory monitor error: {e}")
                await asyncio.sleep(10)
    
    def get_history(self) -> List[MemoryStats]:
        """Get memory history."""
        return list(self._history)


# ============================================================================
# MEMORY MANAGER
# ============================================================================

class MemoryManager:
    """
    Central memory management system.
    Coordinates caches, monitoring, and garbage collection.
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.monitor = MemoryMonitor(self.config)
        
        self._caches: Dict[str, SizeLimitedLRUCache] = {}
        self._ring_buffers: Dict[str, RingBuffer] = {}
        self._weak_caches: Dict[str, WeakRefCache] = {}
        self._lock = threading.Lock()
        
        # Register default pressure handlers
        self.monitor.on_pressure(MemoryPressure.HIGH, self._on_high_pressure)
        self.monitor.on_pressure(MemoryPressure.CRITICAL, self._on_critical_pressure)
    
    def _on_high_pressure(self, stats: MemoryStats):
        """Handle high memory pressure."""
        logger.warning(f"High memory pressure: {stats.percent_used:.1%} used")
        
        # Clear expired cache items
        for cache in self._caches.values():
            cache._evict_if_needed()
        
        # Cleanup weak references
        for weak_cache in self._weak_caches.values():
            weak_cache.cleanup()
    
    def _on_critical_pressure(self, stats: MemoryStats):
        """Handle critical memory pressure."""
        logger.error(f"Critical memory pressure: {stats.percent_used:.1%} used")
        
        # Aggressive cache clearing
        for cache in self._caches.values():
            cache.clear()
        
        # Force GC
        self.monitor.force_gc()
    
    def create_cache(
        self,
        name: str,
        max_size_mb: float = 100,
        max_items: int = 10000,
        ttl_seconds: Optional[int] = None,
    ) -> SizeLimitedLRUCache:
        """Create a managed cache."""
        with self._lock:
            cache = SizeLimitedLRUCache(max_size_mb, max_items, ttl_seconds)
            self._caches[name] = cache
            return cache
    
    def get_cache(self, name: str) -> Optional[SizeLimitedLRUCache]:
        """Get existing cache."""
        return self._caches.get(name)
    
    def create_ring_buffer(self, name: str, capacity: int) -> RingBuffer:
        """Create a managed ring buffer."""
        with self._lock:
            buffer = RingBuffer(capacity)
            self._ring_buffers[name] = buffer
            return buffer
    
    def get_ring_buffer(self, name: str) -> Optional[RingBuffer]:
        """Get existing ring buffer."""
        return self._ring_buffers.get(name)
    
    def create_weak_cache(self, name: str) -> WeakRefCache:
        """Create a managed weak reference cache."""
        with self._lock:
            cache = WeakRefCache()
            self._weak_caches[name] = cache
            return cache
    
    def get_weak_cache(self, name: str) -> Optional[WeakRefCache]:
        """Get existing weak cache."""
        return self._weak_caches.get(name)
    
    def get_stats(self) -> Dict:
        """Get memory management statistics."""
        memory_stats = self.monitor.get_memory_stats()
        
        cache_stats = {}
        for name, cache in self._caches.items():
            cache_stats[name] = cache.get_stats()
        
        return {
            'memory': {
                'total_mb': memory_stats.total_mb,
                'used_mb': memory_stats.used_mb,
                'available_mb': memory_stats.available_mb,
                'percent_used': memory_stats.percent_used,
                'gc_count': memory_stats.gc_count,
            },
            'pressure': self.monitor.get_pressure_level().value,
            'caches': cache_stats,
            'ring_buffers': {name: len(buf) for name, buf in self._ring_buffers.items()},
            'weak_caches': {name: len(cache) for name, cache in self._weak_caches.items()},
        }
    
    def clear_all_caches(self):
        """Clear all managed caches."""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()
            for buffer in self._ring_buffers.values():
                buffer.clear()
            for weak_cache in self._weak_caches.values():
                weak_cache.cleanup()
    
    async def start(self):
        """Start memory management."""
        if self.config.enable_monitoring:
            await self.monitor.start_monitoring()
    
    async def stop(self):
        """Stop memory management."""
        await self.monitor.stop_monitoring()


# ============================================================================
# DECORATORS
# ============================================================================

def memory_limited(max_mb: float = 100):
    """Decorator to limit memory usage of function."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_memory_manager()
            stats = manager.monitor.get_memory_stats()
            
            if stats.used_mb > max_mb:
                manager.monitor.force_gc()
                stats = manager.monitor.get_memory_stats()
                
                if stats.used_mb > max_mb:
                    raise MemoryError(f"Memory limit exceeded: {stats.used_mb:.1f}MB > {max_mb}MB")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def cached(cache_name: str, ttl_seconds: Optional[int] = None):
    """Decorator for caching function results."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_memory_manager()
            cache = manager.get_cache(cache_name)
            
            if cache is None:
                cache = manager.create_cache(cache_name, ttl_seconds=ttl_seconds)
            
            # Create cache key
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Check cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute and cache
            result = func(*args, **kwargs)
            cache.set(key, result)
            
            return result
        
        return wrapper
    return decorator


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get global memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'MemoryConfig', 'MemoryStats', 'MemoryPressure',
    'SizeLimitedLRUCache', 'RingBuffer', 'WeakRefCache',
    'MemoryMonitor', 'MemoryManager',
    'memory_limited', 'cached', 'get_memory_manager',
]
