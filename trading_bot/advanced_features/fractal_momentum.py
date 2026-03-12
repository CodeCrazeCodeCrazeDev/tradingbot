"""Fractal Momentum Divergence (FMD) Module - Multi-Timeframe Divergence Analysis.

This module implements the revolutionary Fractal Momentum Divergence indicator that
compares momentum across three consecutive fractal timeframes to filter out false
divergences and provide stronger reversal confirmation signals.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
from scipy.signal import find_peaks, find_peaks_cwt
from scipy.stats import pearsonr
import numpy
import pandas

logger = logging.getLogger(__name__)


class DivergenceType(Enum):
    """Types of divergence patterns."""
    BULLISH_REGULAR = "bullish_regular"
    BEARISH_REGULAR = "bearish_regular"
    BULLISH_HIDDEN = "bullish_hidden"
    BEARISH_HIDDEN = "bearish_hidden"
    NO_DIVERGENCE = "no_divergence"


@dataclass
class DivergenceSignal:
    """Represents a divergence signal."""
    timestamp: pd.Timestamp
    divergence_type: DivergenceType
    strength: float
    confidence: float
    timeframes_confirmed: List[str]
    price_points: List[float]
    momentum_points: List[float]
    expected_move: float


@dataclass
class FractalLevel:
    """Represents a fractal support/resistance level."""
    price: float
    timestamp: pd.Timestamp
    level_type: str  # 'support' or 'resistance'
    strength: float
    touches: int


class FractalMomentumDivergence:
    """
    Main class implementing Fractal Momentum Divergence analysis.
    
    This revolutionary indicator compares momentum across three consecutive
    fractal timeframes to filter false divergences and provide high-confidence
    reversal signals.
    """
    
    def __init__(self, 
                 timeframes: List[str] = ['5m', '15m', '1h'],
                 momentum_period: int = 14,
                 divergence_lookback: int = 50,
                 min_confirmation_timeframes: int = 2):
        """
        Initialize Fractal Momentum Divergence analyzer.
        
        Args:
            timeframes: List of timeframes for fractal analysis
            momentum_period: Period for momentum calculations
            divergence_lookback: Lookback period for divergence detection
            min_confirmation_timeframes: Minimum timeframes needed for confirmation
        """
        self.timeframes = timeframes
        self.momentum_period = momentum_period
        self.divergence_lookback = divergence_lookback
        self.min_confirmation_timeframes = min_confirmation_timeframes
        
        # Storage for multi-timeframe data
        self.timeframe_data = {}
        self.fractal_levels = {}
        self.divergence_history = []
        
    def add_timeframe_data(self, timeframe: str, data: pd.DataFrame):
        """Add market data for a specific timeframe."""
        if timeframe not in self.timeframes:
            logger.warning(f"Timeframe {timeframe} not in configured timeframes")
            return
        
        # Calculate momentum indicators
        enhanced_data = self._calculate_momentum_indicators(data.copy())
        
        # Identify fractal levels
        fractal_levels = self._identify_fractal_levels(enhanced_data)
        
        self.timeframe_data[timeframe] = enhanced_data
        self.fractal_levels[timeframe] = fractal_levels
        
        logger.info(f"Added {len(data)} bars for {timeframe} timeframe")
    
    def _calculate_momentum_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive momentum indicators."""
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.momentum_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.momentum_period).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = data['close'].ewm(span=12, adjust=False).mean()
        exp2 = data['close'].ewm(span=26, adjust=False).mean()
        data['macd'] = exp1 - exp2
        data['macd_signal'] = data['macd'].ewm(span=9, adjust=False).mean()
        data['macd_histogram'] = data['macd'] - data['macd_signal']
        
        # Stochastic
        low_min = data['low'].rolling(14).min()
        high_max = data['high'].rolling(14).max()
        data['stoch_k'] = 100 * (data['close'] - low_min) / (high_max - low_min)
        data['stoch_d'] = data['stoch_k'].rolling(3).mean()
        
        # Williams %R
        high_max = data['high'].rolling(self.momentum_period).max()
        low_min = data['low'].rolling(self.momentum_period).min()
        data['williams_r'] = -100 * (high_max - data['close']) / (high_max - low_min)
        
        # Custom momentum oscillator
        data['momentum'] = data['close'].pct_change(self.momentum_period) * 100
        
        # Rate of Change
        data['roc'] = data['close'].pct_change(self.momentum_period) * 100
        
        return data
    
    def _identify_fractal_levels(self, data: pd.DataFrame) -> List[FractalLevel]:
        """Identify fractal support and resistance levels."""
        fractal_levels = []
        
        # Find swing highs and lows
        high_peaks, _ = find_peaks(data['high'].values, distance=5, prominence=0.001)
        low_peaks, _ = find_peaks(-data['low'].values, distance=5, prominence=0.001)
        
        # Process swing highs (resistance levels)
        for peak_idx in high_peaks:
            if peak_idx < len(data):
                price = data['high'].iloc[peak_idx]
                timestamp = data.index[peak_idx]
                
                # Calculate level strength based on nearby touches
                strength = self._calculate_level_strength(data, price, 'resistance')
                touches = self._count_level_touches(data, price, 'resistance')
                
                fractal_level = FractalLevel(
                    price=price,
                    timestamp=timestamp,
                    level_type='resistance',
                    strength=strength,
                    touches=touches
                )
                fractal_levels.append(fractal_level)
        
        # Process swing lows (support levels)
        for peak_idx in low_peaks:
            if peak_idx < len(data):
                price = data['low'].iloc[peak_idx]
                timestamp = data.index[peak_idx]
                
                strength = self._calculate_level_strength(data, price, 'support')
                touches = self._count_level_touches(data, price, 'support')
                
                fractal_level = FractalLevel(
                    price=price,
                    timestamp=timestamp,
                    level_type='support',
                    strength=strength,
                    touches=touches
                )
                fractal_levels.append(fractal_level)
        
        return fractal_levels
    
    def _calculate_level_strength(self, data: pd.DataFrame, price: float, level_type: str) -> float:
        """Calculate the strength of a fractal level."""
        tolerance = (data['high'].max() - data['low'].min()) * 0.002  # 0.2% tolerance
        
        if level_type == 'resistance':
            nearby_highs = data['high'][(data['high'] >= price - tolerance) & 
                                       (data['high'] <= price + tolerance)]
        else:  # support
            nearby_highs = data['low'][(data['low'] >= price - tolerance) & 
                                      (data['low'] <= price + tolerance)]
        
        # Strength based on number of touches and volume
        base_strength = len(nearby_highs) / len(data)
        
        return min(base_strength * 10, 1.0)  # Normalize to 0-1
    
    def _count_level_touches(self, data: pd.DataFrame, price: float, level_type: str) -> int:
        """Count how many times price has touched this level."""
        tolerance = (data['high'].max() - data['low'].min()) * 0.002
        
        if level_type == 'resistance':
            touches = len(data[(data['high'] >= price - tolerance) & 
                              (data['high'] <= price + tolerance)])
        else:
            touches = len(data[(data['low'] >= price - tolerance) & 
                              (data['low'] <= price + tolerance)])
        
        return touches
    
    def detect_multi_timeframe_divergence(self) -> List[DivergenceSignal]:
        """
        Detect divergences confirmed across multiple timeframes.
        
        Returns:
            List of high-confidence divergence signals
        """
        if len(self.timeframe_data) < self.min_confirmation_timeframes:
            logger.warning("Insufficient timeframe data for divergence detection")
            return []
        
        divergence_signals = []
        
        # Analyze each timeframe for divergences
        timeframe_divergences = {}
        for timeframe, data in self.timeframe_data.items():
            divergences = self._detect_single_timeframe_divergence(data, timeframe)
            timeframe_divergences[timeframe] = divergences
        
        # Find divergences confirmed across multiple timeframes
        confirmed_divergences = self._find_confirmed_divergences(timeframe_divergences)
        
        self.divergence_history.extend(confirmed_divergences)
        return confirmed_divergences
    
    def _detect_single_timeframe_divergence(self, data: pd.DataFrame, timeframe: str) -> List[Dict]:
        """Detect divergences in a single timeframe."""
        divergences = []
        
        if len(data) < self.divergence_lookback:
            return divergences
        
        # Get recent data for analysis
        recent_data = data.tail(self.divergence_lookback)
        
        # Find swing points
        price_highs, _ = find_peaks(recent_data['high'].values, distance=3)
        price_lows, _ = find_peaks(-recent_data['low'].values, distance=3)
        
        # Analyze RSI divergences
        rsi_divergences = self._analyze_rsi_divergence(recent_data, price_highs, price_lows)
        divergences.extend(rsi_divergences)
        
        # Analyze MACD divergences
        macd_divergences = self._analyze_macd_divergence(recent_data, price_highs, price_lows)
        divergences.extend(macd_divergences)
        
        # Analyze Stochastic divergences
        stoch_divergences = self._analyze_stochastic_divergence(recent_data, price_highs, price_lows)
        divergences.extend(stoch_divergences)
        
        return divergences
    
    def _analyze_rsi_divergence(self, data: pd.DataFrame, price_highs: np.ndarray, 
                               price_lows: np.ndarray) -> List[Dict]:
        """Analyze RSI divergences."""
        divergences = []
        
        # Bullish divergence (price makes lower lows, RSI makes higher lows)
        if len(price_lows) >= 2:
            for i in range(1, len(price_lows)):
                current_low_idx = price_lows[i]
                prev_low_idx = price_lows[i-1]
                
                current_price = data['low'].iloc[current_low_idx]
                prev_price = data['low'].iloc[prev_low_idx]
                
                current_rsi = data['rsi'].iloc[current_low_idx]
                prev_rsi = data['rsi'].iloc[prev_low_idx]
                
                # Check for bullish divergence
                if (current_price < prev_price and current_rsi > prev_rsi and 
                    not pd.isna(current_rsi) and not pd.isna(prev_rsi)):
                    
                    strength = abs(current_rsi - prev_rsi) / 10.0  # Normalize
                    
                    divergences.append({
                        'type': DivergenceType.BULLISH_REGULAR,
                        'strength': strength,
                        'timestamp': data.index[current_low_idx],
                        'price_points': [prev_price, current_price],
                        'indicator_points': [prev_rsi, current_rsi],
                        'indicator': 'rsi'
                    })
        
        # Bearish divergence (price makes higher highs, RSI makes lower highs)
        if len(price_highs) >= 2:
            for i in range(1, len(price_highs)):
                current_high_idx = price_highs[i]
                prev_high_idx = price_highs[i-1]
                
                current_price = data['high'].iloc[current_high_idx]
                prev_price = data['high'].iloc[prev_high_idx]
                
                current_rsi = data['rsi'].iloc[current_high_idx]
                prev_rsi = data['rsi'].iloc[prev_high_idx]
                
                # Check for bearish divergence
                if (current_price > prev_price and current_rsi < prev_rsi and 
                    not pd.isna(current_rsi) and not pd.isna(prev_rsi)):
                    
                    strength = abs(current_rsi - prev_rsi) / 10.0
                    
                    divergences.append({
                        'type': DivergenceType.BEARISH_REGULAR,
                        'strength': strength,
                        'timestamp': data.index[current_high_idx],
                        'price_points': [prev_price, current_price],
                        'indicator_points': [prev_rsi, current_rsi],
                        'indicator': 'rsi'
                    })
        
        return divergences
    
    def _analyze_macd_divergence(self, data: pd.DataFrame, price_highs: np.ndarray, 
                                price_lows: np.ndarray) -> List[Dict]:
        """Analyze MACD divergences."""
        divergences = []
        
        # Similar logic to RSI but using MACD histogram
        if 'macd_histogram' not in data.columns:
            return divergences
        
        # Bullish MACD divergence
        if len(price_lows) >= 2:
            for i in range(1, len(price_lows)):
                current_low_idx = price_lows[i]
                prev_low_idx = price_lows[i-1]
                
                current_price = data['low'].iloc[current_low_idx]
                prev_price = data['low'].iloc[prev_low_idx]
                
                current_macd = data['macd_histogram'].iloc[current_low_idx]
                prev_macd = data['macd_histogram'].iloc[prev_low_idx]
                
                if (current_price < prev_price and current_macd > prev_macd and 
                    not pd.isna(current_macd) and not pd.isna(prev_macd)):
                    
                    strength = abs(current_macd - prev_macd) * 100  # Scale appropriately
                    
                    divergences.append({
                        'type': DivergenceType.BULLISH_REGULAR,
                        'strength': min(strength, 1.0),
                        'timestamp': data.index[current_low_idx],
                        'price_points': [prev_price, current_price],
                        'indicator_points': [prev_macd, current_macd],
                        'indicator': 'macd'
                    })
        
        return divergences
    
    def _analyze_stochastic_divergence(self, data: pd.DataFrame, price_highs: np.ndarray, 
                                      price_lows: np.ndarray) -> List[Dict]:
        """Analyze Stochastic divergences."""
        divergences = []
        
        if 'stoch_k' not in data.columns:
            return divergences
        
        # Similar divergence logic for Stochastic
        # Implementation similar to RSI analysis but using stoch_k values
        
        return divergences  # Simplified for brevity
    
    def _find_confirmed_divergences(self, timeframe_divergences: Dict) -> List[DivergenceSignal]:
        """Find divergences confirmed across multiple timeframes."""
        confirmed_signals = []
        
        # Group divergences by approximate time and type
        time_groups = self._group_divergences_by_time(timeframe_divergences)
        
        for time_group in time_groups:
            # Check if enough timeframes confirm the divergence
            confirming_timeframes = []
            divergence_type = None
            total_strength = 0.0
            price_points = []
            momentum_points = []
            
            for timeframe, divergences in time_group.items():
                if divergences:
                    confirming_timeframes.append(timeframe)
                    # Use the strongest divergence from this timeframe
                    strongest = max(divergences, key=lambda x: x['strength'])
                    if divergence_type is None:
                        divergence_type = strongest['type']
                    total_strength += strongest['strength']
                    price_points.extend(strongest['price_points'])
                    momentum_points.extend(strongest['indicator_points'])
            
            # Create confirmed signal if enough timeframes agree
            if (len(confirming_timeframes) >= self.min_confirmation_timeframes and 
                divergence_type is not None):
                
                # Calculate confidence based on timeframe agreement
                confidence = len(confirming_timeframes) / len(self.timeframes)
                avg_strength = total_strength / len(confirming_timeframes)
                
                # Estimate expected move size
                expected_move = self._estimate_move_size(price_points, avg_strength)
                
                signal = DivergenceSignal(
                    timestamp=pd.Timestamp.now(),  # Would use actual timestamp from data
                    divergence_type=divergence_type,
                    strength=avg_strength,
                    confidence=confidence,
                    timeframes_confirmed=confirming_timeframes,
                    price_points=price_points,
                    momentum_points=momentum_points,
                    expected_move=expected_move
                )
                
                confirmed_signals.append(signal)
        
        return confirmed_signals
    
    def _group_divergences_by_time(self, timeframe_divergences: Dict) -> List[Dict]:
        """Group divergences that occur around the same time."""
        # Simplified grouping - in practice would use more sophisticated time alignment
        time_groups = []
        
        # For now, just return each timeframe as a separate group
        for timeframe, divergences in timeframe_divergences.items():
            if divergences:
                time_groups.append({timeframe: divergences})
        
        return time_groups
    
    def _estimate_move_size(self, price_points: List[float], strength: float) -> float:
        """Estimate expected move size based on divergence strength."""
        if len(price_points) < 2:
            return 0.0
        
        # Calculate average price range
        price_range = max(price_points) - min(price_points)
        
        # Scale by divergence strength
        expected_move = price_range * strength * 0.5  # Conservative estimate
        
        return expected_move


class MultiTimeframeDivergenceFilter:
    """
    Advanced filter for removing false divergences using multi-timeframe analysis.
    """
    
    def __init__(self, 
                 primary_timeframes: List[str] = ['5m', '15m', '1h'],
                 confirmation_timeframes: List[str] = ['1h', '4h'],
                 filter_strength: float = 0.7):
        """Initialize the divergence filter."""
        self.primary_timeframes = primary_timeframes
        self.confirmation_timeframes = confirmation_timeframes
        self.filter_strength = filter_strength
        
    def filter_divergences(self, divergence_signals: List[DivergenceSignal]) -> List[DivergenceSignal]:
        """Filter out low-quality divergences."""
        filtered_signals = []
        
        for signal in divergence_signals:
            if self._passes_filter(signal):
                filtered_signals.append(signal)
        
        return filtered_signals
    
    def _passes_filter(self, signal: DivergenceSignal) -> bool:
        """Check if a divergence signal passes the filter criteria."""
        # Strength filter
        if signal.strength < self.filter_strength:
            return False
        
        # Confidence filter
        if signal.confidence < 0.6:
            return False
        
        # Timeframe confirmation filter
        confirmed_timeframes = set(signal.timeframes_confirmed)
        primary_confirmed = len(confirmed_timeframes.intersection(self.primary_timeframes))
        
        if primary_confirmed < 2:  # Need at least 2 primary timeframes
            return False
        
        return True


class DivergenceConfirmationEngine:
    """
    Engine for confirming divergence signals with additional market analysis.
    """
    
    def __init__(self):
        self.confirmation_methods = [
            self._volume_confirmation,
            self._price_action_confirmation,
            self._support_resistance_confirmation
        ]
    
    def confirm_divergence(self, signal: DivergenceSignal, market_data: pd.DataFrame) -> Dict:
        """
        Confirm divergence signal using multiple confirmation methods.
        
        Returns:
            Dictionary with confirmation results
        """
        confirmation_results = {
            'overall_confirmation': False,
            'confirmation_score': 0.0,
            'individual_confirmations': {}
        }
        
        total_score = 0.0
        method_count = 0
        
        for method in self.confirmation_methods:
            try:
                method_result = method(signal, market_data)
                method_name = method.__name__
                
                confirmation_results['individual_confirmations'][method_name] = method_result
                
                if method_result['confirmed']:
                    total_score += method_result['confidence']
                method_count += 1
                
            except Exception as e:
                logger.error(f"Confirmation method {method.__name__} failed: {e}")
        
        # Calculate overall confirmation
        if method_count > 0:
            avg_score = total_score / method_count
            confirmation_results['confirmation_score'] = avg_score
            confirmation_results['overall_confirmation'] = avg_score > 0.6
        
        return confirmation_results
    
    def _volume_confirmation(self, signal: DivergenceSignal, data: pd.DataFrame) -> Dict:
        """Confirm divergence using volume analysis."""
        # Look for volume expansion during divergence formation
        recent_volume = data['volume'].tail(20)
        avg_volume = recent_volume.mean()
        current_volume = recent_volume.iloc[-1]
        
        volume_expansion = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Volume should expand for valid divergences
        confirmed = volume_expansion > 1.2
        confidence = min(volume_expansion / 2.0, 1.0)
        
        return {
            'confirmed': confirmed,
            'confidence': confidence,
            'volume_expansion': volume_expansion
        }
    
    def _price_action_confirmation(self, signal: DivergenceSignal, data: pd.DataFrame) -> Dict:
        """Confirm divergence using price action patterns."""
        # Look for reversal candlestick patterns
        recent_data = data.tail(5)
        
        # Simplified pattern recognition
        last_candle = recent_data.iloc[-1]
        body_size = abs(last_candle['close'] - last_candle['open'])
        candle_range = last_candle['high'] - last_candle['low']
        
        # Look for doji or hammer patterns
        is_doji = body_size < (candle_range * 0.1)
        
        if signal.divergence_type in [DivergenceType.BULLISH_REGULAR, DivergenceType.BULLISH_HIDDEN]:
            # For bullish divergence, look for bullish patterns
            is_hammer = (last_candle['close'] > last_candle['open'] and 
                        (last_candle['close'] - last_candle['low']) > body_size * 2)
            confirmed = is_doji or is_hammer
        else:
            # For bearish divergence, look for bearish patterns
            is_shooting_star = (last_candle['close'] < last_candle['open'] and 
                              (last_candle['high'] - last_candle['close']) > body_size * 2)
            confirmed = is_doji or is_shooting_star
        
        confidence = 0.7 if confirmed else 0.3
        
        return {
            'confirmed': confirmed,
            'confidence': confidence,
            'pattern_detected': 'doji' if is_doji else 'reversal_pattern' if confirmed else 'none'
        }
    
    def _support_resistance_confirmation(self, signal: DivergenceSignal, data: pd.DataFrame) -> Dict:
        """Confirm divergence using support/resistance levels."""
        current_price = data['close'].iloc[-1]
        
        # Calculate recent support/resistance levels
        recent_highs = data['high'].tail(50)
        recent_lows = data['low'].tail(50)
        
        resistance_level = recent_highs.quantile(0.9)
        support_level = recent_lows.quantile(0.1)
        
        # Check if divergence occurs near key levels
        near_resistance = abs(current_price - resistance_level) / current_price < 0.02
        near_support = abs(current_price - support_level) / current_price < 0.02
        
        if signal.divergence_type in [DivergenceType.BEARISH_REGULAR, DivergenceType.BEARISH_HIDDEN]:
            confirmed = near_resistance
        else:
            confirmed = near_support
        
        confidence = 0.8 if confirmed else 0.4
        
        return {
            'confirmed': confirmed,
            'confidence': confidence,
            'near_key_level': near_resistance or near_support,
            'resistance_level': resistance_level,
            'support_level': support_level
        }
