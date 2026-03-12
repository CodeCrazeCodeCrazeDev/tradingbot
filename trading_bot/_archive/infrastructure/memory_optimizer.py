"""
Memory Optimizer

Reduces memory usage through garbage collection, caching optimization, and resource management.
"""

import gc
import sys
import logging
import psutil
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from functools import wraps
import weakref

logger = logging.getLogger(__name__)


class MemoryOptimizer:
    """Optimize memory usage and prevent memory leaks"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Configuration
        self.min_free_memory_mb = self.config.get('min_free_memory_mb', 500)  # Target: >500MB
        self.gc_threshold = self.config.get('gc_threshold', 0.8)  # Trigger GC at 80% usage
        self.enable_aggressive_gc = self.config.get('enable_aggressive_gc', True)
        self.cache_size_limit_mb = self.config.get('cache_size_limit_mb', 100)
        
        # State
        self.memory_history: List[float] = []
        self.gc_count = 0
        self.last_gc_time = datetime.now()
        
        # Configure garbage collection
        if self.enable_aggressive_gc:
            gc.set_threshold(700, 10, 10)  # More aggressive GC
        
        logger.info(f"Memory optimizer initialized - Min free: {self.min_free_memory_mb}MB")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage
        
        Returns:
            Memory usage statistics in MB
        """
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            # System memory
            virtual_memory = psutil.virtual_memory()
            
            usage = {
                'process_rss_mb': memory_info.rss / (1024 * 1024),
                'process_vms_mb': memory_info.vms / (1024 * 1024),
                'system_total_mb': virtual_memory.total / (1024 * 1024),
                'system_available_mb': virtual_memory.available / (1024 * 1024),
                'system_used_mb': virtual_memory.used / (1024 * 1024),
                'system_percent': virtual_memory.percent
            }
            
            # Record history
            self.memory_history.append(usage['process_rss_mb'])
            if len(self.memory_history) > 1000:
                self.memory_history = self.memory_history[-1000:]
            
            return usage
            
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {}
    
    def is_memory_critical(self) -> bool:
        """
        Check if memory usage is critical
        
        Returns:
            True if memory is critically low
        """
        usage = self.get_memory_usage()
        
        if not usage:
            return False
        
        # Check available memory
        available_mb = usage.get('system_available_mb', 1000)
        
        return available_mb < self.min_free_memory_mb
    
    def optimize_memory(self, force: bool = False) -> Dict[str, Any]:
        """
        Optimize memory usage
        
        Args:
            force: Force optimization even if not critical
            
        Returns:
            Optimization results
        """
        before = self.get_memory_usage()
        
        if not force and not self.is_memory_critical():
            return {
                'optimized': False,
                'reason': 'Memory usage acceptable',
                'before_mb': before.get('process_rss_mb', 0)
            }
        
        logger.info("Starting memory optimization...")
        
        # 1. Clear weak references
        gc.collect(0)
        
        # 2. Full garbage collection
        collected = gc.collect()
        self.gc_count += 1
        self.last_gc_time = datetime.now()
        
        # 3. Clear caches (if available)
        self._clear_caches()
        
        # 4. Final full collection
        gc.collect()
        
        after = self.get_memory_usage()
        
        freed_mb = before.get('process_rss_mb', 0) - after.get('process_rss_mb', 0)
        
        result = {
            'optimized': True,
            'before_mb': before.get('process_rss_mb', 0),
            'after_mb': after.get('process_rss_mb', 0),
            'freed_mb': freed_mb,
            'objects_collected': collected,
            'gc_count': self.gc_count
        }
        
        logger.info(f"Memory optimized: Freed {freed_mb:.1f}MB, collected {collected} objects")
        
        return result
    
    def _clear_caches(self):
        """Clear internal caches"""
        try:
            # Clear function caches
            for obj in gc.get_objects():
                if hasattr(obj, 'cache_clear') and callable(obj.cache_clear):
                    try:
                        obj.cache_clear()
                    except Exception:
                        pass
            
            logger.debug("Caches cleared")
        except Exception as e:
            logger.warning(f"Cache clearing failed: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics
        
        Returns:
            Memory statistics
        """
        usage = self.get_memory_usage()
        
        stats = {
            'current_usage_mb': usage.get('process_rss_mb', 0),
            'available_mb': usage.get('system_available_mb', 0),
            'system_percent': usage.get('system_percent', 0),
            'gc_count': self.gc_count,
            'last_gc': self.last_gc_time.isoformat() if self.last_gc_time else None,
            'is_critical': self.is_memory_critical(),
            'target_free_mb': self.min_free_memory_mb
        }
        
        if self.memory_history:
            stats['avg_usage_mb'] = sum(self.memory_history) / len(self.memory_history)
            stats['max_usage_mb'] = max(self.memory_history)
            stats['min_usage_mb'] = min(self.memory_history)
        
        return stats
    
    def get_optimization_recommendations(self) -> List[str]:
        """
        Get memory optimization recommendations
        
        Returns:
            List of recommendations
        """
        recommendations = []
        usage = self.get_memory_usage()
        
        available_mb = usage.get('system_available_mb', 1000)
        process_mb = usage.get('process_rss_mb', 0)
        
        if available_mb < self.min_free_memory_mb:
            recommendations.append(
                f"Low available memory: {available_mb:.0f}MB (target: >{self.min_free_memory_mb}MB)"
            )
            recommendations.append("Consider running memory optimization")
        
        if process_mb > 1000:
            recommendations.append(
                f"High process memory: {process_mb:.0f}MB - Consider restarting"
            )
        
        if not self.enable_aggressive_gc:
            recommendations.append("Enable aggressive garbage collection")
        
        # Check for memory growth
        if len(self.memory_history) > 100:
            recent_avg = sum(self.memory_history[-100:]) / 100
            old_avg = sum(self.memory_history[:100]) / 100
            growth = ((recent_avg - old_avg) / old_avg) * 100
            
            if growth > 20:
                recommendations.append(
                    f"Memory usage growing: +{growth:.1f}% - Possible memory leak"
                )
        
        return recommendations
    
    def monitor_memory(self) -> bool:
        """
        Monitor memory and optimize if needed
        
        Returns:
            True if optimization was performed
        """
        if self.is_memory_critical():
            logger.warning("Critical memory usage detected - optimizing...")
            result = self.optimize_memory(force=True)
            return result.get('optimized', False)
        
        return False


def memory_efficient(func):
    """
    Decorator to make function memory efficient
    
    Performs garbage collection after function execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        gc.collect()
        return result
    
    return wrapper


def memory_efficient_async(func):
    """
    Decorator to make async function memory efficient
    
    Performs garbage collection after function execution
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        gc.collect()
        return result
    
    return wrapper


class MemoryMonitor:
    """Continuous memory monitoring"""
    
    def __init__(self, optimizer: MemoryOptimizer):
        self.optimizer = optimizer
        self.monitoring = False
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """
        Start continuous memory monitoring
        
        Args:
            interval_seconds: Monitoring interval
        """
        import asyncio
        
        self.monitoring = True
        logger.info(f"Memory monitoring started (interval: {interval_seconds}s)")
        
        while self.monitoring:
            try:
                # Check memory
                self.optimizer.monitor_memory()
                
                # Log stats
                stats = self.optimizer.get_memory_stats()
                logger.info(
                    f"Memory: {stats['current_usage_mb']:.0f}MB used, "
                    f"{stats['available_mb']:.0f}MB available"
                )
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        logger.info("Memory monitoring stopped")


# Singleton instance
_memory_optimizer: Optional[MemoryOptimizer] = None


def get_memory_optimizer(config: Optional[Dict[str, Any]] = None) -> MemoryOptimizer:
    """Get singleton memory optimizer instance"""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer(config)
    return _memory_optimizer


# Utility functions
def optimize_memory_now() -> Dict[str, Any]:
    """Optimize memory immediately"""
    optimizer = get_memory_optimizer()
    return optimizer.optimize_memory(force=True)


def get_current_memory_mb() -> float:
    """Get current process memory usage in MB"""
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def is_memory_available(required_mb: float = 100) -> bool:
    """
    Check if required memory is available
    
    Args:
        required_mb: Required memory in MB
        
    Returns:
        True if memory is available
    """
    try:
        available = psutil.virtual_memory().available / (1024 * 1024)
        return available >= required_mb
    except Exception:
        return True  # Assume available if check fails
