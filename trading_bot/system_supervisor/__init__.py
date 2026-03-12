"""
System Supervisor Module
============================================================

Auto-generated integration file.
"""

# auto_repair_system
try:
    from .auto_repair_system import (
        AutoRepairSystem,
        FailoverManager,
    )
except ImportError as e:
    # auto_repair_system not available
    pass

# system_supervisor
try:
    from .system_supervisor import (
        SystemHealth,
        SystemStatus,
        SystemSupervisor,
    )
except ImportError as e:
    # system_supervisor not available
    pass

__all__ = [
    'AutoRepairSystem',
    'FailoverManager',
    'SystemHealth',
    'SystemStatus',
    'SystemSupervisor',
]
