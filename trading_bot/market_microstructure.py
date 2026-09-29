"""Market Microstructure - flat-path shim merging the subpackage implementations."""

try:
    from trading_bot.adaptive_systems.market_microstructure import *  # noqa: F401,F403
except ImportError:
    pass
try:
    from trading_bot.database.market_microstructure import MarketMicrostructure  # noqa: F401
except ImportError:
    pass
