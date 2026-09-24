"""Analysis Orchestrator - compat shim for ``trading_bot.analysis``."""

try:
    from trading_bot.analysis import *  # noqa: F401,F403
    from trading_bot.analysis import AnalysisOrchestrator  # noqa: F401
except ImportError:
    pass


# --- Legacy contract types expected by core.trading_system -------------------
from dataclasses import dataclass, field as _dc_field
from datetime import datetime as _dt


@dataclass
class Signal:
    """Trading signal consumed by the legacy trading system.

    ``direction``: +1 buy, -1 sell, 0 flat. ``confidence`` is 0-100.
    """
    symbol: str = ""
    direction: int = 0
    confidence: float = 0.0
    urgency: float = 0.5
    source: str = "analysis_orchestrator"
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    timestamp: object = None
    metadata: dict = _dc_field(default_factory=dict)


@dataclass
class MarketContext:
    """Market context attached to legacy analysis results."""
    symbol: str = ""
    regime: str = "unknown"
    volatility: float = 0.0
    timestamp: object = None
    metadata: dict = _dc_field(default_factory=dict)
