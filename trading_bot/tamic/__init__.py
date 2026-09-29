"""
Tamic Module
============================================================

Auto-generated integration file.
"""

# core
try:
    from .core import TAMIC, TimeHorizon, MarketTimeState, SignalHalfLife, create_tamic, quick_start
except ImportError as e:
    pass

# integration
try:
    from .integration import TAMICIntegration, create_tamic_integration
except ImportError as e:
    pass

# institutional_time
try:
    from .institutional_time import (
        InstitutionalTimeEngine,
    )
except ImportError as e:
    # institutional_time not available
    pass

# market_time
try:
    from .market_time import (
        MarketTimeEngine,
    )
except ImportError as e:
    # market_time not available
    pass

# optionality
try:
    from .optionality import (
        OptionalityPreservationEngine,
    )
except ImportError as e:
    # optionality not available
    pass

# time_risk
try:
    from .time_risk import (
        TimeBasedRiskManager,
    )
except ImportError as e:
    # time_risk not available
    pass

__all__ = [
    'TAMICOrchestrator',
    'InstitutionalTimeEngine',
    'MarketTimeEngine',
    'OptionalityPreservationEngine',
    'TimeBasedRiskManager',
]


class TAMICOrchestrator:
    """Stub for TAMICOrchestrator."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}

# Flat-path compat re-exports (real implementation in .core)
try:
    from .core import TAMIC, TAMICConfig, TAMICDecision, TimeHorizon, MarketTimeState, SignalHalfLife, ForbiddenBehaviorType, TAMICGovernanceLayer  # noqa: F401
except ImportError:
    pass
