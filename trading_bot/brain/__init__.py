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
    # adaptive_integration not available
    pass

# alphaalgo_2_0
try:
    from .alphaalgo_2_0 import (
        SystemCapability,
    )
except ImportError as e:
    # alphaalgo_2_0 not available
    pass

# alphaalgo_2_0_system
try:
    from .alphaalgo_2_0_system import (
        Alphaalgo20System,
    )
except ImportError as e:
    # alphaalgo_2_0_system not available
    pass

# brain_architecture
try:
    from .brain_architecture import (
        BrainDecision,
        EliteBrain,
    )
except ImportError as e:
    # brain_architecture not available
    pass

# brain_trader
try:
    from .brain_trader import (
        BrainTrader,
    )
except ImportError as e:
    # brain_trader not available
    pass

# central_controller
try:
    from .central_controller import (
        CentralController,
    )
except ImportError as e:
    # central_controller not available
    pass

# elite_brain
try:
    from .elite_brain import (
        EliteBrainController,
    )
except ImportError as e:
    # elite_brain not available
    pass

# mt5_brain_trader
try:
    from .mt5_brain_trader import (
        MT5BrainTrader,
    )
except ImportError as e:
    # mt5_brain_trader not available
    pass

# tier9_metalearning
try:
    from .tier9_metalearning import (
        MetaLearningSystem,
    )
except ImportError as e:
    # tier9_metalearning not available
    pass

# tier_structure
try:
    from .tier_structure import (
        AlphaBrain,
        EliteBrainSignal,
    )
except ImportError as e:
    # tier_structure not available
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
]

# Alias for backward compatibility
BrainOrchestrator = EliteBrainController
