"""
Adversarial Curriculum Module
============================================================

Auto-generated integration file.
"""

# anti_cheat
try:
    from .anti_cheat import (
        AntiCheatSystem,
    )
except ImportError as e:
    # anti_cheat not available
    pass

# curriculum_orchestrator
try:
    from .curriculum_orchestrator import (
        CurriculumOrchestrator,
    )
except ImportError as e:
    # curriculum_orchestrator not available
    pass

# failure_handler
try:
    from .failure_handler import (
        RegressionManager,
    )
except ImportError as e:
    # failure_handler not available
    pass

__all__ = [
    'AntiCheatSystem',
    'CurriculumOrchestrator',
    'RegressionManager',
]
