"""Code Analyzer - flat-path shim for ``trading_bot.self_improvement.code_analyzer``."""

try:
    from trading_bot.self_improvement.code_analyzer import *  # noqa: F401,F403
    from trading_bot.self_improvement.code_analyzer import CodeIssue  # noqa: F401
except ImportError:
    pass
