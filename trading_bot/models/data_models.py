"""
Data Models
Pydantic models for data validation across the trading system
"""

from pydantic import BaseModel, Field, validator
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

import logging
logger = logging.getLogger(__name__)


class Direction(str, Enum):
    """Trading direction enum"""
    BUY = "buy"
    SELL = "sell"

class TimeFrame(str, Enum):
    """Timeframe enum"""
    TICK = "tick"
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"

class MarketRegime(str, Enum):
    """Market regime enum"""
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"

class MarketTick(BaseModel):
    """Market tick data model"""
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.now)
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: float = 0
    
    @validator('price')
    def price_must_be_positive(cls, v):
        try:
            if v <= 0:
                raise ValueError('Price must be positive')
            return v
        except Exception as e:
            logger.error(f"Error in price_must_be_positive: {e}")
            raise
    
    @validator('bid', 'ask', pre=True, always=True)
    def set_bid_ask_from_price(cls, v, values):
        try:
            if v is None:
                if 'price' in values:
                    return values['price']
            return v
        except Exception as e:
            logger.error(f"Error in set_bid_ask_from_price: {e}")
            raise

class OHLCBar(BaseModel):
    """OHLC bar data model"""
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.now)
    open: float
    high: float
    low: float
    close: float
    volume: float = 0
    timeframe: TimeFrame = TimeFrame.M1
    price: Optional[float] = None
    
    @validator('price', pre=True, always=True)
    def set_price_from_close(cls, v, values):
        try:
            if v is None:
                if 'close' in values:
                    return values['close']
            return v
        except Exception as e:
            logger.error(f"Error in set_price_from_close: {e}")
            raise
    
    @validator('high')
    def high_must_be_highest(cls, v, values):
        try:
            if 'open' in values and 'low' in values and 'close' in values:
                if v < max(values['open'], values['low'], values['close']):
                    raise ValueError('High must be the highest value')
            return v
        except Exception as e:
            logger.error(f"Error in high_must_be_highest: {e}")
            raise
    
    @validator('low')
    def low_must_be_lowest(cls, v, values):
        try:
            if 'open' in values and 'high' in values and 'close' in values:
                if v > min(values['open'], values['high'], values['close']):
                    raise ValueError('Low must be the lowest value')
            return v
        except Exception as e:
            logger.error(f"Error in low_must_be_lowest: {e}")
            raise

class OrderFlowSnapshot(BaseModel):
    """Order flow snapshot data model"""
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.now)
    price: float
    imbalance_ratio: float = Field(ge=-1.0, le=1.0)
    pressure_score: float = Field(ge=-1.0, le=1.0)
    exhaustion_level: float = Field(ge=0.0, le=1.0)
    absorption_score: float = Field(ge=0.0, le=1.0)
    momentum_score: float = Field(ge=-1.0, le=1.0)
    institutional_activity: bool = False
    
    class Config:
        validate_assignment = True

class MicrostructureMetrics(BaseModel):
    """Market microstructure metrics data model"""
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.now)
    price: float
    liquidity_score: float = Field(ge=0.0, le=1.0)
    trade_clusters: List[Dict[str, Any]] = []
    liquidity_zones: List[Dict[str, Any]] = []
    price_impact: float = 0.0
    institutional_levels: List[Dict[str, float]] = []
    
    class Config:
        validate_assignment = True

class AnalyticsResult(BaseModel):
    """Analytics result with predictive signals"""
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.now)
    price: float
    predictions: Dict[str, float] = {}
    confidence: float = Field(ge=0.0, le=1.0)
    features: Dict[str, float] = {}
    market_regime: MarketRegime = MarketRegime.RANGING
    signals: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

class TradingSignal(BaseModel):
    """Trading signal with execution details"""
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.now)
    direction: Direction
    signal_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    size: float
    confidence: float = Field(ge=0.0, le=1.0)
    timeframe: TimeFrame = TimeFrame.M5
    metadata: Dict[str, Any] = {}
    
    @validator('stop_loss')
    def validate_stop_loss(cls, v, values):
        try:
            if 'direction' in values and 'entry_price' in values:
                if values['direction'] == Direction.BUY and v >= values['entry_price']:
                    raise ValueError('Stop loss must be below entry price for buy signals')
                elif values['direction'] == Direction.SELL and v <= values['entry_price']:
                    raise ValueError('Stop loss must be above entry price for sell signals')
            return v
        except Exception as e:
            logger.error(f"Error in validate_stop_loss: {e}")
            raise
    
    @validator('take_profit')
    def validate_take_profit(cls, v, values):
        try:
            if 'direction' in values and 'entry_price' in values:
                if values['direction'] == Direction.BUY and v <= values['entry_price']:
                    raise ValueError('Take profit must be above entry price for buy signals')
                elif values['direction'] == Direction.SELL and v >= values['entry_price']:
                    raise ValueError('Take profit must be below entry price for sell signals')
            return v
        except Exception as e:
            logger.error(f"Error in validate_take_profit: {e}")
            raise

class OpportunityData(BaseModel):
    """Trading opportunity data"""
    id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    type: str
    direction: Direction
    confidence: float = Field(ge=0.0, le=1.0)
    expected_return: float
    risk_score: float = Field(ge=0.0, le=1.0)
    timeframe: TimeFrame = TimeFrame.M5
    entry_price: float
    stop_loss: float
    take_profit: float
    metadata: Dict[str, Any] = {}
    
    @validator('expected_return')
    def validate_expected_return(cls, v, values):
        try:
            if 'risk_score' in values and values['risk_score'] > 0:
                if v / values['risk_score'] < 1.0:
                    raise ValueError('Expected return should be greater than risk (poor risk/reward)')
            return v
        except Exception as e:
            logger.error(f"Error in validate_expected_return: {e}")
            raise

class TradeResult(BaseModel):
    """Trade execution result"""
    trade_id: str
    symbol: str
    direction: Direction
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    size: float
    pnl: float = 0.0
    status: str = "active"  # active, closed
    exit_reason: Optional[str] = None  # take_profit, stop_loss, manual
    signal_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        validate_assignment = True
