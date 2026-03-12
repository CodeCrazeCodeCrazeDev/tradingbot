"""
Phase 8: Production Deployment
Infrastructure for production deployment
"""

# Try to import with optional GPU monitoring
try:
    from .auto_scaling import (
        AutoScaler,
        ResourceMetrics
    )
    _gpu_available = True
except ImportError:
    # Stub implementations without GPUtil
    class ResourceMetrics:
        """Stub implementation without GPU monitoring"""
        def __init__(self):
            self.cpu_percent = 0.0
            self.memory_percent = 0.0
            self.gpu_percent = 0.0
    
    class AutoScaler:
        """Stub implementation of AutoScaler"""
        def __init__(self, *args, **kwargs):
            pass
        def scale(self, *args, **kwargs):
            return {}
    _gpu_available = False

from .monitoring import (
    PerformanceMonitor,
    PerformanceMetrics
)

from .health_check import HealthCheck

try:
    from .health_endpoints import HealthEndpoints
    _endpoints_available = True
except ImportError:
    HealthEndpoints = None
    _endpoints_available = False

__all__ = [
    'AutoScaler',
    'ResourceMetrics',
    'PerformanceMonitor',
    'PerformanceMetrics',
    'HealthCheck',
    'HealthEndpoints'
]
