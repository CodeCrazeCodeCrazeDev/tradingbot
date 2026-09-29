"""Health Monitor - flat-path shim for ``trading_bot.system_health.health_monitor``."""

try:
    from trading_bot.system_health.health_monitor import *  # noqa: F401,F403
    from trading_bot.system_health.health_monitor import SystemHealthMonitor  # noqa: F401
except ImportError:
    pass
