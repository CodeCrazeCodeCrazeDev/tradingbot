"""
Memory Hierarchy Design
=======================
3-Tier memory system for AlphaAlgo:

TIER 1: SHORT-TERM MEMORY (Seconds to Minutes)
- Market microstructure
- Execution context
- Order book state
- Recent trades
- TTL: 5 minutes
- Access: All agents, all models

TIER 2: MID-TERM MEMORY (Hours to Days)
- Session regime
- Volatility states
- Liquidity conditions
- Correlation snapshots
- TTL: 7 days
- Access: Research agents, regime models

TIER 3: LONG-TERM MEMORY (Weeks to Forever)
- Archived events
- Training datasets
- Model versions
- Historical outcomes
- Market shock signatures
- TTL: Forever
- Access: Training pipelines, research agents (read-only)

RETENTION RULES:
- Short-term: Auto-expire after TTL
- Mid-term: Compress and archive after TTL
- Long-term: Never delete, only append

ACCESS RULES:
- Live trading: Short-term only (latency critical)
- Research agents: All tiers (read-only)
- Training pipelines: Long-term (write on completion)
- Governance: All tiers (audit access)
"""

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from threading import RLock
from typing import Any, Dict, List, Optional, Callable, Tuple

logger = logging.getLogger(__name__)


class MemoryTier(Enum):
    """Memory tier classification."""
    SHORT_TERM = auto()  # Seconds to minutes
    MID_TERM = auto()    # Hours to days
    LONG_TERM = auto()   # Weeks to forever


class AccessLevel(Enum):
    """Access level for memory operations."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class AgentType(Enum):
    """Types of agents that can access memory."""
    LIVE_TRADING = "live_trading"
    RESEARCH = "research"
    TRAINING = "training"
    GOVERNANCE = "governance"
    SYSTEM = "system"


@dataclass
class MemoryEntry:
    """A single memory entry."""
    key: str
    value: Any
    tier: MemoryTier
    created_at: datetime
    expires_at: Optional[datetime]
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "tier": self.tier.name,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class MemoryQuery:
    """Query for memory retrieval."""
    tier: Optional[MemoryTier] = None
    tags: Optional[List[str]] = None
    key_prefix: Optional[str] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    limit: int = 100
    include_expired: bool = False


# Access control matrix
ACCESS_MATRIX: Dict[AgentType, Dict[MemoryTier, List[AccessLevel]]] = {
    AgentType.LIVE_TRADING: {
        MemoryTier.SHORT_TERM: [AccessLevel.READ, AccessLevel.WRITE],
        MemoryTier.MID_TERM: [AccessLevel.READ],
        MemoryTier.LONG_TERM: [],  # No access for latency reasons
    },
    AgentType.RESEARCH: {
        MemoryTier.SHORT_TERM: [AccessLevel.READ],
        MemoryTier.MID_TERM: [AccessLevel.READ],
        MemoryTier.LONG_TERM: [AccessLevel.READ],
    },
    AgentType.TRAINING: {
        MemoryTier.SHORT_TERM: [],
        MemoryTier.MID_TERM: [AccessLevel.READ],
        MemoryTier.LONG_TERM: [AccessLevel.READ, AccessLevel.WRITE],
    },
    AgentType.GOVERNANCE: {
        MemoryTier.SHORT_TERM: [AccessLevel.READ, AccessLevel.ADMIN],
        MemoryTier.MID_TERM: [AccessLevel.READ, AccessLevel.ADMIN],
        MemoryTier.LONG_TERM: [AccessLevel.READ, AccessLevel.ADMIN],
    },
    AgentType.SYSTEM: {
        MemoryTier.SHORT_TERM: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN],
        MemoryTier.MID_TERM: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN],
        MemoryTier.LONG_TERM: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN],
    },
}


class MemoryStore(ABC):
    """Abstract base class for memory stores."""
    
    @abstractmethod
    def put(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        pass
    
    @abstractmethod
    def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Query memory entries."""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        pass


class ShortTermMemory(MemoryStore):
    """
    Short-Term Memory (Seconds to Minutes)
    
    Stores:
    - Market microstructure (order book imbalance, spread, toxicity)
    - Execution context (pending orders, recent fills)
    - Recent trades and quotes
    
    Characteristics:
    - In-memory storage (fast access)
    - TTL: 5 minutes default
    - Auto-cleanup of expired entries
    - Ring buffer for high-frequency data
    """
    
    DEFAULT_TTL_SECONDS = 300  # 5 minutes
    MAX_ENTRIES = 100000
    
    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, MemoryEntry] = {}
        self._ring_buffer: deque = deque(maxlen=self.MAX_ENTRIES)
        self._lock = RLock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 60  # Cleanup every 60 seconds
    
    def put(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        with self._lock:
            # Set expiration if not set
            if entry.expires_at is None:
                entry.expires_at = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
            
            entry.tier = MemoryTier.SHORT_TERM
            self._store[entry.key] = entry
            self._ring_buffer.append(entry.key)
            
            # Periodic cleanup
            if time.time() - self._last_cleanup > self._cleanup_interval:
                self.cleanup_expired()
            
            return True
    
    def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._store[key]
                return None
            
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            return entry
    
    def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False
    
    def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Query memory entries."""
        with self._lock:
            results = []
            
            for entry in self._store.values():
                if not query.include_expired and entry.is_expired():
                    continue
                
                if query.key_prefix and not entry.key.startswith(query.key_prefix):
                    continue
                
                if query.tags and not any(t in entry.tags for t in query.tags):
                    continue
                
                if query.time_range:
                    start, end = query.time_range
                    if not (start <= entry.created_at <= end):
                        continue
                
                results.append(entry)
                
                if len(results) >= query.limit:
                    break
            
            return results
    
    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._store.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._store[key]
            
            self._last_cleanup = time.time()
            return len(expired_keys)
    
    # Short-term specific methods
    
    def store_microstructure(
        self,
        symbol: str,
        imbalance: float,
        spread: float,
        toxicity: float,
        timestamp: datetime,
    ) -> bool:
        """Store market microstructure data."""
        entry = MemoryEntry(
            key=f"microstructure:{symbol}:{timestamp.timestamp()}",
            value={
                "symbol": symbol,
                "imbalance": imbalance,
                "spread": spread,
                "toxicity": toxicity,
                "timestamp": timestamp.isoformat(),
            },
            tier=MemoryTier.SHORT_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,  # Will be set by put()
            tags=["microstructure", symbol],
        )
        return self.put(entry)
    
    def store_execution_context(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: float,
        status: str,
        fills: List[Dict],
    ) -> bool:
        """Store execution context."""
        entry = MemoryEntry(
            key=f"execution:{order_id}",
            value={
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "status": status,
                "fills": fills,
            },
            tier=MemoryTier.SHORT_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,
            tags=["execution", symbol, status],
        )
        return self.put(entry)
    
    def get_recent_microstructure(
        self,
        symbol: str,
        lookback_seconds: int = 60,
    ) -> List[Dict]:
        """Get recent microstructure data for a symbol."""
        cutoff = datetime.utcnow() - timedelta(seconds=lookback_seconds)
        query = MemoryQuery(
            tags=["microstructure", symbol],
            time_range=(cutoff, datetime.utcnow()),
            limit=1000,
        )
        entries = self.query(query)
        return [e.value for e in entries]


class MidTermMemory(MemoryStore):
    """
    Mid-Term Memory (Hours to Days)
    
    Stores:
    - Session regime (trending, ranging, volatile)
    - Volatility states (realized, implied, regime)
    - Liquidity conditions (depth, spread dynamics)
    - Correlation snapshots
    
    Characteristics:
    - Disk-backed storage with memory cache
    - TTL: 7 days default
    - Compression for older entries
    - Indexed by regime and time
    """
    
    DEFAULT_TTL_DAYS = 7
    CACHE_SIZE = 10000
    
    def __init__(self, ttl_days: int = DEFAULT_TTL_DAYS, storage_path: Optional[str] = None):
        self.ttl_days = ttl_days
        self.storage_path = storage_path or "mid_term_memory"
        self._cache: Dict[str, MemoryEntry] = {}
        self._cache_order: deque = deque(maxlen=self.CACHE_SIZE)
        self._lock = RLock()
        self._disk_store: Dict[str, MemoryEntry] = {}  # Simulated disk store
    
    def put(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        with self._lock:
            if entry.expires_at is None:
                entry.expires_at = datetime.utcnow() + timedelta(days=self.ttl_days)
            
            entry.tier = MemoryTier.MID_TERM
            
            # Store in cache
            self._cache[entry.key] = entry
            self._cache_order.append(entry.key)
            
            # Persist to disk
            self._disk_store[entry.key] = entry
            
            # Evict from cache if full
            if len(self._cache) > self.CACHE_SIZE:
                oldest_key = self._cache_order.popleft()
                if oldest_key in self._cache:
                    del self._cache[oldest_key]
            
            return True
    
    def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry."""
        with self._lock:
            # Check cache first
            entry = self._cache.get(key)
            
            if entry is None:
                # Check disk
                entry = self._disk_store.get(key)
                if entry:
                    # Promote to cache
                    self._cache[key] = entry
                    self._cache_order.append(key)
            
            if entry is None:
                return None
            
            if entry.is_expired():
                self.delete(key)
                return None
            
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            return entry
    
    def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        with self._lock:
            deleted = False
            if key in self._cache:
                del self._cache[key]
                deleted = True
            if key in self._disk_store:
                del self._disk_store[key]
                deleted = True
            return deleted
    
    def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Query memory entries."""
        with self._lock:
            results = []
            
            # Search disk store (comprehensive)
            for entry in self._disk_store.values():
                if not query.include_expired and entry.is_expired():
                    continue
                
                if query.key_prefix and not entry.key.startswith(query.key_prefix):
                    continue
                
                if query.tags and not any(t in entry.tags for t in query.tags):
                    continue
                
                if query.time_range:
                    start, end = query.time_range
                    if not (start <= entry.created_at <= end):
                        continue
                
                results.append(entry)
                
                if len(results) >= query.limit:
                    break
            
            return results
    
    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._disk_store.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                self.delete(key)
            
            return len(expired_keys)
    
    # Mid-term specific methods
    
    def store_regime(
        self,
        symbol: str,
        regime_id: str,
        regime_type: str,
        confidence: float,
        features: Dict[str, float],
        timestamp: datetime,
    ) -> bool:
        """Store regime detection result."""
        entry = MemoryEntry(
            key=f"regime:{symbol}:{timestamp.date().isoformat()}:{regime_id}",
            value={
                "symbol": symbol,
                "regime_id": regime_id,
                "regime_type": regime_type,
                "confidence": confidence,
                "features": features,
                "timestamp": timestamp.isoformat(),
            },
            tier=MemoryTier.MID_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,
            tags=["regime", symbol, regime_type],
        )
        return self.put(entry)
    
    def store_volatility_state(
        self,
        symbol: str,
        realized_vol: float,
        implied_vol: Optional[float],
        vol_regime: str,
        timestamp: datetime,
    ) -> bool:
        """Store volatility state."""
        entry = MemoryEntry(
            key=f"volatility:{symbol}:{timestamp.timestamp()}",
            value={
                "symbol": symbol,
                "realized_vol": realized_vol,
                "implied_vol": implied_vol,
                "vol_regime": vol_regime,
                "timestamp": timestamp.isoformat(),
            },
            tier=MemoryTier.MID_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,
            tags=["volatility", symbol, vol_regime],
        )
        return self.put(entry)
    
    def store_correlation_snapshot(
        self,
        symbols: List[str],
        correlation_matrix: Dict[str, Dict[str, float]],
        timestamp: datetime,
    ) -> bool:
        """Store correlation snapshot."""
        key_hash = hashlib.md5(json.dumps(sorted(symbols)).encode()).hexdigest()[:8]
        entry = MemoryEntry(
            key=f"correlation:{key_hash}:{timestamp.date().isoformat()}",
            value={
                "symbols": symbols,
                "correlation_matrix": correlation_matrix,
                "timestamp": timestamp.isoformat(),
            },
            tier=MemoryTier.MID_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,
            tags=["correlation"] + symbols,
        )
        return self.put(entry)
    
    def get_regime_history(
        self,
        symbol: str,
        lookback_days: int = 7,
    ) -> List[Dict]:
        """Get regime history for a symbol."""
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        query = MemoryQuery(
            tags=["regime", symbol],
            time_range=(cutoff, datetime.utcnow()),
            limit=1000,
        )
        entries = self.query(query)
        return [e.value for e in entries]


class LongTermMemory(MemoryStore):
    """
    Long-Term Memory (Weeks to Forever)
    
    Stores:
    - Archived events (market shocks, anomalies)
    - Training datasets (versioned)
    - Model versions (with metadata)
    - Historical outcomes (trade results)
    - Market shock signatures
    
    Characteristics:
    - Persistent storage (database/object store)
    - TTL: Forever (never delete)
    - Append-only (immutable)
    - Compressed and indexed
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "long_term_memory"
        self._store: Dict[str, MemoryEntry] = {}  # Simulated persistent store
        self._lock = RLock()
        self._index: Dict[str, List[str]] = {}  # Tag -> keys index
    
    def put(self, entry: MemoryEntry) -> bool:
        """Store a memory entry (append-only)."""
        with self._lock:
            entry.tier = MemoryTier.LONG_TERM
            entry.expires_at = None  # Never expires
            
            # Check for duplicate key (immutable)
            if entry.key in self._store:
                logger.warning(f"Attempted to overwrite immutable entry: {entry.key}")
                return False
            
            self._store[entry.key] = entry
            
            # Update index
            for tag in entry.tags:
                if tag not in self._index:
                    self._index[tag] = []
                self._index[tag].append(entry.key)
            
            return True
    
    def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry."""
        with self._lock:
            entry = self._store.get(key)
            if entry:
                entry.access_count += 1
                entry.last_accessed = datetime.utcnow()
            return entry
    
    def delete(self, key: str) -> bool:
        """Delete is NOT allowed for long-term memory."""
        logger.error(f"Attempted to delete immutable long-term memory: {key}")
        return False
    
    def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Query memory entries."""
        with self._lock:
            results = []
            
            # Use index if tags provided
            if query.tags:
                candidate_keys = set()
                for tag in query.tags:
                    if tag in self._index:
                        candidate_keys.update(self._index[tag])
                entries = [self._store[k] for k in candidate_keys if k in self._store]
            else:
                entries = list(self._store.values())
            
            for entry in entries:
                if query.key_prefix and not entry.key.startswith(query.key_prefix):
                    continue
                
                if query.time_range:
                    start, end = query.time_range
                    if not (start <= entry.created_at <= end):
                        continue
                
                results.append(entry)
                
                if len(results) >= query.limit:
                    break
            
            return results
    
    def cleanup_expired(self) -> int:
        """No cleanup for long-term memory."""
        return 0
    
    # Long-term specific methods
    
    def archive_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        timestamp: datetime,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Archive a significant event."""
        event_hash = hashlib.sha256(
            json.dumps(event_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        
        entry = MemoryEntry(
            key=f"event:{event_type}:{timestamp.isoformat()}:{event_hash}",
            value={
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": timestamp.isoformat(),
            },
            tier=MemoryTier.LONG_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,
            tags=["event", event_type] + (tags or []),
        )
        return self.put(entry)
    
    def store_training_dataset(
        self,
        dataset_id: str,
        version: str,
        metadata: Dict[str, Any],
        data_hash: str,
        size_bytes: int,
    ) -> bool:
        """Store training dataset metadata."""
        entry = MemoryEntry(
            key=f"dataset:{dataset_id}:{version}",
            value={
                "dataset_id": dataset_id,
                "version": version,
                "metadata": metadata,
                "data_hash": data_hash,
                "size_bytes": size_bytes,
                "created_at": datetime.utcnow().isoformat(),
            },
            tier=MemoryTier.LONG_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,
            tags=["dataset", dataset_id],
        )
        return self.put(entry)
    
    def store_model_version(
        self,
        model_id: str,
        version: str,
        config: Dict[str, Any],
        metrics: Dict[str, float],
        weights_hash: str,
    ) -> bool:
        """Store model version metadata."""
        entry = MemoryEntry(
            key=f"model:{model_id}:{version}",
            value={
                "model_id": model_id,
                "version": version,
                "config": config,
                "metrics": metrics,
                "weights_hash": weights_hash,
                "created_at": datetime.utcnow().isoformat(),
            },
            tier=MemoryTier.LONG_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,
            tags=["model", model_id],
        )
        return self.put(entry)
    
    def store_outcome(
        self,
        signal_id: str,
        expected: Dict[str, Any],
        realized: Dict[str, Any],
        attribution: Dict[str, Any],
        timestamp: datetime,
    ) -> bool:
        """Store trade outcome for learning."""
        entry = MemoryEntry(
            key=f"outcome:{signal_id}",
            value={
                "signal_id": signal_id,
                "expected": expected,
                "realized": realized,
                "attribution": attribution,
                "timestamp": timestamp.isoformat(),
            },
            tier=MemoryTier.LONG_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,
            tags=["outcome"],
        )
        return self.put(entry)
    
    def store_shock_signature(
        self,
        shock_type: str,
        signature: Dict[str, Any],
        timestamp: datetime,
        impact: Dict[str, float],
    ) -> bool:
        """Store market shock signature for future detection."""
        sig_hash = hashlib.sha256(
            json.dumps(signature, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        
        entry = MemoryEntry(
            key=f"shock:{shock_type}:{timestamp.date().isoformat()}:{sig_hash}",
            value={
                "shock_type": shock_type,
                "signature": signature,
                "timestamp": timestamp.isoformat(),
                "impact": impact,
            },
            tier=MemoryTier.LONG_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,
            tags=["shock", shock_type],
        )
        return self.put(entry)
    
    def find_similar_shocks(
        self,
        current_signature: Dict[str, Any],
        threshold: float = 0.8,
    ) -> List[Dict]:
        """Find historical shocks similar to current conditions."""
        query = MemoryQuery(tags=["shock"], limit=1000)
        entries = self.query(query)
        
        similar = []
        for entry in entries:
            stored_sig = entry.value.get("signature", {})
            similarity = self._compute_signature_similarity(current_signature, stored_sig)
            if similarity >= threshold:
                similar.append({
                    "shock": entry.value,
                    "similarity": similarity,
                })
        
        return sorted(similar, key=lambda x: x["similarity"], reverse=True)
    
    def _compute_signature_similarity(
        self,
        sig1: Dict[str, Any],
        sig2: Dict[str, Any],
    ) -> float:
        """Compute similarity between two shock signatures."""
        # Simple Jaccard-like similarity for demonstration
        keys1 = set(sig1.keys())
        keys2 = set(sig2.keys())
        
        if not keys1 or not keys2:
            return 0.0
        
        common_keys = keys1 & keys2
        if not common_keys:
            return 0.0
        
        similarity_sum = 0.0
        for key in common_keys:
            v1, v2 = sig1[key], sig2[key]
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                # Numeric similarity
                max_val = max(abs(v1), abs(v2), 1e-10)
                similarity_sum += 1 - abs(v1 - v2) / max_val
            elif v1 == v2:
                similarity_sum += 1.0
        
        return similarity_sum / len(keys1 | keys2)


class MemoryHierarchy:
    """
    Unified Memory Hierarchy Manager.
    
    Coordinates access to all three memory tiers with:
    - Access control enforcement
    - Cross-tier queries
    - Automatic tier promotion/demotion
    - Memory statistics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.short_term = ShortTermMemory(
            ttl_seconds=self.config.get("short_term_ttl", 300)
        )
        self.mid_term = MidTermMemory(
            ttl_days=self.config.get("mid_term_ttl", 7)
        )
        self.long_term = LongTermMemory(
            storage_path=self.config.get("long_term_path")
        )
        
        self._stores = {
            MemoryTier.SHORT_TERM: self.short_term,
            MemoryTier.MID_TERM: self.mid_term,
            MemoryTier.LONG_TERM: self.long_term,
        }
    
    def check_access(
        self,
        agent_type: AgentType,
        tier: MemoryTier,
        access_level: AccessLevel,
    ) -> bool:
        """Check if agent has access to tier with given level."""
        allowed = ACCESS_MATRIX.get(agent_type, {}).get(tier, [])
        return access_level in allowed
    
    def put(
        self,
        entry: MemoryEntry,
        agent_type: AgentType,
    ) -> bool:
        """Store entry with access control."""
        if not self.check_access(agent_type, entry.tier, AccessLevel.WRITE):
            logger.warning(
                f"Access denied: {agent_type.name} cannot write to {entry.tier.name}"
            )
            return False
        
        store = self._stores[entry.tier]
        return store.put(entry)
    
    def get(
        self,
        key: str,
        tier: MemoryTier,
        agent_type: AgentType,
    ) -> Optional[MemoryEntry]:
        """Retrieve entry with access control."""
        if not self.check_access(agent_type, tier, AccessLevel.READ):
            logger.warning(
                f"Access denied: {agent_type.name} cannot read from {tier.name}"
            )
            return None
        
        store = self._stores[tier]
        return store.get(key)
    
    def query(
        self,
        query: MemoryQuery,
        agent_type: AgentType,
    ) -> List[MemoryEntry]:
        """Query entries with access control."""
        results = []
        
        if query.tier:
            # Query specific tier
            if self.check_access(agent_type, query.tier, AccessLevel.READ):
                store = self._stores[query.tier]
                results = store.query(query)
        else:
            # Query all accessible tiers
            for tier, store in self._stores.items():
                if self.check_access(agent_type, tier, AccessLevel.READ):
                    tier_results = store.query(query)
                    results.extend(tier_results)
        
        return results[:query.limit]
    
    def promote_to_long_term(
        self,
        key: str,
        source_tier: MemoryTier,
        agent_type: AgentType,
    ) -> bool:
        """Promote entry from short/mid term to long term."""
        if source_tier == MemoryTier.LONG_TERM:
            return False
        
        if not self.check_access(agent_type, source_tier, AccessLevel.READ):
            return False
        if not self.check_access(agent_type, MemoryTier.LONG_TERM, AccessLevel.WRITE):
            return False
        
        source_store = self._stores[source_tier]
        entry = source_store.get(key)
        
        if entry is None:
            return False
        
        # Create new entry for long-term
        long_term_entry = MemoryEntry(
            key=f"promoted:{entry.key}",
            value=entry.value,
            tier=MemoryTier.LONG_TERM,
            created_at=datetime.utcnow(),
            expires_at=None,
            tags=entry.tags + ["promoted", source_tier.name.lower()],
            metadata={
                **entry.metadata,
                "promoted_from": source_tier.name,
                "original_created": entry.created_at.isoformat(),
            },
        )
        
        return self.long_term.put(long_term_entry)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory hierarchy statistics."""
        return {
            "short_term": {
                "entries": len(self.short_term._store),
                "max_entries": self.short_term.MAX_ENTRIES,
                "ttl_seconds": self.short_term.ttl_seconds,
            },
            "mid_term": {
                "entries": len(self.mid_term._disk_store),
                "cache_entries": len(self.mid_term._cache),
                "cache_size": self.mid_term.CACHE_SIZE,
                "ttl_days": self.mid_term.ttl_days,
            },
            "long_term": {
                "entries": len(self.long_term._store),
                "index_tags": len(self.long_term._index),
            },
        }
    
    def cleanup(self) -> Dict[str, int]:
        """Run cleanup on all tiers."""
        return {
            "short_term_removed": self.short_term.cleanup_expired(),
            "mid_term_removed": self.mid_term.cleanup_expired(),
            "long_term_removed": 0,  # Never removes
        }
