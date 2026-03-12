"""
Elite Performance Profiler & Optimizer
Real-time performance monitoring and bottleneck detection
"""

import time
import asyncio
import functools
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import psutil
import tracemalloc
from collections import defaultdict

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


@dataclass
class PerformanceMetric:
    """Performance metric for a function/operation"""
    name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_call_time: Optional[datetime] = None
    memory_usage: List[float] = field(default_factory=list)


class PerformanceProfiler:
    """
    Elite Performance Profiler
    
    Features:
    - Function execution timing
    - Memory usage tracking
    - CPU usage monitoring
    - Bottleneck detection
    - Performance alerts
    """
    
    def __init__(self, enable_memory_tracking: bool = True):
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.enable_memory_tracking = enable_memory_tracking
        self.bottleneck_threshold = 1.0  # seconds
        
        if enable_memory_tracking:
            tracemalloc.start()
        
        logger.info("Performance Profiler initialized")
    
    def profile(self, name: Optional[str] = None):
        """Decorator to profile function performance"""
        def decorator(func: Callable) -> Callable:
            func_name = name or f"{func.__module__}.{func.__name__}"
            
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    return await self._profile_async(func_name, func, *args, **kwargs)
                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    return self._profile_sync(func_name, func, *args, **kwargs)
                return sync_wrapper
        
        return decorator
    
    def _profile_sync(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """Profile synchronous function"""
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage() if self.enable_memory_tracking else 0
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start_time
            end_memory = self._get_memory_usage() if self.enable_memory_tracking else 0
            memory_delta = end_memory - start_memory
            
            self._record_metric(name, elapsed, memory_delta)
    
    async def _profile_async(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """Profile asynchronous function"""
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage() if self.enable_memory_tracking else 0
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start_time
            end_memory = self._get_memory_usage() if self.enable_memory_tracking else 0
            memory_delta = end_memory - start_memory
            
            self._record_metric(name, elapsed, memory_delta)
    
    def _record_metric(self, name: str, elapsed: float, memory_delta: float):
        """Record performance metric"""
        if name not in self.metrics:
            self.metrics[name] = PerformanceMetric(name=name)
        
        metric = self.metrics[name]
        metric.call_count += 1
        metric.total_time += elapsed
        metric.min_time = min(metric.min_time, elapsed)
        metric.max_time = max(metric.max_time, elapsed)
        metric.avg_time = metric.total_time / metric.call_count
        metric.last_call_time = datetime.now()
        
        if self.enable_memory_tracking:
            metric.memory_usage.append(memory_delta)
        
        # Check for bottleneck
        if elapsed > self.bottleneck_threshold:
            logger.warning(f"⚠️ Bottleneck detected: {name} took {elapsed:.3f}s")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            return current / 1024 / 1024  # Convert to MB
        return 0.0
    
    def get_report(self, top_n: int = 10) -> Dict:
        """Get performance report"""
        # Sort by total time
        sorted_metrics = sorted(
            self.metrics.values(),
            key=lambda m: m.total_time,
            reverse=True
        )[:top_n]
        
        return {
            'total_functions': len(self.metrics),
            'total_calls': sum(m.call_count for m in self.metrics.values()),
            'top_bottlenecks': [
                {
                    'name': m.name,
                    'calls': m.call_count,
                    'total_time': f"{m.total_time:.3f}s",
                    'avg_time': f"{m.avg_time:.3f}s",
                    'min_time': f"{m.min_time:.3f}s",
                    'max_time': f"{m.max_time:.3f}s",
                    'avg_memory': f"{sum(m.memory_usage)/len(m.memory_usage):.2f}MB" if m.memory_usage else "N/A"
                }
                for m in sorted_metrics
            ]
        }
    
    def get_system_metrics(self) -> Dict:
        """Get system resource metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available / 1024 / 1024,
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / 1024 / 1024 / 1024
        }
    
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
        logger.info("Performance metrics reset")


class PerformanceOptimizer:
    """
    Performance Optimizer
    
    Provides optimization recommendations based on profiling data
    """
    
    def __init__(self, profiler: PerformanceProfiler):
        self.profiler = profiler
    
    def analyze_bottlenecks(self) -> List[Dict]:
        """Analyze and provide optimization recommendations"""
        recommendations = []
        
        for name, metric in self.profiler.metrics.items():
            # Slow average execution
            if metric.avg_time > 0.5:
                recommendations.append({
                    'function': name,
                    'issue': 'Slow execution',
                    'avg_time': metric.avg_time,
                    'recommendation': 'Consider async execution, caching, or algorithm optimization'
                })
            
            # High call frequency with moderate time
            if metric.call_count > 1000 and metric.avg_time > 0.01:
                recommendations.append({
                    'function': name,
                    'issue': 'High frequency calls',
                    'call_count': metric.call_count,
                    'recommendation': 'Consider caching results or reducing call frequency'
                })
            
            # High memory usage
            if metric.memory_usage:
                avg_memory = sum(metric.memory_usage) / len(metric.memory_usage)
                if avg_memory > 100:  # More than 100MB
                    recommendations.append({
                        'function': name,
                        'issue': 'High memory usage',
                        'avg_memory_mb': avg_memory,
                        'recommendation': 'Review data structures and consider memory optimization'
                    })
        
        return recommendations
    
    def suggest_optimizations(self) -> Dict:
        """Get optimization suggestions"""
        system_metrics = self.profiler.get_system_metrics()
        bottlenecks = self.analyze_bottlenecks()
        
        suggestions = {
            'system_health': 'GOOD',
            'bottlenecks_found': len(bottlenecks),
            'recommendations': bottlenecks
        }
        
        # System-level recommendations
        if system_metrics['cpu_percent'] > 80:
            suggestions['system_health'] = 'WARNING'
            suggestions['system_recommendations'] = suggestions.get('system_recommendations', [])
            suggestions['system_recommendations'].append('High CPU usage - consider scaling or optimization')
        
        if system_metrics['memory_percent'] > 80:
            suggestions['system_health'] = 'WARNING'
            suggestions['system_recommendations'] = suggestions.get('system_recommendations', [])
            suggestions['system_recommendations'].append('High memory usage - review memory leaks')
        
        return suggestions


# Singleton instance
_profiler_instance: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """Get singleton profiler instance"""
    global _profiler_instance
    if _profiler_instance is None:
        _profiler_instance = PerformanceProfiler()
    return _profiler_instance


# Convenience decorator
def profile(name: Optional[str] = None):
    """Convenience decorator using singleton profiler"""
    return get_profiler().profile(name)


# Export
__all__ = ['PerformanceProfiler', 'PerformanceOptimizer', 'PerformanceMetric', 'profile', 'get_profiler']
