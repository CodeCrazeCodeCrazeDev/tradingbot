"""Exit Strategy - flat-path shim for ``trading_bot.exit_strategies.exit_strategy``."""

try:
    from trading_bot.exit_strategies.exit_strategy import *  # noqa: F401,F403
    from trading_bot.exit_strategies.exit_strategy import ExitType  # noqa: F401
except ImportError:
    pass
