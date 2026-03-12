import logging
logger = logging.getLogger(__name__)
"""Advanced Pattern Recognition System for Adaptive Trading Bot.

This module implements sophisticated pattern recognition capabilities including:
- Multi-timeframe pattern detection
- Machine learning-based pattern classification
- Pattern strength and reliability scoring
- Adaptive pattern weighting based on market conditions
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
try:
    import talib
    TALIB_AVAILABLE = True
except Exception:
    TALIB_AVAILABLE = False
    talib = None
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from loguru import logger
import numpy
import pandas


class PatternType(Enum):
    """Types of trading patterns."""
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    HEAD_SHOULDERS = "head_shoulders"
    INVERSE_HEAD_SHOULDERS = "inverse_head_shoulders"
    TRIANGLE_ASCENDING = "triangle_ascending"
    TRIANGLE_DESCENDING = "triangle_descending"
    TRIANGLE_SYMMETRICAL = "triangle_symmetrical"
    WEDGE_RISING = "wedge_rising"
    WEDGE_FALLING = "wedge_falling"
    FLAG_BULL = "flag_bull"
    FLAG_BEAR = "flag_bear"
    PENNANT = "pennant"
    CUP_HANDLE = "cup_handle"
    CHANNEL_UP = "channel_up"
    CHANNEL_DOWN = "channel_down"


@dataclass
class PatternSignal:
    """Pattern recognition signal."""
    pattern_type: PatternType
    confidence: float
    strength: float
    timeframe: str
    start_idx: int
    end_idx: int
    target_price: float
    stop_loss: float
    expected_duration: int
    reliability_score: float
    market_context: Dict[str, Any]


class AdvancedPatternRecognizer:
    """Advanced pattern recognition system with ML enhancement."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the pattern recognizer."""
        self.config = config or {}
        self.min_pattern_length = self.config.get('min_pattern_length', 20)
        self.max_pattern_length = self.config.get('max_pattern_length', 100)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        
        # ML components
        self.pattern_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Pattern history for learning
        self.pattern_history = []
        self.performance_history = []
        
        logger.info("Advanced Pattern Recognizer initialized")
    
    def detect_patterns(self, data: pd.DataFrame, timeframe: str = "H1") -> List[PatternSignal]:
        """Detect all patterns in the given data."""
        patterns = []
        
        if len(data) < self.min_pattern_length:
            return patterns
        
        # Detect different pattern types
        patterns.extend(self._detect_double_patterns(data, timeframe))
        patterns.extend(self._detect_head_shoulders(data, timeframe))
        patterns.extend(self._detect_triangles(data, timeframe))
        patterns.extend(self._detect_wedges(data, timeframe))
        patterns.extend(self._detect_flags_pennants(data, timeframe))
        patterns.extend(self._detect_channels(data, timeframe))
        
        # Filter by confidence and enhance with ML if trained
        if self.is_trained:
            patterns = self._enhance_with_ml(patterns, data)
        
        # Sort by confidence and return top patterns
        patterns.sort(key=lambda x: x.confidence, reverse=True)
        return [p for p in patterns if p.confidence >= self.confidence_threshold]
    
    def _detect_double_patterns(self, data: pd.DataFrame, timeframe: str) -> List[PatternSignal]:
        """Detect double top and double bottom patterns."""
        patterns = []
        highs = data['high'].values
        lows = data['low'].values
        closes = data['close'].values
        
        # Find potential double tops
        for i in range(20, len(data) - 20):
            # Look for two peaks
            peak1_idx = i
            peak1_val = highs[i]
            
            # Check if it's a local maximum
            if not (highs[i-5:i].max() < peak1_val and highs[i+1:i+6].max() < peak1_val):
                continue
            
            # Look for second peak
            for j in range(i + 10, min(i + 50, len(data) - 10)):
                peak2_val = highs[j]
                
                # Check similarity and local maximum
                if (abs(peak1_val - peak2_val) / peak1_val < 0.02 and
                    highs[j-5:j].max() < peak2_val and highs[j+1:j+6].max() < peak2_val):
                    
                    # Find valley between peaks
                    valley_idx = np.argmin(lows[i:j]) + i
                    valley_val = lows[valley_idx]
                    
                    # Calculate pattern strength
                    height = peak1_val - valley_val
                    strength = height / peak1_val
                    
                    if strength > 0.01:  # Minimum 1% pattern height
                        confidence = self._calculate_pattern_confidence(
                            data.iloc[i-10:j+10], PatternType.DOUBLE_TOP
                        )
                        
                        patterns.append(PatternSignal(
                            pattern_type=PatternType.DOUBLE_TOP,
                            confidence=confidence,
                            strength=strength,
                            timeframe=timeframe,
                            start_idx=i,
                            end_idx=j,
                            target_price=valley_val - height * 0.5,
                            stop_loss=peak2_val * 1.01,
                            expected_duration=30,
                            reliability_score=0.7,
                            market_context=self._get_market_context(data, j)
                        ))
        
        # Similar logic for double bottoms (inverted)
        for i in range(20, len(data) - 20):
            trough1_idx = i
            trough1_val = lows[i]
            
            if not (lows[i-5:i].min() > trough1_val and lows[i+1:i+6].min() > trough1_val):
                continue
            
            for j in range(i + 10, min(i + 50, len(data) - 10)):
                trough2_val = lows[j]
                
                if (abs(trough1_val - trough2_val) / trough1_val < 0.02 and
                    lows[j-5:j].min() > trough2_val and lows[j+1:j+6].min() > trough2_val):
                    
                    peak_idx = np.argmax(highs[i:j]) + i
                    peak_val = highs[peak_idx]
                    
                    height = peak_val - trough1_val
                    strength = height / trough1_val
                    
                    if strength > 0.01:
                        confidence = self._calculate_pattern_confidence(
                            data.iloc[i-10:j+10], PatternType.DOUBLE_BOTTOM
                        )
                        
                        patterns.append(PatternSignal(
                            pattern_type=PatternType.DOUBLE_BOTTOM,
                            confidence=confidence,
                            strength=strength,
                            timeframe=timeframe,
                            start_idx=i,
                            end_idx=j,
                            target_price=peak_val + height * 0.5,
                            stop_loss=trough2_val * 0.99,
                            expected_duration=30,
                            reliability_score=0.7,
                            market_context=self._get_market_context(data, j)
                        ))
        
        return patterns
    
    def _detect_head_shoulders(self, data: pd.DataFrame, timeframe: str) -> List[PatternSignal]:
        """Detect head and shoulders patterns."""
        patterns = []
        highs = data['high'].values
        lows = data['low'].values
        
        # Look for head and shoulders pattern
        for i in range(30, len(data) - 30):
            # Find potential head (highest point)
            head_idx = i
            head_val = highs[i]
            
            # Check if it's a significant local maximum
            if not (highs[i-10:i].max() < head_val and highs[i+1:i+11].max() < head_val):
                continue
            
            # Look for left shoulder
            left_shoulder_idx = None
            for j in range(i - 25, i - 5):
                if (highs[j-5:j].max() < highs[j] and highs[j+1:j+6].max() < highs[j] and
                    0.7 < highs[j] / head_val < 0.95):
                    left_shoulder_idx = j
                    break
            
            if left_shoulder_idx is None:
                continue
            
            # Look for right shoulder
            right_shoulder_idx = None
            for j in range(i + 5, i + 25):
                if (j < len(highs) - 5 and
                    highs[j-5:j].max() < highs[j] and highs[j+1:j+6].max() < highs[j] and
                    0.7 < highs[j] / head_val < 0.95):
                    right_shoulder_idx = j
                    break
            
            if right_shoulder_idx is None:
                continue
            
            # Calculate neckline
            left_valley = np.argmin(lows[left_shoulder_idx:head_idx]) + left_shoulder_idx
            right_valley = np.argmin(lows[head_idx:right_shoulder_idx]) + head_idx
            neckline = (lows[left_valley] + lows[right_valley]) / 2
            
            # Pattern validation
            height = head_val - neckline
            strength = height / head_val
            
            if strength > 0.02:  # Minimum 2% pattern height
                confidence = self._calculate_pattern_confidence(
                    data.iloc[left_shoulder_idx-5:right_shoulder_idx+5], 
                    PatternType.HEAD_SHOULDERS
                )
                
                patterns.append(PatternSignal(
                    pattern_type=PatternType.HEAD_SHOULDERS,
                    confidence=confidence,
                    strength=strength,
                    timeframe=timeframe,
                    start_idx=left_shoulder_idx,
                    end_idx=right_shoulder_idx,
                    target_price=neckline - height,
                    stop_loss=head_val * 1.01,
                    expected_duration=40,
                    reliability_score=0.75,
                    market_context=self._get_market_context(data, right_shoulder_idx)
                ))
        
        return patterns
    
    def _detect_triangles(self, data: pd.DataFrame, timeframe: str) -> List[PatternSignal]:
        """Detect triangle patterns (ascending, descending, symmetrical)."""
        patterns = []
        
        for i in range(30, len(data) - 10):
            window = data.iloc[i-30:i+10]
            
            if len(window) < 30:
                continue
            
            # Find trend lines
            highs_trend = self._find_trend_line(window['high'].values, 'resistance')
            lows_trend = self._find_trend_line(window['low'].values, 'support')
            
            if highs_trend is None or lows_trend is None:
                continue
            
            # Classify triangle type
            highs_slope = highs_trend['slope']
            lows_slope = lows_trend['slope']
            
            pattern_type = None
            if abs(highs_slope) < 0.0001 and lows_slope > 0.0001:
                pattern_type = PatternType.TRIANGLE_ASCENDING
            elif highs_slope < -0.0001 and abs(lows_slope) < 0.0001:
                pattern_type = PatternType.TRIANGLE_DESCENDING
            elif highs_slope < -0.0001 and lows_slope > 0.0001:
                pattern_type = PatternType.TRIANGLE_SYMMETRICAL
            
            if pattern_type:
                # Calculate convergence point
                convergence_x = (lows_trend['intercept'] - highs_trend['intercept']) / (highs_trend['slope'] - lows_trend['slope'])
                
                if 0 < convergence_x < 20:  # Convergence within reasonable timeframe
                    confidence = self._calculate_pattern_confidence(window, pattern_type)
                    
                    patterns.append(PatternSignal(
                        pattern_type=pattern_type,
                        confidence=confidence,
                        strength=0.5,
                        timeframe=timeframe,
                        start_idx=i-30,
                        end_idx=i,
                        target_price=window['close'].iloc[-1] * (1.02 if pattern_type == PatternType.TRIANGLE_ASCENDING else 0.98),
                        stop_loss=window['close'].iloc[-1] * (0.98 if pattern_type == PatternType.TRIANGLE_ASCENDING else 1.02),
                        expected_duration=int(convergence_x),
                        reliability_score=0.65,
                        market_context=self._get_market_context(data, i)
                    ))
        
        return patterns
    
    def _detect_wedges(self, data: pd.DataFrame, timeframe: str) -> List[PatternSignal]:
        """Detect rising and falling wedge patterns."""
        patterns = []
        
        for i in range(40, len(data) - 10):
            window = data.iloc[i-40:i+10]
            
            if len(window) < 40:
                continue
            
            # Find trend lines for wedge
            highs_trend = self._find_trend_line(window['high'].values, 'resistance')
            lows_trend = self._find_trend_line(window['low'].values, 'support')
            
            if highs_trend is None or lows_trend is None:
                continue
            
            # Check for wedge pattern (both lines sloping in same direction)
            if (highs_trend['slope'] > 0 and lows_trend['slope'] > 0 and
                highs_trend['slope'] < lows_trend['slope']):
                # Rising wedge (bearish)
                confidence = self._calculate_pattern_confidence(window, PatternType.WEDGE_RISING)
                
                patterns.append(PatternSignal(
                    pattern_type=PatternType.WEDGE_RISING,
                    confidence=confidence,
                    strength=0.6,
                    timeframe=timeframe,
                    start_idx=i-40,
                    end_idx=i,
                    target_price=window['close'].iloc[-1] * 0.95,
                    stop_loss=window['high'].iloc[-5:].max() * 1.01,
                    expected_duration=25,
                    reliability_score=0.7,
                    market_context=self._get_market_context(data, i)
                ))
            
            elif (highs_trend['slope'] < 0 and lows_trend['slope'] < 0 and
                  highs_trend['slope'] > lows_trend['slope']):
                # Falling wedge (bullish)
                confidence = self._calculate_pattern_confidence(window, PatternType.WEDGE_FALLING)
                
                patterns.append(PatternSignal(
                    pattern_type=PatternType.WEDGE_FALLING,
                    confidence=confidence,
                    strength=0.6,
                    timeframe=timeframe,
                    start_idx=i-40,
                    end_idx=i,
                    target_price=window['close'].iloc[-1] * 1.05,
                    stop_loss=window['low'].iloc[-5:].min() * 0.99,
                    expected_duration=25,
                    reliability_score=0.7,
                    market_context=self._get_market_context(data, i)
                ))
        
        return patterns
    
    def _detect_flags_pennants(self, data: pd.DataFrame, timeframe: str) -> List[PatternSignal]:
        """Detect flag and pennant patterns."""
        patterns = []
        
        # Look for strong moves followed by consolidation
        for i in range(20, len(data) - 15):
            # Check for strong move (flagpole)
            flagpole_start = i - 15
            flagpole_end = i
            
            price_change = (data['close'].iloc[flagpole_end] - data['close'].iloc[flagpole_start]) / data['close'].iloc[flagpole_start]
            
            if abs(price_change) < 0.03:  # Minimum 3% move
                continue
            
            # Check for consolidation (flag)
            consolidation_window = data.iloc[i:i+10]
            if len(consolidation_window) < 10:
                continue
            
            volatility = consolidation_window['close'].pct_change().std()
            
            if volatility < 0.01:  # Low volatility consolidation
                pattern_type = PatternType.FLAG_BULL if price_change > 0 else PatternType.FLAG_BEAR
                
                confidence = self._calculate_pattern_confidence(
                    data.iloc[flagpole_start:i+10], pattern_type
                )
                
                patterns.append(PatternSignal(
                    pattern_type=pattern_type,
                    confidence=confidence,
                    strength=abs(price_change),
                    timeframe=timeframe,
                    start_idx=flagpole_start,
                    end_idx=i+10,
                    target_price=data['close'].iloc[i+10] * (1 + price_change),
                    stop_loss=data['close'].iloc[i+10] * (1 - price_change * 0.3),
                    expected_duration=15,
                    reliability_score=0.8,
                    market_context=self._get_market_context(data, i+10)
                ))
        
        return patterns
    
    def _detect_channels(self, data: pd.DataFrame, timeframe: str) -> List[PatternSignal]:
        """Detect channel patterns."""
        patterns = []
        
        for i in range(50, len(data) - 10):
            window = data.iloc[i-50:i+10]
            
            # Find parallel trend lines
            resistance_line = self._find_trend_line(window['high'].values, 'resistance')
            support_line = self._find_trend_line(window['low'].values, 'support')
            
            if resistance_line is None or support_line is None:
                continue
            
            # Check if lines are roughly parallel
            slope_diff = abs(resistance_line['slope'] - support_line['slope'])
            
            if slope_diff < 0.0005:  # Parallel lines
                if resistance_line['slope'] > 0.0001:
                    pattern_type = PatternType.CHANNEL_UP
                    target_multiplier = 1.02
                    stop_multiplier = 0.99
                elif resistance_line['slope'] < -0.0001:
                    pattern_type = PatternType.CHANNEL_DOWN
                    target_multiplier = 0.98
                    stop_multiplier = 1.01
                else:
                    continue  # Horizontal channel, skip for now
                
                confidence = self._calculate_pattern_confidence(window, pattern_type)
                
                patterns.append(PatternSignal(
                    pattern_type=pattern_type,
                    confidence=confidence,
                    strength=0.4,
                    timeframe=timeframe,
                    start_idx=i-50,
                    end_idx=i,
                    target_price=window['close'].iloc[-1] * target_multiplier,
                    stop_loss=window['close'].iloc[-1] * stop_multiplier,
                    expected_duration=20,
                    reliability_score=0.6,
                    market_context=self._get_market_context(data, i)
                ))
        
        return patterns
    
    def _find_trend_line(self, prices: np.ndarray, line_type: str) -> Optional[Dict]:
        """Find trend line using linear regression on peaks/troughs."""
        if line_type == 'resistance':
            # Find peaks
            peaks = []
            for i in range(2, len(prices) - 2):
                if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                    if prices[i] > prices[i-2] and prices[i] > prices[i+2]:
                        peaks.append((i, prices[i]))
        else:  # support
            # Find troughs
            peaks = []
            for i in range(2, len(prices) - 2):
                if prices[i] < prices[i-1] and prices[i] < prices[i+1]:
                    if prices[i] < prices[i-2] and prices[i] < prices[i+2]:
                        peaks.append((i, prices[i]))
        
        if len(peaks) < 2:
            return None
        
        # Linear regression on peaks/troughs
        x_vals = np.array([p[0] for p in peaks])
        y_vals = np.array([p[1] for p in peaks])
        
        slope, intercept = np.polyfit(x_vals, y_vals, 1)
        
        return {'slope': slope, 'intercept': intercept, 'r_squared': np.corrcoef(x_vals, y_vals)[0, 1]**2}
    
    def _calculate_pattern_confidence(self, data: pd.DataFrame, pattern_type: PatternType) -> float:
        """Calculate confidence score for a pattern."""
        base_confidence = 0.5
        
        # Volume confirmation
        if 'volume' in data.columns:
            volume_trend = np.corrcoef(range(len(data)), data['volume'].values)[0, 1]
            if abs(volume_trend) > 0.3:
                base_confidence += 0.1
        
        # Price action confirmation
        price_volatility = data['close'].pct_change().std()
        if 0.01 < price_volatility < 0.05:  # Moderate volatility
            base_confidence += 0.1
        
        # Pattern-specific adjustments
        if pattern_type in [PatternType.HEAD_SHOULDERS, PatternType.DOUBLE_TOP, PatternType.DOUBLE_BOTTOM]:
            base_confidence += 0.15  # Higher confidence for reversal patterns
        
        return min(base_confidence, 0.95)
    
    def _get_market_context(self, data: pd.DataFrame, idx: int) -> Dict[str, Any]:
        """Get market context around the pattern."""
        window = data.iloc[max(0, idx-20):idx+1]
        
        # Compute RSI with fallback if TA-Lib is unavailable
        if len(window) >= 14:
            if 'TALIB_AVAILABLE' in globals() and TALIB_AVAILABLE:
                try:
                    _rsi_arr = talib.RSI(window['close'].values)
                    rsi_value = float(_rsi_arr[-1]) if not np.isnan(_rsi_arr[-1]) else 50.0
                except Exception:
                    delta = window['close'].diff()
                    gain = (delta.where(delta > 0, 0.0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi_series = 100 - (100 / (1 + rs))
                    rsi_value = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0
            else:
                delta = window['close'].diff()
                gain = (delta.where(delta > 0, 0.0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
                rs = gain / loss
                rsi_series = 100 - (100 / (1 + rs))
                rsi_value = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0
        else:
            rsi_value = 50.0
        
        return {
            'trend': 'up' if window['close'].iloc[-1] > window['close'].iloc[0] else 'down',
            'volatility': window['close'].pct_change().std(),
            'volume_avg': window['volume'].mean() if 'volume' in window.columns else 0,
            'rsi': rsi_value
        }
    
    def _enhance_with_ml(self, patterns: List[PatternSignal], data: pd.DataFrame) -> List[PatternSignal]:
        """Enhance pattern confidence using ML model."""
        if not patterns:
            return patterns
        
        # Extract features for each pattern
        features = []
        for pattern in patterns:
            pattern_data = data.iloc[pattern.start_idx:pattern.end_idx+1]
            feature_vector = self._extract_pattern_features(pattern_data, pattern)
            features.append(feature_vector)
        
        # Predict using trained model
        features_scaled = self.scaler.transform(features)
        ml_confidences = self.pattern_classifier.predict_proba(features_scaled)
        
        # Update pattern confidences
        for i, pattern in enumerate(patterns):
            # Combine original confidence with ML prediction
            ml_conf = ml_confidences[i].max()
            pattern.confidence = (pattern.confidence + ml_conf) / 2
        
        return patterns
    
    def _extract_pattern_features(self, data: pd.DataFrame, pattern: PatternSignal) -> List[float]:
        """Extract features for ML model."""
        features = [
            len(data),  # Pattern length
            pattern.strength,
            data['close'].pct_change().std(),  # Volatility
            (data['close'].iloc[-1] - data['close'].iloc[0]) / data['close'].iloc[0],  # Price change
            data['volume'].mean() if 'volume' in data.columns else 1000,  # Average volume
            pattern.market_context.get('rsi', 50) / 100,  # RSI normalized
        ]
        
        # Add pattern type as one-hot encoding
        pattern_types = list(PatternType)
        for pt in pattern_types:
            features.append(1.0 if pattern.pattern_type == pt else 0.0)
        
        return features
    
    def train_ml_model(self, training_data: List[Dict[str, Any]]):
        """Train the ML model on historical pattern performance."""
        if len(training_data) < 50:
            logger.warning("Insufficient training data for ML model")
            return
        
        features = []
        labels = []
        
        for sample in training_data:
            pattern_features = sample['features']
            performance = sample['performance']  # 1 for successful, 0 for failed
            
            features.append(pattern_features)
            labels.append(performance)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train classifier
        self.pattern_classifier.fit(features_scaled, labels)
        self.is_trained = True
        
        logger.info(f"ML pattern classifier trained on {len(training_data)} samples")
    
    def update_pattern_performance(self, pattern: PatternSignal, success: bool):
        """Update pattern performance for learning."""
        self.pattern_history.append(pattern)
        self.performance_history.append(1 if success else 0)
        
        # Retrain model periodically
        if len(self.pattern_history) % 100 == 0 and len(self.pattern_history) >= 100:
            training_data = []
            for i, hist_pattern in enumerate(self.pattern_history[-100:]):
                # Extract features from historical pattern
                features = [
                    hist_pattern.strength,
                    hist_pattern.confidence,
                    hist_pattern.reliability_score,
                    hist_pattern.expected_duration,
                    hist_pattern.market_context.get('volatility', 0.02),
                    hist_pattern.market_context.get('rsi', 50) / 100,
                ]
                
                # Add pattern type encoding
                pattern_types = list(PatternType)
                for pt in pattern_types:
                    features.append(1.0 if hist_pattern.pattern_type == pt else 0.0)
                
                training_data.append({
                    'features': features,
                    'performance': self.performance_history[-(100-i)]
                })
            
            self.train_ml_model(training_data)
