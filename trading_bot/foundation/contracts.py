"""Versioned, serializable domain contracts for the AlphaAlgo foundation.

These contracts deliberately contain no broker, model, database, or framework
objects. They are the stable boundary shared by replay, paper, research, and
live execution modes.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional
from uuid import uuid4


CONTRACT_VERSION = "1.0"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if dataclasses.is_dataclass(value):
        return {key: _serialize(item) for key, item in dataclasses.asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_serialize(item) for item in value]
    return value


class ContractMixin:
    """Provide a JSON-safe representation without exposing secrets."""

    contract_version: str = CONTRACT_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


class InstrumentType(str, Enum):
    EQUITY = "equity"
    ETF = "etf"
    CRYPTO_SPOT = "crypto_spot"
    CRYPTO_DERIVATIVE = "crypto_derivative"
    FX = "fx"
    FUTURE = "future"
    OPTION = "option"
    INDEX = "index"
    SYNTHETIC = "synthetic"


class MarketEventType(str, Enum):
    TICK = "tick"
    QUOTE = "quote"
    TRADE = "trade"
    BAR = "bar"
    ORDER_BOOK = "order_book"
    FUNDING = "funding"
    CORPORATE_ACTION = "corporate_action"
    NEWS = "news"
    MACRO = "macro"


class DataQuality(str, Enum):
    UNKNOWN = "unknown"
    VALID = "valid"
    DEGRADED = "degraded"
    STALE = "stale"
    INVALID = "invalid"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    CREATED = "created"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_PENDING = "cancel_pending"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Instrument(ContractMixin):
    symbol: str
    instrument_type: InstrumentType
    venue: str
    currency: str = "USD"
    contract_size: float = 1.0
    price_increment: Optional[float] = None
    quantity_increment: Optional[float] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("Instrument symbol must not be empty")
        if not self.venue.strip():
            raise ValueError("Instrument venue must not be empty")
        if self.contract_size <= 0:
            raise ValueError("Instrument contract_size must be positive")


@dataclass(frozen=True)
class Venue(ContractMixin):
    venue_id: str
    name: str
    environment: str = "paper"
    capabilities: frozenset = field(default_factory=frozenset)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MarketEvent(ContractMixin):
    instrument: Instrument
    event_type: MarketEventType
    source_timestamp: datetime
    payload: Mapping[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    ingested_at: datetime = field(default_factory=utc_now)
    quality: DataQuality = DataQuality.UNKNOWN
    provenance: Mapping[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.source_timestamp.tzinfo is None:
            raise ValueError("MarketEvent source_timestamp must be timezone-aware")


@dataclass(frozen=True)
class Position(ContractMixin):
    instrument: Instrument
    quantity: float
    average_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    as_of: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Exposure(ContractMixin):
    instrument: Instrument
    notional: float
    fraction_of_equity: float
    direction: str


@dataclass(frozen=True)
class PortfolioSnapshot(ContractMixin):
    account_id: str
    equity: float
    cash: float
    positions: List[Position] = field(default_factory=list)
    exposures: List[Exposure] = field(default_factory=list)
    as_of: datetime = field(default_factory=utc_now)
    drawdown_fraction: float = 0.0


@dataclass(frozen=True)
class RiskState(ContractMixin):
    account_id: str
    equity: float
    portfolio_exposure: float
    daily_pnl: float
    drawdown_fraction: float
    open_positions: int
    data_is_fresh: bool = True
    trading_enabled: bool = True
    emergency: bool = False
    limits: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Signal(ContractMixin):
    signal_id: str
    instrument: Instrument
    direction: str
    confidence: float
    expected_return: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy_id: str = "unknown"
    reasoning: str = ""
    created_at: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Signal confidence must be between 0 and 1")


@dataclass(frozen=True)
class DecisionProposal(ContractMixin):
    decision_id: str
    signal: Signal
    portfolio: PortfolioSnapshot
    risk_state: RiskState
    rationale: str = ""
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class RiskDecision(ContractMixin):
    approved: bool
    decision_id: str
    reason: str
    approved_quantity: float = 0.0
    risk_score: float = 1.0
    checks: Mapping[str, bool] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.approved and self.approved_quantity <= 0:
            raise ValueError("Approved risk decisions require a positive quantity")
        if not 0.0 <= self.risk_score <= 1.0:
            raise ValueError("Risk score must be between 0 and 1")


@dataclass(frozen=True)
class ApprovalDecision(ContractMixin):
    approved: bool
    decision_id: str
    reason: str
    approver: str = "immutable_shield"
    audit_id: str = field(default_factory=lambda: str(uuid4()))
    evaluated_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class OrderRequest(ContractMixin):
    instrument: Instrument
    side: OrderSide
    order_type: OrderType
    quantity: float
    client_order_id: str
    decision_id: str
    price: Optional[float] = None
    stop_price: Optional[float] = None
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        if not self.client_order_id.strip():
            raise ValueError("client_order_id must not be empty")


@dataclass(frozen=True)
class OrderUpdate(ContractMixin):
    client_order_id: str
    status: OrderStatus
    venue_order_id: Optional[str] = None
    filled_quantity: float = 0.0
    average_price: Optional[float] = None
    reason: Optional[str] = None
    occurred_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Fill(ContractMixin):
    client_order_id: str
    venue_order_id: Optional[str]
    instrument: Instrument
    side: OrderSide
    quantity: float
    price: float
    commission: float = 0.0
    occurred_at: datetime = field(default_factory=utc_now)
    liquidity: Optional[str] = None


@dataclass(frozen=True)
class ExecutionReport(ContractMixin):
    client_order_id: str
    status: OrderStatus
    updates: List[OrderUpdate] = field(default_factory=list)
    fills: List[Fill] = field(default_factory=list)
    expected_price: Optional[float] = None
    slippage_bps: Optional[float] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class ReconciliationResult(ContractMixin):
    venue: str
    checked_at: datetime
    matched: bool
    order_differences: List[str] = field(default_factory=list)
    position_differences: List[str] = field(default_factory=list)
    account_differences: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuditEvent(ContractMixin):
    event_type: str
    actor: str
    action: str
    outcome: str
    correlation_id: str
    occurred_at: datetime = field(default_factory=utc_now)
    details: Mapping[str, Any] = field(default_factory=dict)
