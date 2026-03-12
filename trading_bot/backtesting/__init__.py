"""
backtesting package
"""

try:
    from .advanced_backtester import (
        AdvancedBacktester,
        BacktestOrder,
        BacktestResults,
        BacktestTrade,
        OrderType,
        TestMode
    )
    from .backtester import (
        BacktestResult,
        Backtester,
        Direction,
        Trade
    )
    from .complete_backtest_runner import BacktestMetrics, CompleteBacktestRunner
    from .rigorous_backtest import (
        BacktestResult,
        MonteCarloResult,
        RigorousBacktester,
        SignificanceTest,
        TransactionCostModel,
        ValidationMethod,
        WalkForwardResult
    )
    from .strategy_backtester import StrategyBacktestResult, StrategyBacktester, retry
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in backtesting: {e}')

__all__ = [
    'BacktestingEngine',
    'AdvancedBacktester',
    'BacktestMetrics',
    'BacktestOrder',
    'BacktestResult',
    'BacktestResults',
    'BacktestTrade',
    'Backtester',
    'CompleteBacktestRunner',
    'Direction',
    'MonteCarloResult',
    'OrderType',
    'RigorousBacktester',
    'SignificanceTest',
    'StrategyBacktestResult',
    'StrategyBacktester',
    'TestMode',
    'Trade',
    'TransactionCostModel',
    'ValidationMethod',
    'WalkForwardResult',
    'retry',
]
class BacktestingEngine:
    """Stub implementation for BacktestingEngine."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
