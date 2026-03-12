"""Filters Module - Market Condition Filters."""

try:
    from .market_condition_filters import (
        MarketConditionFilterSystem,
        VolatilityFilter,
        TrendFilter,
        VolumeFilter,
        TimeFilter,
        CorrelationFilter,
        SpreadFilter,
        FilterResult,
        FilterCheck,
        FilterReport,
        MarketCondition,
        TradingSession,
        check_market_conditions,
        is_good_trading_time,
        get_market_condition
    )
except ImportError:
    MarketConditionFilterSystem = None

__all__ = [
    'MarketConditionFilterSystem',
    'VolatilityFilter',
    'TrendFilter',
    'VolumeFilter',
    'TimeFilter',
    'CorrelationFilter',
    'SpreadFilter',
    'FilterResult',
    'FilterCheck',
    'FilterReport',
    'MarketCondition',
    'TradingSession',
    'check_market_conditions',
    'is_good_trading_time',
    'get_market_condition',
]
