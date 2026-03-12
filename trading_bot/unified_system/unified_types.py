"""
Unified Types - Core type definitions for the unified trading system

Provides standardized enums, dataclasses, and type definitions used across all layers.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


# =============================================================================
# SYSTEM STATUS ENUMS
# =============================================================================

class SystemStatus(Enum):
    """Overall system status"""
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"


class LayerStatus(Enum):
    """Status of an individual layer"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    DEGRADED = "degraded"
    ERROR = "error"
    DISABLED = "disabled"


class TradingMode(Enum):
    """Trading operation mode"""
    DISABLED = "disabled"          # No trading at all
    SIMULATION = "simulation"      # Pure simulation, no broker
    PAPER = "paper"                # Paper trading with broker
    LIVE = "live"                  # Live trading with real money
    DRY_RUN = "dry_run"           # Generate signals but don't execute


class OperationMode(Enum):
    """System operation mode"""
    AUTONOMOUS = "autonomous"      # Fully autonomous operation
    SEMI_AUTONOMOUS = "semi"       # Human approval for major decisions
    MANUAL = "manual"              # Human controls all decisions
    EMERGENCY = "emergency"        # Emergency mode - minimal operations


# =============================================================================
# MARKET ENUMS
# =============================================================================

class MarketRegime(Enum):
    """Market regime classification"""
    UNKNOWN = "unknown"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    QUIET = "quiet"
    TRANSITIONING = "transitioning"
    CRISIS = "crisis"


class Timeframe(Enum):
    """Trading timeframes"""
    TICK = "tick"
    S1 = "1s"
    S5 = "5s"
    S15 = "15s"
    S30 = "30s"
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN1 = "1M"


class AssetClass(Enum):
    """Asset class types"""
    FOREX = "forex"
    CRYPTO = "crypto"
    STOCKS = "stocks"
    FUTURES = "futures"
    OPTIONS = "options"
    COMMODITIES = "commodities"
    INDICES = "indices"


# =============================================================================
# SIGNAL ENUMS
# =============================================================================

class SignalDirection(Enum):
    """Trading signal direction"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


class SignalStrength(Enum):
    """Signal strength classification"""
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


class SignalSource(Enum):
    """Source of trading signal"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    ML_MODEL = "ml_model"
    RL_AGENT = "rl_agent"
    ENSEMBLE = "ensemble"
    HUMAN = "human"
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"


# =============================================================================
# RISK ENUMS
# =============================================================================

class RiskLevel(Enum):
    """Risk level classification"""
    MINIMAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    EXTREME = 5
    CRITICAL = 6


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"              # Normal operation
    OPEN = "open"                  # Tripped, blocking operations
    HALF_OPEN = "half_open"        # Testing if safe to resume


class FailSafeMode(Enum):
    """Fail-safe operation modes"""
    NORMAL = "normal"
    CAUTIOUS = "cautious"
    DEFENSIVE = "defensive"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"


# =============================================================================
# EXECUTION ENUMS
# =============================================================================

class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ExecutionAlgorithm(Enum):
    """Execution algorithms"""
    MARKET = "market"
    TWAP = "twap"
    VWAP = "vwap"
    POV = "pov"
    IMPLEMENTATION_SHORTFALL = "is"
    ADAPTIVE = "adaptive"
    ICEBERG = "iceberg"
    SNIPER = "sniper"
    DARK_POOL = "dark_pool"


# =============================================================================
# GOVERNANCE ENUMS
# =============================================================================

class GovernanceLevel(Enum):
    """Governance hierarchy levels"""
    G0_HUMAN = 0       # Human authority (ultimate control)
    G1_SYSTEM = 1      # System-level control
    G2_AGENT = 2       # AI agent level


class ApprovalStatus(Enum):
    """Approval workflow status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MarketData:
    """Unified market data structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    timeframe: Timeframe = Timeframe.M1
    source: str = "unknown"
    quality_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradingSignal:
    """Unified trading signal structure"""
    signal_id: str
    symbol: str
    direction: SignalDirection
    confidence: float
    strength: SignalStrength
    timestamp: datetime
    source: SignalSource
    reasoning: str
    
    # Risk parameters
    risk_score: float = 0.5
    expected_return: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    
    # Context
    regime: MarketRegime = MarketRegime.UNKNOWN
    timeframe: Timeframe = Timeframe.M1
    
    # Verification
    verified: bool = False
    verification_score: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Order:
    """Unified order structure"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_price: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Execution
    algorithm: ExecutionAlgorithm = ExecutionAlgorithm.MARKET
    slippage: float = 0.0
    commission: float = 0.0
    
    # Metadata
    signal_id: Optional[str] = None
    client_order_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """Position tracking structure"""
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float
    
    # P&L
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # Risk
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Timestamps
    opened_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    strategy: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskMetrics:
    """Risk metrics structure"""
    # Portfolio risk
    portfolio_var: float = 0.0
    portfolio_cvar: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    
    # Position risk
    total_exposure: float = 0.0
    largest_position: float = 0.0
    correlation_risk: float = 0.0
    
    # Limits
    daily_loss: float = 0.0
    daily_loss_limit: float = 0.05
    weekly_loss: float = 0.0
    weekly_loss_limit: float = 0.10
    
    # Status
    risk_level: RiskLevel = RiskLevel.LOW
    circuit_breaker: CircuitBreakerState = CircuitBreakerState.CLOSED
    
    # Timestamp
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SystemHealth:
    """System health metrics"""
    status: SystemStatus
    uptime_seconds: float
    
    # Layer health
    layer_status: Dict[str, LayerStatus] = field(default_factory=dict)
    
    # Performance
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    latency_ms: float = 0.0
    
    # Errors
    error_count: int = 0
    warning_count: int = 0
    last_error: Optional[str] = None
    
    # Trading
    signals_generated: int = 0
    trades_executed: int = 0
    active_positions: int = 0
    
    # Timestamp
    checked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TradingDecision:
    """Final trading decision structure"""
    decision_id: str
    signal: TradingSignal
    
    # Decision
    action: SignalDirection
    approved: bool
    confidence: float
    
    # Sizing
    position_size: float
    risk_amount: float
    
    # Levels
    entry_price: float
    stop_loss: float
    take_profit: float
    
    # Verification
    verification_score: float
    risk_check_passed: bool
    
    # Reasoning
    reasoning: str
    reasoning_chain: List[str] = field(default_factory=list)
    
    # Governance
    approval_level: GovernanceLevel = GovernanceLevel.G1_SYSTEM
    approved_by: str = "system"
    
    # Timestamp
    decided_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LayerMetrics:
    """Metrics for a single layer"""
    layer_name: str
    status: LayerStatus
    
    # Performance
    processing_time_ms: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0
    
    # Resources
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    
    # Custom metrics
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Timestamp
    collected_at: datetime = field(default_factory=datetime.utcnow)
