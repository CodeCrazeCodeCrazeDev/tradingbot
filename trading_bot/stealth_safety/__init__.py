"""
Stealth Safety Module
============================================================

Auto-generated integration file.
"""

# stealth_orchestrator
try:
    from .stealth_orchestrator import (
        StealthSafetyOrchestrator,
    )
except ImportError as e:
    # stealth_orchestrator not available
    pass

# systemic_safety
try:
    from .systemic_safety import (
        SystemState,
    )
except ImportError as e:
    # systemic_safety not available
    pass

__all__ = [
    'StealthSafetyOrchestrator',
    'StealthSafetyManager',
    'SystemState',
]

# Alias for backward compatibility
StealthSafetyManager = StealthSafetyOrchestrator
