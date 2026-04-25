"""
Fast Router - Millisecond Latency Optimized
===========================================

High-performance task router optimized for sub-millisecond routing decisions.
Uses pre-computed indices, LRU caching, and minimal overhead.
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from collections import defaultdict, OrderedDict
from functools import lru_cache
import numpy as np

from .capability_registry import CapabilityRegistry, CapabilityRecord

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple LRU cache for routing decisions"""
    
    def __init__(self, capacity: int = 1000):
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        
        if len(self.cache) > self.capacity:
            # Remove oldest
            self.cache.popitem(last=False)
    
    def clear(self):
        self.cache.clear()


@dataclass
class FastRoutingResult:
    """Lightweight routing result optimized for speed"""
    capability_id: Optional[str]
    frontier_model: Optional[str]
    confidence: float
    estimated_latency_ms: float
    decision_time_ms: float
    from_cache: bool


class FastRouter:
    """
    Millisecond-latency optimized router.
    
    Optimizations:
    - Pre-computed capability indices by category
    - LRU cache for repeated task patterns
    - Minimal memory allocations
    - Async-safe without locks where possible
    - SIMD-friendly score computations
    """
    
    def __init__(self, registry: CapabilityRegistry, cache_size: int = 10000):
        self.registry = registry
        
        # Pre-computed indices
        self._category_index: Dict[str, List[CapabilityRecord]] = defaultdict(list)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Caches
        self._routing_cache = LRUCache(cache_size)
        self._capability_cache: Dict[str, CapabilityRecord] = {}
        
        # Performance tracking
        self._stats = {
            'total_routes': 0,
            'cache_hits': 0,
            'avg_decision_time_ms': 0.0
        }
        
        # Frontier model fallbacks
        self._frontier_models: List[str] = []
        self._category_defaults: Dict[str, str] = {}
        
        # Refresh index periodically
        self._last_index_refresh = 0
        self._index_refresh_interval = 60  # seconds
        
        logger.info(f"FastRouter initialized with {cache_size} entry cache")
    
    async def refresh_index(self):
        """Refresh capability indices"""
        current_time = time.time()
        if current_time - self._last_index_refresh < self._index_refresh_interval:
            return
        
        # Clear old indices
        self._category_index.clear()
        self._tag_index.clear()
        self._capability_cache.clear()
        
        # Rebuild from registry
        all_capabilities = self.registry.get_all_capabilities(status='active')
        
        for cap in all_capabilities:
            # Index by category
            self._category_index[cap.task_category].append(cap)
            
            # Index by tags
            for tag in cap.task_tags:
                self._tag_index[tag].add(cap.capability_id)
            
            # Cache capability
            self._capability_cache[cap.capability_id] = cap
        
        # Sort by performance for each category
        for category in self._category_index:
            self._category_index[category].sort(
                key=lambda c: c.performance_score * c.reliability_score,
                reverse=True
            )
        
        self._last_index_refresh = current_time
        logger.debug(f"Index refreshed: {len(all_capabilities)} capabilities")
    
    async def route(self,
                   task_hash: str,
                   task_category: str,
                   tags: Optional[List[str]] = None,
                   max_latency_ms: Optional[float] = None,
                   required_tags: Optional[Set[str]] = None) -> FastRoutingResult:
        """
        Route a task in under 1 millisecond.
        
        Args:
            task_hash: Hash of the task for caching
            task_category: Primary category
            tags: Optional tags for matching
            max_latency_ms: Maximum acceptable latency
            required_tags: Tags that must be present
        
        Returns:
            FastRoutingResult with routing decision
        """
        start_time = time.perf_counter()
        
        # Check cache first
        cached = self._routing_cache.get(task_hash)
        if cached:
            self._stats['cache_hits'] += 1
            self._stats['total_routes'] += 1
            
            decision_time = (time.perf_counter() - start_time) * 1000
            self._update_avg_decision_time(decision_time)
            
            return FastRoutingResult(
                capability_id=cached['capability_id'],
                frontier_model=cached.get('frontier_model'),
                confidence=cached['confidence'],
                estimated_latency_ms=cached['estimated_latency_ms'],
                decision_time_ms=decision_time,
                from_cache=True
            )
        
        # Ensure index is fresh
        await self.refresh_index()
        
        # Find candidates
        candidates = self._category_index.get(task_category, [])
        
        if required_tags:
            # Filter by required tags
            candidates = [
                c for c in candidates
                if required_tags.issubset(set(c.task_tags))
            ]
        
        if max_latency_ms:
            candidates = [c for c in candidates if c.latency_ms <= max_latency_ms]
        
        selected_capability = None
        selected_model = None
        confidence = 0.0
        estimated_latency = 0.0
        
        if candidates:
            # Greedy selection: pick best performer
            best = candidates[0]
            
            # Calculate confidence based on track record
            usage_factor = min(1.0, best.usage_count / 100)  # Confidence grows with usage
            confidence = best.performance_score * best.reliability_score * usage_factor
            
            selected_capability = best.capability_id
            estimated_latency = best.latency_ms
        else:
            # No distilled capabilities - use frontier model
            selected_model = self._category_defaults.get(task_category)
            if not selected_model and self._frontier_models:
                selected_model = self._frontier_models[0]
            
            confidence = 0.6  # Lower confidence for frontier
            estimated_latency = 500  # Default estimate for API call
        
        decision_time = (time.perf_counter() - start_time) * 1000
        self._update_avg_decision_time(decision_time)
        self._stats['total_routes'] += 1
        
        # Cache the decision
        self._routing_cache.put(task_hash, {
            'capability_id': selected_capability,
            'frontier_model': selected_model,
            'confidence': confidence,
            'estimated_latency_ms': estimated_latency
        })
        
        return FastRoutingResult(
            capability_id=selected_capability,
            frontier_model=selected_model,
            confidence=confidence,
            estimated_latency_ms=estimated_latency,
            decision_time_ms=decision_time,
            from_cache=False
        )
    
    def _update_avg_decision_time(self, decision_time_ms: float):
        """Update running average decision time"""
        alpha = 0.1  # EMA smoothing factor
        self._stats['avg_decision_time_ms'] = (
            (1 - alpha) * self._stats['avg_decision_time_ms'] +
            alpha * decision_time_ms
        )
    
    def register_frontier_model(self, model_id: str, default_for: Optional[List[str]] = None):
        """Register a frontier model as fallback"""
        if model_id not in self._frontier_models:
            self._frontier_models.append(model_id)
        
        if default_for:
            for category in default_for:
                self._category_defaults[category] = model_id
    
    def get_capability_implementation(self, capability_id: str) -> Optional[CapabilityRecord]:
        """Get cached capability record"""
        return self._capability_cache.get(capability_id)
    
    def invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate routing cache"""
        if pattern:
            # Invalidate entries matching pattern
            keys_to_remove = [k for k in self._routing_cache.cache.keys() if pattern in k]
            for k in keys_to_remove:
                del self._routing_cache.cache[k]
        else:
            self._routing_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        total = self._stats['total_routes']
        return {
            'total_routes': total,
            'cache_hits': self._stats['cache_hits'],
            'cache_hit_rate': self._stats['cache_hits'] / max(1, total),
            'avg_decision_time_ms': self._stats['avg_decision_time_ms'],
            'indexed_categories': len(self._category_index),
            'cached_capabilities': len(self._capability_cache),
            'cache_entries': len(self._routing_cache.cache)
        }


class AdaptiveFastRouter(FastRouter):
    """
    Fast router with adaptive capabilities.
    
    Learns from routing outcomes to improve decisions.
    """
    
    def __init__(self, registry: CapabilityRegistry, cache_size: int = 10000):
        super().__init__(registry, cache_size)
        
        # Track outcomes for learning
        self._outcome_history: Dict[str, List[bool]] = defaultdict(list)
        self._capability_scores: Dict[str, float] = {}
        
        # Exploration
        self.exploration_rate = 0.05
    
    async def route(self,
                   task_hash: str,
                   task_category: str,
                   tags: Optional[List[str]] = None,
                   max_latency_ms: Optional[float] = None,
                   required_tags: Optional[Set[str]] = None,
                   allow_exploration: bool = True) -> FastRoutingResult:
        """
        Route with adaptive learning.
        """
        # Check for exploration
        if allow_exploration and np.random.random() < self.exploration_rate:
            # Explore: try a less-used capability
            return await self._explore_route(
                task_category, max_latency_ms, required_tags
            )
        
        # Otherwise use standard routing
        return await super().route(
            task_hash, task_category, tags, max_latency_ms, required_tags
        )
    
    async def _explore_route(self,
                            task_category: str,
                            max_latency_ms: Optional[float] = None,
                            required_tags: Optional[Set[str]] = None) -> FastRoutingResult:
        """Explore by trying a less-used capability"""
        candidates = self._category_index.get(task_category, [])
        
        if required_tags:
            candidates = [
                c for c in candidates
                if required_tags.issubset(set(c.task_tags))
            ]
        
        if max_latency_ms:
            candidates = [c for c in candidates if c.latency_ms <= max_latency_ms]
        
        if len(candidates) < 2:
            # Not enough to explore
            return await super().route("", task_category, None, max_latency_ms, required_tags)
        
        # Pick based on inverse usage (favor less-used)
        weights = [1.0 / (1 + c.usage_count) for c in candidates]
        weights = np.array(weights) / sum(weights)
        
        selected = np.random.choice(candidates, p=weights)
        
        start_time = time.perf_counter()
        
        usage_factor = min(1.0, selected.usage_count / 100)
        confidence = selected.performance_score * selected.reliability_score * usage_factor * 0.8  # Lower confidence for exploration
        
        decision_time = (time.perf_counter() - start_time) * 1000
        
        return FastRoutingResult(
            capability_id=selected.capability_id,
            frontier_model=None,
            confidence=confidence,
            estimated_latency_ms=selected.latency_ms,
            decision_time_ms=decision_time,
            from_cache=False
        )
    
    def record_outcome(self, capability_id: str, success: bool):
        """Record outcome for learning"""
        self._outcome_history[capability_id].append(success)
        
        # Keep history bounded
        if len(self._outcome_history[capability_id]) > 100:
            self._outcome_history[capability_id] = self._outcome_history[capability_id][-50:]
        
        # Update score
        outcomes = self._outcome_history[capability_id]
        if outcomes:
            success_rate = sum(outcomes) / len(outcomes)
            recency_weight = np.linspace(0.5, 1.0, len(outcomes))
            weighted_success = np.average(outcomes, weights=recency_weight)
            
            self._capability_scores[capability_id] = weighted_success
    
    def get_capability_score(self, capability_id: str) -> float:
        """Get learned score for capability"""
        return self._capability_scores.get(capability_id, 0.5)


def create_fast_router(registry: CapabilityRegistry, 
                       cache_size: int = 10000,
                       adaptive: bool = True) -> FastRouter:
    """Factory for creating fast router"""
    if adaptive:
        return AdaptiveFastRouter(registry, cache_size)
    return FastRouter(registry, cache_size)
