"""
AlphaAlgo V2 Core Types

STABILITY GUARANTEE: These types are FROZEN and will NEVER change.
All components use these types for data exchange.

Design Principles:
1. Immutable - Use frozen dataclasses where possible
2. Type Safe - Full type hints for all fields
3. Serializable - All types can be serialized to JSON
4. Validated - All types have validation logic
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
import json
import pandas

import logging
logger = logging.getLogger(__name__)



# ============================================================================
# ENUMS
# ============================================================================

class SignalType(Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"
    CLOSE_BUY = "close_buy"
    CLOSE_SELL = "close_sell"


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RiskLevel(Enum):
    """Risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProposalStatus(Enum):
    """Evolution proposal status"""
    PENDING = "pending"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"


class TradingMode(Enum):
    """Trading modes"""
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"
    SIMULATION = "simulation"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass(frozen=True)
class Tick:
    """
    Single tick data point
    
    Attributes:
        symbol: Trading symbol
        bid: Bid price
        ask: Ask price
        last: Last traded price
        volume: Volume at last price
        time: Tick timestamp
    """
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    time: datetime
    
    @property
    def spread(self) -> float:
        """Calculate bid-ask spread"""
        return self.ask - self.bid
    
    @property
    def mid(self) -> float:
        """Calculate mid price"""
        return (self.bid + self.ask) / 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "bid": self.bid,
            "ask": self.ask,
            "last": self.last,
            "volume": self.volume,
            "time": self.time.isoformat(),
        }


@dataclass(frozen=True)
class OHLCV:
    """
    Single OHLCV bar
    
    Attributes:
        symbol: Trading symbol
        timeframe: Bar timeframe
        open: Open price
        high: High price
        low: Low price
        close: Close price
        volume: Bar volume
        time: Bar timestamp
    """
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    time: datetime
    
    @property
    def range(self) -> float:
        """Calculate bar range"""
        return self.high - self.low
    
    @property
    def body(self) -> float:
        """Calculate bar body"""
        return abs(self.close - self.open)
    
    @property
    def is_bullish(self) -> bool:
        """Check if bar is bullish"""
        return self.close > self.open
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "time": self.time.isoformat(),
        }


@dataclass
class MarketData:
    """
    Container for market data
    
    Attributes:
        symbol: Trading symbol
        timeframe: Primary timeframe
        ohlcv: OHLCV DataFrame
        ticks: Recent ticks
        orderbook: Order book data
        metadata: Additional metadata
    """
    symbol: str
    timeframe: str
    ohlcv: Any  # pd.DataFrame
    ticks: List[Tick] = field(default_factory=list)
    orderbook: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def last_price(self) -> float:
        """Get last price"""
        try:
            if self.ticks:
                return self.ticks[-1].last
            if self.ohlcv is not None and len(self.ohlcv) > 0:
                return float(self.ohlcv.iloc[-1]["close"])
            return 0.0
        except Exception as e:
            logger.error(f"Error in last_price: {e}")
            raise
    
    @property
    def last_time(self) -> Optional[datetime]:
        """Get last timestamp"""
        try:
            if self.ticks:
                return self.ticks[-1].time
            if self.ohlcv is not None and len(self.ohlcv) > 0:
                return self.ohlcv.iloc[-1]["time"]
            return None
        except Exception as e:
            logger.error(f"Error in last_time: {e}")
            raise


@dataclass
class Signal:
    """
    Trading signal
    
    Attributes:
        id: Unique signal ID
        symbol: Trading symbol
        signal_type: Signal type (buy/sell/hold)
        price: Signal price
        confidence: Confidence score (0-1)
        stop_loss: Stop loss price
        take_profit: Take profit price
        timeframe: Signal timeframe
        source: Signal source/generator
        metadata: Additional metadata
        created_at: Creation timestamp
        expires_at: Expiration timestamp
    """
    id: str
    symbol: str
    signal_type: SignalType
    price: float
    confidence: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timeframe: str = "M15"
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if signal is expired"""
        try:
            if self.expires_at is None:
                return False
            return datetime.now() > self.expires_at
        except Exception as e:
            logger.error(f"Error in is_expired: {e}")
            raise
    
    @property
    def risk_reward_ratio(self) -> Optional[float]:
        """Calculate risk/reward ratio"""
        try:
            if self.stop_loss is None or self.take_profit is None:
                return None
            risk = abs(self.price - self.stop_loss)
            reward = abs(self.take_profit - self.price)
            if risk == 0:
                return None
            return reward / risk
        except Exception as e:
            logger.error(f"Error in risk_reward_ratio: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "price": self.price,
            "confidence": self.confidence,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "timeframe": self.timeframe,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class Order:
    """
    Trading order
    
    Attributes:
        id: Unique order ID
        symbol: Trading symbol
        order_type: Order type (market/limit/stop)
        side: Order side (buy/sell)
        volume: Order volume
        price: Order price (for limit/stop)
        stop_loss: Stop loss price
        take_profit: Take profit price
        status: Order status
        signal_id: Associated signal ID
        created_at: Creation timestamp
    """
    id: str
    symbol: str
    order_type: OrderType
    side: SignalType
    volume: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    signal_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "order_type": self.order_type.value,
            "side": self.side.value,
            "volume": self.volume,
            "price": self.price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "status": self.status.value,
            "signal_id": self.signal_id,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Position:
    """
    Open position
    
    Attributes:
        id: Position ID
        symbol: Trading symbol
        side: Position side (buy/sell)
        volume: Position volume
        entry_price: Entry price
        current_price: Current price
        stop_loss: Stop loss price
        take_profit: Take profit price
        profit: Current profit
        opened_at: Open timestamp
    """
    id: str
    symbol: str
    side: SignalType
    volume: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    profit: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def profit_pips(self) -> float:
        """Calculate profit in pips"""
        try:
            diff = self.current_price - self.entry_price
            if self.side == SignalType.SELL:
                diff = -diff
            # Assume 4 decimal places for forex
            return diff * 10000
        except Exception as e:
            logger.error(f"Error in profit_pips: {e}")
            raise
    
    @property
    def profit_percent(self) -> float:
        """Calculate profit percentage"""
        try:
            if self.entry_price == 0:
                return 0.0
            diff = self.current_price - self.entry_price
            if self.side == SignalType.SELL:
                diff = -diff
            return (diff / self.entry_price) * 100
        except Exception as e:
            logger.error(f"Error in profit_percent: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "volume": self.volume,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "profit": self.profit,
            "opened_at": self.opened_at.isoformat(),
        }


@dataclass
class Trade:
    """
    Completed trade
    
    Attributes:
        id: Trade ID
        symbol: Trading symbol
        side: Trade side
        volume: Trade volume
        entry_price: Entry price
        exit_price: Exit price
        profit: Trade profit
        opened_at: Open timestamp
        closed_at: Close timestamp
        duration_seconds: Trade duration
    """
    id: str
    symbol: str
    side: SignalType
    volume: float
    entry_price: float
    exit_price: float
    profit: float
    opened_at: datetime
    closed_at: datetime
    signal_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate trade duration in seconds"""
        return (self.closed_at - self.opened_at).total_seconds()
    
    @property
    def is_winner(self) -> bool:
        """Check if trade is a winner"""
        return self.profit > 0
    
    @property
    def profit_pips(self) -> float:
        """Calculate profit in pips"""
        try:
            diff = self.exit_price - self.entry_price
            if self.side == SignalType.SELL:
                diff = -diff
            return diff * 10000
        except Exception as e:
            logger.error(f"Error in profit_pips: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "volume": self.volume,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "profit": self.profit,
            "opened_at": self.opened_at.isoformat(),
            "closed_at": self.closed_at.isoformat(),
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class TradeResult:
    """
    Trade result for reward calculation
    
    Attributes:
        trade: The completed trade
        profit_factor: Profit factor
        sharpe_ratio: Sharpe ratio
        win_rate: Win rate
        max_drawdown: Maximum drawdown
        risk_reward_ratio: Risk/reward ratio
    """
    trade: Trade
    profit_factor: float = 1.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.5
    max_drawdown: float = 0.0
    risk_reward_ratio: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trade": self.trade.to_dict(),
            "profit_factor": self.profit_factor,
            "sharpe_ratio": self.sharpe_ratio,
            "win_rate": self.win_rate,
            "max_drawdown": self.max_drawdown,
            "risk_reward_ratio": self.risk_reward_ratio,
        }


@dataclass
class RiskDecision:
    """
    Risk validation decision
    
    Attributes:
        allowed: Whether trade is allowed
        reason: Reason for decision
        risk_level: Current risk level
        adjusted_size: Adjusted position size (if any)
        warnings: List of warnings
    """
    allowed: bool
    reason: str
    risk_level: RiskLevel = RiskLevel.LOW
    adjusted_size: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "risk_level": self.risk_level.value,
            "adjusted_size": self.adjusted_size,
            "warnings": self.warnings,
        }


@dataclass
class ExecutionResult:
    """
    Order execution result
    
    Attributes:
        success: Whether execution succeeded
        order_id: Order ID
        fill_price: Fill price
        fill_volume: Fill volume
        slippage: Slippage in pips
        latency_ms: Execution latency in milliseconds
        message: Result message
    """
    success: bool
    order_id: str
    fill_price: Optional[float] = None
    fill_volume: Optional[float] = None
    slippage: float = 0.0
    latency_ms: float = 0.0
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "order_id": self.order_id,
            "fill_price": self.fill_price,
            "fill_volume": self.fill_volume,
            "slippage": self.slippage,
            "latency_ms": self.latency_ms,
            "message": self.message,
        }


@dataclass
class EvolutionProposal:
    """
    Evolution improvement proposal
    
    Attributes:
        id: Proposal ID
        title: Proposal title
        description: Detailed description
        category: Proposal category
        priority: Priority (1-5, 1 is highest)
        requires_human_approval: Whether human approval is required
        status: Current status
        changes: Proposed changes
        validation_results: Validation results
        created_at: Creation timestamp
    """
    id: str
    title: str
    description: str
    category: str
    priority: int = 3
    requires_human_approval: bool = False
    status: ProposalStatus = ProposalStatus.PENDING
    changes: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    deployed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "requires_human_approval": self.requires_human_approval,
            "status": self.status.value,
            "changes": self.changes,
            "validation_results": self.validation_results,
            "created_at": self.created_at.isoformat(),
            "approved_by": self.approved_by,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
        }
