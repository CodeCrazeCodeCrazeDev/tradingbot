"""
AlphaAlgo Core Types - STABLE TYPE DEFINITIONS

These types are FROZEN and should NEVER change.
All modules must use these types for interoperability.

Version: 1.0.0 (FROZEN)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional
import hashlib

import logging
logger = logging.getLogger(__name__)



# =============================================================================
# ENUMS - FROZEN
# =============================================================================

class SignalType(Enum):
    """Signal type enumeration - FROZEN"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"


class SignalStrength(Enum):
    """Signal strength enumeration - FROZEN"""
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


class OrderType(Enum):
    """Order type enumeration - FROZEN"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Order side enumeration - FROZEN"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status enumeration - FROZEN"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RiskLevel(Enum):
    """Risk level enumeration - FROZEN"""
    MINIMAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    EXTREME = 5
    CRITICAL = 6


class TradingMode(Enum):
    """Trading mode enumeration - FROZEN"""
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"
    SIMULATION = "simulation"
    DISABLED = "disabled"


class HealthStatus(Enum):
    """Health status enumeration - FROZEN"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class SystemStatus(Enum):
    """System status enumeration - FROZEN"""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


# =============================================================================
# DATA TYPES - FROZEN
# =============================================================================

@dataclass(frozen=True)
class Tick:
    """Single price tick - FROZEN"""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    volume: float = 0.0
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid


@dataclass(frozen=True)
class OHLCV:
    """OHLCV candle data - FROZEN"""
    symbol: str
    timestamp: datetime
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @property
    def range(self) -> float:
        return self.high - self.low
    
    @property
    def body(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open


@dataclass
class OrderBook:
    """Order book snapshot - FROZEN"""
    symbol: str
    timestamp: datetime
    bids: List[tuple]  # [(price, size), ...]
    asks: List[tuple]  # [(price, size), ...]
    
    @property
    def best_bid(self) -> Optional[float]:
        return self.bids[0][0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[float]:
        return self.asks[0][0] if self.asks else None
    
    @property
    def spread(self) -> Optional[float]:
        try:
            if self.best_bid and self.best_ask:
                return self.best_ask - self.best_bid
            return None
        except Exception as e:
            logger.error(f"Error in spread: {e}")
            raise


@dataclass(frozen=True)
class Trade:
    """Single trade record - FROZEN"""
    trade_id: str
    symbol: str
    timestamp: datetime
    side: OrderSide
    price: float
    size: float
    is_maker: bool = False


@dataclass
class MarketData:
    """Aggregated market data - FROZEN"""
    symbol: str
    timestamp: datetime
    tick: Optional[Tick] = None
    ohlcv: Optional[Dict[str, List[OHLCV]]] = None  # {timeframe: [candles]}
    orderbook: Optional[OrderBook] = None
    trades: Optional[List[Trade]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# SIGNAL TYPES - FROZEN
# =============================================================================

@dataclass
class SignalConfidence:
    """Signal confidence metrics - FROZEN"""
    overall: float  # 0.0 to 1.0
    technical: float = 0.0
    fundamental: float = 0.0
    sentiment: float = 0.0
    ml_model: float = 0.0
    
    def __post_init__(self):
        # Clamp values to [0, 1]
        try:
            self.overall = max(0.0, min(1.0, self.overall))
            self.technical = max(0.0, min(1.0, self.technical))
            self.fundamental = max(0.0, min(1.0, self.fundamental))
            self.sentiment = max(0.0, min(1.0, self.sentiment))
            self.ml_model = max(0.0, min(1.0, self.ml_model))
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


@dataclass
class Signal:
    """Trading signal - FROZEN STRUCTURE"""
    signal_id: str
    symbol: str
    timestamp: datetime
    signal_type: SignalType
    strength: SignalStrength
    confidence: SignalConfidence
    
    # Price levels
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Metadata
    source: str = "unknown"
    timeframe: str = "1h"
    expiry: Optional[datetime] = None
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        try:
            if not self.signal_id:
                # Generate unique ID
                data = f"{self.symbol}{self.timestamp}{self.signal_type.value}"
                self.signal_id = hashlib.sha256(data.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise
    
    @property
    def is_expired(self) -> bool:
        try:
            if self.expiry is None:
                return False
            return datetime.now() > self.expiry
        except Exception as e:
            logger.error(f"Error in is_expired: {e}")
            raise
    
    @property
    def risk_reward_ratio(self) -> Optional[float]:
        try:
            if all([self.entry_price, self.stop_loss, self.take_profit]):
                risk = abs(self.entry_price - self.stop_loss)
                reward = abs(self.take_profit - self.entry_price)
                return reward / risk if risk > 0 else None
            return None
        except Exception as e:
            logger.error(f"Error in risk_reward_ratio: {e}")
            raise


# =============================================================================
# ORDER TYPES - FROZEN
# =============================================================================

@dataclass
class Order:
    """Trading order - FROZEN STRUCTURE"""
    order_id: str
    client_order_id: str
    symbol: str
    timestamp: datetime
    side: OrderSide
    order_type: OrderType
    quantity: float
    
    # Price levels
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_price: float = 0.0
    
    # Metadata
    signal_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity
    
    @property
    def is_complete(self) -> bool:
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]


@dataclass
class ExecutionResult:
    """Order execution result - FROZEN STRUCTURE"""
    order_id: str
    success: bool
    timestamp: datetime
    
    # Fill details
    filled_quantity: float = 0.0
    average_price: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    error_message: str = ""
    
    # Metadata
    execution_time_ms: float = 0.0
    venue: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# RISK TYPES - FROZEN
# =============================================================================

@dataclass
class PositionSize:
    """Position sizing result - FROZEN STRUCTURE"""
    quantity: float
    value: float
    risk_amount: float
    risk_percent: float
    method: str
    reasoning: str = ""


@dataclass
class RiskDecision:
    """Risk check decision - FROZEN STRUCTURE"""
    approved: bool
    risk_level: RiskLevel
    position_size: Optional[PositionSize] = None
    
    # Limits
    max_position: float = 0.0
    current_exposure: float = 0.0
    remaining_capacity: float = 0.0
    
    # Reasons
    rejection_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskMetrics:
    """Portfolio risk metrics - FROZEN STRUCTURE"""
    timestamp: datetime
    
    # Position metrics
    total_exposure: float = 0.0
    long_exposure: float = 0.0
    short_exposure: float = 0.0
    net_exposure: float = 0.0
    
    # Risk metrics
    var_95: float = 0.0  # Value at Risk 95%
    var_99: float = 0.0  # Value at Risk 99%
    expected_shortfall: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    
    # Performance metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Limits
    daily_loss: float = 0.0
    daily_loss_limit: float = 0.05
    position_count: int = 0
    max_positions: int = 10


# =============================================================================
# TRADING TYPES - FROZEN
# =============================================================================

@dataclass
class Position:
    """Trading position - FROZEN STRUCTURE"""
    position_id: str
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    entry_time: datetime
    
    # Current state
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # Risk levels
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Metadata
    signal_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def pnl_percent(self) -> float:
        try:
            if self.entry_price > 0:
                if self.side == OrderSide.BUY:
                    return (self.current_price - self.entry_price) / self.entry_price
                else:
                    return (self.entry_price - self.current_price) / self.entry_price
            return 0.0
        except Exception as e:
            logger.error(f"Error in pnl_percent: {e}")
            raise


@dataclass
class Portfolio:
    """Portfolio state - FROZEN STRUCTURE"""
    timestamp: datetime
    
    # Capital
    initial_capital: float
    current_capital: float
    available_capital: float
    
    # Positions
    positions: List[Position] = field(default_factory=list)
    
    # Performance
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    
    # Risk
    risk_metrics: Optional[RiskMetrics] = None
    
    @property
    def position_count(self) -> int:
        return len(self.positions)
    
    @property
    def total_exposure(self) -> float:
        return sum(p.value for p in self.positions)


@dataclass
class TradeResult:
    """Completed trade result - FROZEN STRUCTURE"""
    trade_id: str
    symbol: str
    side: OrderSide
    
    # Entry
    entry_time: datetime
    entry_price: float
    entry_quantity: float
    
    # Exit
    exit_time: datetime
    exit_price: float
    exit_quantity: float
    
    # P&L
    gross_pnl: float
    commission: float
    net_pnl: float
    pnl_percent: float
    
    # Risk metrics
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0
    risk_reward_achieved: float = 0.0
    
    # Metadata
    signal_id: Optional[str] = None
    hold_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_winner(self) -> bool:
        return self.net_pnl > 0
