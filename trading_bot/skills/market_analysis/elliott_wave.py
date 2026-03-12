"""
Skill #3: Elliott Wave Detector
===============================

Automated Elliott Wave counting and projection system.
Identifies impulse waves (1-5) and corrective waves (A-B-C).
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WaveType(Enum):
    """Type of Elliott Wave."""
    IMPULSE = "impulse"  # 5-wave pattern
    CORRECTIVE = "corrective"  # 3-wave pattern
    DIAGONAL = "diagonal"  # Ending/leading diagonal
    TRIANGLE = "triangle"  # Consolidation pattern
    FLAT = "flat"  # Flat correction
    ZIGZAG = "zigzag"  # Sharp correction
    COMPLEX = "complex"  # Complex correction


class WaveDirection(Enum):
    """Direction of wave."""
    UP = "up"
    DOWN = "down"


class WaveDegree(Enum):
    """Degree/timeframe of wave."""
    GRAND_SUPERCYCLE = "grand_supercycle"
    SUPERCYCLE = "supercycle"
    CYCLE = "cycle"
    PRIMARY = "primary"
    INTERMEDIATE = "intermediate"
    MINOR = "minor"
    MINUTE = "minute"
    MINUETTE = "minuette"
    SUBMINUETTE = "subminuette"


@dataclass
class WavePoint:
    """A point in a wave structure."""
    timestamp: datetime
    price: float
    index: int
    label: str  # '1', '2', '3', '4', '5', 'A', 'B', 'C', etc.


@dataclass
class Wave:
    """Represents a single wave."""
    start: WavePoint
    end: WavePoint
    label: str
    wave_type: WaveType
    direction: WaveDirection
    degree: WaveDegree
    fibonacci_ratio: Optional[float] = None
    is_extended: bool = False
    sub_waves: List['Wave'] = field(default_factory=list)


@dataclass
class WaveCount:
    """Complete wave count analysis."""
    waves: List[Wave]
    current_wave: str
    wave_type: WaveType
    direction: WaveDirection
    degree: WaveDegree
    confidence: float
    alternate_counts: List['WaveCount'] = field(default_factory=list)


@dataclass
class WaveProjection:
    """Price projection based on wave analysis."""
    target_prices: List[float]
    fibonacci_levels: Dict[str, float]
    most_likely_target: float
    invalidation_level: float
    time_projection: Optional[int] = None  # Bars to target


@dataclass
class ElliottWaveAnalysis:
    """Complete Elliott Wave analysis result."""
    wave_count: WaveCount
    projection: WaveProjection
    current_position: str  # e.g., "In wave 3 of impulse"
    trading_recommendation: str
    risk_reward: float
    confidence: float


class ElliottWaveDetector:
    """
    Advanced Elliott Wave Detection System.
    
    Automatically identifies wave patterns and provides
    price projections based on Fibonacci relationships.
    """
    
    # Fibonacci ratios for wave relationships
    FIB_RATIOS = {
        'wave2_retracement': [0.382, 0.5, 0.618, 0.786],
        'wave3_extension': [1.618, 2.0, 2.618, 3.0],
        'wave4_retracement': [0.236, 0.382, 0.5],
        'wave5_extension': [0.618, 1.0, 1.618],
        'waveA_retracement': [0.382, 0.5, 0.618],
        'waveB_retracement': [0.382, 0.5, 0.618, 0.786],
        'waveC_extension': [1.0, 1.272, 1.618],
    }
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_wave_size = self.config.get('min_wave_size', 0.01)  # 1% minimum
            self.zigzag_threshold = self.config.get('zigzag_threshold', 0.02)
            self.wave_history: List[WaveCount] = []
        
            logger.info("ElliottWaveDetector initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        timestamps: List[datetime],
        degree: WaveDegree = WaveDegree.MINOR
    ) -> ElliottWaveAnalysis:
        """
        Perform complete Elliott Wave analysis.
        
        Args:
            highs: Array of high prices
            lows: Array of low prices
            closes: Array of close prices
            timestamps: List of timestamps
            degree: Wave degree to analyze
            
        Returns:
            ElliottWaveAnalysis with complete analysis
        """
        # Find swing points (zigzag)
        try:
            swing_points = self._find_swing_points(highs, lows, timestamps)
        
            if len(swing_points) < 5:
                return self._create_insufficient_data_result()
        
            # Identify wave patterns
            wave_count = self._identify_waves(swing_points, degree)
        
            # Calculate projections
            projection = self._calculate_projections(wave_count, closes[-1])
        
            # Determine current position
            current_position = self._get_current_position(wave_count)
        
            # Generate trading recommendation
            recommendation = self._get_trading_recommendation(wave_count, projection)
        
            # Calculate risk/reward
            risk_reward = self._calculate_risk_reward(
                closes[-1], projection, wave_count
            )
        
            # Calculate confidence
            confidence = self._calculate_confidence(wave_count)
        
            return ElliottWaveAnalysis(
                wave_count=wave_count,
                projection=projection,
                current_position=current_position,
                trading_recommendation=recommendation,
                risk_reward=risk_reward,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _find_swing_points(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        timestamps: List[datetime]
    ) -> List[WavePoint]:
        """Find significant swing highs and lows using zigzag."""
        try:
            swing_points = []
            n = len(highs)
        
            if n < 5:
                return swing_points
        
            # Calculate threshold based on ATR
            atr = self._calculate_atr(highs, lows, closes=None, period=14)
            threshold = max(self.zigzag_threshold, atr * 2 / np.mean(highs))
        
            # Initialize
            last_swing_high = highs[0]
            last_swing_low = lows[0]
            last_swing_high_idx = 0
            last_swing_low_idx = 0
            trend = 0  # 1 = up, -1 = down, 0 = undefined
        
            for i in range(1, n):
                if trend >= 0:  # Looking for swing high
                    if highs[i] > last_swing_high:
                        last_swing_high = highs[i]
                        last_swing_high_idx = i
                    elif (last_swing_high - lows[i]) / last_swing_high >= threshold:
                        # Swing high confirmed
                        swing_points.append(WavePoint(
                            timestamp=timestamps[last_swing_high_idx],
                            price=last_swing_high,
                            index=last_swing_high_idx,
                            label='H'
                        ))
                        last_swing_low = lows[i]
                        last_swing_low_idx = i
                        trend = -1
            
                if trend <= 0:  # Looking for swing low
                    if lows[i] < last_swing_low:
                        last_swing_low = lows[i]
                        last_swing_low_idx = i
                    elif (highs[i] - last_swing_low) / last_swing_low >= threshold:
                        # Swing low confirmed
                        swing_points.append(WavePoint(
                            timestamp=timestamps[last_swing_low_idx],
                            price=last_swing_low,
                            index=last_swing_low_idx,
                            label='L'
                        ))
                        last_swing_high = highs[i]
                        last_swing_high_idx = i
                        trend = 1
        
            return swing_points
        except Exception as e:
            logger.error(f"Error in _find_swing_points: {e}")
            raise
    
    def _calculate_atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: Optional[np.ndarray],
        period: int = 14
    ) -> float:
        """Calculate Average True Range."""
        try:
            if closes is None:
                closes = (highs + lows) / 2
        
            tr = np.maximum(
                highs[1:] - lows[1:],
                np.maximum(
                    np.abs(highs[1:] - closes[:-1]),
                    np.abs(lows[1:] - closes[:-1])
                )
            )
        
            if len(tr) < period:
                return np.mean(tr) if len(tr) > 0 else 0
        
            return np.mean(tr[-period:])
        except Exception as e:
            logger.error(f"Error in _calculate_atr: {e}")
            raise
    
    def _identify_waves(
        self,
        swing_points: List[WavePoint],
        degree: WaveDegree
    ) -> WaveCount:
        """Identify Elliott Wave pattern from swing points."""
        try:
            if len(swing_points) < 5:
                return self._create_empty_wave_count(degree)
        
            # Try to identify impulse wave (5 waves)
            impulse_count = self._try_impulse_count(swing_points, degree)
        
            # Try to identify corrective wave (3 waves)
            corrective_count = self._try_corrective_count(swing_points, degree)
        
            # Choose best count based on rules validation
            impulse_score = self._validate_impulse_rules(impulse_count)
            corrective_score = self._validate_corrective_rules(corrective_count)
        
            if impulse_score >= corrective_score:
                main_count = impulse_count
                main_count.alternate_counts = [corrective_count]
            else:
                main_count = corrective_count
                main_count.alternate_counts = [impulse_count]
        
            return main_count
        except Exception as e:
            logger.error(f"Error in _identify_waves: {e}")
            raise
    
    def _try_impulse_count(
        self,
        swing_points: List[WavePoint],
        degree: WaveDegree
    ) -> WaveCount:
        """Try to fit an impulse wave pattern."""
        try:
            waves = []
        
            # Need at least 5 swing points for impulse
            if len(swing_points) < 5:
                return self._create_empty_wave_count(degree)
        
            # Determine direction from first two points
            if swing_points[1].price > swing_points[0].price:
                direction = WaveDirection.UP
            else:
                direction = WaveDirection.DOWN
        
            # Label waves 1-5
            labels = ['1', '2', '3', '4', '5']
        
            for i in range(min(5, len(swing_points) - 1)):
                start = swing_points[i]
                end = swing_points[i + 1]
            
                wave_direction = WaveDirection.UP if end.price > start.price else WaveDirection.DOWN
            
                wave = Wave(
                    start=WavePoint(
                        timestamp=start.timestamp,
                        price=start.price,
                        index=start.index,
                        label=labels[i] if i < len(labels) else str(i + 1)
                    ),
                    end=WavePoint(
                        timestamp=end.timestamp,
                        price=end.price,
                        index=end.index,
                        label=labels[i] if i < len(labels) else str(i + 1)
                    ),
                    label=labels[i] if i < len(labels) else str(i + 1),
                    wave_type=WaveType.IMPULSE,
                    direction=wave_direction,
                    degree=degree
                )
            
                # Calculate Fibonacci ratio
                if i > 0 and waves:
                    wave.fibonacci_ratio = self._calculate_fib_ratio(waves[-1], wave)
            
                # Check for extension (wave 3 typically)
                if i == 2:  # Wave 3
                    wave1_size = abs(waves[0].end.price - waves[0].start.price)
                    wave3_size = abs(wave.end.price - wave.start.price)
                    if wave3_size > wave1_size * 1.618:
                        wave.is_extended = True
            
                waves.append(wave)
        
            # Determine current wave
            current_wave = labels[len(waves) - 1] if waves else '1'
        
            return WaveCount(
                waves=waves,
                current_wave=current_wave,
                wave_type=WaveType.IMPULSE,
                direction=direction,
                degree=degree,
                confidence=0.5
            )
        except Exception as e:
            logger.error(f"Error in _try_impulse_count: {e}")
            raise
    
    def _try_corrective_count(
        self,
        swing_points: List[WavePoint],
        degree: WaveDegree
    ) -> WaveCount:
        """Try to fit a corrective wave pattern."""
        try:
            waves = []
        
            if len(swing_points) < 3:
                return self._create_empty_wave_count(degree)
        
            # Determine direction
            if swing_points[1].price > swing_points[0].price:
                direction = WaveDirection.UP
            else:
                direction = WaveDirection.DOWN
        
            # Label waves A-B-C
            labels = ['A', 'B', 'C']
        
            for i in range(min(3, len(swing_points) - 1)):
                start = swing_points[i]
                end = swing_points[i + 1]
            
                wave_direction = WaveDirection.UP if end.price > start.price else WaveDirection.DOWN
            
                wave = Wave(
                    start=WavePoint(
                        timestamp=start.timestamp,
                        price=start.price,
                        index=start.index,
                        label=labels[i]
                    ),
                    end=WavePoint(
                        timestamp=end.timestamp,
                        price=end.price,
                        index=end.index,
                        label=labels[i]
                    ),
                    label=labels[i],
                    wave_type=WaveType.CORRECTIVE,
                    direction=wave_direction,
                    degree=degree
                )
            
                if i > 0 and waves:
                    wave.fibonacci_ratio = self._calculate_fib_ratio(waves[-1], wave)
            
                waves.append(wave)
        
            current_wave = labels[len(waves) - 1] if waves else 'A'
        
            return WaveCount(
                waves=waves,
                current_wave=current_wave,
                wave_type=WaveType.CORRECTIVE,
                direction=direction,
                degree=degree,
                confidence=0.5
            )
        except Exception as e:
            logger.error(f"Error in _try_corrective_count: {e}")
            raise
    
    def _calculate_fib_ratio(self, prev_wave: Wave, current_wave: Wave) -> float:
        """Calculate Fibonacci ratio between waves."""
        try:
            prev_size = abs(prev_wave.end.price - prev_wave.start.price)
            curr_size = abs(current_wave.end.price - current_wave.start.price)
        
            if prev_size == 0:
                return 0
        
            return curr_size / prev_size
        except Exception as e:
            logger.error(f"Error in _calculate_fib_ratio: {e}")
            raise
    
    def _validate_impulse_rules(self, wave_count: WaveCount) -> float:
        """Validate impulse wave rules and return score."""
        try:
            if not wave_count.waves or len(wave_count.waves) < 5:
                return 0.0
        
            score = 0.5  # Base score
            waves = wave_count.waves
        
            # Rule 1: Wave 2 cannot retrace more than 100% of wave 1
            if len(waves) >= 2:
                wave1_start = waves[0].start.price
                wave1_end = waves[0].end.price
                wave2_end = waves[1].end.price
            
                if wave_count.direction == WaveDirection.UP:
                    if wave2_end > wave1_start:
                        score += 0.1
                else:
                    if wave2_end < wave1_start:
                        score += 0.1
        
            # Rule 2: Wave 3 cannot be the shortest
            if len(waves) >= 5:
                wave_sizes = [abs(w.end.price - w.start.price) for w in waves]
                impulse_sizes = [wave_sizes[0], wave_sizes[2], wave_sizes[4]]
                if wave_sizes[2] != min(impulse_sizes):
                    score += 0.15
        
            # Rule 3: Wave 4 cannot overlap wave 1
            if len(waves) >= 4:
                wave1_end = waves[0].end.price
                wave4_end = waves[3].end.price
            
                if wave_count.direction == WaveDirection.UP:
                    if wave4_end > wave1_end:
                        score += 0.1
                else:
                    if wave4_end < wave1_end:
                        score += 0.1
        
            # Guideline: Wave 3 is often extended (1.618x wave 1)
            if len(waves) >= 3:
                wave1_size = abs(waves[0].end.price - waves[0].start.price)
                wave3_size = abs(waves[2].end.price - waves[2].start.price)
                if wave3_size >= wave1_size * 1.5:
                    score += 0.1
        
            return min(1.0, score)
        except Exception as e:
            logger.error(f"Error in _validate_impulse_rules: {e}")
            raise
    
    def _validate_corrective_rules(self, wave_count: WaveCount) -> float:
        """Validate corrective wave rules and return score."""
        try:
            if not wave_count.waves or len(wave_count.waves) < 3:
                return 0.0
        
            score = 0.5
            waves = wave_count.waves
        
            # Wave B typically retraces 38.2%-78.6% of wave A
            if len(waves) >= 2:
                wave_a_size = abs(waves[0].end.price - waves[0].start.price)
                wave_b_size = abs(waves[1].end.price - waves[1].start.price)
            
                if wave_a_size > 0:
                    b_retracement = wave_b_size / wave_a_size
                    if 0.382 <= b_retracement <= 0.786:
                        score += 0.15
        
            # Wave C often equals wave A or is 1.618x wave A
            if len(waves) >= 3:
                wave_a_size = abs(waves[0].end.price - waves[0].start.price)
                wave_c_size = abs(waves[2].end.price - waves[2].start.price)
            
                if wave_a_size > 0:
                    c_ratio = wave_c_size / wave_a_size
                    if 0.9 <= c_ratio <= 1.1 or 1.5 <= c_ratio <= 1.7:
                        score += 0.15
        
            return min(1.0, score)
        except Exception as e:
            logger.error(f"Error in _validate_corrective_rules: {e}")
            raise
    
    def _calculate_projections(
        self,
        wave_count: WaveCount,
        current_price: float
    ) -> WaveProjection:
        """Calculate price projections based on wave count."""
        try:
            targets = []
            fib_levels = {}
        
            if not wave_count.waves:
                return WaveProjection(
                    target_prices=[current_price],
                    fibonacci_levels={},
                    most_likely_target=current_price,
                    invalidation_level=current_price
                )
        
            waves = wave_count.waves
        
            if wave_count.wave_type == WaveType.IMPULSE:
                # Project based on current wave
                if wave_count.current_wave in ['1', '2']:
                    # Project wave 3 targets
                    wave1_size = abs(waves[0].end.price - waves[0].start.price)
                    wave1_end = waves[0].end.price
                
                    for ratio in [1.618, 2.0, 2.618]:
                        if wave_count.direction == WaveDirection.UP:
                            target = wave1_end + wave1_size * ratio
                        else:
                            target = wave1_end - wave1_size * ratio
                        targets.append(target)
                        fib_levels[f'wave3_{ratio}'] = target
                
                elif wave_count.current_wave in ['3', '4']:
                    # Project wave 5 targets
                    if len(waves) >= 3:
                        wave1_size = abs(waves[0].end.price - waves[0].start.price)
                        wave3_end = waves[2].end.price
                    
                        for ratio in [0.618, 1.0, 1.618]:
                            if wave_count.direction == WaveDirection.UP:
                                target = wave3_end + wave1_size * ratio
                            else:
                                target = wave3_end - wave1_size * ratio
                            targets.append(target)
                            fib_levels[f'wave5_{ratio}'] = target
        
            else:  # Corrective
                if wave_count.current_wave in ['A', 'B']:
                    # Project wave C
                    if waves:
                        wave_a_size = abs(waves[0].end.price - waves[0].start.price)
                        wave_a_start = waves[0].start.price
                    
                        for ratio in [1.0, 1.272, 1.618]:
                            if wave_count.direction == WaveDirection.DOWN:
                                target = wave_a_start - wave_a_size * ratio
                            else:
                                target = wave_a_start + wave_a_size * ratio
                            targets.append(target)
                            fib_levels[f'waveC_{ratio}'] = target
        
            # Calculate invalidation level
            invalidation = self._calculate_invalidation(wave_count)
        
            # Most likely target (middle target)
            most_likely = targets[len(targets) // 2] if targets else current_price
        
            return WaveProjection(
                target_prices=targets if targets else [current_price],
                fibonacci_levels=fib_levels,
                most_likely_target=most_likely,
                invalidation_level=invalidation
            )
        except Exception as e:
            logger.error(f"Error in _calculate_projections: {e}")
            raise
    
    def _calculate_invalidation(self, wave_count: WaveCount) -> float:
        """Calculate the price level that would invalidate the wave count."""
        try:
            if not wave_count.waves:
                return 0.0
        
            waves = wave_count.waves
        
            if wave_count.wave_type == WaveType.IMPULSE:
                # Wave 2 cannot go below wave 1 start
                if wave_count.current_wave == '2':
                    return waves[0].start.price
                # Wave 4 cannot overlap wave 1 territory
                elif wave_count.current_wave == '4' and len(waves) >= 1:
                    return waves[0].end.price
        
            # Default: first wave start
            return waves[0].start.price
        except Exception as e:
            logger.error(f"Error in _calculate_invalidation: {e}")
            raise
    
    def _get_current_position(self, wave_count: WaveCount) -> str:
        """Get human-readable current position description."""
        try:
            wave_type = "impulse" if wave_count.wave_type == WaveType.IMPULSE else "correction"
            direction = "bullish" if wave_count.direction == WaveDirection.UP else "bearish"
        
            return f"In wave {wave_count.current_wave} of {direction} {wave_type}"
        except Exception as e:
            logger.error(f"Error in _get_current_position: {e}")
            raise
    
    def _get_trading_recommendation(
        self,
        wave_count: WaveCount,
        projection: WaveProjection
    ) -> str:
        """Generate trading recommendation based on wave analysis."""
        try:
            current = wave_count.current_wave
            direction = wave_count.direction
        
            if wave_count.wave_type == WaveType.IMPULSE:
                if current == '2':
                    if direction == WaveDirection.UP:
                        return "BUY: Wave 2 pullback complete. Enter long for wave 3."
                    else:
                        return "SELL: Wave 2 pullback complete. Enter short for wave 3."
            
                elif current == '3':
                    if direction == WaveDirection.UP:
                        return "HOLD LONG: In wave 3 (strongest wave). Trail stops."
                    else:
                        return "HOLD SHORT: In wave 3 (strongest wave). Trail stops."
            
                elif current == '4':
                    if direction == WaveDirection.UP:
                        return "PARTIAL EXIT: Wave 4 correction. Consider adding on dip."
                    else:
                        return "PARTIAL EXIT: Wave 4 correction. Consider adding on rally."
            
                elif current == '5':
                    return "PREPARE TO EXIT: Wave 5 completing. Watch for reversal signs."
        
            else:  # Corrective
                if current == 'C':
                    return "PREPARE FOR REVERSAL: Wave C completing. New impulse expected."
                else:
                    return "WAIT: Correction in progress. Wait for completion."
        
            return "NEUTRAL: Unclear wave structure. Wait for clarity."
        except Exception as e:
            logger.error(f"Error in _get_trading_recommendation: {e}")
            raise
    
    def _calculate_risk_reward(
        self,
        current_price: float,
        projection: WaveProjection,
        wave_count: WaveCount
    ) -> float:
        """Calculate risk/reward ratio."""
        try:
            if not projection.target_prices:
                return 0.0
        
            target = projection.most_likely_target
            invalidation = projection.invalidation_level
        
            reward = abs(target - current_price)
            risk = abs(current_price - invalidation)
        
            if risk == 0:
                return 0.0
        
            return reward / risk
        except Exception as e:
            logger.error(f"Error in _calculate_risk_reward: {e}")
            raise
    
    def _calculate_confidence(self, wave_count: WaveCount) -> float:
        """Calculate overall confidence in the wave count."""
        try:
            base_confidence = wave_count.confidence
        
            # Adjust based on number of waves identified
            if len(wave_count.waves) >= 5:
                base_confidence += 0.1
        
            # Adjust based on Fibonacci relationships
            fib_matches = 0
            for wave in wave_count.waves:
                if wave.fibonacci_ratio:
                    # Check if ratio is close to a Fibonacci number
                    fib_numbers = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618]
                    for fib in fib_numbers:
                        if abs(wave.fibonacci_ratio - fib) < 0.1:
                            fib_matches += 1
                            break
        
            base_confidence += fib_matches * 0.05
        
            return min(1.0, base_confidence)
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise
    
    def _create_empty_wave_count(self, degree: WaveDegree) -> WaveCount:
        """Create an empty wave count."""
        return WaveCount(
            waves=[],
            current_wave='?',
            wave_type=WaveType.IMPULSE,
            direction=WaveDirection.UP,
            degree=degree,
            confidence=0.0
        )
    
    def _create_insufficient_data_result(self) -> ElliottWaveAnalysis:
        """Create result for insufficient data."""
        return ElliottWaveAnalysis(
            wave_count=WaveCount(
                waves=[],
                current_wave='?',
                wave_type=WaveType.IMPULSE,
                direction=WaveDirection.UP,
                degree=WaveDegree.MINOR,
                confidence=0.0
            ),
            projection=WaveProjection(
                target_prices=[],
                fibonacci_levels={},
                most_likely_target=0.0,
                invalidation_level=0.0
            ),
            current_position="Insufficient data for wave analysis",
            trading_recommendation="WAIT: Need more price data",
            risk_reward=0.0,
            confidence=0.0
        )
