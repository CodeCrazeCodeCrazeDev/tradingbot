"""Performance Optimizer - flat-path shim merging the implementations."""

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
