"""
Market Teacher Module
============================================================

Auto-generated integration file.
"""

# absolute_laws
try:
    from .absolute_laws import (
        SafetySystemProtection,
    )
except ImportError as e:
    # absolute_laws not available
    pass

# agent_population
try:
    from .agent_population import (
        AgentPopulationController,
    )
except ImportError as e:
    # agent_population not available
    pass

# alpha_meta
try:
    from .alpha_meta import (
        AgentLifecycleManager,
        LearningCoordinator,
        MarketAdaptationManager,
    )
except ImportError as e:
    # alpha_meta not available
    pass

# market_feedback
try:
    from .market_feedback import (
        MarketFeedbackSystem,
    )
except ImportError as e:
    # market_feedback not available
    pass

# market_teacher_orchestrator
try:
    from .market_teacher_orchestrator import (
        MarketTeacherOrchestrator,
    )
except ImportError as e:
    # market_teacher_orchestrator not available
    pass

# safety_framework
try:
    from .safety_framework import (
        HierarchicalRiskManager,
    )
except ImportError as e:
    # safety_framework not available
    pass

# stealth_protection
try:
    from .stealth_protection import (
        DriftDetectionSystem,
    )
except ImportError as e:
    # stealth_protection not available
    pass

# strategy_evolution
try:
    from .strategy_evolution import (
        EvolutionaryStrategySystem,
        PopulationManager,
    )
except ImportError as e:
    # strategy_evolution not available
    pass

__all__ = [
    'AgentLifecycleManager',
    'AgentPopulationController',
    'DriftDetectionSystem',
    'EvolutionaryStrategySystem',
    'HierarchicalRiskManager',
    'LearningCoordinator',
    'MarketAdaptationManager',
    'MarketFeedbackSystem',
    'MarketTeacherOrchestrator',
    'PopulationManager',
    'SafetySystemProtection',
]
