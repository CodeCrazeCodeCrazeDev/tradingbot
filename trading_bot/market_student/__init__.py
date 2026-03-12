"""
Market Student Module
============================================================

Auto-generated integration file.
"""

# evolution_engine
try:
    from .evolution_engine import (
        SafeEvolutionEngine,
    )
except ImportError as e:
    # evolution_engine not available
    pass

# market_student_orchestrator
try:
    from .market_student_orchestrator import (
        MarketStudentOrchestrator,
        OrchestratorConfig,
    )
except ImportError as e:
    # market_student_orchestrator not available
    pass

# reward_system
try:
    from .reward_system import (
        ImmutableRewardSystem,
    )
except ImportError as e:
    # reward_system not available
    pass

__all__ = [
    'ImmutableRewardSystem',
    'MarketStudentOrchestrator',
    'OrchestratorConfig',
    'SafeEvolutionEngine',
]
