"""
Adversarial Decision Module
============================================================

Auto-generated integration file.
"""

# adversarial_core
try:
    from .adversarial_core import (
        AdversarialDecisionEngine,
    )
    # Alias for backward compatibility
    AdversarialDecisionOrchestrator = AdversarialDecisionEngine
except ImportError as e:
    # adversarial_core not available
    AdversarialDecisionOrchestrator = None
    pass

__all__ = [
    'AdversarialDecisionEngine',
    'AdversarialDecisionOrchestrator',
]
