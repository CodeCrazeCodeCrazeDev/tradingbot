"""
Evolution Module
============================================================

Auto-generated integration file.
"""

# analyzer
try:
    from .analyzer import (
        SystemAnalyzer,
    )
except ImportError as e:
    # analyzer not available
    pass

# orchestrator
try:
    from .orchestrator import (
        EvolutionOrchestrator,
    )
except ImportError as e:
    # orchestrator not available
    pass

__all__ = [
    'EvolutionOrchestrator',
    'SystemAnalyzer',
]
