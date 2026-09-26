"""
Alphaalgo V2 Module
============================================================

Auto-generated integration file.
"""

# orchestrator
try:
    from .orchestrator import (
        AlphaAlgoOrchestrator,
        SystemState,
    )
    # Alias for backward compatibility
    AlphaAlgoV2Orchestrator = AlphaAlgoOrchestrator
except ImportError as e:
    # orchestrator not available
    AlphaAlgoOrchestrator = None
    SystemState = None
    AlphaAlgoV2Orchestrator = None

__all__ = [
    'AlphaAlgoOrchestrator',
    'SystemState',
    'AlphaAlgoV2Orchestrator',
]
