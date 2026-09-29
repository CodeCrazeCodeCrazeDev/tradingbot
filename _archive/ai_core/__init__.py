"""
Ai Core Module
============================================================

Auto-generated integration file.
"""

# orchestrator
try:
    from .orchestrator import (
        AIOrchestrator,
    )
except ImportError as e:
    # orchestrator not available
    pass

__all__ = [
    'AIOrchestrator',
    'AICoreOrchestrator',
]

# Alias for backward compatibility
AICoreOrchestrator = AIOrchestrator
