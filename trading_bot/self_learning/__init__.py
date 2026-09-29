"""
Self Learning Module
============================================================

Auto-generated integration file.
"""

import warnings as _warnings
_warnings.warn(
    "trading_bot.self_learning is deprecated: not on the canonical runtime path and carries no improvement authority; use trading_bot.recursive_self_improvement instead.",
    DeprecationWarning,
    stacklevel=2,
)

# core_learning_engine
try:
    from .core_learning_engine import (
        CoreLearningEngine,
    )
except ImportError as e:
    # core_learning_engine not available
    pass

# distributed_learning
try:
    from .distributed_learning import (
        DistributedLearningSystem,
    )
except ImportError as e:
    # distributed_learning not available
    pass

# master_orchestrator
try:
    from .master_orchestrator import (
        MasterSelfLearningOrchestrator,
        SystemMode,
    )
except ImportError as e:
    # master_orchestrator not available
    pass

# self_healing_system
try:
    from .self_healing_system import (
        SelfHealingSystem,
        SystemIssue,
    )
except ImportError as e:
    # self_healing_system not available
    pass

# strategy_evolution
try:
    from .strategy_evolution import (
        StrategyEvolutionEngine,
    )
except ImportError as e:
    # strategy_evolution not available
    pass

__all__ = [
    'SelfLearningEngine',
    'CoreLearningEngine',
    'DistributedLearningSystem',
    'MasterSelfLearningOrchestrator',
    'SelfHealingSystem',
    'StrategyEvolutionEngine',
    'SystemIssue',
    'SystemMode',
]


class SelfLearningEngine:
    """Stub for SelfLearningEngine."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
