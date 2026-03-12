"""
Elite Trading Bot - Performance Monitoring Module

This module provides performance monitoring and profiling capabilities
for tracking execution times, resource usage, and identifying bottlenecks.
"""

import time
import logging
import functools
import threading
import os
import json
import psutil
from pathlib import Path
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, deque

import numpy as np
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""
    EXECUTION_TIME = "execution_time"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    DATABASE_QUERIES = "database_queries"
    API_CALLS = "api_calls"
    FUNCTION_CALLS = "function_calls"
    CUSTOM = "custom"


@dataclass
class ProfileResult:
    """Result of a performance profiling operation."""
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time."""
    timestamp: datetime
    metrics: Dict[str, float]
    context: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Monitors and profiles performance of the Elite Trading Bot.
    
    This class provides tools for tracking execution times, resource usage,
    and identifying performance bottlenecks.
    """
    
    def __init__(self, history_size: int = 1000, auto_save: bool = True, 
                save_interval: int = 300, save_path: Optional[str] = None):
        """
        Initialize the performance monitor.
        
        Args:
            history_size: Maximum number of metrics to keep in history
            auto_save: Whether to automatically save metrics periodically
            save_interval: Interval in seconds for auto-saving metrics
            save_path: Path to save metrics to, or None for default
        """
        self.history_size = history_size
        self.auto_save = auto_save
        self.save_interval = save_interval
        self.save_path = save_path or os.path.join(os.getcwd(), "performance_metrics")
        
        # Ensure save directory exists
        if self.auto_save and not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
        
        # Initialize metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))
        self.snapshots: deque = deque(maxlen=history_size)
        self.active_profilers: Dict[str, Dict[str, Any]] = {}
        
        # Track function call statistics
        self.function_stats: Dict[str, Dict[str, Any]] = {}
        
        # Initialize auto-save thread if enabled
        if self.auto_save:
            self._start_auto_save()
    
    def _start_auto_save(self):
        """Start the auto-save thread."""
        def auto_save_worker():
            while True:
                time.sleep(self.save_interval)
                try:
                    self.save_metrics()
                except Exception as e:
                    logger.error(f"Error auto-saving metrics: {str(e)}")
        
        thread = threading.Thread(target=auto_save_worker, daemon=True)
        thread.start()
        logger.debug(f"Started auto-save thread with interval {self.save_interval}s")
    
    def profile(self, name: str, metric_type: MetricType) -> Callable:
        """
        Decorator to profile a function.
        
        Args:
            name: Name for the profiling metric
            metric_type: Type of metric to profile
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Start profiling
                start_time = time.time()
                
                # Track function call
                self._track_function_call(func.__name__)
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Record execution time
                execution_time = time.time() - start_time
                self.record_metric(name, metric_type, execution_time)
                
                return result
            return wrapper
        return decorator
    
    def start_profiling(self, name: str, metric_type: MetricType, 
                       context: Optional[Dict[str, Any]] = None) -> str:
        """
        Start profiling a block of code.
        
        Args:
            name: Name for the profiling metric
            metric_type: Type of metric to profile
            context: Optional context information
            
        Returns:
            Profiler ID for stopping the profiler
        """
        profiler_id = f"{name}_{time.time()}"
        self.active_profilers[profiler_id] = {
            'name': name,
            'metric_type': metric_type,
            'start_time': time.time(),
            'context': context or {}
        }
        return profiler_id
    
    def stop_profiling(self, profiler_id: str) -> ProfileResult:
        """
        Stop profiling and record the metric.
        
        Args:
            profiler_id: Profiler ID from start_profiling
            
        Returns:
            Profile result
            
        Raises:
            KeyError: If profiler_id is not found
        """
        if profiler_id not in self.active_profilers:
            raise KeyError(f"Profiler ID {profiler_id} not found")
        
        profiler = self.active_profilers.pop(profiler_id)
        execution_time = time.time() - profiler['start_time']
        
        # Record the metric
        result = self.record_metric(
            profiler['name'],
            profiler['metric_type'],
            execution_time,
            profiler['context']
        )
        
        return result
    
    def record_metric(self, name: str, metric_type: MetricType, value: float,
                     context: Optional[Dict[str, Any]] = None) -> ProfileResult:
        """
        Record a performance metric.
        
        Args:
            name: Name for the metric
            metric_type: Type of metric
            value: Metric value
            context: Optional context information
            
        Returns:
            Profile result
        """
        # Create profile result
        result = ProfileResult(
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            context=context or {}
        )
        
        # Store in metrics history
        metric_key = f"{name}_{metric_type.value}"
        self.metrics[metric_key].append(result)
        
        # Log the metric
        logger.debug(f"Recorded metric: {name} ({metric_type.value}) = {value}")
        
        return result
    
    def take_snapshot(self, context: Optional[Dict[str, Any]] = None) -> PerformanceSnapshot:
        """
        Take a snapshot of current performance metrics.
        
        Args:
            context: Optional context information
            
        Returns:
            Performance snapshot
        """
        # Collect current metrics
        current_metrics = {}
        
        try:
            # Add system metrics if available
            process = psutil.Process()
            
            # CPU usage
            current_metrics['cpu_percent'] = process.cpu_percent()
            
            # Memory usage
            memory_info = process.memory_info()
            current_metrics['memory_rss'] = memory_info.rss
            current_metrics['memory_vms'] = memory_info.vms
            
            # Disk I/O
            io_counters = process.io_counters()
            current_metrics['disk_read_bytes'] = io_counters.read_bytes
            current_metrics['disk_write_bytes'] = io_counters.write_bytes
            
            # Network I/O (system-wide)
            net_io = psutil.net_io_counters()
            current_metrics['net_sent_bytes'] = net_io.bytes_sent
            current_metrics['net_recv_bytes'] = net_io.bytes_recv
            
        except (ImportError, AttributeError):
            # psutil not available or metrics not accessible
            pass
        
        # Create snapshot
        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(),
            metrics=current_metrics,
            context=context or {}
        )
        
        # Store snapshot
        self.snapshots.append(snapshot)
        
        return snapshot
    
    def _track_function_call(self, func_name: str):
        """
        Track a function call for statistics.
        
        Args:
            func_name: Name of the function
        """
        if func_name not in self.function_stats:
            self.function_stats[func_name] = {
                'call_count': 0,
                'first_call': datetime.now(),
                'last_call': datetime.now()
            }
        
        stats = self.function_stats[func_name]
        stats['call_count'] += 1
        stats['last_call'] = datetime.now()
    
    def get_metric_statistics(self, name: str, metric_type: MetricType) -> Dict[str, float]:
        """
        Get statistics for a specific metric.
        
        Args:
            name: Name of the metric
            metric_type: Type of metric
            
        Returns:
            Dictionary with statistics
        """
        metric_key = f"{name}_{metric_type.value}"
        if metric_key not in self.metrics or not self.metrics[metric_key]:
            return {}
        
        # Extract values
        values = [result.value for result in self.metrics[metric_key]]
        
        # Calculate statistics
        stats = {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'total': sum(values)
        }
        
        # Calculate standard deviation if more than one value
        if len(values) > 1:
            stats['std_dev'] = statistics.stdev(values)
        
        # Calculate percentiles
        if len(values) >= 10:
            sorted_values = sorted(values)
            stats['p90'] = sorted_values[int(len(sorted_values) * 0.9)]
            stats['p95'] = sorted_values[int(len(sorted_values) * 0.95)]
            stats['p99'] = sorted_values[int(len(sorted_values) * 0.99)]
        
        return stats
    
    def get_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all metrics.
        
        Returns:
            Dictionary with metrics and their statistics
        """
        all_stats = {}
        
        for metric_key in self.metrics:
            if not self.metrics[metric_key]:
                continue
                
            # Parse name and type from key
            parts = metric_key.split('_')
            metric_type_value = parts[-1]
            name = '_'.join(parts[:-1])
            
            # Find matching metric type
            metric_type = None
            for mt in MetricType:
                if mt.value == metric_type_value:
                    metric_type = mt
                    break
            
            if metric_type:
                all_stats[metric_key] = self.get_metric_statistics(name, metric_type)
        
        return all_stats
    
    def get_function_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for function calls.
        
        Returns:
            Dictionary with function statistics
        """
        return self.function_stats
    
    def get_snapshot_trends(self, metric_name: str, 
                          window: Optional[int] = None) -> Dict[str, Any]:
        """
        Get trends from performance snapshots for a specific metric.
        
        Args:
            metric_name: Name of the metric
            window: Number of snapshots to include, or None for all
            
        Returns:
            Dictionary with trend information
        """
        if not self.snapshots:
            return {}
        
        # Get snapshots to analyze
        snapshots_to_analyze = list(self.snapshots)
        if window is not None:
            snapshots_to_analyze = snapshots_to_analyze[-window:]
        
        # Check if metric exists in snapshots
        if not any(metric_name in snapshot.metrics for snapshot in snapshots_to_analyze):
            return {}
        
        # Extract values and timestamps
        values = []
        timestamps = []
        
        for snapshot in snapshots_to_analyze:
            if metric_name in snapshot.metrics:
                values.append(snapshot.metrics[metric_name])
                timestamps.append(snapshot.timestamp)
        
        if not values:
            return {}
        
        # Calculate basic statistics
        stats = {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'start_value': values[0],
            'end_value': values[-1],
            'change': values[-1] - values[0],
            'change_percent': (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0
        }
        
        # Calculate trend direction
        if len(values) >= 2:
            # Simple linear regression for trend
            x = np.arange(len(values))
            y = np.array(values)
            
            # Calculate slope
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0:
                stats['trend'] = 'increasing'
            elif slope < 0:
                stats['trend'] = 'decreasing'
            else:
                stats['trend'] = 'stable'
            
            stats['slope'] = slope
        
        return stats
    
    def identify_bottlenecks(self, threshold_percentile: float = 90) -> List[Dict[str, Any]]:
        """
        Identify performance bottlenecks based on execution time.
        
        Args:
            threshold_percentile: Percentile threshold for identifying bottlenecks
            
        Returns:
            List of bottleneck information
        """
        bottlenecks = []
        
        # Get execution time metrics
        execution_metrics = {}
        for metric_key, results in self.metrics.items():
            if not results:
                continue
                
            # Check if this is an execution time metric
            first_result = results[0]
            if first_result.metric_type == MetricType.EXECUTION_TIME:
                # Calculate statistics
                values = [result.value for result in results]
                
                if len(values) >= 5:  # Need enough samples for meaningful statistics
                    execution_metrics[first_result.name] = {
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'max': max(values),
                        'p90': sorted(values)[int(len(values) * 0.9)],
                        'total': sum(values),
                        'count': len(values)
                    }
        
        # Calculate total execution time across all metrics
        total_execution_time = sum(metrics['total'] for metrics in execution_metrics.values())
        
        # Identify bottlenecks
        for name, metrics in execution_metrics.items():
            # Calculate percentage of total execution time
            percentage = (metrics['total'] / total_execution_time * 100) if total_execution_time > 0 else 0
            
            # Check if this is a bottleneck
            is_bottleneck = percentage >= threshold_percentile / 100 * 100
            
            if is_bottleneck:
                bottlenecks.append({
                    'name': name,
                    'percentage': percentage,
                    'mean_time': metrics['mean'],
                    'max_time': metrics['max'],
                    'p90_time': metrics['p90'],
                    'call_count': metrics['count']
                })
        
        # Sort bottlenecks by percentage
        bottlenecks.sort(key=lambda x: x['percentage'], reverse=True)
        
        return bottlenecks
    
    def save_metrics(self, file_path: Optional[str] = None):
        """
        Save metrics to a file.
        
        Args:
            file_path: Path to save metrics to, or None for default
        """
        if file_path is None:
            # Use default path with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(self.save_path, f"metrics_{timestamp}.json")
        
        # Prepare data to save
        data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'function_stats': self.function_stats,
            'snapshots': []
        }
        
        # Convert metrics to serializable format
        for metric_key, results in self.metrics.items():
            data['metrics'][metric_key] = [
                {
                    'name': result.name,
                    'metric_type': result.metric_type.value,
                    'value': result.value,
                    'timestamp': result.timestamp.isoformat(),
                    'context': result.context
                }
                for result in results
            ]
        
        # Convert snapshots to serializable format
        for snapshot in self.snapshots:
            data['snapshots'].append({
                'timestamp': snapshot.timestamp.isoformat(),
                'metrics': snapshot.metrics,
                'context': snapshot.context
            })
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved performance metrics to {file_path}")
    
    def load_metrics(self, file_path: str):
        """
        Load metrics from a file.
        
        Args:
            file_path: Path to load metrics from
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Clear current metrics
        self.metrics.clear()
        self.snapshots.clear()
        self.function_stats.clear()
        
        # Load function stats
        self.function_stats = data.get('function_stats', {})
        
        # Load metrics
        for metric_key, results in data.get('metrics', {}).items():
            self.metrics[metric_key] = deque(maxlen=self.history_size)
            
            for result_data in results:
                # Parse metric type
                metric_type = MetricType.CUSTOM
                for mt in MetricType:
                    if mt.value == result_data['metric_type']:
                        metric_type = mt
                        break
                
                # Create profile result
                result = ProfileResult(
                    name=result_data['name'],
                    metric_type=metric_type,
                    value=result_data['value'],
                    timestamp=datetime.fromisoformat(result_data['timestamp']),
                    context=result_data.get('context', {})
                )
                
                self.metrics[metric_key].append(result)
        
        # Load snapshots
        for snapshot_data in data.get('snapshots', []):
            snapshot = PerformanceSnapshot(
                timestamp=datetime.fromisoformat(snapshot_data['timestamp']),
                metrics=snapshot_data['metrics'],
                context=snapshot_data.get('context', {})
            )
            
            self.snapshots.append(snapshot)
        
        logger.info(f"Loaded performance metrics from {file_path}")
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Returns:
            Dictionary with report data
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics_summary': self.get_all_metrics(),
            'function_stats': self.get_function_statistics(),
            'bottlenecks': self.identify_bottlenecks(),
            'snapshot_count': len(self.snapshots)
        }
        
        try:
            # Add system metrics if available
            
            # System-wide metrics
            report['system'] = {
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': {path: asdict(psutil.disk_usage(path)) for path in psutil.disk_partitions()}
            }
            
            # Process-specific metrics
            process = psutil.Process()
            report['process'] = {
                'pid': process.pid,
                'cpu_percent': process.cpu_percent(),
                'memory_info': {k: v for k, v in process.memory_info()._asdict().items()},
                'create_time': datetime.fromtimestamp(process.create_time()).isoformat(),
                'num_threads': process.num_threads()
            }
        except (ImportError, AttributeError):
            # psutil not available or metrics not accessible
            pass
        
        return report


# Singleton instance for easy access
_default_monitor = None

def get_default_monitor() -> PerformanceMonitor:
    """Get or create the default performance monitor instance."""
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = PerformanceMonitor()
    return _default_monitor


# Convenience functions for common operations

def profile(name: str, metric_type: MetricType = MetricType.EXECUTION_TIME):
    """
    Decorator to profile a function.
    
    Args:
        name: Name for the profiling metric
        metric_type: Type of metric to profile
        
    Returns:
        Decorator function
    """
    monitor = get_default_monitor()
    return monitor.profile(name, metric_type)


def start_profiling(name: str, metric_type: MetricType = MetricType.EXECUTION_TIME,
                  context: Optional[Dict[str, Any]] = None) -> str:
    """
    Start profiling a block of code.
    
    Args:
        name: Name for the profiling metric
        metric_type: Type of metric to profile
        context: Optional context information
        
    Returns:
        Profiler ID for stopping the profiler
    """
    monitor = get_default_monitor()
    return monitor.start_profiling(name, metric_type, context)


def stop_profiling(profiler_id: str) -> ProfileResult:
    """
    Stop profiling and record the metric.
    
    Args:
        profiler_id: Profiler ID from start_profiling
        
    Returns:
        Profile result
    """
    monitor = get_default_monitor()
    return monitor.stop_profiling(profiler_id)


def record_metric(name: str, metric_type: MetricType, value: float,
                context: Optional[Dict[str, Any]] = None) -> ProfileResult:
    """
    Record a performance metric.
    
    Args:
        name: Name for the metric
        metric_type: Type of metric
        value: Metric value
        context: Optional context information
        
    Returns:
        Profile result
    """
    monitor = get_default_monitor()
    return monitor.record_metric(name, metric_type, value, context)


def take_snapshot(context: Optional[Dict[str, Any]] = None) -> PerformanceSnapshot:
    """
    Take a snapshot of current performance metrics.
    
    Args:
        context: Optional context information
        
    Returns:
        Performance snapshot
    """
    monitor = get_default_monitor()
    return monitor.take_snapshot(context)


def identify_bottlenecks(threshold_percentile: float = 90) -> List[Dict[str, Any]]:
    """
    Identify performance bottlenecks based on execution time.
    
    Args:
        threshold_percentile: Percentile threshold for identifying bottlenecks
        
    Returns:
        List of bottleneck information
    """
    monitor = get_default_monitor()
    return monitor.identify_bottlenecks(threshold_percentile)
