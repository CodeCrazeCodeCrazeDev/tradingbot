"""
Systems Ai Module
============================================================

Auto-generated integration file.
"""

# advanced_features
try:
    from .advanced_features import (
        AdvancedFeaturesCoordinator,
    )
except ImportError as e:
    # advanced_features not available
    pass

# architecture
try:
    from .architecture import (
        SystemArchitecture,
        SystemComponent,
        SystemHealth,
        SystemLayer,
    )
except ImportError as e:
    # architecture not available
    pass

# attribution_engine
try:
    from .attribution_engine import (
        DecisionAttributionEngine,
    )
except ImportError as e:
    # attribution_engine not available
    pass

# governance
try:
    from .governance import (
        GovernanceEngine,
    )
except ImportError as e:
    # governance not available
    pass

# orchestrator
try:
    from .orchestrator import (
        AdaptiveSignalOrchestrator,
        SystemConfig,
        SystemMode,
        SystemsAIOrchestrator,
    )
except ImportError as e:
    # orchestrator not available
    pass

# self_improvement
try:
    from .self_improvement import (
        RetrainingManager,
    )
except ImportError as e:
    # self_improvement not available
    pass

# text_to_system
try:
    from .text_to_system import (
        SystemCommand,
        TextToSystemLayer,
    )
except ImportError as e:
    # text_to_system not available
    pass

__all__ = [
    'AdaptiveSignalOrchestrator',
    'AdvancedFeaturesCoordinator',
    'DecisionAttributionEngine',
    'GovernanceEngine',
    'RetrainingManager',
    'SystemArchitecture',
    'SystemCommand',
    'SystemComponent',
    'SystemConfig',
    'SystemHealth',
    'SystemLayer',
    'SystemMode',
    'SystemsAIOrchestrator',
    'TextToSystemLayer',
]
