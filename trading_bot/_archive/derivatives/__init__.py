"""
Derivatives Module
==================

Options and futures trading infrastructure.
"""

from .options_engine import (
    OptionsEngine,
    BlackScholesModel,
    GreeksCalculator,
    ImpliedVolatilityCalculator,
    BinomialTreeModel,
    OptionsStrategyBuilder,
    VolatilitySurface,
    OptionsScanner,
    FuturesRollManager,
    OptionsPnLAttribution,
    ExpirationManager,
    OptionContract,
    FuturesContract,
    Greeks,
    OptionType,
    OptionStyle,
    StrategyType,
    get_options_engine
)

__all__ = [
    'OptionsEngine',
    'BlackScholesModel',
    'GreeksCalculator',
    'ImpliedVolatilityCalculator',
    'BinomialTreeModel',
    'OptionsStrategyBuilder',
    'VolatilitySurface',
    'OptionsScanner',
    'FuturesRollManager',
    'OptionsPnLAttribution',
    'ExpirationManager',
    'OptionContract',
    'FuturesContract',
    'Greeks',
    'OptionType',
    'OptionStyle',
    'StrategyType',
    'get_options_engine'
]
