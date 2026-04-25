"""Shared contracts for the production trading path."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ModelVote:
    """One model's vote for or against a proposed trade."""

    model_name: str
    direction: str
    confidence: float
    reason: str = ""


@dataclass(frozen=True)
class TradeIntent:
    """Canonical AI signal consumed by the unified decision gate."""

    symbol: str
    direction: str
    confidence: float
    rationale: str
    stop_loss_pips: float
    take_profit_rr: float
    strategy_name: str = "unknown"
    timestamp: datetime = field(default_factory=utc_now)
    model_votes: List[ModelVote] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_signal(cls, signal: Any, *, strategy_name: str = "legacy_strategy") -> "TradeIntent":
        """Create a TradeIntent from existing strategy signal objects."""

        confidence = float(getattr(signal, "confidence", 0.0))
        if confidence > 1.0:
            confidence = confidence / 100.0

        return cls(
            symbol=str(getattr(signal, "symbol")),
            direction=str(getattr(signal, "direction")).lower(),
            confidence=max(0.0, min(confidence, 1.0)),
            rationale=str(getattr(signal, "rationale", "")),
            stop_loss_pips=float(getattr(signal, "stop_loss_pips")),
            take_profit_rr=float(getattr(signal, "take_profit_rr")),
            strategy_name=strategy_name,
            timestamp=getattr(signal, "time", utc_now()) or utc_now(),
        )


@dataclass(frozen=True)
class MarketContext:
    """Market state required before a trade can be approved."""

    symbol: str
    bid: float
    ask: float
    regime: str = "normal"
    session: str = "unknown"
    slippage_bps: float = 0.0
    high_impact_news: bool = False
    market_open: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def mid_price(self) -> float:
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2
        return max(self.bid, self.ask, 0.0)

    @property
    def spread_bps(self) -> float:
        mid = self.mid_price
        if mid <= 0:
            return float("inf")
        return abs(self.ask - self.bid) / mid * 10_000


@dataclass(frozen=True)
class RiskContext:
    """Current account and portfolio risk state."""

    current_drawdown_pct: float = 0.0
    daily_loss_pct: float = 0.0
    open_positions: int = 0
    trades_today: int = 0
    correlated_exposure_pct: float = 0.0
    last_trade_was_loss: bool = False
    minutes_since_last_loss: Optional[float] = None
    kill_switch_active: bool = False
    model_risk_multiplier: float = 1.0
    model_trading_halted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AccountContext:
    """Account information used for risk sizing and validation."""

    equity: float
    balance: float
    margin_level: Optional[float] = None
    currency: str = "USD"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TradeDecision:
    """Final decision from the unified decision gate."""

    approved: bool
    action: str
    intent: TradeIntent
    reasons: List[str]
    explanation: str
    risk_multiplier: float = 1.0
    position_size: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def rejected(self) -> bool:
        return not self.approved
