"""
Async Profiler - Production-grade async profiling and hotspot detection
JIT/Numba optimization support and performance insights
"""

import asyncio
import cProfile
import pstats
import io
import time
import random
import functools
import logging
import traceback
import sys
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ProfileResult:
    """Result of a profiling session"""
    function_name: str
    total_time: float
    calls: int
    time_per_call: float
    cumulative_time: float
    timestamp: datetime
    memory_delta: Optional[int] = None
    async_wait_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'function_name': self.function_name,
            'total_time': self.total_time,
            'calls': self.calls,
            'time_per_call': self.time_per_call,
            'cumulative_time': self.cumulative_time,
            'timestamp': self.timestamp.isoformat(),
            'memory_delta': self.memory_delta,
            'async_wait_time': self.async_wait_time
        }


@dataclass
class HotspotReport:
    """Hotspot analysis report"""
    top_functions: List[ProfileResult]
    total_time: float
    total_calls: int
    hotspot_threshold: float
    recommendations: List[str]
    generated_at: datetime
    
    def to_markdown(self) -> str:
        lines = [
            "# Performance Hotspot Report",
            f"",
            f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Time:** {self.total_time:.4f}s",
            f"**Total Calls:** {self.total_calls}",
            f"",
            "## Top Hotspots",
            "",
            "| Function | Time (s) | Calls | Time/Call (ms) | % Total |",
            "|----------|----------|-------|----------------|---------|",
        ]
        
        for func in self.top_functions[:20]:
            pct = (func.total_time / self.total_time * 100) if self.total_time > 0 else 0
            lines.append(
                f"| {func.function_name[:50]} | {func.total_time:.4f} | "
                f"{func.calls} | {func.time_per_call*1000:.2f} | {pct:.1f}% |"
            )
            
        if self.recommendations:
            lines.extend([
                "",
                "## Recommendations",
                "",
                *[f"- {r}" for r in self.recommendations]
            ])
            
        return "\n".join(lines)


class AsyncProfiler:
    """
    Production-grade async profiler with hotspot detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Profiling settings
        self.enabled = self.config.get('enabled', True)
        self.sample_rate = self.config.get('sample_rate', 1.0)  # 1.0 = profile all
        self.hotspot_threshold = self.config.get('hotspot_threshold', 0.1)  # 10% of time
        self.max_history = self.config.get('max_history', 1000)
        
        # Storage
        self.profile_history: List[ProfileResult] = []
        self.function_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_time': 0,
            'calls': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'errors': 0
        })
        
        # Active profilers
        self._active_profiles: Dict[str, cProfile.Profile] = {}
        self._lock = threading.Lock()
        
        try:
            # Memory tracking (optional)
            import tracemalloc
            self.tracemalloc = tracemalloc
            self.memory_tracking = self.config.get('memory_tracking', False)
        except ImportError:
            self.tracemalloc = None
            self.memory_tracking = False
        # Numba JIT support
            import numba
            self.numba = numba
            self.jit_available = True
        except ImportError:
            self.numba = None
            self.jit_available = False
            
        logger.info(f"Async profiler initialized (JIT available: {self.jit_available})")
        
    def start_memory_tracking(self):
        """Start memory tracking"""
        if self.tracemalloc and self.memory_tracking:
            self.tracemalloc.start()
            
    def stop_memory_tracking(self) -> Optional[int]:
        """Stop memory tracking and return peak memory"""
        if self.tracemalloc and self.memory_tracking:
            current, peak = self.tracemalloc.get_traced_memory()
            self.tracemalloc.stop()
            return peak
        return None
        
    def profile_function(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator to profile a synchronous function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)
                
            # Sample rate check
            if random.random() > self.sample_rate:
                return func(*args, **kwargs)
                
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            # Memory tracking
            if self.memory_tracking:
                self.start_memory_tracking()
                
            # Time tracking
            start_time = time.perf_counter()
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                end_time = time.perf_counter()
                elapsed = end_time - start_time
                
                memory_delta = self.stop_memory_tracking()
                
                self._record_profile(
                    func_name, elapsed, 1, memory_delta, error is not None
                )
                
        return wrapper
    
    def profile_async_function(self, func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """
        Decorator to profile an async function
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not self.enabled:
                return await func(*args, **kwargs)
                
            # Sample rate check
            if random.random() > self.sample_rate:
                return await func(*args, **kwargs)
                
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            # Memory tracking
            if self.memory_tracking:
                self.start_memory_tracking()
                
            # Time tracking
            start_time = time.perf_counter()
            wall_start = time.time()
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                end_time = time.perf_counter()
                wall_end = time.time()
                
                elapsed = end_time - start_time
                wall_elapsed = wall_end - wall_start
                async_wait = wall_elapsed - elapsed  # Time spent waiting
                
                memory_delta = self.stop_memory_tracking()
                
                self._record_profile(
                    func_name, elapsed, 1, memory_delta, error is not None, async_wait
                )
                
        return wrapper
    
    def _record_profile(
        self,
        func_name: str,
        elapsed: float,
        calls: int,
        memory_delta: Optional[int],
        had_error: bool,
        async_wait: Optional[float] = None
    ):
        """Record profiling result"""
        with self._lock:
            # Update function stats
            stats = self.function_stats[func_name]
            stats['total_time'] += elapsed
            stats['calls'] += calls
            stats['min_time'] = min(stats['min_time'], elapsed)
            stats['max_time'] = max(stats['max_time'], elapsed)
            if had_error:
                stats['errors'] += 1
                
            # Create profile result
            result = ProfileResult(
                function_name=func_name,
                total_time=elapsed,
                calls=calls,
                time_per_call=elapsed / calls if calls > 0 else 0,
                cumulative_time=stats['total_time'],
                timestamp=datetime.now(),
                memory_delta=memory_delta,
                async_wait_time=async_wait
            )
            
            self.profile_history.append(result)
            
            # Trim history
            if len(self.profile_history) > self.max_history:
                self.profile_history = self.profile_history[-self.max_history:]
                
    def profile_block(self, name: str):
        """
        Context manager for profiling a code block
        
        Usage:
            with profiler.profile_block("my_operation"):
                # code to profile
        """
        return ProfileBlock(self, name)
    
    async def profile_async_block(self, name: str):
        """
        Async context manager for profiling
        
        Usage:
            async with profiler.profile_async_block("my_operation"):
                # async code to profile
        """
        return AsyncProfileBlock(self, name)
    
    def run_cprofile(self, func: Callable, *args, **kwargs) -> Tuple[Any, pstats.Stats]:
        """
        Run function with cProfile and return result + stats
        """
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
        finally:
            profiler.disable()
            
        stats = pstats.Stats(profiler)
        return result, stats
    
    def get_hotspots(self, top_n: int = 20) -> HotspotReport:
        """
        Analyze and return hotspot report
        """
        with self._lock:
            # Calculate totals
            total_time = sum(s['total_time'] for s in self.function_stats.values())
            total_calls = sum(s['calls'] for s in self.function_stats.values())
            
            # Sort by total time
            sorted_funcs = sorted(
                self.function_stats.items(),
                key=lambda x: x[1]['total_time'],
                reverse=True
            )
            
            # Create profile results
            top_functions = []
            for func_name, stats in sorted_funcs[:top_n]:
                top_functions.append(ProfileResult(
                    function_name=func_name,
                    total_time=stats['total_time'],
                    calls=stats['calls'],
                    time_per_call=stats['total_time'] / stats['calls'] if stats['calls'] > 0 else 0,
                    cumulative_time=stats['total_time'],
                    timestamp=datetime.now()
                ))
                
            # Generate recommendations
            recommendations = self._generate_recommendations(sorted_funcs, total_time)
            
            return HotspotReport(
                top_functions=top_functions,
                total_time=total_time,
                total_calls=total_calls,
                hotspot_threshold=self.hotspot_threshold,
                recommendations=recommendations,
                generated_at=datetime.now()
            )
    
    def _generate_recommendations(
        self,
        sorted_funcs: List[Tuple[str, Dict]],
        total_time: float
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        for func_name, stats in sorted_funcs[:5]:
            pct = stats['total_time'] / total_time if total_time > 0 else 0
            
            if pct > 0.3:
                recommendations.append(
                    f"🔴 CRITICAL: `{func_name}` uses {pct*100:.1f}% of total time. "
                    f"Consider caching, parallelization, or algorithm optimization."
                )
            elif pct > 0.1:
                recommendations.append(
                    f"🟡 WARNING: `{func_name}` uses {pct*100:.1f}% of total time. "
                    f"Review for optimization opportunities."
                )
                
            # Check for high call count with low time per call
            if stats['calls'] > 10000 and stats['total_time'] / stats['calls'] < 0.0001:
                recommendations.append(
                    f"💡 `{func_name}` is called {stats['calls']} times. "
                    f"Consider batching or reducing call frequency."
                )
                
            # Check for high variance
            if stats['max_time'] > stats['min_time'] * 100 and stats['calls'] > 10:
                recommendations.append(
                    f"⚡ `{func_name}` has high variance (min: {stats['min_time']*1000:.2f}ms, "
                    f"max: {stats['max_time']*1000:.2f}ms). Check for edge cases."
                )
                
        if self.jit_available:
            recommendations.append(
                "💡 Numba JIT is available. Consider using @numba.jit for numerical hotspots."
            )
            
        return recommendations
    
    def get_function_stats(self, func_name: str) -> Optional[Dict[str, Any]]:
        """Get stats for a specific function"""
        return dict(self.function_stats.get(func_name, {}))
    
    def get_recent_profiles(self, count: int = 100) -> List[ProfileResult]:
        """Get recent profile results"""
        return self.profile_history[-count:]
    
    def clear_stats(self):
        """Clear all profiling stats"""
        with self._lock:
            self.function_stats.clear()
            self.profile_history.clear()
            
    def export_stats(self, filepath: str):
        """Export stats to JSON file"""
        data = {
            'function_stats': {k: dict(v) for k, v in self.function_stats.items()},
            'recent_profiles': [p.to_dict() for p in self.profile_history[-100:]],
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
            
        logger.info(f"Stats exported to {filepath}")
        
    def save_hotspot_report(self, filepath: str = "hotspot_report.md"):
        """Save hotspot report to file"""
        report = self.get_hotspots()
        
        with open(filepath, 'w') as f:
            f.write(report.to_markdown())
            
        logger.info(f"Hotspot report saved to {filepath}")
        return filepath


class ProfileBlock:
    """Context manager for profiling code blocks"""
    
    def __init__(self, profiler: AsyncProfiler, name: str):
        self.profiler = profiler
        self.name = name
        self.start_time = None
        
    def __enter__(self):
        if self.profiler.memory_tracking:
            self.profiler.start_memory_tracking()
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        memory_delta = self.profiler.stop_memory_tracking()
        self.profiler._record_profile(
            self.name, elapsed, 1, memory_delta, exc_type is not None
        )
        return False


class AsyncProfileBlock:
    """Async context manager for profiling"""
    
    def __init__(self, profiler: AsyncProfiler, name: str):
        self.profiler = profiler
        self.name = name
        self.start_time = None
        self.wall_start = None
        
    async def __aenter__(self):
        if self.profiler.memory_tracking:
            self.profiler.start_memory_tracking()
        self.start_time = time.perf_counter()
        self.wall_start = time.time()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        wall_elapsed = time.time() - self.wall_start
        async_wait = wall_elapsed - elapsed
        memory_delta = self.profiler.stop_memory_tracking()
        self.profiler._record_profile(
            self.name, elapsed, 1, memory_delta, exc_type is not None, async_wait
        )
        return False


# Decorator shortcuts
def profile_async(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorator to profile async function using global profiler"""
    profiler = get_profiler()
    return profiler.profile_async_function(func)


def profile_sync(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to profile sync function using global profiler"""
    profiler = get_profiler()
    return profiler.profile_function(func)


# Global profiler instance
_global_profiler: Optional[AsyncProfiler] = None


def get_profiler(config: Optional[Dict] = None) -> AsyncProfiler:
    """Get or create global profiler instance"""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = AsyncProfiler(config)
    return _global_profiler


def reset_profiler():
    """Reset global profiler"""
    global _global_profiler
    _global_profiler = None


from typing import Tuple

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


