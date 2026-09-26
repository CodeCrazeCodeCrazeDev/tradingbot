"""Performance Optimizer - flat-path shim merging the implementations."""

import warnings as _warnings
_warnings.warn(
    "trading_bot.performance_optimizer is deprecated: not on the canonical runtime path and carries no improvement authority; use trading_bot.recursive_self_improvement instead.",
    DeprecationWarning,
    stacklevel=2,
)

try:
    from trading_bot.performance.performance_profiler import *  # noqa: F401,F403
except ImportError:
    pass
try:
    from trading_bot.ai.self_optimizer import PerformanceMetrics, OptimizationResult  # noqa: F401
except ImportError:
    pass
try:
    from trading_bot.evolution_layer.optimizer import OptimizationTarget  # noqa: F401
except ImportError:
    pass
