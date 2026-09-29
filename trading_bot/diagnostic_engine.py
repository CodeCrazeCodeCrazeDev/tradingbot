"""Diagnostic Engine - flat-path shim for ``trading_bot.self_diagnostic.diagnostic_engine``."""

try:
    from trading_bot.self_diagnostic.diagnostic_engine import *  # noqa: F401,F403
    from trading_bot.self_diagnostic.diagnostic_engine import DiagnosticCategory  # noqa: F401
except ImportError:
    pass
