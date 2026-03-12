"""
Performance Profiler and Optimizer
===================================
Production-grade profiling and optimization system.
Identifies hot paths and optimizes critical code.
"""

import asyncio
import cProfile
import functools
import io
import logging
import pstats
import sys
import threading
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar
import statistics
from typing import Set
import numpy

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ProfileResult:
    """Profile result for a function."""
    function_name: str
    total_calls: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    percentile_95: float
    percentile_99: float
    last_call_time: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HotSpot:
    """Identified hot spot."""
    function_name: str
    file_path: str
    line_number: int
    total_time: float
    call_count: int
    avg_time: float
    cumulative_time: float
    callers: List[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class OptimizationSuggestion:
    """Optimization suggestion."""
    function_name: str
    issue: str
    suggestion: str
    priority: str  # high, medium, low
    estimated_improvement: str


# ============================================================================
# FUNCTION PROFILER
# ============================================================================

class FunctionProfiler:
    """
    Profiles individual function calls.
    Tracks timing, call counts, and statistics.
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._profiles: Dict[str, List[float]] = defaultdict(list)
        self._call_counts: Dict[str, int] = defaultdict(int)
        self._last_call: Dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def record(self, function_name: str, duration: float):
        """Record a function call."""
        with self._lock:
            self._profiles[function_name].append(duration)
            self._call_counts[function_name] += 1
            self._last_call[function_name] = datetime.utcnow()
            
            # Limit history
            if len(self._profiles[function_name]) > self.max_history:
                self._profiles[function_name] = self._profiles[function_name][-self.max_history:]
    
    def get_result(self, function_name: str) -> Optional[ProfileResult]:
        """Get profile result for function."""
        with self._lock:
            if function_name not in self._profiles:
                return None
            
            times = self._profiles[function_name]
            if not times:
                return None
            
            sorted_times = sorted(times)
            
            return ProfileResult(
                function_name=function_name,
                total_calls=self._call_counts[function_name],
                total_time=sum(times),
                avg_time=statistics.mean(times),
                min_time=min(times),
                max_time=max(times),
                std_dev=statistics.stdev(times) if len(times) > 1 else 0,
                percentile_95=sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 20 else max(times),
                percentile_99=sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 100 else max(times),
                last_call_time=self._last_call.get(function_name, datetime.utcnow()),
            )
    
    def get_all_results(self) -> List[ProfileResult]:
        """Get all profile results."""
        results = []
        with self._lock:
            for name in self._profiles:
                result = self.get_result(name)
                if result:
                    results.append(result)
        return sorted(results, key=lambda x: x.total_time, reverse=True)
    
    def get_slowest(self, n: int = 10) -> List[ProfileResult]:
        """Get slowest functions."""
        return self.get_all_results()[:n]
    
    def reset(self, function_name: Optional[str] = None):
        """Reset profiling data."""
        with self._lock:
            if function_name:
                self._profiles.pop(function_name, None)
                self._call_counts.pop(function_name, None)
                self._last_call.pop(function_name, None)
            else:
                self._profiles.clear()
                self._call_counts.clear()
                self._last_call.clear()


# ============================================================================
# CODE PROFILER
# ============================================================================

class CodeProfiler:
    """
    Full code profiler using cProfile.
    Identifies hot spots and bottlenecks.
    """
    
    def __init__(self):
        self._profiler: Optional[cProfile.Profile] = None
        self._is_profiling = False
        self._results: Optional[pstats.Stats] = None
        self._lock = threading.Lock()
    
    def start(self):
        """Start profiling."""
        with self._lock:
            if self._is_profiling:
                return
            
            self._profiler = cProfile.Profile()
            self._profiler.enable()
            self._is_profiling = True
            logger.info("Code profiling started")
    
    def stop(self) -> Optional[str]:
        """Stop profiling and return results."""
        with self._lock:
            if not self._is_profiling:
                return None
            
            self._profiler.disable()
            self._is_profiling = False
            
            # Get stats
            stream = io.StringIO()
            self._results = pstats.Stats(self._profiler, stream=stream)
            self._results.sort_stats('cumulative')
            self._results.print_stats(50)
            
            logger.info("Code profiling stopped")
            return stream.getvalue()
    
    def get_hot_spots(self, n: int = 20) -> List[HotSpot]:
        """Get hot spots from profiling results."""
        if not self._results:
            return []
        
        hot_spots = []
        
        # Get stats
        stats = self._results.stats
        
        for (file_path, line_number, func_name), (cc, nc, tt, ct, callers) in stats.items():
            if tt > 0.001:  # Filter out very fast functions
                hot_spot = HotSpot(
                    function_name=func_name,
                    file_path=file_path,
                    line_number=line_number,
                    total_time=tt,
                    call_count=nc,
                    avg_time=tt / nc if nc > 0 else 0,
                    cumulative_time=ct,
                    callers=[f"{f}:{l}:{fn}" for (f, l, fn) in callers.keys()][:5],
                )
                hot_spots.append(hot_spot)
        
        # Sort by total time
        hot_spots.sort(key=lambda x: x.total_time, reverse=True)
        
        return hot_spots[:n]
    
    def get_suggestions(self) -> List[OptimizationSuggestion]:
        """Get optimization suggestions."""
        hot_spots = self.get_hot_spots()
        suggestions = []
        
        for spot in hot_spots:
            # Analyze and suggest
            if spot.call_count > 10000 and spot.avg_time > 0.0001:
                suggestions.append(OptimizationSuggestion(
                    function_name=spot.function_name,
                    issue=f"Called {spot.call_count} times with avg {spot.avg_time*1000:.2f}ms",
                    suggestion="Consider caching results or reducing call frequency",
                    priority="high",
                    estimated_improvement="20-50%",
                ))
            
            if spot.total_time > 1.0:
                suggestions.append(OptimizationSuggestion(
                    function_name=spot.function_name,
                    issue=f"Total time: {spot.total_time:.2f}s",
                    suggestion="Profile this function in detail for optimization opportunities",
                    priority="high",
                    estimated_improvement="10-30%",
                ))
            
            if "loop" in spot.function_name.lower() or spot.call_count > 100000:
                suggestions.append(OptimizationSuggestion(
                    function_name=spot.function_name,
                    issue="High call count in potential loop",
                    suggestion="Consider vectorization with numpy or parallel processing",
                    priority="medium",
                    estimated_improvement="50-90%",
                ))
        
        return suggestions


# ============================================================================
# ASYNC PROFILER
# ============================================================================

class AsyncProfiler:
    """
    Profiler for async functions.
    """
    
    def __init__(self):
        self._function_profiler = FunctionProfiler()
        self._active_tasks: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def profile_async(self, func: Callable) -> Callable:
        """Decorator for profiling async functions."""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                self._function_profiler.record(func.__qualname__, duration)
        
        return wrapper
    
    def profile_sync(self, func: Callable) -> Callable:
        """Decorator for profiling sync functions."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                self._function_profiler.record(func.__qualname__, duration)
        
        return wrapper
    
    def get_results(self) -> List[ProfileResult]:
        """Get profiling results."""
        return self._function_profiler.get_all_results()
    
    def get_slowest(self, n: int = 10) -> List[ProfileResult]:
        """Get slowest functions."""
        return self._function_profiler.get_slowest(n)


# ============================================================================
# PERFORMANCE OPTIMIZER
# ============================================================================

class PerformanceOptimizer:
    """
    Automatic performance optimizer.
    Identifies and suggests optimizations.
    """
    
    def __init__(self):
        self._function_profiler = FunctionProfiler()
        self._code_profiler = CodeProfiler()
        self._async_profiler = AsyncProfiler()
        self._thresholds = {
            'slow_function_ms': 100,
            'high_call_count': 10000,
            'memory_threshold_mb': 100,
        }
    
    def set_threshold(self, name: str, value: float):
        """Set optimization threshold."""
        self._thresholds[name] = value
    
    def analyze(self) -> Dict:
        """Analyze performance and return report."""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'function_stats': [],
            'hot_spots': [],
            'suggestions': [],
            'summary': {},
        }
        
        # Function stats
        results = self._function_profiler.get_all_results()
        for result in results[:20]:
            report['function_stats'].append({
                'name': result.function_name,
                'calls': result.total_calls,
                'total_time': result.total_time,
                'avg_time_ms': result.avg_time * 1000,
                'p95_ms': result.percentile_95 * 1000,
            })
        
        # Hot spots
        hot_spots = self._code_profiler.get_hot_spots()
        for spot in hot_spots[:10]:
            report['hot_spots'].append({
                'function': spot.function_name,
                'file': spot.file_path,
                'line': spot.line_number,
                'total_time': spot.total_time,
                'calls': spot.call_count,
            })
        
        # Suggestions
        suggestions = self._code_profiler.get_suggestions()
        for suggestion in suggestions[:10]:
            report['suggestions'].append({
                'function': suggestion.function_name,
                'issue': suggestion.issue,
                'suggestion': suggestion.suggestion,
                'priority': suggestion.priority,
            })
        
        # Summary
        total_time = sum(r.total_time for r in results)
        total_calls = sum(r.total_calls for r in results)
        
        report['summary'] = {
            'total_profiled_time': total_time,
            'total_function_calls': total_calls,
            'functions_profiled': len(results),
            'hot_spots_found': len(hot_spots),
            'suggestions_count': len(suggestions),
        }
        
        return report
    
    def optimize_function(self, func: Callable) -> Callable:
        """Apply optimizations to a function."""
        # Add profiling
        if asyncio.iscoroutinefunction(func):
            return self._async_profiler.profile_async(func)
        else:
            return self._async_profiler.profile_sync(func)


# ============================================================================
# DECORATORS
# ============================================================================

_global_profiler = FunctionProfiler()


def profile(func: Callable) -> Callable:
    """Decorator to profile a function."""
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.perf_counter() - start
            _global_profiler.record(func.__qualname__, duration)
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            duration = time.perf_counter() - start
            _global_profiler.record(func.__qualname__, duration)
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def profile_with_threshold(threshold_ms: float = 100):
    """Decorator to profile and log slow functions."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                _global_profiler.record(func.__qualname__, duration)
                
                if duration * 1000 > threshold_ms:
                    logger.warning(
                        f"Slow function: {func.__qualname__} took {duration*1000:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                _global_profiler.record(func.__qualname__, duration)
                
                if duration * 1000 > threshold_ms:
                    logger.warning(
                        f"Slow function: {func.__qualname__} took {duration*1000:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ============================================================================
# GLOBAL FUNCTIONS
# ============================================================================

def get_profiler() -> FunctionProfiler:
    """Get global function profiler."""
    return _global_profiler


def get_profile_results() -> List[ProfileResult]:
    """Get global profile results."""
    return _global_profiler.get_all_results()


def get_slowest_functions(n: int = 10) -> List[ProfileResult]:
    """Get slowest functions."""
    return _global_profiler.get_slowest(n)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'ProfileResult', 'HotSpot', 'OptimizationSuggestion',
    'FunctionProfiler', 'CodeProfiler', 'AsyncProfiler', 'PerformanceOptimizer',
    'profile', 'profile_with_threshold', 'get_profiler',
    'get_profile_results', 'get_slowest_functions',
]
