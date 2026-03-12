"""
Elite Trading Bot - Market Condition Monitor

This module provides real-time market condition monitoring capabilities for the Elite Trading Bot,
enabling detection of volatility changes, liquidity shifts, correlation breakdowns, and regime changes.
"""

import enum
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import math

import numpy as np
import pandas as pd
try:
    from scipy import stats
except ImportError:
    scipy = None

from .event_monitor import EventMonitor, MarketEvent, EventType, EventPriority, EventSource
from enum import Enum
from enum import auto
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



# Configure logging
logger = logging.getLogger(__name__)


class VolatilityState(enum.Enum):
    """Volatility states of the market."""
    EXTREMELY_LOW = "extremely_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREMELY_HIGH = "extremely_high"
    EXPANDING = "expanding"      # Volatility is increasing
    CONTRACTING = "contracting"  # Volatility is decreasing
    BREAKOUT = "breakout"        # Sudden volatility expansion


class LiquidityState(enum.Enum):
    """Liquidity states of the market."""
    VERY_THIN = "very_thin"      # Very low liquidity
    THIN = "thin"                # Below normal liquidity
    NORMAL = "normal"            # Normal liquidity
    DEEP = "deep"                # Above normal liquidity
    VERY_DEEP = "very_deep"      # Very high liquidity
    DRYING = "drying"            # Liquidity is decreasing
    IMPROVING = "improving"      # Liquidity is increasing
    IMBALANCED = "imbalanced"    # Significant bid/ask imbalance


class MarketRegime(enum.Enum):
    """Market regime states."""
    TRENDING_BULLISH = "trending_bullish"
    TRENDING_BEARISH = "trending_bearish"
    RANGING = "ranging"
    VOLATILE_BULLISH = "volatile_bullish"
    VOLATILE_BEARISH = "volatile_bearish"
    VOLATILE_NEUTRAL = "volatile_neutral"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    MEAN_REVERTING = "mean_reverting"
    TRANSITIONING = "transitioning"
    UNKNOWN = "unknown"


@dataclass
class MarketCondition:
    """Current market condition state."""
    symbol: str
    timestamp: datetime
    volatility_state: VolatilityState
    liquidity_state: LiquidityState
    regime: MarketRegime
    atr: float
    atr_percentile: float  # 0-100 percentile of ATR relative to history
    volume: Optional[float] = None
    volume_percentile: Optional[float] = None  # 0-100 percentile
    bid_ask_spread: Optional[float] = None
    spread_percentile: Optional[float] = None  # 0-100 percentile
    hurst_exponent: Optional[float] = None  # Market memory/fractality
    current_correlation_state: Optional[Dict[str, float]] = None  # Correlation with other assets
    timeframe: str = "1h"


class CorrelationTracker:
    """Tracks correlations between assets."""
    
    def __init__(self, lookback_periods: int = 100):
        """
        Initialize correlation tracker.
        
        Args:
            lookback_periods: Number of periods to use for correlation calculation
        """
        self.lookback_periods = lookback_periods
        self.price_history: Dict[str, List[float]] = {}
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        self.correlation_change: Dict[str, Dict[str, float]] = {}
        self.last_update = datetime.now()
    
    def add_price(self, symbol: str, price: float):
        """
        Add a price point for a symbol.
        
        Args:
            symbol: Symbol identifier
            price: Current price
        """
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            
        self.price_history[symbol].append(price)
        
        # Keep only lookback periods
        if len(self.price_history[symbol]) > self.lookback_periods:
            self.price_history[symbol] = self.price_history[symbol][-self.lookback_periods:]
    
    def update_correlations(self):
        """Update correlation matrix for all tracked symbols."""
        # Need at least 2 symbols with enough data
        symbols_with_data = [
            symbol for symbol, prices in self.price_history.items()
            if len(prices) >= 30  # Need at least 30 data points for meaningful correlation
        ]
        
        if len(symbols_with_data) < 2:
            return
            
        # Previous correlation matrix
        prev_matrix = self.correlation_matrix.copy()
        
        # Calculate new correlation matrix
        self.correlation_matrix = {}
        
        for symbol1 in symbols_with_data:
            self.correlation_matrix[symbol1] = {}
            
            for symbol2 in symbols_with_data:
                if symbol1 == symbol2:
                    self.correlation_matrix[symbol1][symbol2] = 1.0
                    continue
                    
                # Get price data
                prices1 = self.price_history[symbol1]
                prices2 = self.price_history[symbol2]
                
                # Calculate returns
                returns1 = [prices1[i] / prices1[i-1] - 1 for i in range(1, len(prices1))]
                returns2 = [prices2[i] / prices2[i-1] - 1 for i in range(1, len(prices2))]
                
                # Use shorter length
                min_len = min(len(returns1), len(returns2))
                returns1 = returns1[-min_len:]
                returns2 = returns2[-min_len:]
                
                # Calculate correlation
                if min_len >= 30:  # Need at least 30 points for meaningful correlation
                    corr, _ = stats.pearsonr(returns1, returns2)
                    self.correlation_matrix[symbol1][symbol2] = corr
                else:
                    self.correlation_matrix[symbol1][symbol2] = 0.0
        
        # Calculate correlation changes
        self.correlation_change = {}
        
        for symbol1 in self.correlation_matrix:
            self.correlation_change[symbol1] = {}
            
            for symbol2 in self.correlation_matrix[symbol1]:
                prev_corr = prev_matrix.get(symbol1, {}).get(symbol2, 0.0)
                curr_corr = self.correlation_matrix[symbol1][symbol2]
                
                self.correlation_change[symbol1][symbol2] = curr_corr - prev_corr
        
        self.last_update = datetime.now()
    
    def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """
        Get correlation between two symbols.
        
        Args:
            symbol1: First symbol
            symbol2: Second symbol
            
        Returns:
            Correlation coefficient or None if not available
        """
        if symbol1 not in self.correlation_matrix or symbol2 not in self.correlation_matrix[symbol1]:
            return None
            
        return self.correlation_matrix[symbol1][symbol2]
    
    def get_correlation_change(self, symbol1: str, symbol2: str) -> Optional[float]:
        """
        Get correlation change between two symbols.
        
        Args:
            symbol1: First symbol
            symbol2: Second symbol
            
        Returns:
            Correlation change or None if not available
        """
        if symbol1 not in self.correlation_change or symbol2 not in self.correlation_change[symbol1]:
            return None
            
        return self.correlation_change[symbol1][symbol2]
    
    def get_highly_correlated(self, symbol: str, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Get symbols highly correlated with the given symbol.
        
        Args:
            symbol: Symbol to check
            threshold: Correlation threshold
            
        Returns:
            List of (symbol, correlation) tuples
        """
        if symbol not in self.correlation_matrix:
            return []
            
        return [
            (other_symbol, corr)
            for other_symbol, corr in self.correlation_matrix[symbol].items()
            if corr >= threshold and other_symbol != symbol
        ]
    
    def get_correlation_breakdown(self, symbol: str, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """
        Get symbols with significant correlation breakdown with the given symbol.
        
        Args:
            symbol: Symbol to check
            threshold: Change threshold
            
        Returns:
            List of (symbol, change) tuples
        """
        if symbol not in self.correlation_change:
            return []
            
        return [
            (other_symbol, change)
            for other_symbol, change in self.correlation_change[symbol].items()
            if abs(change) >= threshold and other_symbol != symbol
        ]


class RegimeDetector:
    """Detects market regimes based on price action and indicators."""
    
    def __init__(self, lookback_periods: int = 100):
        """
        Initialize regime detector.
        
        Args:
            lookback_periods: Number of periods to use for regime detection
        """
        self.lookback_periods = lookback_periods
        self.price_history: Dict[str, pd.DataFrame] = {}
        self.current_regime: Dict[str, MarketRegime] = {}
        self.regime_start_time: Dict[str, datetime] = {}
        self.last_update = datetime.now()
    
    def add_market_data(self, symbol: str, data: pd.DataFrame):
        """
        Add market data for a symbol.
        
        Args:
            symbol: Symbol identifier
            data: DataFrame with OHLCV data
        """
        # Ensure we have the required columns
        required_columns = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Data must contain columns: {required_columns}")
            
        # Store data
        self.price_history[symbol] = data.tail(self.lookback_periods)
    
    def update_regime(self, symbol: str) -> Optional[MarketRegime]:
        """
        Update market regime for a symbol.
        
        Args:
            symbol: Symbol to update
            
        Returns:
            Current market regime or None if not enough data
        """
        if symbol not in self.price_history:
            return None
            
        data = self.price_history[symbol]
        
        if len(data) < 30:  # Need at least 30 data points
            return None
            
        # Calculate indicators
        # 1. Trend indicators
        data['sma20'] = data['close'].rolling(window=20).mean()
        data['sma50'] = data['close'].rolling(window=50).mean()
        
        # 2. Volatility indicators
        data['atr'] = self._calculate_atr(data)
        data['atr_ma'] = data['atr'].rolling(window=20).mean()
        
        # 3. Momentum indicators
        data['rsi'] = self._calculate_rsi(data['close'])
        
        # 4. Mean reversion indicators
        data['zscore'] = (data['close'] - data['close'].rolling(window=20).mean()) / data['close'].rolling(window=20).std()
        
        # Get latest values
        latest = data.iloc[-1]
        
        # Detect regime
        regime = self._detect_regime(data)
        
        # Check if regime has changed
        prev_regime = self.current_regime.get(symbol)
        if prev_regime != regime:
            self.regime_start_time[symbol] = datetime.now()
            
        self.current_regime[symbol] = regime
        self.last_update = datetime.now()
        
        return regime
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = data['high']
        low = data['low']
        close = data['close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _detect_regime(self, data: pd.DataFrame) -> MarketRegime:
        """Detect market regime based on indicators."""
        # Get recent data
        recent = data.tail(20)
        
        # Check for trending market
        sma20_slope = recent['sma20'].diff().mean()
        sma50_slope = recent['sma50'].diff().mean()
        
        # Check for volatility
        recent_atr = recent['atr'].iloc[-1]
        avg_atr = data['atr'].mean()
        volatility_ratio = recent_atr / avg_atr if avg_atr > 0 else 1.0
        
        # Check for mean reversion
        recent_zscore = recent['zscore'].iloc[-1]
        
        # Detect regime
        if volatility_ratio > 1.5:  # High volatility
            if sma20_slope > 0 and sma50_slope > 0:
                return MarketRegime.VOLATILE_BULLISH
            elif sma20_slope < 0 and sma50_slope < 0:
                return MarketRegime.VOLATILE_BEARISH
            else:
                return MarketRegime.VOLATILE_NEUTRAL
        elif abs(recent_zscore) > 2.0:  # Extreme deviation
            return MarketRegime.MEAN_REVERTING
        elif sma20_slope > 0 and sma50_slope > 0:
            return MarketRegime.TRENDING_BULLISH
        elif sma20_slope < 0 and sma50_slope < 0:
            return MarketRegime.TRENDING_BEARISH
        else:
            return MarketRegime.RANGING
    
    def get_regime(self, symbol: str) -> Optional[MarketRegime]:
        """
        Get current market regime for a symbol.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            Current market regime or None if not available
        """
        return self.current_regime.get(symbol)
    
    def get_regime_duration(self, symbol: str) -> Optional[timedelta]:
        """
        Get duration of current regime for a symbol.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            Duration of current regime or None if not available
        """
        if symbol not in self.regime_start_time:
            return None
            
        return datetime.now() - self.regime_start_time[symbol]
    
    def calculate_hurst_exponent(self, symbol: str, min_periods: int = 100) -> Optional[float]:
        """
        Calculate Hurst exponent for a symbol.
        
        The Hurst exponent measures the long-term memory of a time series:
        - H < 0.5: Mean-reverting series
        - H = 0.5: Random walk
        - H > 0.5: Trending series
        
        Args:
            symbol: Symbol to calculate for
            min_periods: Minimum number of periods required
            
        Returns:
            Hurst exponent or None if not enough data
        """
        if symbol not in self.price_history:
            return None
            
        data = self.price_history[symbol]
        
        if len(data) < min_periods:
            return None
            
        # Get log returns
        log_returns = np.log(data['close'] / data['close'].shift(1)).dropna().values
        
        # Calculate Hurst exponent
        lags = range(2, 20)
        tau = [np.sqrt(np.std(np.subtract(log_returns[lag:], log_returns[:-lag]))) for lag in lags]
        
        # Linear fit on log-log plot
        m = np.polyfit(np.log(lags), np.log(tau), 1)
        
        # Hurst exponent is the slope
        hurst = m[0]
        
        return hurst


class MarketConditionMonitor:
    """
    Real-time market condition monitoring system that tracks volatility,
    liquidity, correlations, and market regimes.
    """
    
    def __init__(self, 
                 event_monitor: EventMonitor,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize market condition monitor.
        
        Args:
            event_monitor: Event monitoring system
            config: Optional configuration dictionary
        """
        self.event_monitor = event_monitor
        self.config = config or {}
        self._init_default_config()
        
        # Initialize components
        self.correlation_tracker = CorrelationTracker(
            lookback_periods=self.config["correlation_lookback_periods"]
        )
        self.regime_detector = RegimeDetector(
            lookback_periods=self.config["regime_lookback_periods"]
        )
        
        # Market data storage
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.market_conditions: Dict[str, MarketCondition] = {}
        self.volatility_history: Dict[str, List[float]] = {}
        self.liquidity_history: Dict[str, List[float]] = {}
        
        # Callbacks for condition changes
        self.condition_change_callbacks: List[Callable[[str, MarketCondition, MarketCondition], None]] = []
        
        # Enable market source in event monitor
        self.event_monitor.enable_source(EventSource.PRICE_ACTION)
        
        logger.info("MarketConditionMonitor initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "volatility_window": 14,  # ATR period
            "volatility_history_size": 100,  # Number of ATR values to keep
            "liquidity_window": 14,  # Spread/volume averaging period
            "liquidity_history_size": 100,  # Number of liquidity values to keep
            "correlation_lookback_periods": 100,
            "regime_lookback_periods": 100,
            "high_volatility_percentile": 80,  # Percentile threshold for high volatility
            "low_volatility_percentile": 20,  # Percentile threshold for low volatility
            "extreme_volatility_percentile": 95,  # Percentile threshold for extreme volatility
            "volatility_change_threshold": 0.3,  # Threshold for volatility change events
            "correlation_change_threshold": 0.3,  # Threshold for correlation change events
            "update_interval_seconds": 60,  # How often to update conditions
            "auto_update": True
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def add_market_data(self, symbol: str, data: pd.DataFrame):
        """
        Add market data for a symbol.
        
        Args:
            symbol: Symbol identifier
            data: DataFrame with OHLCV data
        """
        # Ensure we have the required columns
        required_columns = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Data must contain columns: {required_columns}")
            
        # Store data
        self.market_data[symbol] = data
        
        # Initialize history if needed
        if symbol not in self.volatility_history:
            self.volatility_history[symbol] = []
        if symbol not in self.liquidity_history:
            self.liquidity_history[symbol] = []
            
        # Update regime detector
        self.regime_detector.add_market_data(symbol, data)
        
        # Add latest price to correlation tracker
        self.correlation_tracker.add_price(symbol, data['close'].iloc[-1])
        
        # Update market condition
        self.update_market_condition(symbol)
    
    def update_market_data(self, symbol: str, new_data: pd.DataFrame):
        """
        Update market data for a symbol.
        
        Args:
            symbol: Symbol identifier
            new_data: New data to append
        """
        if symbol not in self.market_data:
            self.add_market_data(symbol, new_data)
            return
            
        # Append new data
        self.market_data[symbol] = pd.concat([self.market_data[symbol], new_data]).drop_duplicates()
        
        # Update regime detector
        self.regime_detector.add_market_data(symbol, self.market_data[symbol])
        
        # Add latest price to correlation tracker
        self.correlation_tracker.add_price(symbol, new_data['close'].iloc[-1])
        
        # Update market condition
        self.update_market_condition(symbol)
    
    def update_market_condition(self, symbol: str) -> Optional[MarketCondition]:
        """
        Update market condition for a symbol.
        
        Args:
            symbol: Symbol to update
            
        Returns:
            Updated market condition or None if not enough data
        """
        if symbol not in self.market_data:
            return None
            
        data = self.market_data[symbol]
        
        if len(data) < 30:  # Need at least 30 data points
            return None
            
        # Calculate ATR
        atr = self._calculate_atr(data, self.config["volatility_window"])
        
        # Update volatility history
        self.volatility_history[symbol].append(atr)
        if len(self.volatility_history[symbol]) > self.config["volatility_history_size"]:
            self.volatility_history[symbol] = self.volatility_history[symbol][-self.config["volatility_history_size"]:]
        
        # Calculate ATR percentile
        atr_percentile = self._calculate_percentile(atr, self.volatility_history[symbol])
        
        # Determine volatility state
        volatility_state = self._determine_volatility_state(symbol, atr, atr_percentile)
        
        # Calculate liquidity metrics if available
        volume = None
        volume_percentile = None
        bid_ask_spread = None
        spread_percentile = None
        liquidity_state = LiquidityState.NORMAL
        
        if 'volume' in data.columns:
            volume = data['volume'].iloc[-1]
            
            # Update liquidity history
            self.liquidity_history[symbol].append(volume)
            if len(self.liquidity_history[symbol]) > self.config["liquidity_history_size"]:
                self.liquidity_history[symbol] = self.liquidity_history[symbol][-self.config["liquidity_history_size"]:]
            
            # Calculate volume percentile
            volume_percentile = self._calculate_percentile(volume, self.liquidity_history[symbol])
            
            # Determine liquidity state based on volume
            liquidity_state = self._determine_liquidity_state(symbol, volume, volume_percentile)
        
        # Update regime
        regime = self.regime_detector.update_regime(symbol)
        if regime is None:
            regime = MarketRegime.UNKNOWN
        
        # Calculate Hurst exponent
        hurst_exponent = self.regime_detector.calculate_hurst_exponent(symbol)
        
        # Update correlation matrix
        self.correlation_tracker.update_correlations()
        
        # Get current correlations
        current_correlation_state = {}
        for other_symbol in self.market_data:
            if other_symbol != symbol:
                corr = self.correlation_tracker.get_correlation(symbol, other_symbol)
                if corr is not None:
                    current_correlation_state[other_symbol] = corr
        
        # Create market condition
        new_condition = MarketCondition(
            symbol=symbol,
            timestamp=datetime.now(),
            volatility_state=volatility_state,
            liquidity_state=liquidity_state,
            regime=regime,
            atr=atr,
            atr_percentile=atr_percentile,
            volume=volume,
            volume_percentile=volume_percentile,
            bid_ask_spread=bid_ask_spread,
            spread_percentile=spread_percentile,
            hurst_exponent=hurst_exponent,
            current_correlation_state=current_correlation_state,
            timeframe=self._infer_timeframe(data)
        )
        
        # Check for significant changes
        prev_condition = self.market_conditions.get(symbol)
        if prev_condition:
            self._check_for_condition_changes(symbol, prev_condition, new_condition)
        
        # Store new condition
        self.market_conditions[symbol] = new_condition
        
        return new_condition
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range."""
        high = data['high']
        low = data['low']
        close = data['close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr
    
    def _calculate_percentile(self, value: float, history: List[float]) -> float:
        """Calculate percentile of a value within historical values."""
        if not history:
            return 50.0
            
        return stats.percentileofscore(history, value)
    
    def _determine_volatility_state(self, symbol: str, atr: float, atr_percentile: float) -> VolatilityState:
        """Determine volatility state based on ATR and its percentile."""
        # Get previous condition if available
        prev_condition = self.market_conditions.get(symbol)
        prev_atr = prev_condition.atr if prev_condition else None
        
        # Check for volatility change
        if prev_atr and prev_atr > 0:
            volatility_change = (atr - prev_atr) / prev_atr
        else:
            volatility_change = 0
        
        # Determine state based on percentile and change
        if atr_percentile >= self.config["extreme_volatility_percentile"]:
            return VolatilityState.EXTREMELY_HIGH
        elif atr_percentile >= self.config["high_volatility_percentile"]:
            return VolatilityState.HIGH
        elif atr_percentile <= self.config["low_volatility_percentile"]:
            return VolatilityState.LOW
        elif volatility_change >= self.config["volatility_change_threshold"]:
            return VolatilityState.EXPANDING
        elif volatility_change <= -self.config["volatility_change_threshold"]:
            return VolatilityState.CONTRACTING
        else:
            return VolatilityState.NORMAL
    
    def _determine_liquidity_state(self, symbol: str, volume: float, volume_percentile: float) -> LiquidityState:
        """Determine liquidity state based on volume and its percentile."""
        # Get previous condition if available
        prev_condition = self.market_conditions.get(symbol)
        prev_volume = prev_condition.volume if prev_condition else None
        
        # Check for liquidity change
        if prev_volume and prev_volume > 0:
            volume_change = (volume - prev_volume) / prev_volume
        else:
            volume_change = 0
        
        # Determine state based on percentile and change
        if volume_percentile >= 95:
            return LiquidityState.VERY_DEEP
        elif volume_percentile >= 80:
            return LiquidityState.DEEP
        elif volume_percentile <= 5:
            return LiquidityState.VERY_THIN
        elif volume_percentile <= 20:
            return LiquidityState.THIN
        elif volume_change >= 0.3:
            return LiquidityState.IMPROVING
        elif volume_change <= -0.3:
            return LiquidityState.DRYING
        else:
            return LiquidityState.NORMAL
    
    def _infer_timeframe(self, data: pd.DataFrame) -> str:
        """Infer timeframe from data."""
        if not isinstance(data.index, pd.DatetimeIndex) or len(data) < 2:
            return "unknown"
            
        # Calculate median time difference
        time_diffs = data.index.to_series().diff().dropna()
        median_diff = time_diffs.median()
        
        # Convert to minutes
        minutes = median_diff.total_seconds() / 60
        
        # Determine timeframe
        if minutes < 5:
            return "1m"
        elif minutes < 10:
            return "5m"
        elif minutes < 20:
            return "15m"
        elif minutes < 45:
            return "30m"
        elif minutes < 120:
            return "1h"
        elif minutes < 360:
            return "4h"
        else:
            return "1d"
    
    def _check_for_condition_changes(self, symbol: str, prev: MarketCondition, curr: MarketCondition):
        """Check for significant market condition changes and generate events."""
        changes = []
        
        # Check for volatility state change
        if prev.volatility_state != curr.volatility_state:
            changes.append(f"Volatility changed from {prev.volatility_state.value} to {curr.volatility_state.value}")
            
            # Generate event for significant volatility changes
            if curr.volatility_state in (VolatilityState.EXTREMELY_HIGH, VolatilityState.BREAKOUT):
                self._generate_volatility_event(symbol, curr, "significant_increase")
            elif prev.volatility_state in (VolatilityState.HIGH, VolatilityState.EXTREMELY_HIGH) and curr.volatility_state in (VolatilityState.NORMAL, VolatilityState.LOW):
                self._generate_volatility_event(symbol, curr, "significant_decrease")
        
        # Check for liquidity state change
        if prev.liquidity_state != curr.liquidity_state:
            changes.append(f"Liquidity changed from {prev.liquidity_state.value} to {curr.liquidity_state.value}")
            
            # Generate event for significant liquidity changes
            if curr.liquidity_state in (LiquidityState.VERY_THIN, LiquidityState.DRYING):
                self._generate_liquidity_event(symbol, curr, "significant_decrease")
            elif curr.liquidity_state == LiquidityState.IMBALANCED:
                self._generate_liquidity_event(symbol, curr, "imbalance")
        
        # Check for regime change
        if prev.regime != curr.regime:
            changes.append(f"Regime changed from {prev.regime.value} to {curr.regime.value}")
            
            # Generate event for regime changes
            self._generate_regime_event(symbol, curr, prev.regime)
        
        # Check for correlation breakdowns
        if prev.current_correlation_state and curr.current_correlation_state:
            for other_symbol, prev_corr in prev.current_correlation_state.items():
                if other_symbol in curr.current_correlation_state:
                    curr_corr = curr.current_correlation_state[other_symbol]
                    corr_change = curr_corr - prev_corr
                    
                    if abs(corr_change) >= self.config["correlation_change_threshold"]:
                        changes.append(f"Correlation with {other_symbol} changed from {prev_corr:.2f} to {curr_corr:.2f}")
                        
                        # Generate event for correlation breakdown
                        self._generate_correlation_event(symbol, other_symbol, prev_corr, curr_corr)
        
        # Call callbacks if there are changes
        if changes and self.condition_change_callbacks:
            for callback in self.condition_change_callbacks:
                try:
                    callback(symbol, prev, curr)
                except Exception as e:
                    logger.error(f"Error in condition change callback: {e}")
    
    async def _generate_volatility_event(self, symbol: str, condition: MarketCondition, change_type: str):
        """Generate volatility event."""
        event_id = f"vol_{symbol}_{int(datetime.now().timestamp())}"
        
        if change_type == "significant_increase":
            description = f"Significant volatility increase in {symbol} - ATR: {condition.atr:.5f} ({condition.atr_percentile:.1f}%)"
            priority = EventPriority.HIGH
        else:
            description = f"Significant volatility decrease in {symbol} - ATR: {condition.atr:.5f} ({condition.atr_percentile:.1f}%)"
            priority = EventPriority.MEDIUM
        
        event = MarketEvent(
            id=event_id,
            type=EventType.VOLATILITY,
            priority=priority,
            source=EventSource.PRICE_ACTION,
            timestamp=datetime.now(),
            description=description,
            symbol=symbol,
            price=0.0,  # Will be filled by caller
            volume=condition.volume,
            timeframe=condition.timeframe,
            volatility_impact=condition.atr_percentile / 100.0,
            tags={"volatility_event", change_type, condition.volatility_state.value}
        )
        
        await self.event_monitor.add_event(event)
    
    async def _generate_liquidity_event(self, symbol: str, condition: MarketCondition, change_type: str):
        """Generate liquidity event."""
        event_id = f"liq_{symbol}_{int(datetime.now().timestamp())}"
        
        if change_type == "significant_decrease":
            description = f"Significant liquidity decrease in {symbol} - State: {condition.liquidity_state.value}"
            priority = EventPriority.HIGH
        else:
            description = f"Liquidity imbalance in {symbol} - State: {condition.liquidity_state.value}"
            priority = EventPriority.MEDIUM
        
        event = MarketEvent(
            id=event_id,
            type=EventType.LIQUIDITY,
            priority=priority,
            source=EventSource.PRICE_ACTION,
            timestamp=datetime.now(),
            description=description,
            symbol=symbol,
            price=0.0,  # Will be filled by caller
            volume=condition.volume,
            timeframe=condition.timeframe,
            liquidity_impact=1.0 - (condition.volume_percentile / 100.0) if condition.volume_percentile is not None else 0.5,
            tags={"liquidity_event", change_type, condition.liquidity_state.value}
        )
        
        await self.event_monitor.add_event(event)
    
    async def _generate_regime_event(self, symbol: str, condition: MarketCondition, prev_regime: MarketRegime):
        """Generate regime change event."""
        event_id = f"regime_{symbol}_{int(datetime.now().timestamp())}"
        
        description = f"Market regime change in {symbol} - {prev_regime.value} to {condition.regime.value}"
        
        # Higher priority for more significant regime changes
        if (prev_regime in (MarketRegime.TRENDING_BULLISH, MarketRegime.TRENDING_BEARISH) and 
            condition.regime in (MarketRegime.VOLATILE_BULLISH, MarketRegime.VOLATILE_BEARISH, MarketRegime.VOLATILE_NEUTRAL)):
            priority = EventPriority.HIGH
        elif condition.regime in (MarketRegime.BREAKOUT, MarketRegime.BREAKDOWN):
            priority = EventPriority.HIGH
        else:
            priority = EventPriority.MEDIUM
        
        event = MarketEvent(
            id=event_id,
            type=EventType.MARKET,
            priority=priority,
            source=EventSource.PRICE_ACTION,
            timestamp=datetime.now(),
            description=description,
            symbol=symbol,
            price=0.0,  # Will be filled by caller
            timeframe=condition.timeframe,
            tags={"regime_change", prev_regime.value, condition.regime.value}
        )
        
        await self.event_monitor.add_event(event)
    
    async def _generate_correlation_event(self, symbol1: str, symbol2: str, prev_corr: float, curr_corr: float):
        """Generate correlation change event."""
        event_id = f"corr_{symbol1}_{symbol2}_{int(datetime.now().timestamp())}"
        
        corr_change = curr_corr - prev_corr
        
        if abs(corr_change) >= 0.5:  # Major correlation change
            description = f"Major correlation change between {symbol1} and {symbol2}: {prev_corr:.2f} to {curr_corr:.2f}"
            priority = EventPriority.HIGH
        else:
            description = f"Correlation change between {symbol1} and {symbol2}: {prev_corr:.2f} to {curr_corr:.2f}"
            priority = EventPriority.MEDIUM
        
        event = MarketEvent(
            id=event_id,
            type=EventType.CORRELATION,
            priority=priority,
            source=EventSource.PRICE_ACTION,
            timestamp=datetime.now(),
            description=description,
            symbol=symbol1,
            price=0.0,  # Will be filled by caller
            tags={"correlation_change", symbol2}
        )
        
        await self.event_monitor.add_event(event)
    
    def register_condition_change_callback(self, callback: Callable[[str, MarketCondition, MarketCondition], None]):
        """
        Register a callback for market condition changes.
        
        Args:
            callback: Function to call when market conditions change
        """
        self.condition_change_callbacks.append(callback)
    
    def get_market_condition(self, symbol: str) -> Optional[MarketCondition]:
        """
        Get current market condition for a symbol.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            Current market condition or None if not available
        """
        return self.market_conditions.get(symbol)
    
    def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """
        Get correlation between two symbols.
        
        Args:
            symbol1: First symbol
            symbol2: Second symbol
            
        Returns:
            Correlation coefficient or None if not available
        """
        return self.correlation_tracker.get_correlation(symbol1, symbol2)
    
    def get_regime(self, symbol: str) -> Optional[MarketRegime]:
        """
        Get current market regime for a symbol.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            Current market regime or None if not available
        """
        return self.regime_detector.get_regime(symbol)
    
    async def start_auto_update(self, interval_seconds: Optional[int] = None):
        """
        Start automatic updates of market conditions.
        
        Args:
            interval_seconds: Optional update interval in seconds
        """
        if not self.config["auto_update"]:
            logger.info("Auto-update is disabled in configuration")
            return
            
        interval = interval_seconds or self.config["update_interval_seconds"]
        
        async def update_loop():
            logger.info(f"Starting market condition auto-update every {interval} seconds")
            while True:
                try:
                    # Update all symbols
                    for symbol in list(self.market_data.keys()):
                        self.update_market_condition(symbol)
                    
                    # Update correlations
                    self.correlation_tracker.update_correlations()
                    
                except Exception as e:
                    logger.error(f"Error in market condition update: {e}")
                
                await asyncio.sleep(interval)
        
        # Start update loop
        asyncio.create_task(update_loop())
