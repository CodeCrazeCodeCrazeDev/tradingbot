"""
Superintelligence Module
============================================================

Auto-generated integration file.
"""

# memory_systems
try:
    from .memory_systems import (
        MemorySystem,
        MemoryType,
        MemoryImportance,
        MarketLesson,
        MemoryConsolidation,
    )
    MemorySystems = MemorySystem  # backward-compat alias
except ImportError as e:
    # memory_systems not available
    pass

# multi_brain_ensemble
try:
    from .multi_brain_ensemble import (
        MultiBrainEnsemble,
        VoteWeight,
        CollectiveDecision,
    )
except ImportError as e:
    # multi_brain_ensemble not available
    pass

# regime_strategy_engine
try:
    from .regime_strategy_engine import (
        RegimeStrategyEngine,
        MarketRegime,
    )
except ImportError as e:
    # regime_strategy_engine not available
    pass

# self_optimizing_core
try:
    from .self_optimizing_core import (
        SelfOptimizingCore,
        LearningExperience,
        LearningSource,
    )
except ImportError as e:
    # self_optimizing_core not available
    pass

# self_regulation_engine
try:
    from .self_regulation_engine import (
        SelfRegulationEngine,
        RegulationLevel,
    )
except ImportError as e:
    # self_regulation_engine not available
    pass

# superintelligence_orchestrator
try:
    from .superintelligence_orchestrator import (
        SuperintelligenceOrchestrator,
    )
except ImportError as e:
    # superintelligence_orchestrator not available
    pass

__all__ = [
    'MemorySystem',
    'MemorySystems',
    'MemoryType',
    'MemoryImportance',
    'MarketLesson',
    'MemoryConsolidation',
    'MultiBrainEnsemble',
    'VoteWeight',
    'CollectiveDecision',
    'RegimeStrategyEngine',
    'MarketRegime',
    'SelfOptimizingCore',
    'LearningExperience',
    'LearningSource',
    'SelfRegulationEngine',
    'RegulationLevel',
    'SuperintelligenceOrchestrator',
]
