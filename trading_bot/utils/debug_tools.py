"""
Debug and Profiling Tools for Trading Bot
Provides utilities for debugging, tracing, and performance analysis
"""

import functools
import time
import tracemalloc
import logging
from typing import Any, Callable, Dict, Optional
from datetime import datetime
from pathlib import Path
import json
import psutil
import os

logger = logging.getLogger(__name__)


class DebugTracer:
    """Function execution tracer for debugging"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.traces = []
        
    def trace(self, func: Callable) -> Callable:
        """Decorator to trace function execution"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                trace_info = {
                    'timestamp': datetime.now().isoformat(),
                    'function': func_name,
                    'duration': duration,
                    'status': 'success',
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
                
                self.traces.append(trace_info)
                logger.debug(f"TRACE: {func_name} completed in {duration:.4f}s")
                
                if self.log_file:
                    self._save_trace(trace_info)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                trace_info = {
                    'timestamp': datetime.now().isoformat(),
                    'function': func_name,
                    'duration': duration,
                    'status': 'error',
                    'error': str(e),
                    'traceback': tracemalloc.format_exception(e)
                }
                
                self.traces.append(trace_info)
                logger.error(f"TRACE ERROR: {func_name} failed after {duration:.4f}s: {e}")
                
                if self.log_file:
                    self._save_trace(trace_info)
                
                raise
        
        return wrapper
    
    def _save_trace(self, trace_info: Dict):
        """Save trace to log file"""
        try:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_path, 'a') as f:
                f.write(json.dumps(trace_info) + '\n')
        except Exception as e:
            logger.warning(f"Failed to save trace: {e}")
    
    def get_summary(self) -> Dict:
        """Get summary of traced executions"""
        if not self.traces:
            return {}
        
        total_calls = len(self.traces)
        successful_calls = sum(1 for t in self.traces if t['status'] == 'success')
        failed_calls = total_calls - successful_calls
        total_duration = sum(t['duration'] for t in self.traces)
        avg_duration = total_duration / total_calls if total_calls > 0 else 0
        
        return {
            'total_calls': total_calls,
            'successful': successful_calls,
            'failed': failed_calls,
            'total_duration': total_duration,
            'avg_duration': avg_duration,
            'traces': self.traces
        }


class MemoryProfiler:
    """Memory usage profiler"""
    
    def __init__(self):
        self.snapshots = {}
        self.tracking = False
        
    def start(self):
        """Start memory tracking"""
        tracemalloc.start()
        self.tracking = True
        logger.info("Memory tracking started")
    
    def stop(self):
        """Stop memory tracking"""
        if self.tracking:
            tracemalloc.stop()
            self.tracking = False
            logger.info("Memory tracking stopped")
    
    def snapshot(self, name: str):
        """Take memory snapshot"""
        if not self.tracking:
            self.start()
        
        snapshot = tracemalloc.take_snapshot()
        self.snapshots[name] = {
            'timestamp': datetime.now().isoformat(),
            'snapshot': snapshot,
            'stats': self._get_memory_stats()
        }
        
        logger.info(f"Memory snapshot '{name}' taken: {self.snapshots[name]['stats']}")
        
        return self.snapshots[name]['stats']
    
    def compare(self, snapshot1: str, snapshot2: str, top: int = 10):
        """Compare two memory snapshots"""
        if snapshot1 not in self.snapshots or snapshot2 not in self.snapshots:
            logger.error("One or both snapshots not found")
            return None
        
        snap1 = self.snapshots[snapshot1]['snapshot']
        snap2 = self.snapshots[snapshot2]['snapshot']
        
        stats = snap2.compare_to(snap1, 'lineno')
        
        print(f"\n{'='*70}")
        print(f"Memory Comparison: {snapshot1} -> {snapshot2}")
        print(f"{'='*70}")
        
        for stat in stats[:top]:
            print(stat)
        
        return stats
    
    def _get_memory_stats(self) -> Dict:
        """Get current memory statistics"""
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        return {
            'rss_mb': mem_info.rss / 1024 / 1024,
            'vms_mb': mem_info.vms / 1024 / 1024,
            'percent': process.memory_percent()
        }


class PerformanceProfiler:
    """Performance profiler for code sections"""
    
    def __init__(self):
        self.profiles = {}
        
    def __call__(self, name: str):
        """Context manager for profiling code sections"""
        return self._ProfileContext(self, name)
    
    class _ProfileContext:
        def __init__(self, profiler, name):
            self.profiler = profiler
            self.name = name
            self.start_time = None
            self.start_memory = None
            
        def __enter__(self):
            self.start_time = time.time()
            process = psutil.Process(os.getpid())
            self.start_memory = process.memory_info().rss / 1024 / 1024
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            process = psutil.Process(os.getpid())
            end_memory = process.memory_info().rss / 1024 / 1024
            memory_delta = end_memory - self.start_memory
            
            profile_data = {
                'timestamp': datetime.now().isoformat(),
                'duration': duration,
                'memory_delta_mb': memory_delta,
                'success': exc_type is None
            }
            
            if self.name not in self.profiler.profiles:
                self.profiler.profiles[self.name] = []
            
            self.profiler.profiles[self.name].append(profile_data)
            
            logger.debug(f"PROFILE [{self.name}]: {duration:.4f}s, Memory: {memory_delta:+.2f}MB")
    
    def get_summary(self) -> Dict:
        """Get profiling summary"""
        summary = {}
        
        for name, profiles in self.profiles.items():
            if not profiles:
                continue
            
            durations = [p['duration'] for p in profiles]
            memory_deltas = [p['memory_delta_mb'] for p in profiles]
            
            summary[name] = {
                'calls': len(profiles),
                'total_duration': sum(durations),
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'avg_memory_delta': sum(memory_deltas) / len(memory_deltas),
                'total_memory_delta': sum(memory_deltas)
            }
        
        return summary
    
    def print_summary(self):
        """Print profiling summary"""
        summary = self.get_summary()
        
        print(f"\n{'='*70}")
        print("PERFORMANCE PROFILE SUMMARY")
        print(f"{'='*70}")
        
        for name, stats in sorted(summary.items(), key=lambda x: x[1]['total_duration'], reverse=True):
            print(f"\n{name}:")
            print(f"  Calls: {stats['calls']}")
            print(f"  Total Duration: {stats['total_duration']:.4f}s")
            print(f"  Avg Duration: {stats['avg_duration']:.4f}s")
            print(f"  Min/Max: {stats['min_duration']:.4f}s / {stats['max_duration']:.4f}s")
            print(f"  Avg Memory Delta: {stats['avg_memory_delta']:+.2f}MB")


class SystemMonitor:
    """System resource monitor"""
    
    @staticmethod
    def get_system_stats() -> Dict:
        """Get current system statistics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count()
            },
            'memory': {
                'total_gb': memory.total / 1024 / 1024 / 1024,
                'available_gb': memory.available / 1024 / 1024 / 1024,
                'percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total / 1024 / 1024 / 1024,
                'free_gb': disk.free / 1024 / 1024 / 1024,
                'percent': disk.percent
            },
            'process': {
                'memory_mb': process_memory.rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent()
            }
        }
    
    @staticmethod
    def print_stats():
        """Print system statistics"""
        stats = SystemMonitor.get_system_stats()
        
        print(f"\n{'='*70}")
        print("SYSTEM STATISTICS")
        print(f"{'='*70}")
        print(f"\nCPU: {stats['cpu']['percent']}% ({stats['cpu']['count']} cores)")
        print(f"Memory: {stats['memory']['percent']}% used ({stats['memory']['available_gb']:.1f}GB available)")
        print(f"Disk: {stats['disk']['percent']}% used ({stats['disk']['free_gb']:.1f}GB free)")
        print(f"\nProcess Memory: {stats['process']['memory_mb']:.1f}MB")
        print(f"Process CPU: {stats['process']['cpu_percent']}%")


# Global instances
_tracer = DebugTracer(log_file='logs/debug_trace.log')
_memory_profiler = MemoryProfiler()
_performance_profiler = PerformanceProfiler()


# Convenience functions
def debug_trace(func: Callable) -> Callable:
    """Decorator to trace function execution"""
    return _tracer.trace(func)


def memory_snapshot(name: str):
    """Take a memory snapshot"""
    return _memory_profiler.snapshot(name)


def memory_compare(snapshot1: str, snapshot2: str, top: int = 10):
    """Compare two memory snapshots"""
    return _memory_profiler.compare(snapshot1, snapshot2, top)


def performance_profile(name: str):
    """Context manager for performance profiling"""
    return _performance_profiler(name)


def get_performance_summary():
    """Get performance profiling summary"""
    return _performance_profiler.get_summary()


def print_performance_summary():
    """Print performance profiling summary"""
    _performance_profiler.print_summary()


def get_system_stats():
    """Get system statistics"""
    return SystemMonitor.get_system_stats()


def print_system_stats():
    """Print system statistics"""
    SystemMonitor.print_stats()


# Example usage
if __name__ == '__main__':
    # Example 1: Function tracing
    @debug_trace
    def example_function(x, y):
        time.sleep(0.1)
        return x + y
    
    result = example_function(5, 3)
    print(f"Result: {result}")
    
    # Example 2: Memory profiling
    memory_snapshot('start')
    large_list = [i for i in range(1000000)]
    memory_snapshot('after_list')
    memory_compare('start', 'after_list')
    
    # Example 3: Performance profiling
    with performance_profile('test_section'):
        time.sleep(0.2)
        data = [i**2 for i in range(100000)]
    
    print_performance_summary()
    
    # Example 4: System monitoring
    print_system_stats()
