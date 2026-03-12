"""
Forecast Improvements Module
============================================================

Auto-generated integration file.
"""

# master_orchestrator
try:
    from .master_orchestrator import (
        ForecastImprovementsOrchestrator,
        SystemStatus,
    )
except ImportError as e:
    # master_orchestrator not available
    pass

# ml_signal_enhancement
try:
    from .ml_signal_enhancement import (
        FeatureEngineer,
    )
except ImportError as e:
    # ml_signal_enhancement not available
    pass

# news_integration
try:
    from .news_integration import (
        PreNewsPositionManager,
    )
except ImportError as e:
    # news_integration not available
    pass

# real_broker_connection
try:
    from .real_broker_connection import (
        BrokerConnectionManager,
    )
except ImportError as e:
    # real_broker_connection not available
    pass

# spread_slippage
try:
    from .spread_slippage import (
        SpreadSlippageManager,
    )
except ImportError as e:
    # spread_slippage not available
    pass

__all__ = [
    'BrokerConnectionManager',
    'FeatureEngineer',
    'ForecastImprovementsOrchestrator',
    'PreNewsPositionManager',
    'SpreadSlippageManager',
    'SystemStatus',
]
