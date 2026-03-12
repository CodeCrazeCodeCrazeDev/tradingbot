"""
Monitoring Module
============================================================

Auto-generated integration file.
"""

# Stub class for graceful degradation
class MonitoringOrchestrator:
    def __init__(self, config=None):
        self.config = config or {}
    async def start(self):
        pass
    async def stop(self):
        pass

# alerting_system
try:
    from .alerting_system import (
        AlertingSystem,
    )
except ImportError as e:
    # alerting_system not available
    pass

# health_check
try:
    from .health_check import (
        AlertManager,
    )
except ImportError as e:
    # health_check not available
    pass

# live_monitor
try:
    from .live_monitor import (
        SystemMetrics,
    )
except ImportError as e:
    # live_monitor not available
    pass

# monitoring_system
try:
    from .monitoring_system import (
        MonitoringSystem,
    )
except ImportError as e:
    # monitoring_system not available
    pass

# performance_monitor
try:
    from .performance_monitor import (
        AlertManager,
    )
except ImportError as e:
    # performance_monitor not available
    pass

# production_monitoring
try:
    from .production_monitoring import (
        AlertManager,
    )
except ImportError as e:
    # production_monitoring not available
    pass

# prometheus_exporter
try:
    from .prometheus_exporter import (
        AlertManager,
    )
except ImportError as e:
    # prometheus_exporter not available
    pass

# prometheus_metrics
try:
    from .prometheus_metrics import (
        SystemMonitor,
    )
except ImportError as e:
    # prometheus_metrics not available
    pass

# system_monitor
try:
    from .system_monitor import (
        SystemMetrics,
        SystemMonitor,
    )
except ImportError as e:
    # system_monitor not available
    pass

__all__ = [
    'AlertManager',
    'AlertingSystem',
    'MonitoringOrchestrator',
    'MonitoringSystem',
    'SystemMetrics',
    'SystemMonitor',
]
