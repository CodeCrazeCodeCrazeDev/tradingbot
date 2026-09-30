"""
Infrastructure Module
============================================================

Auto-generated integration file.
"""

# config
try:
    from .config import (
        InfrastructureConfigManager,
    )
except ImportError as e:
    # config not available
    pass

# orchestration
try:
    from .orchestration import (
        InfrastructureOrchestrator,
    )
except ImportError as e:
    # orchestration not available
    pass

# Compat re-export: flat trading_bot.infrastructure.PrometheusExporter path
# backed by the REAL in-tree adapter (never _archive — production must not
# import quarantined code, per test_no_archive_imports_in_production).
try:
    from trading_bot.monitoring.prometheus_exporter import (  # noqa: F401
        PrometheusExporter,
    )
except ImportError:
    pass

# Legacy performance-tracking helpers (in-tree replacement for the archived
# performance_optimizer surface; keeps flat trading_bot.infrastructure imports
# working without touching _archive).
from .performance_metrics import (  # noqa: F401
    measure_performance,
    get_performance_monitor,
)

__all__ = [
    'InfrastructureConfigManager',
    'InfrastructureOrchestrator',
    'PrometheusExporter',
    'measure_performance',
    'get_performance_monitor',
]
