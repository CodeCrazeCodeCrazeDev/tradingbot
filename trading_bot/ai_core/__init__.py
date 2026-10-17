"""AI Core package - minimal orchestration surface.

QUARANTINED 2026-10: AIOrchestrator is a SECOND orchestrator — the CSC
(trading_bot.core.csc.controller) is the sole decision authority and
UnifiedTradingBot is the canonical runtime path. This package may be
imported for compatibility only; it carries no decision, sizing, veto,
or execution authority. Do not wire it into the order path."""

import warnings as _warnings
_warnings.warn(
    "trading_bot.ai_core.AIOrchestrator is quarantined: a parallel "
    "orchestrator with no decision authority; CSC is the only brain",
    DeprecationWarning,
    stacklevel=2,
)

try:
    from .orchestrator import AIOrchestrator  # noqa: F401
except ImportError:
    pass
