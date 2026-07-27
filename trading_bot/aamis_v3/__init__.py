"""
Aamis V3 Module
============================================================

Auto-generated integration file.
"""

# aamis_master_orchestrator
try:
    from .aamis_master_orchestrator import (
        AAMISMasterOrchestrator,
    )
    # Alias for backward compatibility
    AAMISOrchestrator = AAMISMasterOrchestrator
except ImportError as e:
    # aamis_master_orchestrator not available
    AAMISOrchestrator = None
    pass

# complete_aamis_system
try:
    from .complete_aamis_system import (
        CompleteAAMISSystem,
        SystemMode,
    )
except ImportError as e:
    # complete_aamis_system not available
    pass

__all__ = [
    'AAMISMasterOrchestrator',
    'AAMISOrchestrator',
    'CompleteAAMISSystem',
    'SystemMode',
]
