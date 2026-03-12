"""
Elite Ai System Module
============================================================

Auto-generated integration file.
"""

# elite_execution_engine
try:
    from .elite_execution_engine import (
        EliteExecutionEngine,
    )
except ImportError as e:
    # elite_execution_engine not available
    pass

# elite_trading_orchestrator
try:
    from .elite_trading_orchestrator import (
        EliteTradingOrchestrator,
        SystemStatus,
    )
except ImportError as e:
    # elite_trading_orchestrator not available
    pass

# emergency_response_system
try:
    from .emergency_response_system import (
        EmergencyResponseSystem,
        LiquidityCrisisManager,
    )
except ImportError as e:
    # emergency_response_system not available
    pass

# market_psychology_engine
try:
    from .market_psychology_engine import (
        MarketPsychologyEngine,
    )
except ImportError as e:
    # market_psychology_engine not available
    pass

# signal_validation_system
try:
    from .signal_validation_system import (
        SignalValidationSystem,
    )
except ImportError as e:
    # signal_validation_system not available
    pass

# slow_inference_engine
try:
    from .slow_inference_engine import (
        SlowInferenceEngine,
    )
except ImportError as e:
    # slow_inference_engine not available
    pass

# trade_scoring_system
try:
    from .trade_scoring_system import (
        TradeScoringSystem,
    )
except ImportError as e:
    # trade_scoring_system not available
    pass

__all__ = [
    'EliteExecutionEngine',
    'EliteTradingOrchestrator',
    'EmergencyResponseSystem',
    'LiquidityCrisisManager',
    'MarketPsychologyEngine',
    'SignalValidationSystem',
    'SlowInferenceEngine',
    'SystemStatus',
    'TradeScoringSystem',
]
