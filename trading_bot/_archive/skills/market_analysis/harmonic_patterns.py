"""
Skill #4: Harmonic Pattern Scanner
==================================

Detects harmonic patterns: Gartley, Butterfly, Bat, Crab, Shark, Cypher.
Uses precise Fibonacci ratios for pattern identification.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HarmonicPatternType(Enum):
    """Types of harmonic patterns."""
    GARTLEY = "gartley"
    BUTTERFLY = "butterfly"
    BAT = "bat"
    CRAB = "crab"
    SHARK = "shark"
    CYPHER = "cypher"
    ABCD = "abcd"
    THREE_DRIVES = "three_drives"


class PatternDirection(Enum):
    """Direction of the pattern."""
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass
class PatternPoint:
    """A point in a harmonic pattern (X, A, B, C, D)."""
    label: str
    timestamp: datetime
    price: float
    index: int


@dataclass
class FibonacciRatio:
    """Fibonacci ratio measurement."""
    name: str
    actual: float
    expected_min: float
    expected_max: float
    is_valid: bool
    deviation: float


@dataclass
class HarmonicPattern:
    """Detected harmonic pattern."""
    pattern_type: HarmonicPatternType
    direction: PatternDirection
    points: Dict[str, PatternPoint]  # X, A, B, C, D
    ratios: List[FibonacciRatio]
    completion_percentage: float
    prz_low: float  # Potential Reversal Zone low
    prz_high: float  # Potential Reversal Zone high
    stop_loss: float
    target_1: float  # 38.2% retracement of AD
    target_2: float  # 61.8% retracement of AD
    target_3: float  # 100% retracement of AD
    confidence: float
    is_complete: bool


@dataclass
class HarmonicScanResult:
    """Result of harmonic pattern scan."""
    patterns: List[HarmonicPattern]
    forming_patterns: List[HarmonicPattern]
    best_pattern: Optional[HarmonicPattern]
    trading_signal: Optional[str]
    confidence: float


class HarmonicPatternScanner:
    """
    Advanced Harmonic Pattern Detection System.
    
    Identifies XABCD patterns with precise Fibonacci ratios.
    """
    
    # Pattern definitions with Fibonacci ratios
    PATTERN_RATIOS = {
        HarmonicPatternType.GARTLEY: {
            'AB_XA': (0.618, 0.618),  # (min, max)
            'BC_AB': (0.382, 0.886),
            'CD_BC': (1.272, 1.618),
            'AD_XA': (0.786, 0.786),
        },
        HarmonicPatternType.BUTTERFLY: {
            'AB_XA': (0.786, 0.786),
            'BC_AB': (0.382, 0.886),
            'CD_BC': (1.618, 2.618),
            'AD_XA': (1.272, 1.618),
        },
        HarmonicPatternType.BAT: {
            'AB_XA': (0.382, 0.5),
            'BC_AB': (0.382, 0.886),
            'CD_BC': (1.618, 2.618),
            'AD_XA': (0.886, 0.886),
        },
        HarmonicPatternType.CRAB: {
            'AB_XA': (0.382, 0.618),
            'BC_AB': (0.382, 0.886),
            'CD_BC': (2.24, 3.618),
            'AD_XA': (1.618, 1.618),
        },
        HarmonicPatternType.SHARK: {
            'AB_XA': (1.13, 1.618),
            'BC_AB': (1.13, 1.618),
            'CD_BC': (1.618, 2.24),
            'AD_XA': (0.886, 1.13),
        },
        HarmonicPatternType.CYPHER: {
            'AB_XA': (0.382, 0.618),
            'BC_AB': (1.272, 1.414),
            'CD_XC': (0.786, 0.786),
            'AD_XA': (0.786, 0.786),
        },
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.tolerance = self.config.get('tolerance', 0.05)  # 5% tolerance
        self.min_pattern_bars = self.config.get('min_pattern_bars', 10)
        self.max_pattern_bars = self.config.get('max_pattern_bars', 200)
        self.detected_patterns: List[HarmonicPattern] = []
        
        logger.info("HarmonicPatternScanner initialized")
    
    def scan(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        timestamps: List[datetime]
    ) -> HarmonicScanResult:
        """
        Scan for harmonic patterns.
        
        Args:
            highs: Array of high prices
            lows: Array of low prices
            closes: Array of close prices
            timestamps: List of timestamps
            
        Returns:
            HarmonicScanResult with detected patterns
        """
        # Find swing points
        swing_points = self._find_swing_points(highs, lows, timestamps)
        
        if len(swing_points) < 5:
            return HarmonicScanResult(
                patterns=[],
                forming_patterns=[],
                best_pattern=None,
                trading_signal=None,
                confidence=0.0
            )
        
        complete_patterns = []
        forming_patterns = []
        
        # Scan for each pattern type
        for pattern_type in HarmonicPatternType:
            if pattern_type in [HarmonicPatternType.ABCD, HarmonicPatternType.THREE_DRIVES]:
                continue  # Handle separately
            
            # Scan for bullish patterns
            bullish = self._scan_for_pattern(
                swing_points, pattern_type, PatternDirection.BULLISH, closes[-1]
            )
            complete_patterns.extend([p for p in bullish if p.is_complete])
            forming_patterns.extend([p for p in bullish if not p.is_complete])
            
            # Scan for bearish patterns
            bearish = self._scan_for_pattern(
                swing_points, pattern_type, PatternDirection.BEARISH, closes[-1]
            )
            complete_patterns.extend([p for p in bearish if p.is_complete])
            forming_patterns.extend([p for p in bearish if not p.is_complete])
        
        # Find best pattern
        best_pattern = None
        if complete_patterns:
            best_pattern = max(complete_patterns, key=lambda p: p.confidence)
        elif forming_patterns:
            best_pattern = max(forming_patterns, key=lambda p: p.completion_percentage)
        
        # Generate trading signal
        trading_signal = self._generate_signal(best_pattern, closes[-1])
        
        # Overall confidence
        confidence = best_pattern.confidence if best_pattern else 0.0
        
        self.detected_patterns = complete_patterns + forming_patterns
        
        return HarmonicScanResult(
            patterns=complete_patterns,
            forming_patterns=forming_patterns,
            best_pattern=best_pattern,
            trading_signal=trading_signal,
            confidence=confidence
        )
    
    def _find_swing_points(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        timestamps: List[datetime]
    ) -> List[PatternPoint]:
        """Find significant swing highs and lows."""
        swing_points = []
        n = len(highs)
        lookback = 5
        
        for i in range(lookback, n - lookback):
            # Check for swing high
            is_swing_high = True
            for j in range(1, lookback + 1):
                if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_points.append(PatternPoint(
                    label='H',
                    timestamp=timestamps[i],
                    price=highs[i],
                    index=i
                ))
            
            # Check for swing low
            is_swing_low = True
            for j in range(1, lookback + 1):
                if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_points.append(PatternPoint(
                    label='L',
                    timestamp=timestamps[i],
                    price=lows[i],
                    index=i
                ))
        
        # Sort by index
        swing_points.sort(key=lambda p: p.index)
        
        return swing_points
    
    def _scan_for_pattern(
        self,
        swing_points: List[PatternPoint],
        pattern_type: HarmonicPatternType,
        direction: PatternDirection,
        current_price: float
    ) -> List[HarmonicPattern]:
        """Scan for a specific pattern type."""
        patterns = []
        n = len(swing_points)
        
        # Need at least 5 points for XABCD
        for i in range(n - 4):
            # Get potential XABCD points
            x = swing_points[i]
            a = swing_points[i + 1]
            b = swing_points[i + 2]
            c = swing_points[i + 3]
            
            # Check if we have a D point or if pattern is forming
            if i + 4 < n:
                d = swing_points[i + 4]
                is_complete = True
            else:
                # Pattern forming - D is current price
                d = PatternPoint(
                    label='D',
                    timestamp=datetime.now(),
                    price=current_price,
                    index=len(swing_points)
                )
                is_complete = False
            
            # Validate direction
            if direction == PatternDirection.BULLISH:
                # X should be low, A high, B low, C high, D low
                if not (x.label == 'L' and a.label == 'H' and b.label == 'L' and c.label == 'H'):
                    continue
            else:
                # X should be high, A low, B high, C low, D high
                if not (x.label == 'H' and a.label == 'L' and b.label == 'H' and c.label == 'L'):
                    continue
            
            # Calculate ratios
            ratios = self._calculate_ratios(x, a, b, c, d, pattern_type)
            
            # Check if ratios match pattern
            if not self._validate_ratios(ratios, pattern_type):
                continue
            
            # Calculate PRZ (Potential Reversal Zone)
            prz_low, prz_high = self._calculate_prz(x, a, b, c, pattern_type, direction)
            
            # Calculate targets
            targets = self._calculate_targets(a, d, direction)
            
            # Calculate stop loss
            stop_loss = self._calculate_stop_loss(x, d, direction)
            
            # Calculate confidence
            confidence = self._calculate_pattern_confidence(ratios)
            
            # Calculate completion percentage
            completion = self._calculate_completion(d.price, prz_low, prz_high, direction)
            
            pattern = HarmonicPattern(
                pattern_type=pattern_type,
                direction=direction,
                points={
                    'X': PatternPoint('X', x.timestamp, x.price, x.index),
                    'A': PatternPoint('A', a.timestamp, a.price, a.index),
                    'B': PatternPoint('B', b.timestamp, b.price, b.index),
                    'C': PatternPoint('C', c.timestamp, c.price, c.index),
                    'D': PatternPoint('D', d.timestamp, d.price, d.index),
                },
                ratios=ratios,
                completion_percentage=completion,
                prz_low=prz_low,
                prz_high=prz_high,
                stop_loss=stop_loss,
                target_1=targets[0],
                target_2=targets[1],
                target_3=targets[2],
                confidence=confidence,
                is_complete=is_complete and completion >= 0.9
            )
            
            patterns.append(pattern)
        
        return patterns
    
    def _calculate_ratios(
        self,
        x: PatternPoint,
        a: PatternPoint,
        b: PatternPoint,
        c: PatternPoint,
        d: PatternPoint,
        pattern_type: HarmonicPatternType
    ) -> List[FibonacciRatio]:
        """Calculate Fibonacci ratios for the pattern."""
        ratios = []
        
        xa = abs(a.price - x.price)
        ab = abs(b.price - a.price)
        bc = abs(c.price - b.price)
        cd = abs(d.price - c.price)
        ad = abs(d.price - a.price)
        xc = abs(c.price - x.price)
        
        pattern_def = self.PATTERN_RATIOS.get(pattern_type, {})
        
        # AB/XA ratio
        if xa > 0:
            ab_xa = ab / xa
            expected = pattern_def.get('AB_XA', (0, 1))
            ratios.append(FibonacciRatio(
                name='AB/XA',
                actual=ab_xa,
                expected_min=expected[0],
                expected_max=expected[1],
                is_valid=expected[0] * (1 - self.tolerance) <= ab_xa <= expected[1] * (1 + self.tolerance),
                deviation=self._calculate_deviation(ab_xa, expected[0], expected[1])
            ))
        
        # BC/AB ratio
        if ab > 0:
            bc_ab = bc / ab
            expected = pattern_def.get('BC_AB', (0, 1))
            ratios.append(FibonacciRatio(
                name='BC/AB',
                actual=bc_ab,
                expected_min=expected[0],
                expected_max=expected[1],
                is_valid=expected[0] * (1 - self.tolerance) <= bc_ab <= expected[1] * (1 + self.tolerance),
                deviation=self._calculate_deviation(bc_ab, expected[0], expected[1])
            ))
        
        # CD/BC ratio
        if bc > 0:
            cd_bc = cd / bc
            expected = pattern_def.get('CD_BC', (0, 1))
            ratios.append(FibonacciRatio(
                name='CD/BC',
                actual=cd_bc,
                expected_min=expected[0],
                expected_max=expected[1],
                is_valid=expected[0] * (1 - self.tolerance) <= cd_bc <= expected[1] * (1 + self.tolerance),
                deviation=self._calculate_deviation(cd_bc, expected[0], expected[1])
            ))
        
        # AD/XA ratio
        if xa > 0:
            ad_xa = ad / xa
            expected = pattern_def.get('AD_XA', (0, 1))
            ratios.append(FibonacciRatio(
                name='AD/XA',
                actual=ad_xa,
                expected_min=expected[0],
                expected_max=expected[1],
                is_valid=expected[0] * (1 - self.tolerance) <= ad_xa <= expected[1] * (1 + self.tolerance),
                deviation=self._calculate_deviation(ad_xa, expected[0], expected[1])
            ))
        
        return ratios
    
    def _calculate_deviation(self, actual: float, expected_min: float, expected_max: float) -> float:
        """Calculate deviation from expected range."""
        if expected_min <= actual <= expected_max:
            return 0.0
        elif actual < expected_min:
            return (expected_min - actual) / expected_min
        else:
            return (actual - expected_max) / expected_max
    
    def _validate_ratios(self, ratios: List[FibonacciRatio], pattern_type: HarmonicPatternType) -> bool:
        """Validate if ratios match the pattern requirements."""
        if not ratios:
            return False
        
        # At least 3 out of 4 ratios should be valid
        valid_count = sum(1 for r in ratios if r.is_valid)
        return valid_count >= 3
    
    def _calculate_prz(
        self,
        x: PatternPoint,
        a: PatternPoint,
        b: PatternPoint,
        c: PatternPoint,
        pattern_type: HarmonicPatternType,
        direction: PatternDirection
    ) -> Tuple[float, float]:
        """Calculate Potential Reversal Zone."""
        xa = abs(a.price - x.price)
        bc = abs(c.price - b.price)
        
        pattern_def = self.PATTERN_RATIOS.get(pattern_type, {})
        ad_xa = pattern_def.get('AD_XA', (0.786, 0.786))
        cd_bc = pattern_def.get('CD_BC', (1.272, 1.618))
        
        if direction == PatternDirection.BULLISH:
            # D should be below A
            prz_from_xa = a.price - xa * ad_xa[1]
            prz_from_bc = c.price - bc * cd_bc[0]
            prz_low = min(prz_from_xa, prz_from_bc)
            prz_high = max(prz_from_xa, prz_from_bc)
        else:
            # D should be above A
            prz_from_xa = a.price + xa * ad_xa[1]
            prz_from_bc = c.price + bc * cd_bc[0]
            prz_low = min(prz_from_xa, prz_from_bc)
            prz_high = max(prz_from_xa, prz_from_bc)
        
        return prz_low, prz_high
    
    def _calculate_targets(
        self,
        a: PatternPoint,
        d: PatternPoint,
        direction: PatternDirection
    ) -> Tuple[float, float, float]:
        """Calculate profit targets."""
        ad = abs(d.price - a.price)
        
        if direction == PatternDirection.BULLISH:
            target_1 = d.price + ad * 0.382
            target_2 = d.price + ad * 0.618
            target_3 = d.price + ad * 1.0
        else:
            target_1 = d.price - ad * 0.382
            target_2 = d.price - ad * 0.618
            target_3 = d.price - ad * 1.0
        
        return target_1, target_2, target_3
    
    def _calculate_stop_loss(
        self,
        x: PatternPoint,
        d: PatternPoint,
        direction: PatternDirection
    ) -> float:
        """Calculate stop loss level."""
        buffer = abs(d.price - x.price) * 0.1  # 10% buffer
        
        if direction == PatternDirection.BULLISH:
            return x.price - buffer
        else:
            return x.price + buffer
    
    def _calculate_pattern_confidence(self, ratios: List[FibonacciRatio]) -> float:
        """Calculate confidence based on ratio accuracy."""
        if not ratios:
            return 0.0
        
        # Base confidence
        confidence = 0.5
        
        # Add for each valid ratio
        valid_count = sum(1 for r in ratios if r.is_valid)
        confidence += valid_count * 0.1
        
        # Subtract for deviations
        avg_deviation = np.mean([r.deviation for r in ratios])
        confidence -= avg_deviation * 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_completion(
        self,
        d_price: float,
        prz_low: float,
        prz_high: float,
        direction: PatternDirection
    ) -> float:
        """Calculate pattern completion percentage."""
        if direction == PatternDirection.BULLISH:
            if d_price <= prz_low:
                return 1.0
            elif d_price >= prz_high:
                return 0.5
            else:
                return 0.5 + 0.5 * (prz_high - d_price) / (prz_high - prz_low)
        else:
            if d_price >= prz_high:
                return 1.0
            elif d_price <= prz_low:
                return 0.5
            else:
                return 0.5 + 0.5 * (d_price - prz_low) / (prz_high - prz_low)
    
    def _generate_signal(
        self,
        pattern: Optional[HarmonicPattern],
        current_price: float
    ) -> Optional[str]:
        """Generate trading signal from pattern."""
        if not pattern:
            return None
        
        if pattern.is_complete:
            if pattern.direction == PatternDirection.BULLISH:
                return (
                    f"BUY {pattern.pattern_type.value.upper()}: "
                    f"Entry near {pattern.prz_low:.4f}-{pattern.prz_high:.4f}, "
                    f"SL: {pattern.stop_loss:.4f}, "
                    f"TP1: {pattern.target_1:.4f}, TP2: {pattern.target_2:.4f}"
                )
            else:
                return (
                    f"SELL {pattern.pattern_type.value.upper()}: "
                    f"Entry near {pattern.prz_low:.4f}-{pattern.prz_high:.4f}, "
                    f"SL: {pattern.stop_loss:.4f}, "
                    f"TP1: {pattern.target_1:.4f}, TP2: {pattern.target_2:.4f}"
                )
        else:
            return (
                f"FORMING {pattern.pattern_type.value.upper()} "
                f"({pattern.direction.value}): "
                f"{pattern.completion_percentage:.0%} complete. "
                f"Watch PRZ: {pattern.prz_low:.4f}-{pattern.prz_high:.4f}"
            )
    
    def get_pattern_description(self, pattern_type: HarmonicPatternType) -> str:
        """Get description of a pattern type."""
        descriptions = {
            HarmonicPatternType.GARTLEY: (
                "Gartley: The original harmonic pattern. "
                "AB retraces 61.8% of XA, D completes at 78.6% of XA."
            ),
            HarmonicPatternType.BUTTERFLY: (
                "Butterfly: Extension pattern. "
                "D extends beyond X, typically to 127.2% or 161.8% of XA."
            ),
            HarmonicPatternType.BAT: (
                "Bat: Deep retracement pattern. "
                "AB retraces 38.2%-50% of XA, D completes at 88.6% of XA."
            ),
            HarmonicPatternType.CRAB: (
                "Crab: Extreme extension pattern. "
                "D extends to 161.8% of XA. High reward potential."
            ),
            HarmonicPatternType.SHARK: (
                "Shark: Newer pattern with unique structure. "
                "Uses 0/5 labeling instead of XABCD."
            ),
            HarmonicPatternType.CYPHER: (
                "Cypher: Uses XC leg for D calculation. "
                "D completes at 78.6% of XC."
            ),
        }
        return descriptions.get(pattern_type, "Unknown pattern type")
