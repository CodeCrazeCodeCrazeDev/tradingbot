"""
Macro Economic Analysis Module
"""

try:
    from .macro_regime_detector import (
        MacroRegimeDetector,
        MacroIndicators,
        MacroRegimeState,
        FedPolicyRegime,
        InflationRegime,
        GrowthRegime,
        RiskRegime,
        YieldCurveRegime,
        BusinessCycle,
        StrategyAdjustment
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed for macro_regime_detector: {e}')

__all__ = [
    'MacroRegimeDetector',
    'MacroIndicators',
    'MacroRegimeState',
    'FedPolicyRegime',
    'InflationRegime',
    'GrowthRegime',
    'RiskRegime',
    'YieldCurveRegime',
    'BusinessCycle',
    'StrategyAdjustment'
]



class MacroOrchestrator:
    """Auto-generated stub orchestrator for macro."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running, "initialized": self._initialized}
