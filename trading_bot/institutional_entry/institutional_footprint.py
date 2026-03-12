"""
Elite Trading Bot - Institutional Footprint

This module provides institutional footprint analysis capabilities for the Elite Trading Bot,
detecting and analyzing institutional order flow patterns.
"""

import enum
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class FootprintPattern(enum.Enum):
    """Types of institutional footprint patterns."""
    ABSORPTION = "absorption"                 # Volume absorption
    DELTA_DIVERGENCE = "delta_divergence"     # Volume delta divergence
    IMBALANCE = "imbalance"                   # Order flow imbalance
    CLIMAX = "climax"                         # Volume climax
    EXHAUSTION = "exhaustion"                 # Buying/selling exhaustion
    STOPPING_VOLUME = "stopping_volume"       # Stopping volume
    EFFORT_VS_RESULT = "effort_vs_result"     # Effort vs result anomaly
    HIDDEN_LIQUIDITY = "hidden_liquidity"     # Hidden liquidity
    INSTITUTIONAL_SWEEP = "institutional_sweep"  # Institutional sweep
    CUSTOM = "custom"                         # Custom pattern


@dataclass
class FootprintSignal:
    """Signal generated from institutional footprint analysis."""
    pattern: FootprintPattern
    timestamp: datetime
    price_level: float
    is_bullish: bool
    strength: float  # 0.0 to 1.0
    volume: Optional[float] = None
    delta: Optional[float] = None  # Volume delta (buying vs selling)
    description: str = ""
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderFlowImbalance:
    """Order flow imbalance structure."""
    timestamp: datetime
    price_level: float
    is_bullish: bool
    imbalance_ratio: float  # Ratio of buying to selling volume
    volume: float
    delta: float
    description: str = ""


class AbsorptionDetector:
    """
    Detects volume absorption patterns in market data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize absorption detector.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            logger.info("AbsorptionDetector initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            defaults = {
                "volume_ma_period": 20,
                "high_volume_threshold": 1.5,  # Multiple of average volume
                "absorption_threshold": 0.7,  # Ratio of body to range for absorption
                "min_delta_ratio": 0.6,  # Minimum delta ratio for valid absorption
                "min_volume_for_valid_signal": 1.0  # Minimum volume multiple for valid signal
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def detect_absorption(self, df: pd.DataFrame) -> List[FootprintSignal]:
        """
        Detect absorption patterns in price data.
        
        Args:
            df: OHLCV DataFrame with optional bid/ask volume
            
        Returns:
            List of detected absorption signals
        """
        try:
            signals = []
        
            # Need at least volume data
            if 'volume' not in df.columns:
                return signals
            
            # Calculate volume metrics
            df = df.copy()
            df['vol_ma'] = df['volume'].rolling(window=self.config["volume_ma_period"]).mean()
            df['rel_volume'] = df['volume'] / df['vol_ma']
        
            # Calculate candle properties
            df['body'] = abs(df['close'] - df['open'])
            df['range'] = df['high'] - df['low']
            df['body_ratio'] = df['body'] / df['range']
            df['is_bullish'] = df['close'] > df['open']
            df['is_bearish'] = df['close'] < df['open']
        
            # Calculate delta if bid/ask volume available
            has_delta = 'bid_volume' in df.columns and 'ask_volume' in df.columns
            if has_delta:
                df['delta'] = df['ask_volume'] - df['bid_volume']
                df['delta_ratio'] = df['delta'].abs() / df['volume']
            else:
                # Estimate delta based on price action
                df['delta'] = df['body'] * df['volume'] * df['is_bullish'].map({True: 1, False: -1})
                df['delta_ratio'] = df['body_ratio']
        
            # Look for absorption patterns
            for i in range(1, len(df)):
                # Skip if volume is too low
                if df.iloc[i]['rel_volume'] < self.config["min_volume_for_valid_signal"]:
                    continue
                
                # Bullish absorption (high volume, small range, price holding)
                if (df.iloc[i]['rel_volume'] >= self.config["high_volume_threshold"] and
                    df.iloc[i]['body_ratio'] >= self.config["absorption_threshold"] and
                    df.iloc[i]['is_bullish'] and
                    df.iloc[i]['delta_ratio'] >= self.config["min_delta_ratio"]):
                
                    # Check if price is holding at support
                    is_support = False
                    for j in range(max(0, i-5), i):
                        if df.iloc[j]['low'] <= df.iloc[i]['low'] * 1.01:
                            is_support = True
                            break
                
                    if is_support:
                        signal = FootprintSignal(
                            pattern=FootprintPattern.ABSORPTION,
                            timestamp=df.index[i],
                            price_level=df.iloc[i]['close'],
                            is_bullish=True,
                            strength=min(1.0, df.iloc[i]['rel_volume'] / 2),
                            volume=df.iloc[i]['volume'],
                            delta=df.iloc[i]['delta'] if has_delta else None,
                            description="Bullish absorption at support"
                        )
                        signals.append(signal)
            
                # Bearish absorption (high volume, small range, price holding)
                elif (df.iloc[i]['rel_volume'] >= self.config["high_volume_threshold"] and
                     df.iloc[i]['body_ratio'] >= self.config["absorption_threshold"] and
                     df.iloc[i]['is_bearish'] and
                     df.iloc[i]['delta_ratio'] >= self.config["min_delta_ratio"]):
                
                    # Check if price is holding at resistance
                    is_resistance = False
                    for j in range(max(0, i-5), i):
                        if df.iloc[j]['high'] >= df.iloc[i]['high'] * 0.99:
                            is_resistance = True
                            break
                
                    if is_resistance:
                        signal = FootprintSignal(
                            pattern=FootprintPattern.ABSORPTION,
                            timestamp=df.index[i],
                            price_level=df.iloc[i]['close'],
                            is_bullish=False,
                            strength=min(1.0, df.iloc[i]['rel_volume'] / 2),
                            volume=df.iloc[i]['volume'],
                            delta=df.iloc[i]['delta'] if has_delta else None,
                            description="Bearish absorption at resistance"
                        )
                        signals.append(signal)
        
            return signals
        except Exception as e:
            logger.error(f"Error in detect_absorption: {e}")
            raise


class InstitutionalFootprint:
    """
    Analyzes institutional footprint in market data to detect
    institutional order flow patterns.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize institutional footprint analyzer.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            # Initialize components
            self.absorption_detector = AbsorptionDetector(self.config.get("absorption_detector_config"))
        
            logger.info("InstitutionalFootprint initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            defaults = {
                "volume_ma_period": 20,
                "delta_ma_period": 10,
                "imbalance_threshold": 0.7,  # Minimum imbalance ratio
                "climax_volume_threshold": 2.5,  # Multiple of average volume for climax
                "exhaustion_threshold": 3.0,  # Multiple of average volume for exhaustion
                "stopping_volume_threshold": 2.0,  # Multiple of average volume for stopping volume
                "effort_result_threshold": 0.5,  # Maximum price change ratio for effort vs result
                "min_volume_for_valid_signal": 1.0  # Minimum volume multiple for valid signal
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def analyze_footprint(self, 
                        df: pd.DataFrame, 
                        timeframe: str) -> Dict[str, Any]:
        """
        Analyze institutional footprint in market data.
        
        Args:
            df: OHLCV DataFrame with optional bid/ask volume
            timeframe: Timeframe of data
            
        Returns:
            Dictionary with analysis results
        """
        try:
            results = {
                "timeframe": timeframe,
                "timestamp": datetime.now(),
                "signals": [],
                "imbalances": [],
                "has_delta_data": 'bid_volume' in df.columns and 'ask_volume' in df.columns
            }
        
            # Need at least volume data
            if 'volume' not in df.columns:
                return results
            
            # Calculate volume metrics
            df = df.copy()
            df['vol_ma'] = df['volume'].rolling(window=self.config["volume_ma_period"]).mean()
            df['rel_volume'] = df['volume'] / df['vol_ma']
        
            # Calculate delta if bid/ask volume available
            has_delta = results["has_delta_data"]
            if has_delta:
                df['delta'] = df['ask_volume'] - df['bid_volume']
                df['delta_ma'] = df['delta'].rolling(window=self.config["delta_ma_period"]).mean()
                df['delta_ratio'] = df['delta'].abs() / df['volume']
            else:
                # Estimate delta based on price action
                df['body'] = abs(df['close'] - df['open'])
                df['range'] = df['high'] - df['low']
                df['body_ratio'] = df['body'] / df['range']
                df['is_bullish'] = df['close'] > df['open']
                df['delta'] = df['body'] * df['volume'] * df['is_bullish'].map({True: 1, False: -1})
                df['delta_ma'] = df['delta'].rolling(window=self.config["delta_ma_period"]).mean()
                df['delta_ratio'] = df['body_ratio']
        
            # Detect absorption patterns
            absorption_signals = self.absorption_detector.detect_absorption(df)
            results["signals"].extend(absorption_signals)
        
            # Detect delta divergence
            delta_signals = self._detect_delta_divergence(df, has_delta)
            results["signals"].extend(delta_signals)
        
            # Detect order flow imbalances
            imbalances = self._detect_imbalances(df, has_delta)
            results["imbalances"] = imbalances
        
            # Detect volume climax
            climax_signals = self._detect_volume_climax(df)
            results["signals"].extend(climax_signals)
        
            # Detect exhaustion
            exhaustion_signals = self._detect_exhaustion(df, has_delta)
            results["signals"].extend(exhaustion_signals)
        
            # Detect stopping volume
            stopping_signals = self._detect_stopping_volume(df)
            results["signals"].extend(stopping_signals)
        
            # Detect effort vs result anomalies
            effort_result_signals = self._detect_effort_vs_result(df)
            results["signals"].extend(effort_result_signals)
        
            # Sort signals by timestamp
            results["signals"].sort(key=lambda x: x.timestamp)
        
            return results
        except Exception as e:
            logger.error(f"Error in analyze_footprint: {e}")
            raise
    
    def _detect_delta_divergence(self, 
                               df: pd.DataFrame, 
                               has_delta: bool) -> List[FootprintSignal]:
        """
        Detect delta divergence patterns.
        
        Args:
            df: Prepared DataFrame
            has_delta: Whether real delta data is available
            
        Returns:
            List of detected signals
        """
        try:
            signals = []
        
            # Need at least 20 candles
            if len(df) < 20:
                return signals
            
            # Look for delta divergence
            for i in range(10, len(df)):
                # Skip if volume is too low
                if df.iloc[i]['rel_volume'] < self.config["min_volume_for_valid_signal"]:
                    continue
                
                # Bullish divergence (price making lower low, delta making higher low)
                if (df.iloc[i]['low'] < df.iloc[i-1:i-6]['low'].min() and
                    df.iloc[i]['delta'] > df.iloc[i-1:i-6]['delta'].min()):
                
                    signal = FootprintSignal(
                        pattern=FootprintPattern.DELTA_DIVERGENCE,
                        timestamp=df.index[i],
                        price_level=df.iloc[i]['close'],
                        is_bullish=True,
                        strength=0.7 if has_delta else 0.5,  # Lower strength if estimated delta
                        volume=df.iloc[i]['volume'],
                        delta=df.iloc[i]['delta'],
                        description="Bullish delta divergence"
                    )
                    signals.append(signal)
            
                # Bearish divergence (price making higher high, delta making lower high)
                elif (df.iloc[i]['high'] > df.iloc[i-1:i-6]['high'].max() and
                     df.iloc[i]['delta'] < df.iloc[i-1:i-6]['delta'].max()):
                
                    signal = FootprintSignal(
                        pattern=FootprintPattern.DELTA_DIVERGENCE,
                        timestamp=df.index[i],
                        price_level=df.iloc[i]['close'],
                        is_bullish=False,
                        strength=0.7 if has_delta else 0.5,  # Lower strength if estimated delta
                        volume=df.iloc[i]['volume'],
                        delta=df.iloc[i]['delta'],
                        description="Bearish delta divergence"
                    )
                    signals.append(signal)
        
            return signals
        except Exception as e:
            logger.error(f"Error in _detect_delta_divergence: {e}")
            raise
    
    def _detect_imbalances(self, 
                         df: pd.DataFrame, 
                         has_delta: bool) -> List[OrderFlowImbalance]:
        """
        Detect order flow imbalances.
        
        Args:
            df: Prepared DataFrame
            has_delta: Whether real delta data is available
            
        Returns:
            List of detected imbalances
        """
        try:
            imbalances = []
        
            # Need at least 5 candles
            if len(df) < 5:
                return imbalances
            
            # Look for imbalances
            for i in range(1, len(df)):
                # Skip if volume is too low
                if df.iloc[i]['rel_volume'] < self.config["min_volume_for_valid_signal"]:
                    continue
                
                # Calculate imbalance ratio
                if has_delta:
                    # Real delta data
                    imbalance_ratio = abs(df.iloc[i]['delta']) / df.iloc[i]['volume']
                    is_bullish = df.iloc[i]['delta'] > 0
                else:
                    # Estimated delta
                    imbalance_ratio = df.iloc[i]['body_ratio']
                    is_bullish = df.iloc[i]['is_bullish']
            
                # Check if imbalance is significant
                if imbalance_ratio >= self.config["imbalance_threshold"]:
                    imbalance = OrderFlowImbalance(
                        timestamp=df.index[i],
                        price_level=df.iloc[i]['close'],
                        is_bullish=is_bullish,
                        imbalance_ratio=imbalance_ratio,
                        volume=df.iloc[i]['volume'],
                        delta=df.iloc[i]['delta'],
                        description=f"{'Bullish' if is_bullish else 'Bearish'} order flow imbalance"
                    )
                    imbalances.append(imbalance)
        
            return imbalances
        except Exception as e:
            logger.error(f"Error in _detect_imbalances: {e}")
            raise
    
    def _detect_volume_climax(self, df: pd.DataFrame) -> List[FootprintSignal]:
        """
        Detect volume climax patterns.
        
        Args:
            df: Prepared DataFrame
            
        Returns:
            List of detected signals
        """
        try:
            signals = []
        
            # Need at least 20 candles
            if len(df) < 20:
                return signals
            
            # Look for volume climax
            for i in range(10, len(df)):
                # Check for extremely high volume
                if df.iloc[i]['rel_volume'] >= self.config["climax_volume_threshold"]:
                    # Determine if bullish or bearish
                    is_bullish = df.iloc[i]['close'] > df.iloc[i]['open']
                
                    # Check if this is a local extreme
                    is_extreme = False
                    if is_bullish:
                        # Check if price is at local high
                        is_extreme = df.iloc[i]['high'] >= df.iloc[i-5:i]['high'].max()
                    else:
                        # Check if price is at local low
                        is_extreme = df.iloc[i]['low'] <= df.iloc[i-5:i]['low'].min()
                
                    if is_extreme:
                        signal = FootprintSignal(
                            pattern=FootprintPattern.CLIMAX,
                            timestamp=df.index[i],
                            price_level=df.iloc[i]['close'],
                            is_bullish=is_bullish,
                            strength=min(1.0, df.iloc[i]['rel_volume'] / 3),
                            volume=df.iloc[i]['volume'],
                            delta=df.iloc[i]['delta'],
                            description=f"{'Bullish' if is_bullish else 'Bearish'} volume climax"
                        )
                        signals.append(signal)
        
            return signals
        except Exception as e:
            logger.error(f"Error in _detect_volume_climax: {e}")
            raise
    
    def _detect_exhaustion(self, 
                         df: pd.DataFrame, 
                         has_delta: bool) -> List[FootprintSignal]:
        """
        Detect exhaustion patterns.
        
        Args:
            df: Prepared DataFrame
            has_delta: Whether real delta data is available
            
        Returns:
            List of detected signals
        """
        try:
            signals = []
        
            # Need at least 20 candles
            if len(df) < 20:
                return signals
            
            # Look for exhaustion
            for i in range(10, len(df) - 1):
                # Check for extremely high volume
                if df.iloc[i]['rel_volume'] >= self.config["exhaustion_threshold"]:
                    # Determine if bullish or bearish exhaustion
                    is_bullish_candle = df.iloc[i]['close'] > df.iloc[i]['open']
                
                    # Check for reversal in next candle
                    reversal = (is_bullish_candle and df.iloc[i+1]['close'] < df.iloc[i+1]['open']) or \
                              (not is_bullish_candle and df.iloc[i+1]['close'] > df.iloc[i+1]['open'])
                
                    if reversal:
                        # Bullish exhaustion (selling exhaustion)
                        if not is_bullish_candle:
                            signal = FootprintSignal(
                                pattern=FootprintPattern.EXHAUSTION,
                                timestamp=df.index[i],
                                price_level=df.iloc[i]['close'],
                                is_bullish=True,  # Bullish signal (selling exhaustion)
                                strength=min(1.0, df.iloc[i]['rel_volume'] / 3),
                                volume=df.iloc[i]['volume'],
                                delta=df.iloc[i]['delta'],
                                description="Selling exhaustion"
                            )
                            signals.append(signal)
                        # Bearish exhaustion (buying exhaustion)
                        else:
                            signal = FootprintSignal(
                                pattern=FootprintPattern.EXHAUSTION,
                                timestamp=df.index[i],
                                price_level=df.iloc[i]['close'],
                                is_bullish=False,  # Bearish signal (buying exhaustion)
                                strength=min(1.0, df.iloc[i]['rel_volume'] / 3),
                                volume=df.iloc[i]['volume'],
                                delta=df.iloc[i]['delta'],
                                description="Buying exhaustion"
                            )
                            signals.append(signal)
        
            return signals
        except Exception as e:
            logger.error(f"Error in _detect_exhaustion: {e}")
            raise
    
    def _detect_stopping_volume(self, df: pd.DataFrame) -> List[FootprintSignal]:
        """
        Detect stopping volume patterns.
        
        Args:
            df: Prepared DataFrame
            
        Returns:
            List of detected signals
        """
        try:
            signals = []
        
            # Need at least 20 candles
            if len(df) < 20:
                return signals
            
            # Look for stopping volume
            for i in range(10, len(df) - 1):
                # Check for high volume
                if df.iloc[i]['rel_volume'] >= self.config["stopping_volume_threshold"]:
                    # Determine if bullish or bearish
                    is_bullish = df.iloc[i]['close'] > df.iloc[i]['open']
                
                    # Check for trend before this candle
                    prev_trend_bullish = df.iloc[i-5:i]['close'].mean() > df.iloc[i-10:i-5]['close'].mean()
                
                    # Check for stopping volume pattern
                    is_stopping_volume = False
                
                    if prev_trend_bullish and not is_bullish:
                        # Bearish candle stopping an uptrend
                        is_stopping_volume = True
                        is_bullish_signal = False  # Bearish signal
                    elif not prev_trend_bullish and is_bullish:
                        # Bullish candle stopping a downtrend
                        is_stopping_volume = True
                        is_bullish_signal = True  # Bullish signal
                
                    if is_stopping_volume:
                        signal = FootprintSignal(
                            pattern=FootprintPattern.STOPPING_VOLUME,
                            timestamp=df.index[i],
                            price_level=df.iloc[i]['close'],
                            is_bullish=is_bullish_signal,
                            strength=min(1.0, df.iloc[i]['rel_volume'] / 2.5),
                            volume=df.iloc[i]['volume'],
                            delta=df.iloc[i]['delta'],
                            description=f"{'Bullish' if is_bullish_signal else 'Bearish'} stopping volume"
                        )
                        signals.append(signal)
        
            return signals
        except Exception as e:
            logger.error(f"Error in _detect_stopping_volume: {e}")
            raise
    
    def _detect_effort_vs_result(self, df: pd.DataFrame) -> List[FootprintSignal]:
        """
        Detect effort vs result anomalies.
        
        Args:
            df: Prepared DataFrame
            
        Returns:
            List of detected signals
        """
        try:
            signals = []
        
            # Need at least 20 candles
            if len(df) < 20:
                return signals
            
            # Look for effort vs result anomalies
            for i in range(10, len(df)):
                # Skip if volume is too low
                if df.iloc[i]['rel_volume'] < self.config["min_volume_for_valid_signal"]:
                    continue
                
                # Check for high volume with small price movement
                price_change = abs(df.iloc[i]['close'] - df.iloc[i]['open'])
                avg_price = (df.iloc[i]['close'] + df.iloc[i]['open']) / 2
                price_change_ratio = price_change / avg_price
            
                if (df.iloc[i]['rel_volume'] >= self.config["stopping_volume_threshold"] and
                    price_change_ratio <= self.config["effort_result_threshold"]):
                
                    # Determine if bullish or bearish
                    is_bullish = df.iloc[i]['close'] > df.iloc[i]['open']
                
                    # Check for trend before this candle
                    prev_trend_bullish = df.iloc[i-5:i]['close'].mean() > df.iloc[i-10:i-5]['close'].mean()
                
                    # Effort vs result is bullish at support, bearish at resistance
                    if prev_trend_bullish:
                        # Potential resistance
                        signal = FootprintSignal(
                            pattern=FootprintPattern.EFFORT_VS_RESULT,
                            timestamp=df.index[i],
                            price_level=df.iloc[i]['close'],
                            is_bullish=False,  # Bearish signal at resistance
                            strength=min(1.0, df.iloc[i]['rel_volume'] / 2.5),
                            volume=df.iloc[i]['volume'],
                            delta=df.iloc[i]['delta'],
                            description="Effort vs result anomaly at resistance"
                        )
                        signals.append(signal)
                    else:
                        # Potential support
                        signal = FootprintSignal(
                            pattern=FootprintPattern.EFFORT_VS_RESULT,
                            timestamp=df.index[i],
                            price_level=df.iloc[i]['close'],
                            is_bullish=True,  # Bullish signal at support
                            strength=min(1.0, df.iloc[i]['rel_volume'] / 2.5),
                            volume=df.iloc[i]['volume'],
                            delta=df.iloc[i]['delta'],
                            description="Effort vs result anomaly at support"
                        )
                        signals.append(signal)
        
            return signals
        except Exception as e:
            logger.error(f"Error in _detect_effort_vs_result: {e}")
            raise
    
    def detect_institutional_sweep(self, 
                                 df: pd.DataFrame, 
                                 liquidity_levels: List[Tuple[float, float]]) -> List[FootprintSignal]:
        """
        Detect institutional sweep patterns.
        
        Args:
            df: OHLCV DataFrame
            liquidity_levels: List of (price, strength) tuples representing liquidity levels
            
        Returns:
            List of detected signals
        """
        try:
            signals = []
        
            # Need at least volume data and liquidity levels
            if 'volume' not in df.columns or not liquidity_levels:
                return signals
            
            # Calculate volume metrics
            df = df.copy()
            df['vol_ma'] = df['volume'].rolling(window=self.config["volume_ma_period"]).mean()
            df['rel_volume'] = df['volume'] / df['vol_ma']
        
            # Look for sweeps of liquidity levels
            for i in range(1, len(df)):
                # Skip if volume is too low
                if df.iloc[i]['rel_volume'] < self.config["min_volume_for_valid_signal"]:
                    continue
                
                # Check for high volume
                if df.iloc[i]['rel_volume'] >= self.config["high_volume_threshold"]:
                    # Check if price swept through liquidity levels
                    for level, strength in liquidity_levels:
                        # Bullish sweep (price sweeps below level then closes above)
                        if (df.iloc[i]['low'] < level and 
                            df.iloc[i]['close'] > level and 
                            df.iloc[i-1]['low'] > level):
                        
                            signal = FootprintSignal(
                                pattern=FootprintPattern.INSTITUTIONAL_SWEEP,
                                timestamp=df.index[i],
                                price_level=level,
                                is_bullish=True,
                                strength=min(1.0, strength * df.iloc[i]['rel_volume'] / 2),
                                volume=df.iloc[i]['volume'],
                                delta=df.iloc[i]['delta'] if 'delta' in df.columns else None,
                                description="Bullish institutional sweep"
                            )
                            signals.append(signal)
                    
                        # Bearish sweep (price sweeps above level then closes below)
                        elif (df.iloc[i]['high'] > level and 
                              df.iloc[i]['close'] < level and 
                              df.iloc[i-1]['high'] < level):
                        
                            signal = FootprintSignal(
                                pattern=FootprintPattern.INSTITUTIONAL_SWEEP,
                                timestamp=df.index[i],
                                price_level=level,
                                is_bullish=False,
                                strength=min(1.0, strength * df.iloc[i]['rel_volume'] / 2),
                                volume=df.iloc[i]['volume'],
                                delta=df.iloc[i]['delta'] if 'delta' in df.columns else None,
                                description="Bearish institutional sweep"
                            )
                            signals.append(signal)
        
            return signals
        except Exception as e:
            logger.error(f"Error in detect_institutional_sweep: {e}")
            raise
    
    def get_footprint_signals(self, 
                            symbol: str, 
                            data: Dict[str, pd.DataFrame],
                            liquidity_levels: Optional[Dict[str, List[Tuple[float, float]]]] = None) -> Dict[str, List[FootprintSignal]]:
        """
        Get institutional footprint signals for all timeframes.
        
        Args:
            symbol: Symbol to analyze
            data: Dictionary of timeframe -> OHLCV DataFrame
            liquidity_levels: Optional dictionary of timeframe -> liquidity levels
            
        Returns:
            Dictionary of timeframe -> signals
        """
        try:
            results = {}
        
            for timeframe, df in data.items():
                if df.empty:
                    continue
                
                # Analyze footprint
                analysis = self.analyze_footprint(df, timeframe)
                signals = analysis["signals"]
            
                # Detect institutional sweeps if liquidity levels provided
                if liquidity_levels and timeframe in liquidity_levels:
                    sweep_signals = self.detect_institutional_sweep(df, liquidity_levels[timeframe])
                    signals.extend(sweep_signals)
            
                # Sort by timestamp
                signals.sort(key=lambda x: x.timestamp)
            
                results[timeframe] = signals
        
            return results
        except Exception as e:
            logger.error(f"Error in get_footprint_signals: {e}")
            raise
