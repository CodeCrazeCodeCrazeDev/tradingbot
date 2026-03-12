"""
Market Data Schema Definitions
Defines Pydantic models for market data validation
"""

from pydantic import BaseModel, Field, validator
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

import logging
logger = logging.getLogger(__name__)



class TimeFrame(str, Enum):
    """Time frames for market data"""
    TICK = "tick"
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN1 = "1M"


class MarketTick(BaseModel):
    """Single market tick data"""
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    price: float
    volume: float = 0.0
    bid: Optional[float] = None
    ask: Optional[float] = None
    direction: Optional[str] = None  # "buy" or "sell"
    source: Optional[str] = None
    
    @validator('price', 'bid', 'ask', 'volume')
    def validate_numeric(cls, v):
        try:
            if v is not None and v < 0:
                raise ValueError("Numeric values must be non-negative")
            return v
        except Exception as e:
            logger.error(f"Error in validate_numeric: {e}")
            raise
    
    @validator('direction')
    def validate_direction(cls, v):
        try:
            if v is not None and v not in ["buy", "sell"]:
                raise ValueError("Direction must be 'buy' or 'sell'")
            return v
        except Exception as e:
            logger.error(f"Error in validate_direction: {e}")
            raise


class OHLCBar(BaseModel):
    """OHLC bar data"""
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    timeframe: TimeFrame
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    tick_count: Optional[int] = None
    
    @validator('high')
    def high_greater_than_low(cls, v, values):
        try:
            if 'low' in values and v < values['low']:
                raise ValueError("High must be greater than or equal to low")
            return v
        except Exception as e:
            logger.error(f"Error in high_greater_than_low: {e}")
            raise
    
    @validator('high')
    def high_greater_than_open_close(cls, v, values):
        try:
            if 'open' in values and v < values['open']:
                raise ValueError("High must be greater than or equal to open")
            if 'close' in values and v < values['close']:
                raise ValueError("High must be greater than or equal to close")
            return v
        except Exception as e:
            logger.error(f"Error in high_greater_than_open_close: {e}")
            raise
    
    @validator('low')
    def low_less_than_open_close(cls, v, values):
        try:
            if 'open' in values and v > values['open']:
                raise ValueError("Low must be less than or equal to open")
            if 'close' in values and v > values['close']:
                raise ValueError("Low must be less than or equal to close")
            return v
        except Exception as e:
            logger.error(f"Error in low_less_than_open_close: {e}")
            raise


class OrderBookLevel(BaseModel):
    """Single level in the order book"""
    price: float
    volume: float
    count: Optional[int] = None


class OrderBook(BaseModel):
    """Order book snapshot"""
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    
    @validator('bids')
    def validate_bids(cls, v):
        try:
            if not v:
                raise ValueError("Bids cannot be empty")
            return v
        except Exception as e:
            logger.error(f"Error in validate_bids: {e}")
            raise
    
    @validator('asks')
    def validate_asks(cls, v):
        try:
            if not v:
                raise ValueError("Asks cannot be empty")
            return v
        except Exception as e:
            logger.error(f"Error in validate_asks: {e}")
            raise


class OrderFlowSnapshot(BaseModel):
    """Order flow analysis snapshot"""
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    delta: float  # Buy volume - sell volume
    imbalance: float  # Ratio of buy/sell
    absorption: Optional[float] = None  # Price absorption metric
    exhaustion: Optional[float] = None  # Buying/selling exhaustion
    large_orders: Optional[List[Dict[str, Any]]] = None  # Large order detection
    
    class Config:
        arbitrary_types_allowed = True


class MarketMicrostructureMetrics(BaseModel):
    """Market microstructure metrics"""
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    liquidity: float  # Market liquidity metric
    spread: float  # Bid-ask spread
    depth: float  # Market depth
    volatility: float  # Price volatility
    efficiency: Optional[float] = None  # Market efficiency ratio
    fragmentation: Optional[float] = None  # Market fragmentation
    
    @validator('spread', 'volatility')
    def validate_non_negative(cls, v):
        try:
            if v < 0:
                raise ValueError("Value must be non-negative")
            return v
        except Exception as e:
            logger.error(f"Error in validate_non_negative: {e}")
            raise


class MarketSignal(BaseModel):
    """Market signal from analysis"""
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    signal_type: str  # e.g., "momentum", "reversal", "breakout"
    direction: str  # "buy" or "sell"
    strength: float  # Signal strength (0-1)
    timeframe: TimeFrame
    source: str  # Signal source/strategy
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('strength')
    def validate_strength(cls, v):
        try:
            if not 0 <= v <= 1:
                raise ValueError("Strength must be between 0 and 1")
            return v
        except Exception as e:
            logger.error(f"Error in validate_strength: {e}")
            raise
    
    @validator('direction')
    def validate_direction(cls, v):
        try:
            if v not in ["buy", "sell", "neutral"]:
                raise ValueError("Direction must be 'buy', 'sell', or 'neutral'")
            return v
        except Exception as e:
            logger.error(f"Error in validate_direction: {e}")
            raise


class MarketState(BaseModel):
    """Overall market state"""
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    trend: str  # "bullish", "bearish", "sideways"
    volatility: float  # Current volatility level
    liquidity: float  # Current liquidity level
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"
    regime: Optional[str] = None  # "trending", "ranging", "chaotic"
    
    @validator('trend')
    def validate_trend(cls, v):
        try:
            if v not in ["bullish", "bearish", "sideways"]:
                raise ValueError("Trend must be 'bullish', 'bearish', or 'sideways'")
            return v
        except Exception as e:
            logger.error(f"Error in validate_trend: {e}")
            raise
    
    @validator('sentiment')
    def validate_sentiment(cls, v):
        try:
            if v is not None and v not in ["positive", "negative", "neutral"]:
                raise ValueError("Sentiment must be 'positive', 'negative', or 'neutral'")
            return v
        except Exception as e:
            logger.error(f"Error in validate_sentiment: {e}")
            raise
