"""
schemas package
"""

try:
    from .market_data import (
        MarketMicrostructureMetrics,
        MarketSignal,
        MarketState,
        MarketTick,
        OHLCBar,
        OrderBook,
        OrderBookLevel,
        OrderFlowSnapshot,
        TimeFrame
    )
    from .trading import (
        Direction,
        ExecutionAlgorithm,
        ExecutionPlan,
        ExecutionResult,
        ExitReason,
        OpportunityType,
        OrderType,
        PerformanceMetrics,
        Trade,
        TradeStatus,
        TradingDecision,
        TradingOpportunity
    )
    from .validation import (
        BacktestConfig,
        LatencyMeasurement,
        LiveParityTestConfig,
        PerformanceReport,
        PerformanceThresholds,
        SchemaValidationConfig,
        SyntheticDataConfig,
        TestCase,
        TestReport,
        TestResult,
        TestSuite,
        ValidationLevel,
        ValidationResult
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in schemas: {e}')

__all__ = [
    'SchemaManager',
    'BacktestConfig',
    'Direction',
    'ExecutionAlgorithm',
    'ExecutionPlan',
    'ExecutionResult',
    'ExitReason',
    'LatencyMeasurement',
    'LiveParityTestConfig',
    'MarketMicrostructureMetrics',
    'MarketSignal',
    'MarketState',
    'MarketTick',
    'OHLCBar',
    'OpportunityType',
    'OrderBook',
    'OrderBookLevel',
    'OrderFlowSnapshot',
    'OrderType',
    'PerformanceMetrics',
    'PerformanceReport',
    'PerformanceThresholds',
    'SchemaValidationConfig',
    'SyntheticDataConfig',
    'TestCase',
    'TestReport',
    'TestResult',
    'TestSuite',
    'TimeFrame',
    'Trade',
    'TradeStatus',
    'TradingDecision',
    'TradingOpportunity',
    'ValidationLevel',
    'ValidationResult',
]

class SchemasOrchestrator:
    """Auto-generated stub orchestrator for schemas."""
    
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

class SchemaManager:
    """Stub implementation for SchemaManager."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
