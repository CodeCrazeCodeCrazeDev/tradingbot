"""
Agents Module
============================================================

Auto-generated integration file.
"""

# orchestrator
try:
    from .orchestrator import (
        AgentOrchestrator,
    )
except ImportError as e:
    # orchestrator not available
    pass

__all__ = [
    'AgentOrchestrator',
]
