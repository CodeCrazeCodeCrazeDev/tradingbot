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
        TestMode,
        InstitutionalBacktester,
        InstitutionalTrade,
        InstitutionalBacktestResult
    )
    from .backtester import (
        # .rigorous_backtest.BacktestResult is the richer canonical result and
        # keeps the public ``BacktestResult`` name; expose this one explicitly.
        BacktestResult as BasicBacktestResult,
        Backtester,
        Direction,
        Trade
    )
    from .backtesting_engine import BacktestingEngine
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
    'BasicBacktestResult',
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
    'InstitutionalBacktester',
    'InstitutionalTrade',
    'InstitutionalBacktestResult'
]
