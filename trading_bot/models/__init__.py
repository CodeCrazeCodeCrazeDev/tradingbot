"""
models package
"""

try:
    from .data_models import (
        AnalyticsResult,
        Direction,
        MarketRegime,
        MarketTick,
        MicrostructureMetrics,
        OHLCBar,
        OpportunityData,
        OrderFlowSnapshot,
        TimeFrame,
        TradeResult,
        TradingSignal
    )
    from .schema_integration import SchemaValidator
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in models: {e}')

__all__ = [
    'ModelsOrchestrator',
    'ModelManager',
    'AnalyticsResult',
    'Direction',
    'MarketRegime',
    'MarketTick',
    'MicrostructureMetrics',
    'OHLCBar',
    'OpportunityData',
    'OrderFlowSnapshot',
    'SchemaValidator',
    'TimeFrame',
    'TradeResult',
    'TradingSignal',
]
class ModelManager:
    """Stub implementation for ModelManager."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}


class ModelsOrchestrator:
    """Stub for ModelsOrchestrator."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
