"""
Performance Tracking System
Monitors and records performance metrics for the trading system
"""

import asyncio
import time
import logging
import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime, timedelta
from collections import deque
import json
import os
import threading
import functools
import traceback
from pathlib import Path

logger = logging.getLogger(__name__)


class LatencyTracker:
    """
    Tracks execution latency for different components
    """
    
    def __init__(self, name: str, max_samples: int = 1000):
        self.name = name
        self.latencies = deque(maxlen=max_samples)
        self.start_times = {}
        self.lock = threading.RLock()
    
    def start(self, operation_id: str = None) -> str:
        """Start timing an operation"""
        with self.lock:
            if operation_id is None:
                operation_id = f"{self.name}_{time.time()}"
            
            self.start_times[operation_id] = time.time()
            return operation_id
    
    def stop(self, operation_id: str) -> float:
        """Stop timing an operation and return latency in ms"""
        with self.lock:
            if operation_id not in self.start_times:
                logger.warning(f"Operation {operation_id} not found in {self.name} tracker")
                return 0
            
            latency = (time.time() - self.start_times[operation_id]) * 1000  # ms
            self.latencies.append(latency)
            del self.start_times[operation_id]
            
            return latency
    
    def get_metrics(self) -> Dict[str, float]:
        """Get latency metrics"""
        with self.lock:
            if not self.latencies:
                return {
                    'avg': 0,
                    'min': 0,
                    'max': 0,
                    'p50': 0,
                    'p95': 0,
                    'p99': 0,
                    'count': 0
                }
            
            latencies = list(self.latencies)
            
            return {
                'avg': np.mean(latencies),
                'min': np.min(latencies),
                'max': np.max(latencies),
                'p50': np.percentile(latencies, 50),
                'p95': np.percentile(latencies, 95),
                'p99': np.percentile(latencies, 99),
                'count': len(latencies)
            }


class ThroughputTracker:
    """
    Tracks throughput for different components
    """
    
    def __init__(self, name: str, window_size: int = 60):
        self.name = name
        self.window_size = window_size  # seconds
        self.events = deque()
        self.lock = threading.RLock()
    
    def record_event(self, count: int = 1):
        """Record an event"""
        with self.lock:
            self.events.append((time.time(), count))
            self._cleanup_old_events()
    
    def _cleanup_old_events(self):
        """Remove events outside the window"""
        with self.lock:
            cutoff_time = time.time() - self.window_size
            while self.events and self.events[0][0] < cutoff_time:
                self.events.popleft()
    
    def get_throughput(self) -> float:
        """Get current throughput (events per second)"""
        with self.lock:
            self._cleanup_old_events()
            
            if not self.events:
                return 0
            
            total_events = sum(count for _, count in self.events)
            window_duration = time.time() - self.events[0][0] if self.events else self.window_size
            
            # Avoid division by zero
            if window_duration <= 0:
                return 0
            
            return total_events / window_duration


class ResourceMonitor:
    """
    Monitors system resource usage
    """
    
    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self.cpu_usage = deque(maxlen=60)
        self.memory_usage = deque(maxlen=60)
        self.disk_io = deque(maxlen=60)
        self.network_io = deque(maxlen=60)
        self.stop_event = threading.Event()
        self.monitor_thread = None
    
    def start(self):
        """Start monitoring resources"""
        if self.monitor_thread is not None:
            return
        
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop(self):
        """Stop monitoring resources"""
        if self.monitor_thread is None:
            return
        
        self.stop_event.set()
        self.monitor_thread.join(timeout=5)
        self.monitor_thread = None
    
    def _monitor_loop(self):
        """Background thread for resource monitoring"""
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not available, resource monitoring disabled")
            return
        
        while not self.stop_event.is_set():
            try:
                # CPU usage
                self.cpu_usage.append(psutil.cpu_percent(interval=None))
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.memory_usage.append(memory.percent)
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                self.disk_io.append((disk_io.read_bytes, disk_io.write_bytes))
                
                # Network I/O
                net_io = psutil.net_io_counters()
                self.network_io.append((net_io.bytes_sent, net_io.bytes_recv))
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
            
            # Sleep until next sample
            self.stop_event.wait(self.sample_interval)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get resource metrics"""
        if not self.cpu_usage:
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_read_bps': 0,
                'disk_write_bps': 0,
                'net_send_bps': 0,
                'net_recv_bps': 0
            }
        
        # Calculate disk I/O rates
        disk_read_bps = disk_write_bps = 0
        if len(self.disk_io) >= 2:
            time_diff = self.sample_interval * (len(self.disk_io) - 1)
            read_diff = self.disk_io[-1][0] - self.disk_io[0][0]
            write_diff = self.disk_io[-1][1] - self.disk_io[0][1]
            disk_read_bps = read_diff / time_diff
            disk_write_bps = write_diff / time_diff
        
        # Calculate network I/O rates
        net_send_bps = net_recv_bps = 0
        if len(self.network_io) >= 2:
            time_diff = self.sample_interval * (len(self.network_io) - 1)
            send_diff = self.network_io[-1][0] - self.network_io[0][0]
            recv_diff = self.network_io[-1][1] - self.network_io[0][1]
            net_send_bps = send_diff / time_diff
            net_recv_bps = recv_diff / time_diff
        
        return {
            'cpu_percent': np.mean(self.cpu_usage),
            'memory_percent': np.mean(self.memory_usage),
            'disk_read_bps': disk_read_bps,
            'disk_write_bps': disk_write_bps,
            'net_send_bps': net_send_bps,
            'net_recv_bps': net_recv_bps
        }


class PerformanceTracker:
    """
    Comprehensive performance tracking system
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Component trackers
        self.latency_trackers = {}
        self.throughput_trackers = {}
        
        # Resource monitor
        self.resource_monitor = ResourceMonitor()
        
        # Performance thresholds
        self.thresholds = self.config.get('thresholds', {
            'latency': {
                'data_processing': 10,  # ms
                'opportunity_scanning': 50,  # ms
                'signal_generation': 20,  # ms
                'execution': 100  # ms
            },
            'throughput': {
                'data_processing': 100,  # events/s
                'opportunity_scanning': 10,  # events/s
                'signal_generation': 5,  # events/s
                'execution': 1  # events/s
            },
            'resources': {
                'cpu_percent': 80,
                'memory_percent': 80
            }
        })
        
        # Alerts
        self.alerts = deque(maxlen=1000)
        
        # Metrics storage
        self.metrics_dir = self.config.get('metrics_dir', 'metrics')
        Path(self.metrics_dir).mkdir(parents=True, exist_ok=True)
        
        # Start resource monitoring
        self.resource_monitor.start()
        
        logger.info("Performance tracker initialized")
    
    def get_latency_tracker(self, component: str) -> LatencyTracker:
        """Get or create a latency tracker for a component"""
        if component not in self.latency_trackers:
            self.latency_trackers[component] = LatencyTracker(component)
        
        return self.latency_trackers[component]
    
    def get_throughput_tracker(self, component: str) -> ThroughputTracker:
        """Get or create a throughput tracker for a component"""
        if component not in self.throughput_trackers:
            self.throughput_trackers[component] = ThroughputTracker(component)
        
        return self.throughput_trackers[component]
    
    def track_latency(self, component: str):
        """
        Decorator to track function latency
        
        Usage:
            @performance_tracker.track_latency("component_name")
            async def my_function():
                ...
        """
        def decorator(func):
            tracker = self.get_latency_tracker(component)
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                operation_id = tracker.start()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    latency = tracker.stop(operation_id)
                    self._check_latency_threshold(component, latency)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                operation_id = tracker.start()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    latency = tracker.stop(operation_id)
                    self._check_latency_threshold(component, latency)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    def track_throughput(self, component: str):
        """
        Decorator to track function throughput
        
        Usage:
            @performance_tracker.track_throughput("component_name")
            async def my_function():
                ...
        """
        def decorator(func):
            tracker = self.get_throughput_tracker(component)
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                tracker.record_event()
                self._check_throughput_threshold(component)
                return result
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                tracker.record_event()
                self._check_throughput_threshold(component)
                return result
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    def _check_latency_threshold(self, component: str, latency: float):
        """Check if latency exceeds threshold"""
        threshold = self.thresholds.get('latency', {}).get(component)
        if threshold is not None and latency > threshold:
            self._add_alert(
                component=component,
                alert_type='latency',
                value=latency,
                threshold=threshold,
                message=f"{component} latency ({latency:.2f}ms) exceeds threshold ({threshold}ms)"
            )
    
    def _check_throughput_threshold(self, component: str):
        """Check if throughput is below threshold"""
        tracker = self.throughput_trackers.get(component)
        if tracker is None:
            return
        
        throughput = tracker.get_throughput()
        threshold = self.thresholds.get('throughput', {}).get(component)
        
        if threshold is not None and throughput < threshold:
            self._add_alert(
                component=component,
                alert_type='throughput',
                value=throughput,
                threshold=threshold,
                message=f"{component} throughput ({throughput:.2f}/s) below threshold ({threshold}/s)"
            )
    
    def _check_resource_thresholds(self):
        """Check if resource usage exceeds thresholds"""
        metrics = self.resource_monitor.get_metrics()
        
        # Check CPU usage
        cpu_threshold = self.thresholds.get('resources', {}).get('cpu_percent')
        if cpu_threshold is not None and metrics['cpu_percent'] > cpu_threshold:
            self._add_alert(
                component='system',
                alert_type='cpu',
                value=metrics['cpu_percent'],
                threshold=cpu_threshold,
                message=f"CPU usage ({metrics['cpu_percent']:.1f}%) exceeds threshold ({cpu_threshold}%)"
            )
        
        # Check memory usage
        memory_threshold = self.thresholds.get('resources', {}).get('memory_percent')
        if memory_threshold is not None and metrics['memory_percent'] > memory_threshold:
            self._add_alert(
                component='system',
                alert_type='memory',
                value=metrics['memory_percent'],
                threshold=memory_threshold,
                message=f"Memory usage ({metrics['memory_percent']:.1f}%) exceeds threshold ({memory_threshold}%)"
            )
    
    def _add_alert(self, component: str, alert_type: str, value: float, threshold: float, message: str):
        """Add a performance alert"""
        alert = {
            'timestamp': datetime.now(),
            'component': component,
            'type': alert_type,
            'value': value,
            'threshold': threshold,
            'message': message
        }
        
        self.alerts.append(alert)
        logger.warning(message)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        # Get latency metrics
        latency_metrics = {
            component: tracker.get_metrics()
            for component, tracker in self.latency_trackers.items()
        }
        
        # Get throughput metrics
        throughput_metrics = {
            component: {'throughput': tracker.get_throughput()}
            for component, tracker in self.throughput_trackers.items()
        }
        
        # Get resource metrics
        resource_metrics = self.resource_monitor.get_metrics()
        
        # Check resource thresholds
        self._check_resource_thresholds()
        
        # Combine metrics
        return {
            'timestamp': datetime.now(),
            'latency': latency_metrics,
            'throughput': throughput_metrics,
            'resources': resource_metrics,
            'alerts': list(self.alerts)
        }
    
    def save_metrics(self, metrics: Optional[Dict[str, Any]] = None):
        """Save metrics to file"""
        if metrics is None:
            metrics = self.get_metrics()
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.metrics_dir, f"metrics_{timestamp}.json")
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(metrics, f, default=str, indent=2)
    
    def cleanup(self):
        """Clean up resources"""
        self.resource_monitor.stop()
        logger.info("Performance tracker cleaned up")


# Global performance tracker instance
_performance_tracker = None


def get_performance_tracker(config: Optional[Dict[str, Any]] = None) -> PerformanceTracker:
    """Get the global performance tracker instance"""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker(config)
    return _performance_tracker
