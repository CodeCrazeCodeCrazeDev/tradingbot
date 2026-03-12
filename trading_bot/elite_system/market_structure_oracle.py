"""
Market Structure Oracle - Advanced BOS/CHoCH Detection and SMC Analysis

This module implements institutional-grade market structure analysis including:
1. Break of Structure (BOS) and Change of Character (CHoCH) detection
2. Smart Money Concepts (SMC) driven swing point analysis
3. ICT Silver Bullet zones identification
4. Market phase classification using wavelet transforms
5. Fractal validation and internal/external structure mapping
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
try:
    from scipy import signal, stats
except ImportError:
    scipy = None
from scipy.signal import find_peaks, find_peaks_cwt
import pywt
from sklearn.cluster import DBSCAN
from datetime import datetime, timedelta
import warnings
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

class StructureType(Enum):
    """Market structure types"""
    BOS_BULLISH = "bos_bullish"
    BOS_BEARISH = "bos_bearish"
    CHOCH_BULLISH = "choch_bullish"
    CHOCH_BEARISH = "choch_bearish"
    INTERNAL_LIQUIDITY = "internal_liquidity"
    EXTERNAL_LIQUIDITY = "external_liquidity"

class MarketPhase(Enum):
    """Market phase classifications"""
    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"
    REACCUMULATION = "reaccumulation"
    REDISTRIBUTION = "redistribution"
    CONTINUATION = "continuation"
    PULLBACK = "pullback"

class SwingType(Enum):
    """Swing point types"""
    SWING_HIGH = "swing_high"
    SWING_LOW = "swing_low"
    INTERNAL_HIGH = "internal_high"
    INTERNAL_LOW = "internal_low"
    EXTERNAL_HIGH = "external_high"
    EXTERNAL_LOW = "external_low"

@dataclass
class SwingPoint:
    """Swing point data structure"""
    price: float
    index: int
    timestamp: datetime
    swing_type: SwingType
    strength: float
    volume: float
    confirmed: bool
    liquidity_level: float

@dataclass
class StructureBreak:
    """Structure break event"""
    break_type: StructureType
    price: float
    index: int
    timestamp: datetime
    previous_structure: SwingPoint
    confirmation_strength: float
    volume_confirmation: bool
    fractal_validation: bool

@dataclass
class SilverBulletZone:
    """ICT Silver Bullet zone"""
    start_time: datetime
    end_time: datetime
    high: float
    low: float
    direction: str
    strength: float
    hit_rate: float
    active: bool

@dataclass
class MarketStructureState:
    """Current market structure state"""
    trend_direction: str
    structure_breaks: List[StructureBreak]
    swing_points: List[SwingPoint]
    current_phase: MarketPhase
    phase_confidence: float
    liquidity_levels: List[float]
    silver_bullet_zones: List[SilverBulletZone]

class SwingPointDetector:
    """Advanced swing point detection with internal/external classification"""
    
    def __init__(self, lookback_period: int = 5):
        self.lookback_period = lookback_period
        self.swing_history = []
        
    def detect_swing_points(self, df: pd.DataFrame, volume_threshold: float = 1.5) -> List[SwingPoint]:
        """
        Detect swing points with SMC classification
        
        Args:
            df: OHLCV data
            volume_threshold: Volume multiplier for significance
            
        Returns:
            List of detected swing points
        """
        swing_points = []
        
        # Detect swing highs and lows
        swing_highs = self._find_swing_highs(df)
        swing_lows = self._find_swing_lows(df)
        
        # Process swing highs
        for idx, price in swing_highs:
            swing_point = self._create_swing_point(
                df, idx, price, SwingType.SWING_HIGH, volume_threshold
            )
            swing_points.append(swing_point)
        
        # Process swing lows
        for idx, price in swing_lows:
            swing_point = self._create_swing_point(
                df, idx, price, SwingType.SWING_LOW, volume_threshold
            )
            swing_points.append(swing_point)
        
        # Sort by index
        swing_points.sort(key=lambda x: x.index)
        
        # Classify internal/external structure
        self._classify_internal_external(swing_points)
        
        return swing_points
    
    def _find_swing_highs(self, df: pd.DataFrame) -> List[Tuple[int, float]]:
        """Find swing high points"""
        highs = []
        
        for i in range(self.lookback_period, len(df) - self.lookback_period):
            current_high = df['high'].iloc[i]
            
            # Check if current high is higher than surrounding bars
            is_swing_high = True
            for j in range(i - self.lookback_period, i + self.lookback_period + 1):
                if j != i and df['high'].iloc[j] >= current_high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                highs.append((i, current_high))
        
        return highs
    
    def _find_swing_lows(self, df: pd.DataFrame) -> List[Tuple[int, float]]:
        """Find swing low points"""
        lows = []
        
        for i in range(self.lookback_period, len(df) - self.lookback_period):
            current_low = df['low'].iloc[i]
            
            # Check if current low is lower than surrounding bars
            is_swing_low = True
            for j in range(i - self.lookback_period, i + self.lookback_period + 1):
                if j != i and df['low'].iloc[j] <= current_low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                lows.append((i, current_low))
        
        return lows
    
    def _create_swing_point(self, df: pd.DataFrame, idx: int, price: float, 
                          swing_type: SwingType, volume_threshold: float) -> SwingPoint:
        """Create swing point with additional analysis"""
        # Calculate strength based on price movement and volume
        price_range = df['high'].iloc[idx] - df['low'].iloc[idx]
        avg_range = df['high'].rolling(20).mean().iloc[idx] - df['low'].rolling(20).mean().iloc[idx]
        strength = price_range / avg_range if avg_range > 0 else 1.0
        
        # Volume analysis
        volume = df['volume'].iloc[idx] if 'volume' in df.columns else 0
        avg_volume = df['volume'].rolling(20).mean().iloc[idx] if 'volume' in df.columns else 1
        volume_confirmation = volume > avg_volume * volume_threshold
        
        # Liquidity level estimation
        liquidity_level = self._estimate_liquidity_level(df, idx, swing_type)
        
        # Timestamp
        timestamp = pd.to_datetime(df.index[idx]) if hasattr(df.index[idx], 'to_pydatetime') else datetime.now()
        
        return SwingPoint(
            price=price,
            index=idx,
            timestamp=timestamp,
            swing_type=swing_type,
            strength=strength,
            volume=volume,
            confirmed=volume_confirmation,
            liquidity_level=liquidity_level
        )
    
    def _estimate_liquidity_level(self, df: pd.DataFrame, idx: int, swing_type: SwingType) -> float:
        """Estimate liquidity level at swing point"""
        # Look for equal highs/lows around this point
        window = 20
        start_idx = max(0, idx - window)
        end_idx = min(len(df), idx + window)
        
        if swing_type in [SwingType.SWING_HIGH, SwingType.INTERNAL_HIGH, SwingType.EXTERNAL_HIGH]:
            price = df['high'].iloc[idx]
            nearby_highs = df['high'].iloc[start_idx:end_idx]
            tolerance = price * 0.001  # 0.1% tolerance
            equal_highs = np.sum(np.abs(nearby_highs - price) < tolerance)
        else:
            price = df['low'].iloc[idx]
            nearby_lows = df['low'].iloc[start_idx:end_idx]
            tolerance = price * 0.001
            equal_highs = np.sum(np.abs(nearby_lows - price) < tolerance)
        
        return float(equal_highs)
    
    def _classify_internal_external(self, swing_points: List[SwingPoint]):
        """Classify swing points as internal or external structure"""
        if len(swing_points) < 3:
            return
        
        for i in range(1, len(swing_points) - 1):
            current = swing_points[i]
            prev = swing_points[i - 1]
            next_point = swing_points[i + 1]
            
            # Internal structure: swing point that doesn't break previous structure
            # External structure: swing point that breaks previous structure
            
            if current.swing_type in [SwingType.SWING_HIGH, SwingType.INTERNAL_HIGH, SwingType.EXTERNAL_HIGH]:
                # For highs, check if it's higher than previous high
                prev_high = None
                for j in range(i - 1, -1, -1):
                    if swing_points[j].swing_type in [SwingType.SWING_HIGH, SwingType.INTERNAL_HIGH, SwingType.EXTERNAL_HIGH]:
                        prev_high = swing_points[j]
                        break
                
                if prev_high and current.price > prev_high.price:
                    current.swing_type = SwingType.EXTERNAL_HIGH
                else:
                    current.swing_type = SwingType.INTERNAL_HIGH
            
            else:  # Swing lows
                prev_low = None
                for j in range(i - 1, -1, -1):
                    if swing_points[j].swing_type in [SwingType.SWING_LOW, SwingType.INTERNAL_LOW, SwingType.EXTERNAL_LOW]:
                        prev_low = swing_points[j]
                        break
                
                if prev_low and current.price < prev_low.price:
                    current.swing_type = SwingType.EXTERNAL_LOW
                else:
                    current.swing_type = SwingType.INTERNAL_LOW

class StructureBreakDetector:
    """BOS and CHoCH detection engine"""
    
    def __init__(self):
        self.structure_history = []
        self.last_trend = "neutral"
        
    def detect_structure_breaks(self, swing_points: List[SwingPoint], df: pd.DataFrame) -> List[StructureBreak]:
        """
        Detect BOS and CHoCH events
        
        Args:
            swing_points: List of swing points
            df: OHLCV data for confirmation
            
        Returns:
            List of structure break events
        """
        structure_breaks = []
        
        if len(swing_points) < 4:
            return structure_breaks
        
        # Separate highs and lows
        highs = [sp for sp in swing_points if 'HIGH' in sp.swing_type.value.upper()]
        lows = [sp for sp in swing_points if 'LOW' in sp.swing_type.value.upper()]
        
        # Detect bullish structure breaks
        bullish_breaks = self._detect_bullish_breaks(highs, lows, df)
        structure_breaks.extend(bullish_breaks)
        
        # Detect bearish structure breaks
        bearish_breaks = self._detect_bearish_breaks(highs, lows, df)
        structure_breaks.extend(bearish_breaks)
        
        # Sort by index
        structure_breaks.sort(key=lambda x: x.index)
        
        return structure_breaks
    
    def _detect_bullish_breaks(self, highs: List[SwingPoint], lows: List[SwingPoint], 
                             df: pd.DataFrame) -> List[StructureBreak]:
        """Detect bullish BOS and CHoCH"""
        breaks = []
        
        if len(highs) < 2:
            return breaks
        
        for i in range(1, len(highs)):
            current_high = highs[i]
            prev_high = highs[i - 1]
            
            # Check if current high breaks previous high
            if current_high.price > prev_high.price:
                # Determine if BOS or CHoCH
                break_type = self._classify_bullish_break(current_high, prev_high, lows)
                
                # Get confirmation data
                confirmation_strength = self._calculate_confirmation_strength(
                    current_high, prev_high, df
                )
                
                volume_confirmation = self._check_volume_confirmation(
                    current_high.index, df
                )
                
                fractal_validation = self._validate_fractal_break(
                    current_high, prev_high, df
                )
                
                structure_break = StructureBreak(
                    break_type=break_type,
                    price=current_high.price,
                    index=current_high.index,
                    timestamp=current_high.timestamp,
                    previous_structure=prev_high,
                    confirmation_strength=confirmation_strength,
                    volume_confirmation=volume_confirmation,
                    fractal_validation=fractal_validation
                )
                
                breaks.append(structure_break)
        
        return breaks
    
    def _detect_bearish_breaks(self, highs: List[SwingPoint], lows: List[SwingPoint], 
                             df: pd.DataFrame) -> List[StructureBreak]:
        """Detect bearish BOS and CHoCH"""
        breaks = []
        
        if len(lows) < 2:
            return breaks
        
        for i in range(1, len(lows)):
            current_low = lows[i]
            prev_low = lows[i - 1]
            
            # Check if current low breaks previous low
            if current_low.price < prev_low.price:
                # Determine if BOS or CHoCH
                break_type = self._classify_bearish_break(current_low, prev_low, highs)
                
                # Get confirmation data
                confirmation_strength = self._calculate_confirmation_strength(
                    current_low, prev_low, df
                )
                
                volume_confirmation = self._check_volume_confirmation(
                    current_low.index, df
                )
                
                fractal_validation = self._validate_fractal_break(
                    current_low, prev_low, df
                )
                
                structure_break = StructureBreak(
                    break_type=break_type,
                    price=current_low.price,
                    index=current_low.index,
                    timestamp=current_low.timestamp,
                    previous_structure=prev_low,
                    confirmation_strength=confirmation_strength,
                    volume_confirmation=volume_confirmation,
                    fractal_validation=fractal_validation
                )
                
                breaks.append(structure_break)
        
        return breaks
    
    def _classify_bullish_break(self, current_high: SwingPoint, prev_high: SwingPoint, 
                              lows: List[SwingPoint]) -> StructureType:
        """Classify bullish break as BOS or CHoCH"""
        # Find the most recent low between the two highs
        recent_lows = [low for low in lows if prev_high.index < low.index < current_high.index]
        
        if not recent_lows:
            return StructureType.BOS_BULLISH
        
        # Get the lowest point between the highs
        lowest_point = min(recent_lows, key=lambda x: x.price)
        
        # CHoCH: if we had a lower low before breaking higher
        # BOS: continuation of existing trend
        if self.last_trend == "bearish":
            self.last_trend = "bullish"
            return StructureType.CHOCH_BULLISH
        else:
            return StructureType.BOS_BULLISH
    
    def _classify_bearish_break(self, current_low: SwingPoint, prev_low: SwingPoint, 
                              highs: List[SwingPoint]) -> StructureType:
        """Classify bearish break as BOS or CHoCH"""
        # Find the most recent high between the two lows
        recent_highs = [high for high in highs if prev_low.index < high.index < current_low.index]
        
        if not recent_highs:
            return StructureType.BOS_BEARISH
        
        # Get the highest point between the lows
        highest_point = max(recent_highs, key=lambda x: x.price)
        
        # CHoCH: if we had a higher high before breaking lower
        # BOS: continuation of existing trend
        if self.last_trend == "bullish":
            self.last_trend = "bearish"
            return StructureType.CHOCH_BEARISH
        else:
            return StructureType.BOS_BEARISH
    
    def _calculate_confirmation_strength(self, current_point: SwingPoint, 
                                       prev_point: SwingPoint, df: pd.DataFrame) -> float:
        """Calculate confirmation strength of structure break"""
        # Price movement strength
        price_move = abs(current_point.price - prev_point.price) / prev_point.price
        
        # Time factor (longer time = stronger confirmation)
        time_factor = min((current_point.index - prev_point.index) / 20, 1.0)
        
        # Volume factor
        volume_factor = 1.0
        if 'volume' in df.columns:
            avg_volume = df['volume'].rolling(20).mean().iloc[current_point.index]
            current_volume = df['volume'].iloc[current_point.index]
            volume_factor = min(current_volume / avg_volume, 2.0) if avg_volume > 0 else 1.0
        
        # Combined strength
        strength = (price_move * 100 + time_factor + volume_factor) / 3
        return min(strength, 1.0)
    
    def _check_volume_confirmation(self, index: int, df: pd.DataFrame) -> bool:
        """Check if volume confirms the structure break"""
        if 'volume' not in df.columns:
            return False
        
        current_volume = df['volume'].iloc[index]
        avg_volume = df['volume'].rolling(20).mean().iloc[index]
        
        return current_volume > avg_volume * 1.5
    
    def _validate_fractal_break(self, current_point: SwingPoint, 
                              prev_point: SwingPoint, df: pd.DataFrame) -> bool:
        """Validate structure break using fractal analysis"""
        # Simple fractal validation - check if break is sustained
        lookforward = min(5, len(df) - current_point.index - 1)
        
        if lookforward < 2:
            return False
        
        if 'HIGH' in current_point.swing_type.value.upper():
            # For bullish breaks, check if price stays above previous high
            future_lows = df['low'].iloc[current_point.index:current_point.index + lookforward]
            return future_lows.min() > prev_point.price * 0.999  # Allow small retracement
        else:
            # For bearish breaks, check if price stays below previous low
            future_highs = df['high'].iloc[current_point.index:current_point.index + lookforward]
            return future_highs.max() < prev_point.price * 1.001  # Allow small retracement

class SilverBulletDetector:
    """ICT Silver Bullet zones identification"""
    
    def __init__(self):
        self.london_session = (8, 10)  # 8-10 AM London time
        self.new_york_session = (13, 15)  # 1-3 PM London time (8-10 AM NY)
        self.asian_session = (0, 2)  # 12-2 AM London time
        
    def detect_silver_bullet_zones(self, df: pd.DataFrame) -> List[SilverBulletZone]:
        """
        Detect ICT Silver Bullet zones during key sessions
        
        Args:
            df: OHLCV data with datetime index
            
        Returns:
            List of Silver Bullet zones
        """
        zones = []
        
        # Ensure we have datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            return zones
        
        # Detect zones for each session
        london_zones = self._detect_session_zones(df, self.london_session, "London")
        ny_zones = self._detect_session_zones(df, self.new_york_session, "New York")
        asian_zones = self._detect_session_zones(df, self.asian_session, "Asian")
        
        zones.extend(london_zones)
        zones.extend(ny_zones)
        zones.extend(asian_zones)
        
        return zones
    
    def _detect_session_zones(self, df: pd.DataFrame, session_hours: Tuple[int, int], 
                            session_name: str) -> List[SilverBulletZone]:
        """Detect Silver Bullet zones for a specific session"""
        zones = []
        start_hour, end_hour = session_hours
        
        # Group data by date
        df_grouped = df.groupby(df.index.date)
        
        for date, day_data in df_grouped:
            # Filter for session hours
            session_data = day_data[
                (day_data.index.hour >= start_hour) & 
                (day_data.index.hour < end_hour)
            ]
            
            if len(session_data) < 10:  # Need sufficient data
                continue
            
            # Identify potential zones based on price action
            zones_for_day = self._identify_zones_in_session(session_data, session_name)
            zones.extend(zones_for_day)
        
        return zones
    
    def _identify_zones_in_session(self, session_data: pd.DataFrame, 
                                 session_name: str) -> List[SilverBulletZone]:
        """Identify zones within a trading session"""
        zones = []
        
        if len(session_data) < 10:
            return zones
        
        # Look for significant price moves during the session
        session_high = session_data['high'].max()
        session_low = session_data['low'].min()
        session_range = session_high - session_low
        
        # Minimum move threshold (0.5% of session range)
        min_move = session_range * 0.005
        
        # Find rapid price movements
        for i in range(5, len(session_data) - 5):
            current_idx = session_data.index[i]
            
            # Look for rapid moves in 30-minute windows
            window_start = i - 5
            window_end = i + 5
            window_data = session_data.iloc[window_start:window_end]
            
            window_high = window_data['high'].max()
            window_low = window_data['low'].min()
            window_range = window_high - window_low
            
            # Check if this represents a significant move
            if window_range > min_move:
                # Determine direction based on close vs open
                direction = "bullish" if window_data['close'].iloc[-1] > window_data['open'].iloc[0] else "bearish"
                
                # Calculate strength based on speed and volume
                strength = self._calculate_zone_strength(window_data)
                
                # Estimate hit rate based on historical performance
                hit_rate = self._estimate_hit_rate(session_name, direction)
                
                zone = SilverBulletZone(
                    start_time=window_data.index[0],
                    end_time=window_data.index[-1],
                    high=window_high,
                    low=window_low,
                    direction=direction,
                    strength=strength,
                    hit_rate=hit_rate,
                    active=True
                )
                
                zones.append(zone)
        
        return zones
    
    def _calculate_zone_strength(self, window_data: pd.DataFrame) -> float:
        """Calculate the strength of a Silver Bullet zone"""
        # Price movement strength
        price_range = window_data['high'].max() - window_data['low'].min()
        avg_range = window_data['high'].mean() - window_data['low'].mean()
        price_strength = price_range / avg_range if avg_range > 0 else 1.0
        
        # Volume strength (if available)
        volume_strength = 1.0
        if 'volume' in window_data.columns:
            avg_volume = window_data['volume'].mean()
            total_volume = window_data['volume'].sum()
            volume_strength = total_volume / (avg_volume * len(window_data)) if avg_volume > 0 else 1.0
        
        # Time compression (faster moves are stronger)
        time_strength = 1.0 / len(window_data)
        
        # Combined strength
        strength = (price_strength + volume_strength + time_strength) / 3
        return min(strength, 1.0)
    
    def _estimate_hit_rate(self, session_name: str, direction: str) -> float:
        """Estimate hit rate based on session and direction"""
        # Historical hit rates for different sessions (simplified)
        hit_rates = {
            "London": {"bullish": 0.65, "bearish": 0.62},
            "New York": {"bullish": 0.68, "bearish": 0.65},
            "Asian": {"bullish": 0.55, "bearish": 0.58}
        }
        
        return hit_rates.get(session_name, {}).get(direction, 0.60)

class MarketPhaseClassifier:
    """Market phase classification using wavelet transforms"""
    
    def __init__(self):
        self.phase_history = []
        self.wavelet = 'db4'  # Daubechies wavelet
        
    def classify_market_phase(self, df: pd.DataFrame, 
                            structure_breaks: List[StructureBreak]) -> Tuple[MarketPhase, float]:
        """
        Classify current market phase using wavelet analysis
        
        Args:
            df: OHLCV data
            structure_breaks: Recent structure breaks
            
        Returns:
            Tuple of (market phase, confidence)
        """
        if len(df) < 100:
            return MarketPhase.CONTINUATION, 0.5
        
        # Wavelet decomposition of price data
        prices = df['close'].values
        wavelet_analysis = self._perform_wavelet_analysis(prices)
        
        # Volume analysis
        volume_analysis = self._analyze_volume_patterns(df)
        
        # Structure analysis
        structure_analysis = self._analyze_structure_patterns(structure_breaks)
        
        # Combine analyses to determine phase
        phase, confidence = self._determine_phase(wavelet_analysis, volume_analysis, structure_analysis)
        
        return phase, confidence
    
    def _perform_wavelet_analysis(self, prices: np.ndarray) -> Dict[str, Any]:
        """Perform wavelet decomposition analysis"""
        try:
            # Decompose price series
            coeffs = pywt.wavedec(prices, self.wavelet, level=4)
            
            # Analyze different frequency components
            trend = coeffs[0]  # Approximation coefficients (trend)
            details = coeffs[1:]  # Detail coefficients (noise/cycles)
            
            # Calculate trend strength
            trend_slope = np.polyfit(range(len(trend)), trend, 1)[0]
            trend_strength = abs(trend_slope) / np.std(trend) if np.std(trend) > 0 else 0
            
            # Calculate cyclical components
            cycle_energy = [np.sum(d**2) for d in details]
            dominant_cycle = np.argmax(cycle_energy)
            
            # Calculate volatility from detail coefficients
            volatility = np.std(details[0]) if len(details) > 0 else 0
            
            return {
                'trend_slope': trend_slope,
                'trend_strength': trend_strength,
                'dominant_cycle': dominant_cycle,
                'cycle_energy': cycle_energy,
                'volatility': volatility,
                'trend_direction': 'up' if trend_slope > 0 else 'down'
            }
        except Exception as e:
            logger.info(f"Wavelet analysis error: {e}")
            return {
                'trend_slope': 0,
                'trend_strength': 0,
                'dominant_cycle': 0,
                'cycle_energy': [0],
                'volatility': 0,
                'trend_direction': 'neutral'
            }
    
    def _analyze_volume_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns for phase identification"""
        if 'volume' not in df.columns:
            return {'volume_available': False}
        
        volume = df['volume'].values
        prices = df['close'].values
        
        # Volume trend
        volume_ma_short = pd.Series(volume).rolling(10).mean()
        volume_ma_long = pd.Series(volume).rolling(30).mean()
        volume_trend = 'increasing' if volume_ma_short.iloc[-1] > volume_ma_long.iloc[-1] else 'decreasing'
        
        # Price-volume relationship
        price_changes = np.diff(prices)
        volume_changes = np.diff(volume)
        
        # Correlation between price and volume changes
        pv_correlation = np.corrcoef(price_changes[-50:], volume_changes[-50:])[0, 1] if len(price_changes) >= 50 else 0
        
        # Volume spikes
        volume_std = np.std(volume)
        volume_mean = np.mean(volume)
        recent_spikes = np.sum(volume[-10:] > volume_mean + 2 * volume_std)
        
        return {
            'volume_available': True,
            'volume_trend': volume_trend,
            'pv_correlation': pv_correlation,
            'volume_spikes': recent_spikes,
            'volume_strength': volume_ma_short.iloc[-1] / volume_ma_long.iloc[-1] if volume_ma_long.iloc[-1] > 0 else 1.0
        }
    
    def _analyze_structure_patterns(self, structure_breaks: List[StructureBreak]) -> Dict[str, Any]:
        """Analyze structure break patterns"""
        if not structure_breaks:
            return {'breaks_available': False}
        
        recent_breaks = structure_breaks[-10:]  # Last 10 breaks
        
        # Count break types
        bos_count = len([b for b in recent_breaks if 'BOS' in b.break_type.value])
        choch_count = len([b for b in recent_breaks if 'CHOCH' in b.break_type.value])
        
        # Direction analysis
        bullish_breaks = len([b for b in recent_breaks if 'BULLISH' in b.break_type.value])
        bearish_breaks = len([b for b in recent_breaks if 'BEARISH' in b.break_type.value])
        
        # Time between breaks
        if len(recent_breaks) > 1:
            time_diffs = [(recent_breaks[i].index - recent_breaks[i-1].index) 
                         for i in range(1, len(recent_breaks))]
            avg_time_between_breaks = np.mean(time_diffs)
        else:
            avg_time_between_breaks = 0
        
        return {
            'breaks_available': True,
            'bos_count': bos_count,
            'choch_count': choch_count,
            'bullish_breaks': bullish_breaks,
            'bearish_breaks': bearish_breaks,
            'break_frequency': len(recent_breaks),
            'avg_time_between_breaks': avg_time_between_breaks
        }
    
    def _determine_phase(self, wavelet_analysis: Dict[str, Any], 
                        volume_analysis: Dict[str, Any], 
                        structure_analysis: Dict[str, Any]) -> Tuple[MarketPhase, float]:
        """Determine market phase from combined analysis"""
        phase_scores = {
            MarketPhase.ACCUMULATION: 0,
            MarketPhase.MARKUP: 0,
            MarketPhase.DISTRIBUTION: 0,
            MarketPhase.MARKDOWN: 0,
            MarketPhase.REACCUMULATION: 0,
            MarketPhase.REDISTRIBUTION: 0,
            MarketPhase.CONTINUATION: 0,
            MarketPhase.PULLBACK: 0
        }
        
        # Wavelet-based scoring
        trend_strength = wavelet_analysis['trend_strength']
        trend_direction = wavelet_analysis['trend_direction']
        volatility = wavelet_analysis['volatility']
        
        if trend_strength > 0.5:
            if trend_direction == 'up':
                phase_scores[MarketPhase.MARKUP] += 0.3
                phase_scores[MarketPhase.CONTINUATION] += 0.2
            else:
                phase_scores[MarketPhase.MARKDOWN] += 0.3
                phase_scores[MarketPhase.CONTINUATION] += 0.2
        else:
            phase_scores[MarketPhase.ACCUMULATION] += 0.2
            phase_scores[MarketPhase.DISTRIBUTION] += 0.2
        
        # Volume-based scoring
        if volume_analysis.get('volume_available'):
            volume_trend = volume_analysis['volume_trend']
            pv_correlation = volume_analysis.get('pv_correlation', 0)
            
            if volume_trend == 'increasing' and pv_correlation > 0.3:
                if trend_direction == 'up':
                    phase_scores[MarketPhase.MARKUP] += 0.2
                else:
                    phase_scores[MarketPhase.MARKDOWN] += 0.2
            elif volume_trend == 'decreasing':
                phase_scores[MarketPhase.ACCUMULATION] += 0.15
                phase_scores[MarketPhase.DISTRIBUTION] += 0.15
        
        # Structure-based scoring
        if structure_analysis.get('breaks_available'):
            choch_count = structure_analysis['choch_count']
            bos_count = structure_analysis['bos_count']
            
            if choch_count > bos_count:
                phase_scores[MarketPhase.ACCUMULATION] += 0.2
                phase_scores[MarketPhase.DISTRIBUTION] += 0.2
            elif bos_count > choch_count:
                phase_scores[MarketPhase.CONTINUATION] += 0.3
        
        # Find phase with highest score
        best_phase = max(phase_scores, key=phase_scores.get)
        confidence = phase_scores[best_phase]
        
        # Normalize confidence
        confidence = min(confidence, 1.0)
        
        return best_phase, confidence

class MarketStructureOracle:
    """Main oracle combining all market structure analysis components"""
    
    def __init__(self, lookback_period: int = 5):
        self.swing_detector = SwingPointDetector(lookback_period)
        self.structure_detector = StructureBreakDetector()
        self.silver_bullet_detector = SilverBulletDetector()
        self.phase_classifier = MarketPhaseClassifier()
        
    def analyze_market_structure(self, df: pd.DataFrame) -> MarketStructureState:
        """
        Comprehensive market structure analysis
        
        Args:
            df: OHLCV data with datetime index
            
        Returns:
            Complete market structure state
        """
        # Detect swing points
        swing_points = self.swing_detector.detect_swing_points(df)
        
        # Detect structure breaks
        structure_breaks = self.structure_detector.detect_structure_breaks(swing_points, df)
        
        # Detect Silver Bullet zones
        silver_bullet_zones = self.silver_bullet_detector.detect_silver_bullet_zones(df)
        
        # Classify market phase
        current_phase, phase_confidence = self.phase_classifier.classify_market_phase(df, structure_breaks)
        
        # Determine trend direction
        trend_direction = self._determine_trend_direction(structure_breaks, swing_points)
        
        # Extract liquidity levels
        liquidity_levels = self._extract_liquidity_levels(swing_points)
        
        return MarketStructureState(
            trend_direction=trend_direction,
            structure_breaks=structure_breaks,
            swing_points=swing_points,
            current_phase=current_phase,
            phase_confidence=phase_confidence,
            liquidity_levels=liquidity_levels,
            silver_bullet_zones=silver_bullet_zones
        )
    
    def _determine_trend_direction(self, structure_breaks: List[StructureBreak], 
                                 swing_points: List[SwingPoint]) -> str:
        """Determine overall trend direction"""
        if not structure_breaks:
            return "neutral"
        
        # Look at recent structure breaks
        recent_breaks = structure_breaks[-5:]
        
        bullish_breaks = len([b for b in recent_breaks if 'BULLISH' in b.break_type.value])
        bearish_breaks = len([b for b in recent_breaks if 'BEARISH' in b.break_type.value])
        
        if bullish_breaks > bearish_breaks:
            return "bullish"
        elif bearish_breaks > bullish_breaks:
            return "bearish"
        else:
            return "neutral"
    
    def _extract_liquidity_levels(self, swing_points: List[SwingPoint]) -> List[float]:
        """Extract key liquidity levels from swing points"""
        if not swing_points:
            return []
        
        # Get swing points with high liquidity levels
        high_liquidity_points = [sp for sp in swing_points if sp.liquidity_level >= 2]
        
        # Extract unique price levels
        liquidity_levels = list(set([sp.price for sp in high_liquidity_points]))
        
        # Sort by liquidity strength
        liquidity_with_strength = [(level, max([sp.liquidity_level for sp in high_liquidity_points if sp.price == level])) 
                                  for level in liquidity_levels]
        
        # Sort by strength and return top levels
        liquidity_with_strength.sort(key=lambda x: x[1], reverse=True)
        
        return [level for level, strength in liquidity_with_strength[:10]]
    
    def get_trading_signals(self, market_state: MarketStructureState) -> Dict[str, Any]:
        """Generate trading signals from market structure analysis"""
        signals = {
            'trend_signal': self._generate_trend_signal(market_state),
            'structure_signal': self._generate_structure_signal(market_state),
            'phase_signal': self._generate_phase_signal(market_state),
            'liquidity_signal': self._generate_liquidity_signal(market_state),
            'silver_bullet_signal': self._generate_silver_bullet_signal(market_state)
        }
        
        # Overall signal strength
        signal_strengths = [abs(s.get('strength', 0)) for s in signals.values() if isinstance(s, dict)]
        overall_strength = np.mean(signal_strengths) if signal_strengths else 0
        
        signals['overall'] = {
            'strength': overall_strength,
            'direction': market_state.trend_direction,
            'confidence': market_state.phase_confidence,
            'quality': 'high' if overall_strength > 0.7 else 'medium' if overall_strength > 0.4 else 'low'
        }
        
        return signals
    
    def _generate_trend_signal(self, market_state: MarketStructureState) -> Dict[str, Any]:
        """Generate trend-based signal"""
        direction = market_state.trend_direction
        
        # Count recent structure breaks in trend direction
        recent_breaks = market_state.structure_breaks[-5:] if market_state.structure_breaks else []
        
        if direction == "bullish":
            trend_breaks = len([b for b in recent_breaks if 'BULLISH' in b.break_type.value])
            strength = min(trend_breaks / 3, 1.0)  # Max strength with 3+ breaks
        elif direction == "bearish":
            trend_breaks = len([b for b in recent_breaks if 'BEARISH' in b.break_type.value])
            strength = min(trend_breaks / 3, 1.0)
        else:
            strength = 0
        
        return {
            'direction': direction,
            'strength': strength,
            'signal': 'buy' if direction == 'bullish' and strength > 0.5 else 'sell' if direction == 'bearish' and strength > 0.5 else 'neutral'
        }
    
    def _generate_structure_signal(self, market_state: MarketStructureState) -> Dict[str, Any]:
        """Generate structure break signal"""
        if not market_state.structure_breaks:
            return {'signal': 'neutral', 'strength': 0}
        
        latest_break = market_state.structure_breaks[-1]
        
        # Signal strength based on confirmation
        strength = latest_break.confirmation_strength
        if latest_break.volume_confirmation:
            strength += 0.2
        if latest_break.fractal_validation:
            strength += 0.2
        
        strength = min(strength, 1.0)
        
        if 'BULLISH' in latest_break.break_type.value:
            signal = 'buy' if strength > 0.5 else 'neutral'
        elif 'BEARISH' in latest_break.break_type.value:
            signal = 'sell' if strength > 0.5 else 'neutral'
        else:
            signal = 'neutral'
        
        return {
            'signal': signal,
            'strength': strength,
            'break_type': latest_break.break_type.value,
            'confirmation': latest_break.volume_confirmation and latest_break.fractal_validation
        }
    
    def _generate_phase_signal(self, market_state: MarketStructureState) -> Dict[str, Any]:
        """Generate phase-based signal"""
        phase = market_state.current_phase
        confidence = market_state.phase_confidence
        
        # Phase-based signals
        phase_signals = {
            MarketPhase.ACCUMULATION: 'buy_setup',
            MarketPhase.MARKUP: 'buy',
            MarketPhase.DISTRIBUTION: 'sell_setup',
            MarketPhase.MARKDOWN: 'sell',
            MarketPhase.REACCUMULATION: 'buy_setup',
            MarketPhase.REDISTRIBUTION: 'sell_setup',
            MarketPhase.CONTINUATION: 'hold',
            MarketPhase.PULLBACK: 'wait'
        }
        
        signal = phase_signals.get(phase, 'neutral')
        
        return {
            'signal': signal,
            'phase': phase.value,
            'confidence': confidence,
            'strength': confidence
        }
    
    def _generate_liquidity_signal(self, market_state: MarketStructureState) -> Dict[str, Any]:
        """Generate liquidity-based signal"""
        if not market_state.liquidity_levels:
            return {'signal': 'neutral', 'strength': 0}
        
        # This would require current price to determine proximity to liquidity
        # For now, return basic signal based on number of liquidity levels
        num_levels = len(market_state.liquidity_levels)
        strength = min(num_levels / 5, 1.0)  # Max strength with 5+ levels
        
        return {
            'signal': 'watch_levels',
            'strength': strength,
            'levels_count': num_levels,
            'key_levels': market_state.liquidity_levels[:3]  # Top 3 levels
        }
    
    def _generate_silver_bullet_signal(self, market_state: MarketStructureState) -> Dict[str, Any]:
        """Generate Silver Bullet zone signal"""
        active_zones = [zone for zone in market_state.silver_bullet_zones if zone.active]
        
        if not active_zones:
            return {'signal': 'neutral', 'strength': 0}
        
        # Find strongest active zone
        strongest_zone = max(active_zones, key=lambda x: x.strength * x.hit_rate)
        
        signal = 'buy' if strongest_zone.direction == 'bullish' else 'sell'
        strength = strongest_zone.strength * strongest_zone.hit_rate
        
        return {
            'signal': signal,
            'strength': strength,
            'zone_direction': strongest_zone.direction,
            'hit_rate': strongest_zone.hit_rate,
            'active_zones': len(active_zones)
        }
