"""
Dashboard Module
============================================================

Auto-generated integration file.
"""

# components_system
try:
    from .components_system import (
        SystemPanel,
    )
except ImportError as e:
    # components_system not available
    pass

# performance_attribution
try:
    from .performance_attribution import (
        PerformanceAttributionSystem,
    )
except ImportError as e:
    # performance_attribution not available
    pass

# survival_dashboard
try:
    from .survival_dashboard import (
        SystemStatus,
    )
except ImportError as e:
    # survival_dashboard not available
    pass

# system_panel
try:
    from .system_panel import (
        SystemPanel,
    )
except ImportError as e:
    # system_panel not available
    pass

__all__ = [
    'PerformanceAttributionSystem',
    'SystemPanel',
    'SystemStatus',
]
