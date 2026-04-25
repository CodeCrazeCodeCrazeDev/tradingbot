"""
Backtest Result Cache
Caches backtest results to improve performance and avoid redundant computations
"""

import hashlib
import json
import pickle
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import threading
from enum import Enum

from .backtesting_engine import BacktestResult
from .strategy_genome import StrategyGenome

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In First Out


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    result: BacktestResult
    created_at: datetime
    last_accessed: datetime
    access_count: int
    size_bytes: int
    ttl: Optional[timedelta] = None
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl is None:
            return False
        return datetime.now() > self.created_at + self.ttl
    
    def touch(self) -> None:
        """Update last accessed time and increment count"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class BacktestCache:
    """
    High-performance cache for backtest results with multiple eviction strategies.
    
    Features:
    - Configurable eviction strategies
    - Size and time-based limits
    - Persistent storage option
    - Thread-safe operations
    - Cache statistics
    """
    
    def __init__(self, 
                 config: Dict[str, Any]):
        self.config = config
        
        # Cache configuration
        self.max_size = config.get('max_size', 1000)
        self.max_memory_mb = config.get('max_memory_mb', 1024)
        self.strategy = CacheStrategy(config.get('strategy', 'lru'))
        self.default_ttl = config.get('default_ttl')
        self.persistent = config.get('persistent', False)
        self.cache_dir = Path(config.get('cache_dir', './cache/backtest'))
        
        # Internal storage
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU/FIFO
        self._frequency_order: Dict[str, int] = {}  # For LFU
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_size_bytes = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize persistent storage if enabled
        if self.persistent:
            self._init_persistent_storage()
            self._load_persistent_cache()
        
        logger.info(f"Backtest cache initialized: strategy={self.strategy.value}, "
                   f"max_size={self.max_size}, max_memory={self.max_memory_mb}MB")
    
    def get(self, 
            strategy_genome: StrategyGenome,
            market_data_hash: str,
            backtest_config: Dict[str, Any]) -> Optional[BacktestResult]:
        """
        Get cached backtest result for a strategy.
        
        Args:
            strategy_genome: The strategy genome
            market_data_hash: Hash of market data used
            backtest_config: Backtest configuration
            
        Returns:
            Cached BacktestResult or None if not found
        """
        key = self._generate_key(strategy_genome, market_data_hash, backtest_config)
        
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check expiration
                if entry.is_expired():
                    self._remove_entry(key)
                    self.misses += 1
                    return None
                
                # Update access tracking
                entry.touch()
                self._update_access_tracking(key)
                self.hits += 1
                
                logger.debug(f"Cache hit for key: {key[:16]}...")
                return entry.result
            
            self.misses += 1
            return None
    
    def put(self, 
            strategy_genome: StrategyGenome,
            market_data_hash: str,
            backtest_config: Dict[str, Any],
            result: BacktestResult) -> None:
        """
        Store a backtest result in cache.
        
        Args:
            strategy_genome: The strategy genome
            market_data_hash: Hash of market data used
            backtest_config: Backtest configuration
            result: Backtest result to cache
        """
        key = self._generate_key(strategy_genome, market_data_hash, backtest_config)
        
        # Serialize result to determine size
        result_bytes = pickle.dumps(result)
        size_bytes = len(result_bytes)
        
        # Check if result is too large
        if size_bytes > self.max_memory_mb * 1024 * 1024 * 0.5:  # 50% of max memory
            logger.warning(f"Backtest result too large for cache: {size_bytes / 1024 / 1024:.2f}MB")
            return
        
        with self._lock:
            # Create cache entry
            ttl = None
            if self.default_ttl:
                ttl = timedelta(seconds=self.default_ttl)
            
            entry = CacheEntry(
                key=key,
                result=result,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                size_bytes=size_bytes,
                ttl=ttl
            )
            
            # Check if we need to evict
            while self._should_evict(size_bytes):
                self._evict_one()
            
            # Add to cache
            self._cache[key] = entry
            self.total_size_bytes += size_bytes
            
            # Update tracking structures
            self._update_access_tracking(key, new_entry=True)
            
            # Persist if enabled
            if self.persistent:
                self._persist_entry(entry)
            
            logger.debug(f"Cached result for key: {key[:16]}...")
    
    def invalidate(self, 
                   strategy_genome: Optional[StrategyGenome] = None,
                   market_data_hash: Optional[str] = None) -> None:
        """
        Invalidate cache entries matching criteria.
        
        Args:
            strategy_genome: Specific strategy to invalidate
            market_data_hash: Specific market data to invalidate
        """
        with self._lock:
            keys_to_remove = []
            
            for key, entry in self._cache.items():
                # Parse key to check matches
                key_parts = key.split(':')
                key_strategy_hash = key_parts[0] if len(key_parts) > 0 else None
                key_data_hash = key_parts[1] if len(key_parts) > 1 else None
                
                remove = True
                
                if strategy_genome is not None:
                    strategy_hash = self._hash_strategy(strategy_genome)
                    if key_strategy_hash != strategy_hash:
                        remove = False
                
                if market_data_hash is not None:
                    if key_data_hash != market_data_hash:
                        remove = False
                
                if remove:
                    keys_to_remove.append(key)
            
            # Remove matched entries
            for key in keys_to_remove:
                self._remove_entry(key)
            
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._frequency_order.clear()
            self.total_size_bytes = 0
            
            if self.persistent:
                self._clear_persistent_storage()
            
            logger.info("Cache cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / max(1, total_requests)
            
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'evictions': self.evictions,
                'entries': len(self._cache),
                'total_size_mb': self.total_size_bytes / 1024 / 1024,
                'avg_entry_size_kb': self.total_size_bytes / max(1, len(self._cache)) / 1024,
                'memory_utilization': self.total_size_bytes / (self.max_memory_mb * 1024 * 1024),
                'strategy': self.strategy.value
            }
    
    def _generate_key(self, 
                     strategy_genome: StrategyGenome,
                     market_data_hash: str,
                     backtest_config: Dict[str, Any]) -> str:
        """Generate unique cache key for a backtest"""
        # Hash strategy genome
        strategy_hash = self._hash_strategy(strategy_genome)
        
        # Hash backtest config
        config_hash = hashlib.md5(
            json.dumps(backtest_config, sort_keys=True).encode()
        ).hexdigest()
        
        return f"{strategy_hash}:{market_data_hash}:{config_hash}"
    
    def _hash_strategy(self, strategy_genome: StrategyGenome) -> str:
        """Generate hash for strategy genome"""
        # Convert to dict and sort for consistent hashing
        strategy_dict = asdict(strategy_genome)
        strategy_json = json.dumps(strategy_dict, sort_keys=True, default=str)
        return hashlib.sha256(strategy_json.encode()).hexdigest()
    
    def _should_evict(self, new_entry_size: int) -> bool:
        """Check if we should evict entries"""
        # Check count limit
        if len(self._cache) >= self.max_size:
            return True
        
        # Check memory limit
        if self.total_size_bytes + new_entry_size > self.max_memory_mb * 1024 * 1024:
            return True
        
        return False
    
    def _evict_one(self) -> None:
        """Evict a single entry based on strategy"""
        if not self._cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            self._evict_lru()
        elif self.strategy == CacheStrategy.LFU:
            self._evict_lfu()
        elif self.strategy == CacheStrategy.TTL:
            self._evict_expired()
        elif self.strategy == CacheStrategy.FIFO:
            self._evict_fifo()
        
        self.evictions += 1
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if self._access_order:
            key = self._access_order[0]
            self._remove_entry(key)
    
    def _evict_lfu(self) -> None:
        """Evict least frequently used entry"""
        if self._frequency_order:
            key = min(self._frequency_order.keys(), key=self._frequency_order.get)
            self._remove_entry(key)
    
    def _evict_expired(self) -> None:
        """Evict expired entries"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        if expired_keys:
            self._remove_entry(expired_keys[0])
        elif self._access_order:
            # Fallback to LRU if no expired entries
            self._evict_lru()
    
    def _evict_fifo(self) -> None:
        """Evict first in entry"""
        if self._access_order:
            key = self._access_order[0]
            self._remove_entry(key)
    
    def _remove_entry(self, key: Union[str, List[str]]) -> None:
        """Remove entry/entries from cache"""
        if isinstance(key, str):
            keys = [key]
        else:
            keys = key
        
        for k in keys:
            if k in self._cache:
                entry = self._cache[k]
                self.total_size_bytes -= entry.size_bytes
                del self._cache[k]
                
                # Update tracking
                if k in self._access_order:
                    self._access_order.remove(k)
                if k in self._frequency_order:
                    del self._frequency_order[k]
    
    def _update_access_tracking(self, key: str, new_entry: bool = False) -> None:
        """Update access tracking structures"""
        if self.strategy == CacheStrategy.LRU or self.strategy == CacheStrategy.FIFO:
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
        
        elif self.strategy == CacheStrategy.LFU:
            self._frequency_order[key] = self._cache[key].access_count
    
    def _init_persistent_storage(self) -> None:
        """Initialize persistent storage database"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "backtest_cache.db"
        
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                data BLOB,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER,
                size_bytes INTEGER,
                ttl_seconds INTEGER
            )
        """)
        conn.commit()
        conn.close()
    
    def _persist_entry(self, entry: CacheEntry) -> None:
        """Persist cache entry to database"""
        conn = sqlite3.connect(str(self.db_path))
        
        ttl_seconds = entry.ttl.total_seconds() if entry.ttl else None
        
        conn.execute("""
            INSERT OR REPLACE INTO cache_entries 
            (key, data, created_at, last_accessed, access_count, size_bytes, ttl_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.key,
            pickle.dumps(entry.result),
            entry.created_at.isoformat(),
            entry.last_accessed.isoformat(),
            entry.access_count,
            entry.size_bytes,
            ttl_seconds
        ))
        
        conn.commit()
        conn.close()
    
    def _load_persistent_cache(self) -> None:
        """Load cache entries from persistent storage"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            SELECT key, data, created_at, last_accessed, access_count, size_bytes, ttl_seconds
            FROM cache_entries
        """)
        
        loaded = 0
        for row in cursor:
            key, data_blob, created_str, accessed_str, count, size, ttl_seconds = row
            
            try:
                # Reconstruct entry
                result = pickle.loads(data_blob)
                ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else None
                
                entry = CacheEntry(
                    key=key,
                    result=result,
                    created_at=datetime.fromisoformat(created_str),
                    last_accessed=datetime.fromisoformat(accessed_str),
                    access_count=count,
                    size_bytes=size,
                    ttl=ttl
                )
                
                # Skip expired entries
                if not entry.is_expired():
                    self._cache[key] = entry
                    self.total_size_bytes += size
                    self._update_access_tracking(key, new_entry=True)
                    loaded += 1
                    
            except Exception as e:
                logger.warning(f"Failed to load cache entry {key}: {e}")
        
        conn.close()
        logger.info(f"Loaded {loaded} entries from persistent cache")
    
    def _clear_persistent_storage(self) -> None:
        """Clear persistent storage"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("DELETE FROM cache_entries")
        conn.commit()
        conn.close()
