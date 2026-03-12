"""
Elite Trading Bot - Advanced Order Flow Analyzer

This module provides institutional-grade order flow analysis including
footprint analysis, delta profiling, and market microstructure insights.
"""

import enum
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import uuid

import numpy as np
import pandas as pd
try:
    from scipy import stats
except ImportError:
    scipy = None
from collections import deque
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class OrderFlowSignal(enum.Enum):
    """Order flow signal types."""
    BULLISH_ABSORPTION = "bullish_absorption"     # Buying absorbing selling
    BEARISH_ABSORPTION = "bearish_absorption"     # Selling absorbing buying
    DELTA_DIVERGENCE = "delta_divergence"         # Price/delta divergence
    VOLUME_CLIMAX = "volume_climax"               # Exhaustion volume
    ICEBERG_DETECTED = "iceberg_detected"         # Large hidden orders
    MOMENTUM_SHIFT = "momentum_shift"             # Order flow momentum change


class FlowStrength(enum.Enum):
    """Order flow strength levels."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    EXTREME = "extreme"


@dataclass
class OrderFlowBar:
    """Detailed order flow data for a single bar."""
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    delta: float = 0.0                    # Buy volume - Sell volume
    cumulative_delta: float = 0.0         # Running delta sum
    volume_profile: Dict[float, float] = field(default_factory=dict)  # Price -> Volume
    bid_ask_spread: float = 0.0
    market_impact: float = 0.0            # Price impact per unit volume


@dataclass
class OrderFlowSignalData:
    """Order flow signal with metadata."""
    id: str
    signal_type: OrderFlowSignal
    strength: FlowStrength
    timestamp: datetime
    price_level: float
    volume: float
    delta: float
    confidence: float = 0.0               # 0-1 confidence score
    duration: int = 1                     # Bars duration
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderFlowProfile:
    """Complete order flow profile."""
    symbol: str
    timestamp: datetime
    timeframe: str
    bars: List[OrderFlowBar] = field(default_factory=list)
    signals: List[OrderFlowSignalData] = field(default_factory=list)
    
    # Aggregate metrics
    total_delta: float = 0.0
    delta_momentum: float = 0.0           # Rate of delta change
    volume_weighted_delta: float = 0.0
    absorption_ratio: float = 0.0         # Absorption strength
    flow_imbalance: float = 0.0          # Buy/sell imbalance
    
    # Advanced metrics
    iceberg_probability: float = 0.0      # Probability of hidden orders
    momentum_score: float = 0.0           # Overall momentum strength
    microstructure_score: float = 0.0     # Market quality score


class AdvancedOrderFlowAnalyzer:
    """
    Advanced order flow analysis system for institutional trading.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize advanced order flow analyzer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Order flow tracking
        self.flow_profiles: Dict[str, OrderFlowProfile] = {}
        self.flow_history: Dict[str, deque] = {}
        self.delta_series: Dict[str, deque] = {}
        
        logger.info("AdvancedOrderFlowAnalyzer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "lookback_periods": 100,          # Periods for analysis
            "delta_smoothing": 14,            # EMA period for delta smoothing
            "volume_threshold": 1.5,          # Volume spike threshold (multiple of average)
            "absorption_threshold": 0.7,      # Absorption ratio threshold
            "divergence_periods": 20,         # Periods for divergence analysis
            "iceberg_detection_window": 10,   # Window for iceberg detection
            "momentum_periods": 14,           # Momentum calculation periods
            "confidence_threshold": 0.6,      # Minimum signal confidence
            "max_history_size": 1000,         # Maximum history to keep
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def analyze_order_flow(self, 
                          ohlcv_data: pd.DataFrame,
                          tick_data: Optional[pd.DataFrame] = None,
                          symbol: str = "UNKNOWN",
                          timeframe: str = "1H") -> OrderFlowProfile:
        """
        Analyze order flow from market data.
        
        Args:
            ohlcv_data: OHLC volume data
            tick_data: Optional tick-by-tick data for enhanced analysis
            symbol: Trading symbol
            timeframe: Timeframe string
            
        Returns:
            OrderFlowProfile with analysis results
        """
        if len(ohlcv_data) < self.config["lookback_periods"]:
            return OrderFlowProfile(symbol, datetime.now(), timeframe)
        
        # Create order flow bars
        flow_bars = self._create_flow_bars(ohlcv_data, tick_data)
        
        # Calculate delta and cumulative delta
        flow_bars = self._calculate_delta_metrics(flow_bars)
        
        # Detect order flow signals
        signals = self._detect_order_flow_signals(flow_bars)
        
        # Calculate aggregate metrics
        profile = self._create_flow_profile(symbol, timeframe, flow_bars, signals)
        
        # Store in history
        self._update_history(symbol, profile)
        
        return profile
    
    def _create_flow_bars(self, 
                         ohlcv_data: pd.DataFrame,
                         tick_data: Optional[pd.DataFrame] = None) -> List[OrderFlowBar]:
        """Create order flow bars from market data."""
        flow_bars = []
        
        for idx, row in ohlcv_data.iterrows():
            # Basic bar data
            bar = OrderFlowBar(
                timestamp=idx,
                open_price=row['open'],
                high_price=row['high'],
                low_price=row['low'],
                close_price=row['close'],
                volume=row['volume']
            )
            
            # Estimate buy/sell volume if tick data not available
            if tick_data is None:
                bar.buy_volume, bar.sell_volume = self._estimate_buy_sell_volume(row)
            else:
                # Use tick data for precise calculation
                bar_tick_data = self._get_bar_tick_data(tick_data, idx)
                bar.buy_volume, bar.sell_volume = self._calculate_precise_volume(bar_tick_data)
                bar.volume_profile = self._create_volume_profile(bar_tick_data)
                bar.bid_ask_spread = self._calculate_avg_spread(bar_tick_data)
                bar.market_impact = self._calculate_market_impact(bar_tick_data, row)
            
            # Calculate delta
            bar.delta = bar.buy_volume - bar.sell_volume
            
            flow_bars.append(bar)
        
        return flow_bars
    
    def _estimate_buy_sell_volume(self, bar_data: pd.Series) -> Tuple[float, float]:
        """Estimate buy/sell volume from OHLC data."""
        total_volume = bar_data['volume']
        
        # Use price action to estimate buy/sell pressure
        price_change = bar_data['close'] - bar_data['open']
        price_range = bar_data['high'] - bar_data['low']
        
        if price_range == 0:
            return total_volume / 2, total_volume / 2
        
        # Estimate based on where close is in the range
        close_position = (bar_data['close'] - bar_data['low']) / price_range
        
        # Adjust for price change direction
        if price_change > 0:
            buy_ratio = 0.5 + (close_position * 0.3) + (price_change / price_range * 0.2)
        else:
            buy_ratio = 0.5 - ((1 - close_position) * 0.3) + (price_change / price_range * 0.2)
        
        buy_ratio = max(0.1, min(0.9, buy_ratio))  # Clamp between 10% and 90%
        
        buy_volume = total_volume * buy_ratio
        sell_volume = total_volume * (1 - buy_ratio)
        
        return buy_volume, sell_volume
    
    def _get_bar_tick_data(self, tick_data: pd.DataFrame, bar_timestamp: pd.Timestamp) -> pd.DataFrame:
        """Extract tick data for a specific bar period."""
        # This would need to be implemented based on the specific tick data format
        # For now, return empty DataFrame
        return pd.DataFrame()
    
    def _calculate_precise_volume(self, tick_data: pd.DataFrame) -> Tuple[float, float]:
        """Calculate precise buy/sell volume from tick data."""
        if tick_data.empty:
            return 0.0, 0.0
        
        # Classify trades as buy/sell based on trade price vs bid/ask
        buy_volume = tick_data[tick_data['side'] == 'buy']['volume'].sum()
        sell_volume = tick_data[tick_data['side'] == 'sell']['volume'].sum()
        
        return buy_volume, sell_volume
    
    def _create_volume_profile(self, tick_data: pd.DataFrame) -> Dict[float, float]:
        """Create volume profile from tick data."""
        if tick_data.empty:
            return {}
        
        # Group by price and sum volume
        volume_profile = tick_data.groupby('price')['volume'].sum().to_dict()
        return volume_profile
    
    def _calculate_avg_spread(self, tick_data: pd.DataFrame) -> float:
        """Calculate average bid-ask spread."""
        if tick_data.empty or 'bid' not in tick_data.columns or 'ask' not in tick_data.columns:
            return 0.0
        
        spreads = tick_data['ask'] - tick_data['bid']
        return spreads.mean()
    
    def _calculate_market_impact(self, tick_data: pd.DataFrame, bar_data: pd.Series) -> float:
        """Calculate market impact per unit volume."""
        if tick_data.empty:
            return 0.0
        
        price_change = abs(bar_data['close'] - bar_data['open'])
        total_volume = bar_data['volume']
        
        if total_volume == 0:
            return 0.0
        
        return price_change / total_volume
    
    def _calculate_delta_metrics(self, flow_bars: List[OrderFlowBar]) -> List[OrderFlowBar]:
        """Calculate delta and cumulative delta metrics."""
        cumulative_delta = 0.0
        
        for bar in flow_bars:
            cumulative_delta += bar.delta
            bar.cumulative_delta = cumulative_delta
        
        return flow_bars
    
    def _detect_order_flow_signals(self, flow_bars: List[OrderFlowBar]) -> List[OrderFlowSignalData]:
        """Detect order flow signals from flow bars."""
        signals = []
        
        if len(flow_bars) < self.config["divergence_periods"]:
            return signals
        
        # Convert to arrays for analysis
        deltas = np.array([bar.delta for bar in flow_bars])
        volumes = np.array([bar.volume for bar in flow_bars])
        prices = np.array([bar.close_price for bar in flow_bars])
        cum_deltas = np.array([bar.cumulative_delta for bar in flow_bars])
        
        # Detect absorption patterns
        absorption_signals = self._detect_absorption_patterns(flow_bars, deltas, volumes, prices)
        signals.extend(absorption_signals)
        
        # Detect delta divergences
        divergence_signals = self._detect_delta_divergences(flow_bars, deltas, prices, cum_deltas)
        signals.extend(divergence_signals)
        
        # Detect volume climax
        climax_signals = self._detect_volume_climax(flow_bars, volumes, deltas)
        signals.extend(climax_signals)
        
        # Detect iceberg orders
        iceberg_signals = self._detect_iceberg_orders(flow_bars, volumes, deltas)
        signals.extend(iceberg_signals)
        
        # Detect momentum shifts
        momentum_signals = self._detect_momentum_shifts(flow_bars, deltas, cum_deltas)
        signals.extend(momentum_signals)
        
        return signals
    
    def _detect_absorption_patterns(self, 
                                  flow_bars: List[OrderFlowBar],
                                  deltas: np.ndarray,
                                  volumes: np.ndarray,
                                  prices: np.ndarray) -> List[OrderFlowSignalData]:
        """Detect order flow absorption patterns."""
        signals = []
        window = 5  # Look at 5-bar windows
        
        for i in range(window, len(flow_bars)):
            window_bars = flow_bars[i-window:i]
            window_deltas = deltas[i-window:i]
            window_volumes = volumes[i-window:i]
            window_prices = prices[i-window:i]
            
            # Check for bullish absorption
            if (window_prices[-1] > window_prices[0] and  # Price up
                np.sum(window_deltas) > 0 and            # Net buying
                np.sum(window_deltas[window_deltas < 0]) < -np.mean(volumes) * 0.5):  # Significant selling absorbed
                
                confidence = min(1.0, abs(np.sum(window_deltas)) / np.sum(window_volumes))
                strength = self._determine_signal_strength(confidence, np.sum(window_volumes))
                
                signal = OrderFlowSignalData(
                    id=f"abs_bull_{uuid.uuid4().hex[:8]}",
                    signal_type=OrderFlowSignal.BULLISH_ABSORPTION,
                    strength=strength,
                    timestamp=flow_bars[i-1].timestamp,
                    price_level=flow_bars[i-1].close_price,
                    volume=np.sum(window_volumes),
                    delta=np.sum(window_deltas),
                    confidence=confidence,
                    duration=window,
                    metadata={
                        "price_change": window_prices[-1] - window_prices[0],
                        "absorption_ratio": abs(np.sum(window_deltas[window_deltas < 0])) / np.sum(window_volumes)
                    }
                )
                signals.append(signal)
            
            # Check for bearish absorption
            elif (window_prices[-1] < window_prices[0] and  # Price down
                  np.sum(window_deltas) < 0 and            # Net selling
                  np.sum(window_deltas[window_deltas > 0]) > np.mean(volumes) * 0.5):  # Significant buying absorbed
                
                confidence = min(1.0, abs(np.sum(window_deltas)) / np.sum(window_volumes))
                strength = self._determine_signal_strength(confidence, np.sum(window_volumes))
                
                signal = OrderFlowSignalData(
                    id=f"abs_bear_{uuid.uuid4().hex[:8]}",
                    signal_type=OrderFlowSignal.BEARISH_ABSORPTION,
                    strength=strength,
                    timestamp=flow_bars[i-1].timestamp,
                    price_level=flow_bars[i-1].close_price,
                    volume=np.sum(window_volumes),
                    delta=np.sum(window_deltas),
                    confidence=confidence,
                    duration=window,
                    metadata={
                        "price_change": window_prices[-1] - window_prices[0],
                        "absorption_ratio": np.sum(window_deltas[window_deltas > 0]) / np.sum(window_volumes)
                    }
                )
                signals.append(signal)
        
        return signals
    
    def _detect_delta_divergences(self, 
                                flow_bars: List[OrderFlowBar],
                                deltas: np.ndarray,
                                prices: np.ndarray,
                                cum_deltas: np.ndarray) -> List[OrderFlowSignalData]:
        """Detect price/delta divergences."""
        signals = []
        periods = self.config["divergence_periods"]
        
        if len(flow_bars) < periods * 2:
            return signals
        
        # Look for divergences in the last period
        recent_prices = prices[-periods:]
        recent_cum_deltas = cum_deltas[-periods:]
        
        # Calculate price and delta trends
        price_slope = np.polyfit(range(periods), recent_prices, 1)[0]
        delta_slope = np.polyfit(range(periods), recent_cum_deltas, 1)[0]
        
        # Check for divergence
        if price_slope > 0 and delta_slope < 0:  # Price up, delta down
            confidence = abs(price_slope * delta_slope) / (abs(price_slope) + abs(delta_slope))
            strength = self._determine_signal_strength(confidence, np.mean(deltas[-periods:]))
            
            signal = OrderFlowSignalData(
                id=f"div_bear_{uuid.uuid4().hex[:8]}",
                signal_type=OrderFlowSignal.DELTA_DIVERGENCE,
                strength=strength,
                timestamp=flow_bars[-1].timestamp,
                price_level=flow_bars[-1].close_price,
                volume=np.sum([bar.volume for bar in flow_bars[-periods:]]),
                delta=np.sum(deltas[-periods:]),
                confidence=confidence,
                duration=periods,
                metadata={
                    "price_slope": price_slope,
                    "delta_slope": delta_slope,
                    "divergence_type": "bearish"
                }
            )
            signals.append(signal)
        
        elif price_slope < 0 and delta_slope > 0:  # Price down, delta up
            confidence = abs(price_slope * delta_slope) / (abs(price_slope) + abs(delta_slope))
            strength = self._determine_signal_strength(confidence, np.mean(deltas[-periods:]))
            
            signal = OrderFlowSignalData(
                id=f"div_bull_{uuid.uuid4().hex[:8]}",
                signal_type=OrderFlowSignal.DELTA_DIVERGENCE,
                strength=strength,
                timestamp=flow_bars[-1].timestamp,
                price_level=flow_bars[-1].close_price,
                volume=np.sum([bar.volume for bar in flow_bars[-periods:]]),
                delta=np.sum(deltas[-periods:]),
                confidence=confidence,
                duration=periods,
                metadata={
                    "price_slope": price_slope,
                    "delta_slope": delta_slope,
                    "divergence_type": "bullish"
                }
            )
            signals.append(signal)
        
        return signals
    
    def _detect_volume_climax(self, 
                            flow_bars: List[OrderFlowBar],
                            volumes: np.ndarray,
                            deltas: np.ndarray) -> List[OrderFlowSignalData]:
        """Detect volume climax patterns."""
        signals = []
        
        # Find volume spikes
        avg_volume = np.mean(volumes)
        volume_threshold = avg_volume * self.config["volume_threshold"]
        
        for i, bar in enumerate(flow_bars):
            if bar.volume >= volume_threshold:
                # Check if this is exhaustion volume
                delta_ratio = abs(bar.delta) / bar.volume if bar.volume > 0 else 0
                
                # Low delta ratio with high volume suggests climax
                if delta_ratio < 0.3:
                    confidence = (1 - delta_ratio) * (bar.volume / volume_threshold) / 2
                    strength = self._determine_signal_strength(confidence, bar.volume)
                    
                    signal = OrderFlowSignalData(
                        id=f"climax_{uuid.uuid4().hex[:8]}",
                        signal_type=OrderFlowSignal.VOLUME_CLIMAX,
                        strength=strength,
                        timestamp=bar.timestamp,
                        price_level=bar.close_price,
                        volume=bar.volume,
                        delta=bar.delta,
                        confidence=confidence,
                        metadata={
                            "delta_ratio": delta_ratio,
                            "volume_multiple": bar.volume / avg_volume
                        }
                    )
                    signals.append(signal)
        
        return signals
    
    def _detect_iceberg_orders(self, 
                             flow_bars: List[OrderFlowBar],
                             volumes: np.ndarray,
                             deltas: np.ndarray) -> List[OrderFlowSignalData]:
        """Detect potential iceberg orders."""
        signals = []
        window = self.config["iceberg_detection_window"]
        
        for i in range(window, len(flow_bars)):
            window_volumes = volumes[i-window:i]
            window_deltas = deltas[i-window:i]
            
            # Look for consistent volume with minimal price impact
            volume_consistency = 1 - np.std(window_volumes) / np.mean(window_volumes)
            delta_consistency = np.std(window_deltas) / np.mean(np.abs(window_deltas)) if np.mean(np.abs(window_deltas)) > 0 else 0
            
            # High volume consistency with low delta variation suggests iceberg
            if volume_consistency > 0.7 and delta_consistency < 0.5:
                confidence = volume_consistency * (1 - delta_consistency)
                strength = self._determine_signal_strength(confidence, np.mean(window_volumes))
                
                signal = OrderFlowSignalData(
                    id=f"iceberg_{uuid.uuid4().hex[:8]}",
                    signal_type=OrderFlowSignal.ICEBERG_DETECTED,
                    strength=strength,
                    timestamp=flow_bars[i-1].timestamp,
                    price_level=flow_bars[i-1].close_price,
                    volume=np.sum(window_volumes),
                    delta=np.sum(window_deltas),
                    confidence=confidence,
                    duration=window,
                    metadata={
                        "volume_consistency": volume_consistency,
                        "delta_consistency": delta_consistency
                    }
                )
                signals.append(signal)
        
        return signals
    
    def _detect_momentum_shifts(self, 
                              flow_bars: List[OrderFlowBar],
                              deltas: np.ndarray,
                              cum_deltas: np.ndarray) -> List[OrderFlowSignalData]:
        """Detect order flow momentum shifts."""
        signals = []
        periods = self.config["momentum_periods"]
        
        if len(flow_bars) < periods * 2:
            return signals
        
        # Calculate momentum change
        recent_momentum = np.mean(deltas[-periods:])
        previous_momentum = np.mean(deltas[-periods*2:-periods])
        
        momentum_change = recent_momentum - previous_momentum
        momentum_ratio = abs(momentum_change) / (abs(previous_momentum) + 1e-6)
        
        # Significant momentum shift
        if momentum_ratio > 1.0:
            confidence = min(1.0, momentum_ratio / 3.0)  # Scale to 0-1
            strength = self._determine_signal_strength(confidence, abs(momentum_change))
            
            signal = OrderFlowSignalData(
                id=f"momentum_{uuid.uuid4().hex[:8]}",
                signal_type=OrderFlowSignal.MOMENTUM_SHIFT,
                strength=strength,
                timestamp=flow_bars[-1].timestamp,
                price_level=flow_bars[-1].close_price,
                volume=np.sum([bar.volume for bar in flow_bars[-periods:]]),
                delta=np.sum(deltas[-periods:]),
                confidence=confidence,
                duration=periods,
                metadata={
                    "momentum_change": momentum_change,
                    "momentum_ratio": momentum_ratio,
                    "direction": "bullish" if momentum_change > 0 else "bearish"
                }
            )
            signals.append(signal)
        
        return signals
    
    def _determine_signal_strength(self, confidence: float, volume_or_delta: float) -> FlowStrength:
        """Determine signal strength based on confidence and volume/delta."""
        if confidence > 0.8:
            return FlowStrength.EXTREME
        elif confidence > 0.7:
            return FlowStrength.STRONG
        elif confidence > 0.6:
            return FlowStrength.MODERATE
        else:
            return FlowStrength.WEAK
    
    def _create_flow_profile(self, 
                           symbol: str,
                           timeframe: str,
                           flow_bars: List[OrderFlowBar],
                           signals: List[OrderFlowSignalData]) -> OrderFlowProfile:
        """Create complete order flow profile."""
        # Calculate aggregate metrics
        total_delta = sum(bar.delta for bar in flow_bars)
        total_volume = sum(bar.volume for bar in flow_bars)
        
        # Delta momentum (rate of change)
        if len(flow_bars) >= 2:
            recent_delta = sum(bar.delta for bar in flow_bars[-10:])
            previous_delta = sum(bar.delta for bar in flow_bars[-20:-10]) if len(flow_bars) >= 20 else 0
            delta_momentum = recent_delta - previous_delta
        else:
            delta_momentum = 0.0
        
        # Volume weighted delta
        if total_volume > 0:
            volume_weighted_delta = sum(bar.delta * bar.volume for bar in flow_bars) / total_volume
        else:
            volume_weighted_delta = 0.0
        
        # Absorption ratio
        total_buy_volume = sum(bar.buy_volume for bar in flow_bars)
        total_sell_volume = sum(bar.sell_volume for bar in flow_bars)
        
        if total_sell_volume > 0:
            absorption_ratio = total_buy_volume / total_sell_volume
        else:
            absorption_ratio = float('inf')
        
        # Flow imbalance
        if total_volume > 0:
            flow_imbalance = abs(total_delta) / total_volume
        else:
            flow_imbalance = 0.0
        
        # Advanced metrics
        iceberg_probability = len([s for s in signals if s.signal_type == OrderFlowSignal.ICEBERG_DETECTED]) / max(1, len(flow_bars)) * 10
        momentum_score = abs(delta_momentum) / max(1, total_volume) * 1000
        
        # Microstructure score (based on signal quality and consistency)
        signal_confidences = [s.confidence for s in signals if s.confidence >= self.config["confidence_threshold"]]
        microstructure_score = np.mean(signal_confidences) if signal_confidences else 0.0
        
        return OrderFlowProfile(
            symbol=symbol,
            timestamp=datetime.now(),
            timeframe=timeframe,
            bars=flow_bars,
            signals=signals,
            total_delta=total_delta,
            delta_momentum=delta_momentum,
            volume_weighted_delta=volume_weighted_delta,
            absorption_ratio=absorption_ratio,
            flow_imbalance=flow_imbalance,
            iceberg_probability=min(1.0, iceberg_probability),
            momentum_score=momentum_score,
            microstructure_score=microstructure_score
        )
    
    def _update_history(self, symbol: str, profile: OrderFlowProfile):
        """Update order flow history."""
        if symbol not in self.flow_history:
            self.flow_history[symbol] = deque(maxlen=self.config["max_history_size"])
            self.delta_series[symbol] = deque(maxlen=self.config["max_history_size"])
        
        self.flow_history[symbol].append(profile)
        self.delta_series[symbol].extend([bar.delta for bar in profile.bars])
        
        # Update current profile
        self.flow_profiles[symbol] = profile
    
    def get_flow_summary(self, symbol: str) -> Dict[str, Any]:
        """Get order flow summary for a symbol."""
        if symbol not in self.flow_profiles:
            return {"error": "No order flow data available"}
        
        profile = self.flow_profiles[symbol]
        
        # Recent signals
        recent_signals = [
            {
                "type": s.signal_type.value,
                "strength": s.strength.value,
                "confidence": s.confidence,
                "timestamp": s.timestamp,
                "price": s.price_level
            }
            for s in profile.signals[-5:]  # Last 5 signals
        ]
        
        return {
            "symbol": symbol,
            "timestamp": profile.timestamp,
            "timeframe": profile.timeframe,
            "total_bars": len(profile.bars),
            "total_signals": len(profile.signals),
            "total_delta": profile.total_delta,
            "delta_momentum": profile.delta_momentum,
            "volume_weighted_delta": profile.volume_weighted_delta,
            "absorption_ratio": profile.absorption_ratio,
            "flow_imbalance": profile.flow_imbalance,
            "iceberg_probability": profile.iceberg_probability,
            "momentum_score": profile.momentum_score,
            "microstructure_score": profile.microstructure_score,
            "recent_signals": recent_signals,
            "signal_breakdown": {
                signal_type.value: len([s for s in profile.signals if s.signal_type == signal_type])
                for signal_type in OrderFlowSignal
            }
        }
