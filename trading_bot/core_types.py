"""
Core Types - flat-path shim.

Canonical definitions live in ``trading_bot.alphaalgo_institutional.core_types``.
"""

try:
    from trading_bot.alphaalgo_institutional.core_types import *  # noqa: F401,F403
    from trading_bot.alphaalgo_institutional.core_types import (
        VolatilityRegime,
        RiskMetrics,
        ModelHypothesis,
        ModelFamily,
        MarketType,
        ExecutionPlan,
        EvolutionEvent,
        CapitalAllocation,
    )
except ImportError:
    pass
