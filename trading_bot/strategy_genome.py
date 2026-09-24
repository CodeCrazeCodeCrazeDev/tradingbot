"""Strategy Genome - flat-path shim for ``trading_bot.alpha_evolve.strategy_genome``."""

try:
    from trading_bot.alpha_evolve.strategy_genome import *  # noqa: F401,F403
except ImportError:
    pass
