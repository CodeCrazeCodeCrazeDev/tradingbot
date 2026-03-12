"""
Health check endpoints and system status monitoring.
Provides HTTP endpoints for monitoring system health.
"""

import logging
import time
from typing import Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, Response
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not installed. Install with: pip install fastapi uvicorn")


class HealthCheckServer:
    """Health check HTTP server."""
    
    def __init__(self, port: int = 8001):
        """
        Initialize health check server.
        
        Args:
            port: Port for health check server
        """
        self.port = port
        self.start_time = time.time()
        self.health_status = {
            'status': 'healthy',
            'components': {}
        }
        
        if FASTAPI_AVAILABLE:
            self.app = FastAPI(title="AlphaAlgo Health Check")
            self._setup_routes()
        else:
            self.app = None
        
        logger.info(f"Health check server initialized on port {port}")
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/health")
        async def health():
            """Basic health check."""
            return JSONResponse({
                'status': 'healthy',
                'uptime': time.time() - self.start_time,
                'timestamp': time.time()
            })
        
        @self.app.get("/health/detailed")
        async def detailed_health():
            """Detailed health check with component status."""
            return JSONResponse(self.get_detailed_health())
        
        @self.app.get("/metrics/system")
        async def system_metrics():
            """System resource metrics."""
            return JSONResponse(self.get_system_metrics())
        
        @self.app.get("/ready")
        async def readiness():
            """Readiness probe for Kubernetes."""
            if self.health_status['status'] == 'healthy':
                return JSONResponse({'ready': True})
            else:
                return JSONResponse({'ready': False}, status_code=503)
        
        @self.app.get("/live")
        async def liveness():
            """Liveness probe for Kubernetes."""
            return JSONResponse({'alive': True})
    
    def get_detailed_health(self) -> Dict:
        """Get detailed health status."""
        return {
            'status': self.health_status['status'],
            'uptime_seconds': time.time() - self.start_time,
            'components': self.health_status['components'],
            'system': self.get_system_metrics(),
            'timestamp': time.time()
        }
    
    def get_system_metrics(self) -> Dict:
        """Get system resource metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                }
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    def update_component_health(self, component: str, status: str, message: str = ""):
        """
        Update health status for a component.
        
        Args:
            component: Component name
            status: 'healthy', 'degraded', or 'unhealthy'
            message: Optional status message
        """
        self.health_status['components'][component] = {
            'status': status,
            'message': message,
            'timestamp': time.time()
        }
        
        # Update overall status
        component_statuses = [c['status'] for c in self.health_status['components'].values()]
        if 'unhealthy' in component_statuses:
            self.health_status['status'] = 'unhealthy'
        elif 'degraded' in component_statuses:
            self.health_status['status'] = 'degraded'
        else:
            self.health_status['status'] = 'healthy'
    
    def start(self):
        """Start health check server."""
        if not FASTAPI_AVAILABLE:
            logger.warning("FastAPI not available - health check server disabled")
            return
        
        logger.info(f"Starting health check server on port {self.port}")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="warning")


class AlertManager:
    """Alert threshold management and notification."""
    
    def __init__(self):
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'error_rate': 0.05,  # 5%
            'latency_ms': 100.0
        }
        self.alerts = []
        
        logger.info("Alert manager initialized")
    
    def check_thresholds(self, metrics: Dict) -> list:
        """
        Check if any thresholds are breached.
        
        Args:
            metrics: Dictionary of current metrics
            
        Returns:
            List of alert messages
        """
        alerts = []
        
        # CPU check
        if metrics.get('cpu_percent', 0) > self.thresholds['cpu_percent']:
            alerts.append(f"CPU usage {metrics['cpu_percent']:.1f}% exceeds threshold {self.thresholds['cpu_percent']:.1f}%")
        
        # Memory check
        if metrics.get('memory_percent', 0) > self.thresholds['memory_percent']:
            alerts.append(f"Memory usage {metrics['memory_percent']:.1f}% exceeds threshold {self.thresholds['memory_percent']:.1f}%")
        
        # Latency check
        if metrics.get('latency_ms', 0) > self.thresholds['latency_ms']:
            alerts.append(f"Latency {metrics['latency_ms']:.1f}ms exceeds threshold {self.thresholds['latency_ms']:.1f}ms")
        
        # Store alerts
        for alert in alerts:
            self.alerts.append({
                'message': alert,
                'timestamp': time.time(),
                'severity': 'warning'
            })
            logger.warning(f"ALERT: {alert}")
        
        return alerts
    
    def get_active_alerts(self, max_age_seconds: int = 3600) -> list:
        """Get active alerts within time window."""
        current_time = time.time()
        return [
            alert for alert in self.alerts
            if current_time - alert['timestamp'] < max_age_seconds
        ]
