"""
Trading Schema Definitions
Defines Pydantic models for trading opportunities, decisions, and execution
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
from uuid import uuid4

from trading_bot.schemas.market_data import TimeFrame

import logging
logger = logging.getLogger(__name__)



class OpportunityType(str, Enum):
    """Types of trading opportunities"""
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    FLOW = "flow"
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"
    NEWS = "news"
    CORRELATION = "correlation"
    BREAKOUT = "breakout"
    MEAN_REVERSION = "mean_reversion"
    MICROSTRUCTURE = "microstructure"


class Direction(str, Enum):
    """Trade direction"""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"


class TradingOpportunity(BaseModel):
    """Trading opportunity data model"""
    id: str = Field(default_factory=lambda: f"OPP_{uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    type: OpportunityType
    direction: Direction
    confidence: float = Field(ge=0.0, le=1.0)
    expected_return: float
    risk_score: float = Field(ge=0.0, le=1.0)
    timeframe: TimeFrame
    entry_price: float
    stop_loss: float
    take_profit: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def validate_risk_reward(self):
        """Validate risk-reward ratio"""
        try:
            entry = self.entry_price
            stop = self.stop_loss
            target = self.take_profit
            direction = self.direction
        
            if all(v is not None for v in [entry, stop, target, direction]):
                if direction == Direction.BUY:
                    risk = entry - stop
                    reward = target - entry
                else:  # SELL
                    risk = stop - entry
                    reward = entry - target
                
                if risk <= 0:
                    raise ValueError("Risk must be positive (stop loss must be valid)")
            
                if reward <= 0:
                    raise ValueError("Reward must be positive (take profit must be valid)")
        
            return self
        except Exception as e:
            logger.error(f"Error in validate_risk_reward: {e}")
            raise


class OrderType(str, Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    ICEBERG = "iceberg"
    TRAILING_STOP = "trailing_stop"


class ExecutionAlgorithm(str, Enum):
    """Execution algorithms"""
    TWAP = "twap"  # Time-Weighted Average Price
    VWAP = "vwap"  # Volume-Weighted Average Price
    POV = "pov"    # Percentage of Volume
    IS = "is"      # Implementation Shortfall
    ADAPTIVE = "adaptive"
    SNIPER = "sniper"
    GUERRILLA = "guerrilla"
    LIQUIDITY_SEEKING = "liquidity_seeking"


class ExecutionPlan(BaseModel):
    """Execution plan for a trading decision"""
    allocation: float
    entry_method: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[List[float]] = None
    time_limit: int = 60  # seconds
    execution_algo: ExecutionAlgorithm = ExecutionAlgorithm.ADAPTIVE
    slippage_limit: float = 0.002
    urgency: float = Field(ge=0.0, le=1.0, default=0.5)
    
    @field_validator('allocation')
    @classmethod
    def validate_allocation(cls, v):
        try:
            if v <= 0:
                raise ValueError("Allocation must be positive")
            return v
        except Exception as e:
            logger.error(f"Error in validate_allocation: {e}")
            raise


class TradingDecision(BaseModel):
    """Trading decision model"""
    decision_id: str = Field(default_factory=lambda: f"DEC_{uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.now)
    opportunity_ids: List[str]
    action: str  # BUY/SELL/HOLD
    symbols: List[str]
    allocation: Dict[str, float]
    risk_score: float = Field(ge=0.0, le=1.0)
    expected_return: float
    confidence: float = Field(ge=0.0, le=1.0)
    execution_plan: ExecutionPlan
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v):
        try:
            if not v:
                raise ValueError("Symbols list cannot be empty")
            return v
        except Exception as e:
            logger.error(f"Error in validate_symbols: {e}")
            raise
    
    @field_validator('opportunity_ids')
    @classmethod
    def validate_opportunity_ids(cls, v):
        try:
            if not v:
                raise ValueError("Opportunity IDs list cannot be empty")
            return v
        except Exception as e:
            logger.error(f"Error in validate_opportunity_ids: {e}")
            raise


class ExecutionResult(BaseModel):
    """Result of order execution"""
    order_id: str
    success: bool
    executed_price: float
    executed_quantity: float
    slippage: float
    execution_time: float  # seconds
    fees: float
    venue: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TradeStatus(str, Enum):
    """Trade status"""
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class ExitReason(str, Enum):
    """Reasons for trade exit"""
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    MANUAL = "manual"
    TIME_LIMIT = "time_limit"
    SIGNAL_REVERSAL = "signal_reversal"
    RISK_MANAGEMENT = "risk_management"
    TECHNICAL = "technical"


class Trade(BaseModel):
    """Trade model with full lifecycle information"""
    trade_id: str = Field(default_factory=lambda: f"TRADE_{uuid4().hex[:8]}")
    decision_id: str
    opportunity_ids: List[str]
    symbol: str
    direction: Direction
    entry_price: float
    current_price: Optional[float] = None
    stop_loss: float
    take_profit: float
    size: float
    status: TradeStatus = TradeStatus.PENDING
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    pnl: Optional[float] = None
    execution_details: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate trade duration in seconds"""
        try:
            if self.entry_time and self.exit_time:
                return (self.exit_time - self.entry_time).total_seconds()
            elif self.entry_time:
                return (datetime.now() - self.entry_time).total_seconds()
            return None
        except Exception as e:
            logger.error(f"Error in duration: {e}")
            raise
    
    @property
    def unrealized_pnl(self) -> Optional[float]:
        """Calculate unrealized PnL"""
        try:
            if self.current_price is None or self.entry_price is None:
                return None
            
            if self.direction == Direction.BUY:
                return (self.current_price - self.entry_price) * self.size
            else:  # SELL
                return (self.entry_price - self.current_price) * self.size
        except Exception as e:
            logger.error(f"Error in unrealized_pnl: {e}")
            raise


class PerformanceMetrics(BaseModel):
    """Trading performance metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    total_pnl: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percentage: float = 0.0
    average_trade_duration: float = 0.0  # seconds
    
    @field_validator('win_rate', 'profit_factor', 'sharpe_ratio', 'sortino_ratio')
    @classmethod
    def validate_ratios(cls, v):
        try:
            if v < 0:
                raise ValueError("Ratio metrics must be non-negative")
            return v
        except Exception as e:
            logger.error(f"Error in validate_ratios: {e}")
            raise
