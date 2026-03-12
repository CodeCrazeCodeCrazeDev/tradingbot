"""
Self Diagnostic Module
============================================================

Auto-generated integration file.
"""

# auto_repair
try:
    from .auto_repair import (
        AutoRepairEngine,
    )
except ImportError as e:
    # auto_repair not available
    pass

# diagnostic_engine
try:
    from .diagnostic_engine import (
        DiagnosticEngine,
    )
except ImportError as e:
    # diagnostic_engine not available
    pass

# self_manager
try:
    from .self_manager import (
        SelfDiagnosticManager,
    )
    # Alias for backward compatibility
    SelfManager = SelfDiagnosticManager
except ImportError as e:
    # self_manager not available
    SelfDiagnosticManager = None
    SelfManager = None

__all__ = [
    'AutoRepairEngine',
    'DiagnosticEngine',
    'SelfDiagnosticManager',
    'SelfManager',
]
