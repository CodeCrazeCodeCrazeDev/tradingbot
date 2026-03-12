"""
Cognitive Architecture Module
============================================================

Auto-generated integration file.
"""

# cognitive_core
try:
    from .cognitive_core import (
        AlphaAlgoCognitiveCore,
    )
    # Alias for backward compatibility
    CognitiveOrchestrator = AlphaAlgoCognitiveCore
except ImportError as e:
    # cognitive_core not available
    CognitiveOrchestrator = None
    pass

# layer10_evolution
try:
    from .layer10_evolution import (
        ContinuousEvolutionEngine,
    )
except ImportError as e:
    # layer10_evolution not available
    pass

# layer1_market_state_detection
try:
    from .layer1_market_state_detection import (
        MarketStateEngine,
    )
except ImportError as e:
    # layer1_market_state_detection not available
    pass

# layer2_adaptive_integration
try:
    from .layer2_adaptive_integration import (
        AdaptiveIntegrationCore,
    )
except ImportError as e:
    # layer2_adaptive_integration not available
    pass

# layer4_neuro_symbolic
try:
    from .layer4_neuro_symbolic import (
        NeuroSymbolicSystem,
        ReasoningEngine,
    )
except ImportError as e:
    # layer4_neuro_symbolic not available
    pass

# layer7_self_healing
try:
    from .layer7_self_healing import (
        AutoRepairEngine,
        OptimizationManager,
        SafetyManager,
    )
except ImportError as e:
    # layer7_self_healing not available
    pass

__all__ = [
    'AdaptiveIntegrationCore',
    'AlphaAlgoCognitiveCore',
    'AutoRepairEngine',
    'CognitiveOrchestrator',
    'ContinuousEvolutionEngine',
    'MarketStateEngine',
    'NeuroSymbolicSystem',
    'OptimizationManager',
    'ReasoningEngine',
    'SafetyManager',
]
