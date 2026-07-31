"""
Brain Module
============================================================

Auto-generated integration file.
"""

# adaptive_integration
try:
    from .adaptive_integration import (
        AdaptiveIntegrationSystem,
    )
except ImportError as e:
    pass

# alphaalgo_2_0
try:
    from .alphaalgo_2_0 import (
        SystemCapability,
    )
except ImportError as e:
    pass

# alphaalgo_2_0_system
try:
    from .alphaalgo_2_0_system import (
        Alphaalgo20System,
    )
except ImportError as e:
    pass

# brain_architecture
try:
    from .brain_architecture import (
        BrainDecision,
        EliteBrain,
    )
except ImportError as e:
    pass

# brain_trader
try:
    from .brain_trader import (
        BrainTrader,
    )
except ImportError as e:
    pass

# central_controller
try:
    from .central_controller import (
        CentralController,
    )
except ImportError as e:
    pass

# elite_brain
try:
    from .elite_brain import (
        EliteBrainController,
    )
except ImportError as e:
    pass

# mt5_brain_trader
try:
    from .mt5_brain_trader import (
        MT5BrainTrader,
    )
except ImportError as e:
    pass

# tier9_metalearning
try:
    from .tier9_metalearning import (
        MetaLearningSystem,
        Tier9MetaLearning,
    )
except ImportError as e:
    pass

# tier_structure
try:
    from .tier_structure import (
        AlphaBrain,
        EliteBrainSignal,
    )
except ImportError as e:
    pass

# Import Tiers 1-8 cleanly
try:
    from .tier1_technical import Tier1TechnicalAnalysis
    from .tier2_orderflow import Tier2OrderFlowIntelligence
    from .tier3_structure import Tier3MarketStructure
    from .tier4_regime import Tier4RegimeDetection
    from .tier5_sentiment import Tier5SentimentAnalysis
    from .tier6_macro import Tier6MacroAnalysis
    from .tier7_risk import Tier7RiskManagement
    from .tier8_execution import Tier8ExecutionIntelligence
except ImportError as e:
    pass

__all__ = [
    'AdaptiveIntegrationSystem',
    'AlphaBrain',
    'Alphaalgo20System',
    'BrainDecision',
    'BrainTrader',
    'CentralController',
    'EliteBrain',
    'EliteBrainController',
    'BrainOrchestrator',
    'EliteBrainSignal',
    'MT5BrainTrader',
    'MetaLearningSystem',
    'SystemCapability',
    'Tier1TechnicalAnalysis',
    'Tier2OrderFlowIntelligence',
    'Tier3MarketStructure',
    'Tier4RegimeDetection',
    'Tier5SentimentAnalysis',
    'Tier6MacroAnalysis',
    'Tier7RiskManagement',
    'Tier8ExecutionIntelligence',
    'Tier9MetaLearning',
]

# Alias for backward compatibility
BrainOrchestrator = EliteBrainController
