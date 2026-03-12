"""
Alerts Module
============================================================

Auto-generated integration file.
"""

# alert_manager
try:
    from .alert_manager import (
        AlertManager,
    )
except ImportError as e:
    # alert_manager not available
    pass

# alert_system
try:
    from .alert_system import (
        AlertSystem,
    )
except ImportError as e:
    # alert_system not available
    pass

__all__ = [
    'AlertManager',
    'AlertSystem',
]
