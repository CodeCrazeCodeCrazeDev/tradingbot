"""
Data Pipeline Monitoring System
Tracks performance metrics and identifies bottlenecks in real-time
"""

import asyncio
import numpy as np
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
import logging
import psutil
import redis.asyncio
from dataclasses import dataclass
import json
import plotly.graph_objects as go
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import numpy

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
class PipelineMetrics:
    """Metrics for a pipeline component"""
    throughput: float = 0.0
    latency: float = 0.0
    error_rate: float = 0.0
    queue_size: int = 0
    processing_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

class PipelineMonitor:
    """
    Real-time monitoring system for data pipeline performance
    Features:
    - Component-level metrics
    - Bottleneck detection
    - Performance visualization
    - Alerting system
    - Resource monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Metrics storage
        self.metrics: Dict[str, PipelineMetrics] = {}
        self.historical_metrics: Dict[str, deque] = {}
        
        # Performance thresholds
        self.thresholds = config.get('thresholds', {
            'max_latency': 1.0,  # seconds
            'max_error_rate': 0.01,  # 1%
            'max_queue_size': 1000,
            'max_cpu_usage': 80.0,  # percent
            'max_memory_usage': 80.0  # percent
        })
        
        # Prometheus metrics
        self.prom_metrics = {
            'throughput': Gauge('pipeline_throughput', 'Messages per second', ['component']),
            'latency': Histogram('pipeline_latency', 'Processing latency', ['component']),
            'errors': Counter('pipeline_errors', 'Error count', ['component']),
            'queue_size': Gauge('pipeline_queue_size', 'Queue size', ['component']),
            'memory_usage': Gauge('pipeline_memory_usage', 'Memory usage', ['component']),
            'cpu_usage': Gauge('pipeline_cpu_usage', 'CPU usage', ['component'])
        }
        
        # Start Prometheus server
        start_http_server(config.get('prometheus_port', 8000))
        
        # Redis for metrics storage
        self.redis = None
        
        # Alert history
        self.alerts = deque(maxlen=1000)
        
        logger.info("Pipeline monitor initialized")
    
    async def initialize(self):
        """Initialize monitoring system"""
        # Initialize Redis connection
        self.redis = await redis.asyncio.from_url(
            self.config.get('redis_url', 'redis://localhost'),
            decode_responses=True
        )
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_resources())
        asyncio.create_task(self._detect_bottlenecks())
        
        logger.info("Monitoring system started")
    
    async def record_metrics(self, component: str, metrics: Dict[str, float]):
        """Record metrics for a pipeline component"""
        # Update current metrics
        if component not in self.metrics:
            self.metrics[component] = PipelineMetrics()
        
        pipeline_metrics = self.metrics[component]
        
        # Update metrics
        pipeline_metrics.throughput = metrics.get('throughput', pipeline_metrics.throughput)
        pipeline_metrics.latency = metrics.get('latency', pipeline_metrics.latency)
        pipeline_metrics.error_rate = metrics.get('error_rate', pipeline_metrics.error_rate)
        pipeline_metrics.queue_size = metrics.get('queue_size', pipeline_metrics.queue_size)
        pipeline_metrics.processing_time = metrics.get('processing_time', pipeline_metrics.processing_time)
        
        # Update Prometheus metrics
        self.prom_metrics['throughput'].labels(component).set(pipeline_metrics.throughput)
        self.prom_metrics['latency'].labels(component).observe(pipeline_metrics.latency)
        if metrics.get('errors', 0) > 0:
            self.prom_metrics['errors'].labels(component).inc(metrics['errors'])
        self.prom_metrics['queue_size'].labels(component).set(pipeline_metrics.queue_size)
        
        # Store historical metrics
        if component not in self.historical_metrics:
            self.historical_metrics[component] = deque(maxlen=1000)
        
        self.historical_metrics[component].append({
            'timestamp': datetime.now(),
            **metrics
        })
        
        # Store in Redis
        await self._store_metrics_in_redis(component, metrics)
        
        # Check for alerts
        await self._check_alerts(component, pipeline_metrics)
    
    async def _store_metrics_in_redis(self, component: str, metrics: Dict[str, float]):
        """Store metrics in Redis"""
        key = f"pipeline_metrics:{component}:{datetime.now().strftime('%Y%m%d%H%M')}"
        await self.redis.set(key, json.dumps(metrics), expire=86400)  # 24 hour retention
    
    async def _check_alerts(self, component: str, metrics: PipelineMetrics):
        """Check metrics against thresholds and generate alerts"""
        alerts = []
        
        if metrics.latency > self.thresholds['max_latency']:
            alerts.append({
                'component': component,
                'type': 'latency',
                'value': metrics.latency,
                'threshold': self.thresholds['max_latency']
            })
        
        if metrics.error_rate > self.thresholds['max_error_rate']:
            alerts.append({
                'component': component,
                'type': 'error_rate',
                'value': metrics.error_rate,
                'threshold': self.thresholds['max_error_rate']
            })
        
        if metrics.queue_size > self.thresholds['max_queue_size']:
            alerts.append({
                'component': component,
                'type': 'queue_size',
                'value': metrics.queue_size,
                'threshold': self.thresholds['max_queue_size']
            })
        
        # Log alerts
        for alert in alerts:
            logger.warning(f"Alert: {component} {alert['type']} exceeded threshold: "
                         f"{alert['value']} > {alert['threshold']}")
            self.alerts.append({
                'timestamp': datetime.now(),
                **alert
            })
    
    async def _monitor_resources(self):
        """Monitor system resources"""
        while True:
            try:
                # Get CPU and memory usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                # Update metrics for each component
                for component in self.metrics:
                    self.metrics[component].cpu_usage = cpu_percent
                    self.metrics[component].memory_usage = memory_percent
                    
                    # Update Prometheus metrics
                    self.prom_metrics['cpu_usage'].labels(component).set(cpu_percent)
                    self.prom_metrics['memory_usage'].labels(component).set(memory_percent)
                
                # Check resource thresholds
                if cpu_percent > self.thresholds['max_cpu_usage']:
                    logger.warning(f"High CPU usage: {cpu_percent}%")
                
                if memory_percent > self.thresholds['max_memory_usage']:
                    logger.warning(f"High memory usage: {memory_percent}%")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                await asyncio.sleep(5)
    
    async def _detect_bottlenecks(self):
        """Detect bottlenecks in the pipeline"""
        while True:
            try:
                bottlenecks = []
                
                # Analyze component metrics
                for component, metrics in self.metrics.items():
                    # Check for bottleneck indicators
                    if (metrics.queue_size > self.thresholds['max_queue_size'] and
                        metrics.latency > self.thresholds['max_latency']):
                        bottlenecks.append({
                            'component': component,
                            'queue_size': metrics.queue_size,
                            'latency': metrics.latency,
                            'severity': 'high'
                        })
                    elif metrics.queue_size > self.thresholds['max_queue_size']:
                        bottlenecks.append({
                            'component': component,
                            'queue_size': metrics.queue_size,
                            'latency': metrics.latency,
                            'severity': 'medium'
                        })
                
                # Log bottlenecks
                for bottleneck in bottlenecks:
                    logger.warning(
                        f"Bottleneck detected in {bottleneck['component']}: "
                        f"queue_size={bottleneck['queue_size']}, "
                        f"latency={bottleneck['latency']:.2f}s, "
                        f"severity={bottleneck['severity']}"
                    )
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error detecting bottlenecks: {e}")
                await asyncio.sleep(10)
    
    def get_component_metrics(self, component: str) -> Optional[Dict[str, Any]]:
        """Get current metrics for a component"""
        if component not in self.metrics:
            return None
        
        metrics = self.metrics[component]
        return {
            'throughput': metrics.throughput,
            'latency': metrics.latency,
            'error_rate': metrics.error_rate,
            'queue_size': metrics.queue_size,
            'processing_time': metrics.processing_time,
            'cpu_usage': metrics.cpu_usage,
            'memory_usage': metrics.memory_usage
        }
    
    def get_historical_metrics(self, component: str, 
                             minutes: int = 60) -> List[Dict[str, Any]]:
        """Get historical metrics for a component"""
        if component not in self.historical_metrics:
            return []
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            metric for metric in self.historical_metrics[component]
            if metric['timestamp'] >= cutoff_time
        ]
    
    def generate_dashboard(self) -> Dict[str, Any]:
        """Generate monitoring dashboard data"""
        dashboard = {
            'components': {},
            'system_metrics': {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent
            },
            'alerts': list(self.alerts)
        }
        
        for component in self.metrics:
            metrics = self.get_component_metrics(component)
            historical = self.get_historical_metrics(component)
            
            # Create time series plots
            throughput_fig = go.Figure()
            throughput_fig.add_trace(go.Scatter(
                x=[m['timestamp'] for m in historical],
                y=[m.get('throughput', 0) for m in historical],
                name='Throughput'
            ))
            
            latency_fig = go.Figure()
            latency_fig.add_trace(go.Scatter(
                x=[m['timestamp'] for m in historical],
                y=[m.get('latency', 0) for m in historical],
                name='Latency'
            ))
            
            dashboard['components'][component] = {
                'current_metrics': metrics,
                'plots': {
                    'throughput': throughput_fig.to_dict(),
                    'latency': latency_fig.to_dict()
                }
            }
        
        return dashboard
    
    async def cleanup(self):
        """Cleanup monitoring resources"""
        if self.redis:
            await self.redis.aclose()
        logger.info("Pipeline monitor cleaned up")
