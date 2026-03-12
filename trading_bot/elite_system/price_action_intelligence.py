"""
Price Action Intelligence Engine - Advanced Candlestick Quantum Analysis

This module implements sophisticated price action analysis using:
1. Candlestick Quantum Analysis with Markov chains
2. Naked Trading Core for pattern-agnostic decisions
3. Multi-Timeframe Synergy with fractal confirmation
4. Probabilistic modeling of candle behavior at key levels
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from scipy import stats
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("TA-Lib not available - using fallback pattern detection")

class CandlePattern(Enum):
    """Enhanced candlestick pattern types"""
    DOJI = "doji"
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"
    ENGULFING_BULL = "engulfing_bull"
    ENGULFING_BEAR = "engulfing_bear"
    HARAMI_BULL = "harami_bull"
    HARAMI_BEAR = "harami_bear"
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"
    THREE_WHITE_SOLDIERS = "three_white_soldiers"
    THREE_BLACK_CROWS = "three_black_crows"
    PIERCING_LINE = "piercing_line"
    DARK_CLOUD_COVER = "dark_cloud_cover"

class TimeFrame(Enum):
    """Multi-timeframe analysis periods"""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN = "MN"

@dataclass
class QuantumCandleState:
    """Quantum state representation of candlestick behavior"""
    pattern: CandlePattern
    probability: float
    energy_level: float
    momentum_vector: np.ndarray
    volatility_signature: float
    market_phase: str
    confidence: float

@dataclass
class MarkovTransition:
    """Markov chain transition probabilities for candle patterns"""
    from_pattern: CandlePattern
    to_pattern: CandlePattern
    probability: float
    success_rate: float
    avg_move: float

@dataclass
class FractalConfirmation:
    """Multi-timeframe fractal confirmation"""
    timeframe: TimeFrame
    signal_strength: float
    alignment_score: float
    weight: float
    confirmation: bool

class CandlestickQuantumAnalyzer:
    """Advanced candlestick analysis using quantum probability models"""
    
    def __init__(self):
        self.markov_chains = {}
        self.quantum_states = []
        self.pattern_history = []
        self.transition_matrix = None
        self.energy_levels = {}
        
    def analyze_quantum_candle_behavior(self, df: pd.DataFrame, key_levels: List[float]) -> List[QuantumCandleState]:
        """
        Analyze candlestick behavior using quantum probability models
        
        Args:
            df: OHLCV data
            key_levels: Important price levels for analysis
            
        Returns:
            List of quantum candle states
        """
        quantum_states = []
        
        # Detect candlestick patterns
        patterns = self._detect_enhanced_patterns(df)
        
        # Calculate quantum properties for each candle
        for i in range(len(df)):
            if i < 20:  # Need sufficient history
                continue
                
            candle_data = df.iloc[i-20:i+1]
            
            # Calculate quantum properties
            energy_level = self._calculate_energy_level(candle_data, key_levels)
            momentum_vector = self._calculate_momentum_vector(candle_data)
            volatility_signature = self._calculate_volatility_signature(candle_data)
            market_phase = self._identify_market_phase(candle_data)
            
            # Get pattern for current candle
            current_pattern = patterns.get(i, CandlePattern.DOJI)
            
            # Calculate probability using Markov chain
            probability = self._calculate_pattern_probability(current_pattern, candle_data)
            
            # Calculate confidence based on multiple factors
            confidence = self._calculate_quantum_confidence(
                energy_level, momentum_vector, volatility_signature, probability
            )
            
            quantum_state = QuantumCandleState(
                pattern=current_pattern,
                probability=probability,
                energy_level=energy_level,
                momentum_vector=momentum_vector,
                volatility_signature=volatility_signature,
                market_phase=market_phase,
                confidence=confidence
            )
            
            quantum_states.append(quantum_state)
            
        return quantum_states
    
    def _detect_enhanced_patterns(self, df: pd.DataFrame) -> Dict[int, CandlePattern]:
        """Detect enhanced candlestick patterns using TA-Lib and custom logic"""
        patterns = {}
        
        # TA-Lib pattern recognition
        if TALIB_AVAILABLE:
            try:
                # Single candle patterns
                # Single candle patterns
                doji = talib.CDLDOJI(df['open'], df['high'], df['low'], df['close'])
                hammer = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
                shooting_star = talib.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close'])
                
                # Two candle patterns
                engulfing = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
                harami = talib.CDLHARAMI(df['open'], df['high'], df['low'], df['close'])
                piercing = talib.CDLPIERCING(df['open'], df['high'], df['low'], df['close'])
                dark_cloud = talib.CDLDARKCLOUDCOVER(df['open'], df['high'], df['low'], df['close'])
                
                # Three candle patterns
                morning_star = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close'])
                evening_star = talib.CDLEVENINGSTAR(df['open'], df['high'], df['low'], df['close'])
                three_white = talib.CDL3WHITESOLDIERS(df['open'], df['high'], df['low'], df['close'])
                three_black = talib.CDL3BLACKCROWS(df['open'], df['high'], df['low'], df['close'])
                
                # Map patterns to enum
                for i in range(len(df)):
                    if doji.iloc[i] != 0:
                        patterns[i] = CandlePattern.DOJI
                    elif hammer.iloc[i] > 0:
                        patterns[i] = CandlePattern.HAMMER
                    elif shooting_star.iloc[i] > 0:
                        patterns[i] = CandlePattern.SHOOTING_STAR
                    elif engulfing.iloc[i] > 0:
                        patterns[i] = CandlePattern.ENGULFING_BULL
                    elif engulfing.iloc[i] < 0:
                        patterns[i] = CandlePattern.ENGULFING_BEAR
                    elif harami.iloc[i] > 0:
                        patterns[i] = CandlePattern.HARAMI_BULL
                    elif harami.iloc[i] < 0:
                        patterns[i] = CandlePattern.HARAMI_BEAR
                    elif morning_star.iloc[i] > 0:
                        patterns[i] = CandlePattern.MORNING_STAR
                    elif evening_star.iloc[i] > 0:
                        patterns[i] = CandlePattern.EVENING_STAR
                    elif three_white.iloc[i] > 0:
                        patterns[i] = CandlePattern.THREE_WHITE_SOLDIERS
                    elif three_black.iloc[i] > 0:
                        patterns[i] = CandlePattern.THREE_BLACK_CROWS
                    elif piercing.iloc[i] > 0:
                        patterns[i] = CandlePattern.PIERCING_LINE
                    elif dark_cloud.iloc[i] > 0:
                        patterns[i] = CandlePattern.DARK_CLOUD_COVER
                    
            except Exception as e:
                print(f"TA-Lib pattern detection error: {e}")
        else:
            # Fallback pattern detection when TA-Lib is not available
            print("Using fallback pattern detection (TA-Lib not available)")
            patterns = self._fallback_pattern_detection(df)
            
        return patterns
    
    def _fallback_pattern_detection(self, df: pd.DataFrame) -> Dict[int, CandlePattern]:
        """Simple fallback pattern detection when TA-Lib is not available"""
        patterns = {}
        
        for i in range(1, len(df)):
            # Simple doji detection
            body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
            candle_range = df['high'].iloc[i] - df['low'].iloc[i]
            
            if candle_range > 0 and body_size / candle_range < 0.1:
                patterns[i] = CandlePattern.DOJI
        
        return patterns
    
    def _calculate_energy_level(self, candle_data: pd.DataFrame, key_levels: List[float]) -> float:
        """Calculate quantum energy level based on proximity to key levels"""
        current_price = candle_data['close'].iloc[-1]
        
        if not key_levels:
            return 0.5
        
        # Find closest key level
        distances = [abs(current_price - level) for level in key_levels]
        min_distance = min(distances)
        
        # Calculate energy based on distance (closer = higher energy)
        avg_range = candle_data['high'].mean() - candle_data['low'].mean()
        normalized_distance = min_distance / avg_range if avg_range > 0 else 1.0
        
        # Energy decreases exponentially with distance
        energy = np.exp(-normalized_distance)
        
        return min(max(energy, 0.0), 1.0)
    
    def _calculate_momentum_vector(self, candle_data: pd.DataFrame) -> np.ndarray:
        """Calculate multi-dimensional momentum vector"""
        # Price momentum
        price_momentum = (candle_data['close'].iloc[-1] - candle_data['close'].iloc[0]) / candle_data['close'].iloc[0]
        
        # Volume momentum (if available)
        volume_momentum = 0.0
        if 'volume' in candle_data.columns:
            recent_vol = candle_data['volume'].iloc[-5:].mean()
            avg_vol = candle_data['volume'].mean()
            volume_momentum = (recent_vol - avg_vol) / avg_vol if avg_vol > 0 else 0.0
        
        # Volatility momentum
        volatility = candle_data['high'] - candle_data['low']
        recent_vol = volatility.iloc[-5:].mean()
        avg_vol = volatility.mean()
        volatility_momentum = (recent_vol - avg_vol) / avg_vol if avg_vol > 0 else 0.0
        
        return np.array([price_momentum, volume_momentum, volatility_momentum])
    
    def _calculate_volatility_signature(self, candle_data: pd.DataFrame) -> float:
        """Calculate unique volatility signature"""
        # True Range calculation
        high_low = candle_data['high'] - candle_data['low']
        high_close = np.abs(candle_data['high'] - candle_data['close'].shift(1))
        low_close = np.abs(candle_data['low'] - candle_data['close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(14).mean().iloc[-1]
        
        # Volatility clustering
        returns = candle_data['close'].pct_change().dropna()
        volatility_clustering = returns.rolling(5).std().std()
        
        # Combine ATR and clustering
        signature = atr * (1 + volatility_clustering)
        
        return signature if not np.isnan(signature) else 0.0
    
    def _identify_market_phase(self, candle_data: pd.DataFrame) -> str:
        """Identify current market phase"""
        # Calculate moving averages
        sma_20 = candle_data['close'].rolling(20).mean()
        sma_50 = candle_data['close'].rolling(50).mean() if len(candle_data) >= 50 else sma_20
        
        current_price = candle_data['close'].iloc[-1]
        sma_20_current = sma_20.iloc[-1]
        sma_50_current = sma_50.iloc[-1]
        
        # Determine phase
        if current_price > sma_20_current > sma_50_current:
            return "uptrend"
        elif current_price < sma_20_current < sma_50_current:
            return "downtrend"
        elif abs(sma_20_current - sma_50_current) / current_price < 0.001:
            return "consolidation"
        else:
            return "transition"
    
    def _calculate_pattern_probability(self, pattern: CandlePattern, candle_data: pd.DataFrame) -> float:
        """Calculate pattern success probability using Markov chains"""
        # This would use historical pattern analysis
        # For now, return base probabilities
        base_probabilities = {
            CandlePattern.DOJI: 0.5,
            CandlePattern.HAMMER: 0.65,
            CandlePattern.SHOOTING_STAR: 0.65,
            CandlePattern.ENGULFING_BULL: 0.70,
            CandlePattern.ENGULFING_BEAR: 0.70,
            CandlePattern.HARAMI_BULL: 0.60,
            CandlePattern.HARAMI_BEAR: 0.60,
            CandlePattern.MORNING_STAR: 0.75,
            CandlePattern.EVENING_STAR: 0.75,
            CandlePattern.THREE_WHITE_SOLDIERS: 0.80,
            CandlePattern.THREE_BLACK_CROWS: 0.80,
            CandlePattern.PIERCING_LINE: 0.65,
            CandlePattern.DARK_CLOUD_COVER: 0.65,
        }
        
        return base_probabilities.get(pattern, 0.5)
    
    def _calculate_quantum_confidence(self, energy_level: float, momentum_vector: np.ndarray, 
                                    volatility_signature: float, probability: float) -> float:
        """Calculate overall confidence in quantum analysis"""
        # Weight different factors
        energy_weight = 0.3
        momentum_weight = 0.3
        volatility_weight = 0.2
        probability_weight = 0.2
        
        # Normalize momentum magnitude
        momentum_magnitude = np.linalg.norm(momentum_vector)
        normalized_momentum = min(momentum_magnitude, 1.0)
        
        # Normalize volatility
        normalized_volatility = min(volatility_signature / 0.02, 1.0)  # Assume 2% is high volatility
        
        # Calculate weighted confidence
        confidence = (
            energy_level * energy_weight +
            normalized_momentum * momentum_weight +
            normalized_volatility * volatility_weight +
            probability * probability_weight
        )
        
        return min(max(confidence, 0.0), 1.0)

class NakedTradingCore:
    """Pattern-agnostic decision making based on pure price reactions"""
    
    def __init__(self):
        self.price_memory = []
        self.reaction_patterns = {}
        
    def analyze_naked_price_action(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze pure price action without indicators
        
        Args:
            df: OHLCV data
            
        Returns:
            Dictionary with naked trading signals
        """
        signals = {
            'trend_strength': self._calculate_trend_strength(df),
            'support_resistance': self._find_naked_levels(df),
            'price_rejection': self._detect_price_rejection(df),
            'momentum_shift': self._detect_momentum_shift(df),
            'market_structure': self._analyze_market_structure(df),
            'volume_confirmation': self._analyze_volume_confirmation(df)
        }
        
        return signals
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength using pure price action"""
        # Higher highs and higher lows for uptrend
        # Lower highs and lower lows for downtrend
        
        highs = df['high'].rolling(5).max()
        lows = df['low'].rolling(5).min()
        
        # Count consecutive higher highs/lows
        higher_highs = (highs > highs.shift(1)).rolling(10).sum()
        higher_lows = (lows > lows.shift(1)).rolling(10).sum()
        lower_highs = (highs < highs.shift(1)).rolling(10).sum()
        lower_lows = (lows < lows.shift(1)).rolling(10).sum()
        
        uptrend_strength = (higher_highs.iloc[-1] + higher_lows.iloc[-1]) / 20
        downtrend_strength = (lower_highs.iloc[-1] + lower_lows.iloc[-1]) / 20
        
        # Return net trend strength (-1 to 1)
        return uptrend_strength - downtrend_strength
    
    def _find_naked_levels(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find support/resistance levels using price clustering"""
        # Use DBSCAN clustering on price levels
        price_points = np.concatenate([df['high'].values, df['low'].values]).reshape(-1, 1)
        
        # Normalize prices for clustering
        price_range = price_points.max() - price_points.min()
        eps = price_range * 0.001  # 0.1% of price range
        
        clustering = DBSCAN(eps=eps, min_samples=3).fit(price_points)
        
        levels = []
        for label in set(clustering.labels_):
            if label == -1:  # Noise
                continue
                
            cluster_points = price_points[clustering.labels_ == label]
            level_price = np.mean(cluster_points)
            strength = len(cluster_points)
            
            # Determine if support or resistance
            touches_above = np.sum(df['low'] <= level_price) 
            touches_below = np.sum(df['high'] >= level_price)
            
            level_type = "support" if touches_above > touches_below else "resistance"
            
            levels.append({
                'price': level_price,
                'strength': strength,
                'type': level_type,
                'touches': touches_above + touches_below
            })
        
        return sorted(levels, key=lambda x: x['strength'], reverse=True)
    
    def _detect_price_rejection(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect price rejection patterns"""
        rejections = []
        
        for i in range(2, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            prev2 = df.iloc[i-2]
            
            # Long wick rejection at high
            body_size = abs(current['close'] - current['open'])
            upper_wick = current['high'] - max(current['close'], current['open'])
            lower_wick = min(current['close'], current['open']) - current['low']
            
            # Upper rejection
            if upper_wick > body_size * 2 and upper_wick > lower_wick * 1.5:
                rejections.append({
                    'type': 'upper_rejection',
                    'price': current['high'],
                    'strength': upper_wick / body_size if body_size > 0 else 5,
                    'index': i
                })
            
            # Lower rejection
            if lower_wick > body_size * 2 and lower_wick > upper_wick * 1.5:
                rejections.append({
                    'type': 'lower_rejection',
                    'price': current['low'],
                    'strength': lower_wick / body_size if body_size > 0 else 5,
                    'index': i
                })
        
        return rejections
    
    def _detect_momentum_shift(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect momentum shifts in price action"""
        # Calculate price momentum
        returns = df['close'].pct_change()
        momentum = returns.rolling(5).mean()
        
        # Detect momentum divergence
        price_highs = df['high'].rolling(10).max()
        momentum_highs = momentum.rolling(10).max()
        
        # Bearish divergence: higher price highs, lower momentum highs
        bearish_div = (price_highs.iloc[-1] > price_highs.iloc[-10]) and (momentum_highs.iloc[-1] < momentum_highs.iloc[-10])
        
        # Bullish divergence: lower price lows, higher momentum lows
        price_lows = df['low'].rolling(10).min()
        momentum_lows = momentum.rolling(10).min()
        bullish_div = (price_lows.iloc[-1] < price_lows.iloc[-10]) and (momentum_lows.iloc[-1] > momentum_lows.iloc[-10])
        
        return {
            'bearish_divergence': bearish_div,
            'bullish_divergence': bullish_div,
            'current_momentum': momentum.iloc[-1],
            'momentum_trend': 'up' if momentum.iloc[-1] > momentum.iloc[-5] else 'down'
        }
    
    def _analyze_market_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market structure breaks"""
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(df)-2):
            # Swing high: higher than 2 bars on each side
            if (df['high'].iloc[i] > df['high'].iloc[i-2] and 
                df['high'].iloc[i] > df['high'].iloc[i-1] and
                df['high'].iloc[i] > df['high'].iloc[i+1] and 
                df['high'].iloc[i] > df['high'].iloc[i+2]):
                swing_highs.append({'price': df['high'].iloc[i], 'index': i})
            
            # Swing low: lower than 2 bars on each side
            if (df['low'].iloc[i] < df['low'].iloc[i-2] and 
                df['low'].iloc[i] < df['low'].iloc[i-1] and
                df['low'].iloc[i] < df['low'].iloc[i+1] and 
                df['low'].iloc[i] < df['low'].iloc[i+2]):
                swing_lows.append({'price': df['low'].iloc[i], 'index': i})
        
        # Analyze structure breaks
        structure_break = None
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            last_high = swing_highs[-1]['price']
            last_low = swing_lows[-1]['price']
            current_price = df['close'].iloc[-1]
            
            if current_price > last_high:
                structure_break = 'bullish_break'
            elif current_price < last_low:
                structure_break = 'bearish_break'
        
        return {
            'swing_highs': swing_highs[-5:],  # Last 5 swing highs
            'swing_lows': swing_lows[-5:],   # Last 5 swing lows
            'structure_break': structure_break,
            'trend_structure': self._determine_trend_structure(swing_highs, swing_lows)
        }
    
    def _determine_trend_structure(self, swing_highs: List[Dict], swing_lows: List[Dict]) -> str:
        """Determine overall trend structure"""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return 'undefined'
        
        # Check for higher highs and higher lows
        recent_highs = swing_highs[-2:]
        recent_lows = swing_lows[-2:]
        
        higher_highs = recent_highs[-1]['price'] > recent_highs[0]['price']
        higher_lows = recent_lows[-1]['price'] > recent_lows[0]['price']
        
        lower_highs = recent_highs[-1]['price'] < recent_highs[0]['price']
        lower_lows = recent_lows[-1]['price'] < recent_lows[0]['price']
        
        if higher_highs and higher_lows:
            return 'uptrend'
        elif lower_highs and lower_lows:
            return 'downtrend'
        else:
            return 'sideways'
    
    def _analyze_volume_confirmation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume confirmation for price moves"""
        if 'volume' not in df.columns:
            return {'volume_available': False}
        
        # Volume moving average
        vol_ma = df['volume'].rolling(20).mean()
        current_vol = df['volume'].iloc[-1]
        
        # Price change
        price_change = df['close'].pct_change().iloc[-1]
        
        # Volume confirmation
        high_volume = current_vol > vol_ma.iloc[-1] * 1.5
        volume_trend = df['volume'].rolling(5).mean().iloc[-1] > df['volume'].rolling(20).mean().iloc[-1]
        
        return {
            'volume_available': True,
            'high_volume': high_volume,
            'volume_trend': 'increasing' if volume_trend else 'decreasing',
            'volume_confirmation': high_volume and abs(price_change) > 0.001,
            'relative_volume': current_vol / vol_ma.iloc[-1] if vol_ma.iloc[-1] > 0 else 1.0
        }

class MultiTimeframeSynergy:
    """Fractal confirmation across multiple timeframes with weighted consensus"""
    
    def __init__(self):
        self.timeframe_weights = {
            TimeFrame.M1: 0.05,
            TimeFrame.M5: 0.10,
            TimeFrame.M15: 0.15,
            TimeFrame.M30: 0.15,
            TimeFrame.H1: 0.20,
            TimeFrame.H4: 0.20,
            TimeFrame.D1: 0.10,
            TimeFrame.W1: 0.03,
            TimeFrame.MN: 0.02
        }
    
    def analyze_multi_timeframe_synergy(self, data_dict: Dict[TimeFrame, pd.DataFrame]) -> Dict[str, Any]:
        """
        Analyze synergy across multiple timeframes
        
        Args:
            data_dict: Dictionary mapping timeframes to OHLCV data
            
        Returns:
            Multi-timeframe analysis results
        """
        confirmations = []
        total_weight = 0
        weighted_signal = 0
        
        for timeframe, df in data_dict.items():
            if len(df) < 50:  # Need sufficient data
                continue
                
            # Analyze this timeframe
            tf_analysis = self._analyze_single_timeframe(df, timeframe)
            
            # Create fractal confirmation
            confirmation = FractalConfirmation(
                timeframe=timeframe,
                signal_strength=tf_analysis['signal_strength'],
                alignment_score=tf_analysis['alignment_score'],
                weight=self.timeframe_weights.get(timeframe, 0.1),
                confirmation=tf_analysis['confirmation']
            )
            
            confirmations.append(confirmation)
            
            # Add to weighted consensus
            weight = confirmation.weight
            total_weight += weight
            weighted_signal += confirmation.signal_strength * weight
        
        # Calculate consensus
        consensus_signal = weighted_signal / total_weight if total_weight > 0 else 0
        
        # Calculate fractal alignment
        fractal_alignment = self._calculate_fractal_alignment(confirmations)
        
        return {
            'confirmations': confirmations,
            'consensus_signal': consensus_signal,
            'fractal_alignment': fractal_alignment,
            'total_weight': total_weight,
            'signal_quality': self._assess_signal_quality(confirmations, consensus_signal)
        }
    
    def _analyze_single_timeframe(self, df: pd.DataFrame, timeframe: TimeFrame) -> Dict[str, Any]:
        """Analyze a single timeframe for signals"""
        # Trend analysis
        sma_20 = df['close'].rolling(20).mean()
        sma_50 = df['close'].rolling(50).mean()
        
        current_price = df['close'].iloc[-1]
        trend_signal = 0
        
        if current_price > sma_20.iloc[-1] > sma_50.iloc[-1]:
            trend_signal = 1  # Bullish
        elif current_price < sma_20.iloc[-1] < sma_50.iloc[-1]:
            trend_signal = -1  # Bearish
        
        # Custom momentum analysis
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        
        momentum_signal = 0
        if rsi.iloc[-1] > 50 and macd.iloc[-1] > macd_signal.iloc[-1]:
            momentum_signal = 1
        elif rsi.iloc[-1] < 50 and macd.iloc[-1] < macd_signal.iloc[-1]:
            momentum_signal = -1
        
        # Volume analysis (if available)
        volume_signal = 0
        if 'volume' in df.columns:
            vol_ma = df['volume'].rolling(20).mean()
            if df['volume'].iloc[-1] > vol_ma.iloc[-1] * 1.2:
                volume_signal = 0.5 if trend_signal > 0 else -0.5
        
        # Combined signal strength
        signal_strength = (trend_signal + momentum_signal + volume_signal) / 3
        
        # Alignment score (how well indicators align)
        signals = [trend_signal, momentum_signal, volume_signal]
        non_zero_signals = [s for s in signals if s != 0]
        
        if len(non_zero_signals) == 0:
            alignment_score = 0
        else:
            # Check if all non-zero signals have same sign
            same_direction = all(s > 0 for s in non_zero_signals) or all(s < 0 for s in non_zero_signals)
            alignment_score = 1.0 if same_direction else 0.5
        
        return {
            'signal_strength': signal_strength,
            'alignment_score': alignment_score,
            'confirmation': abs(signal_strength) > 0.3 and alignment_score > 0.5,
            'trend_signal': trend_signal,
            'momentum_signal': momentum_signal,
            'volume_signal': volume_signal
        }
    
    def _calculate_fractal_alignment(self, confirmations: List[FractalConfirmation]) -> float:
        """Calculate overall fractal alignment across timeframes"""
        if not confirmations:
            return 0.0
        
        # Group by signal direction
        bullish_weight = sum(c.weight for c in confirmations if c.signal_strength > 0.1)
        bearish_weight = sum(c.weight for c in confirmations if c.signal_strength < -0.1)
        neutral_weight = sum(c.weight for c in confirmations if abs(c.signal_strength) <= 0.1)
        
        total_weight = bullish_weight + bearish_weight + neutral_weight
        
        if total_weight == 0:
            return 0.0
        
        # Calculate alignment as the dominance of the strongest direction
        max_directional_weight = max(bullish_weight, bearish_weight)
        alignment = max_directional_weight / total_weight
        
        return alignment
    
    def _assess_signal_quality(self, confirmations: List[FractalConfirmation], consensus_signal: float) -> str:
        """Assess the quality of the multi-timeframe signal"""
        if abs(consensus_signal) > 0.7:
            return "excellent"
        elif abs(consensus_signal) > 0.5:
            return "good"
        elif abs(consensus_signal) > 0.3:
            return "moderate"
        elif abs(consensus_signal) > 0.1:
            return "weak"
        else:
            return "no_signal"

class PriceActionIntelligenceEngine:
    """Main engine combining all price action intelligence components"""
    
    def __init__(self):
        self.quantum_analyzer = CandlestickQuantumAnalyzer()
        self.naked_core = NakedTradingCore()
        self.multi_tf_synergy = MultiTimeframeSynergy()
        
    def analyze_comprehensive_price_action(self, 
                                         data_dict: Dict[TimeFrame, pd.DataFrame],
                                         key_levels: List[float] = None) -> Dict[str, Any]:
        """
        Comprehensive price action analysis combining all components
        
        Args:
            data_dict: Multi-timeframe OHLCV data
            key_levels: Important price levels for quantum analysis
            
        Returns:
            Complete price action intelligence report
        """
        if key_levels is None:
            key_levels = []
        
        # Get primary timeframe data (H1 if available, otherwise first available)
        primary_tf = TimeFrame.H1 if TimeFrame.H1 in data_dict else list(data_dict.keys())[0]
        primary_data = data_dict[primary_tf]
        
        # Quantum candlestick analysis
        quantum_states = self.quantum_analyzer.analyze_quantum_candle_behavior(primary_data, key_levels)
        
        # Naked trading analysis
        naked_signals = self.naked_core.analyze_naked_price_action(primary_data)
        
        # Multi-timeframe synergy
        mtf_analysis = self.multi_tf_synergy.analyze_multi_timeframe_synergy(data_dict)
        
        # Generate final intelligence report
        intelligence_report = {
            'quantum_analysis': {
                'latest_quantum_state': quantum_states[-1] if quantum_states else None,
                'pattern_confidence': quantum_states[-1].confidence if quantum_states else 0,
                'energy_level': quantum_states[-1].energy_level if quantum_states else 0,
                'market_phase': quantum_states[-1].market_phase if quantum_states else 'unknown'
            },
            'naked_trading': naked_signals,
            'multi_timeframe': mtf_analysis,
            'overall_signal': self._generate_overall_signal(quantum_states, naked_signals, mtf_analysis),
            'risk_assessment': self._assess_risk_factors(quantum_states, naked_signals, mtf_analysis),
            'entry_recommendations': self._generate_entry_recommendations(quantum_states, naked_signals, mtf_analysis)
        }
        
        return intelligence_report
    
    def _generate_overall_signal(self, quantum_states: List[QuantumCandleState], 
                               naked_signals: Dict[str, Any], 
                               mtf_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall trading signal from all components"""
        # Quantum signal
        quantum_signal = 0
        if quantum_states:
            latest_state = quantum_states[-1]
            if latest_state.pattern in [CandlePattern.HAMMER, CandlePattern.ENGULFING_BULL, 
                                      CandlePattern.MORNING_STAR, CandlePattern.THREE_WHITE_SOLDIERS]:
                quantum_signal = latest_state.confidence
            elif latest_state.pattern in [CandlePattern.SHOOTING_STAR, CandlePattern.ENGULFING_BEAR,
                                        CandlePattern.EVENING_STAR, CandlePattern.THREE_BLACK_CROWS]:
                quantum_signal = -latest_state.confidence
        
        # Naked trading signal
        naked_signal = naked_signals.get('trend_strength', 0) * 0.5
        if naked_signals.get('momentum_shift', {}).get('bullish_divergence'):
            naked_signal += 0.3
        elif naked_signals.get('momentum_shift', {}).get('bearish_divergence'):
            naked_signal -= 0.3
        
        # Multi-timeframe signal
        mtf_signal = mtf_analysis.get('consensus_signal', 0)
        
        # Weighted combination
        overall_signal = (quantum_signal * 0.4 + naked_signal * 0.3 + mtf_signal * 0.3)
        
        # Signal strength classification
        if abs(overall_signal) > 0.7:
            strength = "strong"
        elif abs(overall_signal) > 0.4:
            strength = "moderate"
        elif abs(overall_signal) > 0.2:
            strength = "weak"
        else:
            strength = "neutral"
        
        direction = "bullish" if overall_signal > 0 else "bearish" if overall_signal < 0 else "neutral"
        
        return {
            'signal_value': overall_signal,
            'direction': direction,
            'strength': strength,
            'confidence': abs(overall_signal),
            'components': {
                'quantum': quantum_signal,
                'naked_trading': naked_signal,
                'multi_timeframe': mtf_signal
            }
        }
    
    def _assess_risk_factors(self, quantum_states: List[QuantumCandleState], 
                           naked_signals: Dict[str, Any], 
                           mtf_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk factors from price action analysis"""
        risk_factors = []
        risk_score = 0.5  # Base risk
        
        # Quantum risk factors
        if quantum_states:
            latest_state = quantum_states[-1]
            if latest_state.volatility_signature > 0.02:  # High volatility
                risk_factors.append("High volatility detected")
                risk_score += 0.2
            
            if latest_state.energy_level < 0.3:  # Far from key levels
                risk_factors.append("Price far from key levels")
                risk_score += 0.1
        
        # Naked trading risk factors
        if naked_signals.get('trend_strength', 0) == 0:
            risk_factors.append("No clear trend direction")
            risk_score += 0.1
        
        rejections = naked_signals.get('price_rejection', [])
        if len(rejections) > 2:
            risk_factors.append("Multiple price rejections detected")
            risk_score += 0.1
        
        # Multi-timeframe risk factors
        fractal_alignment = mtf_analysis.get('fractal_alignment', 0)
        if fractal_alignment < 0.5:
            risk_factors.append("Poor multi-timeframe alignment")
            risk_score += 0.2
        
        signal_quality = mtf_analysis.get('signal_quality', 'no_signal')
        if signal_quality in ['weak', 'no_signal']:
            risk_factors.append("Weak multi-timeframe signal")
            risk_score += 0.1
        
        return {
            'risk_score': min(risk_score, 1.0),
            'risk_level': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.4 else 'low',
            'risk_factors': risk_factors
        }
    
    def _generate_entry_recommendations(self, quantum_states: List[QuantumCandleState], 
                                      naked_signals: Dict[str, Any], 
                                      mtf_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific entry recommendations"""
        recommendations = []
        
        # Quantum-based recommendations
        if quantum_states:
            latest_state = quantum_states[-1]
            if latest_state.confidence > 0.7:
                recommendations.append(f"High confidence {latest_state.pattern.value} pattern detected")
            
            if latest_state.energy_level > 0.8:
                recommendations.append("Price near high-energy key level - watch for reaction")
        
        # Naked trading recommendations
        support_resistance = naked_signals.get('support_resistance', [])
        if support_resistance:
            strongest_level = max(support_resistance, key=lambda x: x['strength'])
            recommendations.append(f"Strong {strongest_level['type']} at {strongest_level['price']:.5f}")
        
        # Multi-timeframe recommendations
        signal_quality = mtf_analysis.get('signal_quality', 'no_signal')
        if signal_quality in ['excellent', 'good']:
            consensus = mtf_analysis.get('consensus_signal', 0)
            direction = 'bullish' if consensus > 0 else 'bearish'
            recommendations.append(f"Strong multi-timeframe {direction} alignment")
        
        return {
            'recommendations': recommendations,
            'entry_timing': self._assess_entry_timing(quantum_states, naked_signals, mtf_analysis),
            'confirmation_required': len(recommendations) < 2
        }
    
    def _assess_entry_timing(self, quantum_states: List[QuantumCandleState], 
                           naked_signals: Dict[str, Any], 
                           mtf_analysis: Dict[str, Any]) -> str:
        """Assess optimal entry timing"""
        # Check for immediate entry conditions
        immediate_conditions = 0
        
        if quantum_states and quantum_states[-1].confidence > 0.8:
            immediate_conditions += 1
        
        if mtf_analysis.get('signal_quality') in ['excellent', 'good']:
            immediate_conditions += 1
        
        if naked_signals.get('volume_confirmation', {}).get('volume_confirmation'):
            immediate_conditions += 1
        
        if immediate_conditions >= 2:
            return "immediate"
        elif immediate_conditions == 1:
            return "wait_for_confirmation"
        else:
            return "wait_for_setup"
