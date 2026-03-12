"""
Market Breadth Analyzer

Analyzes market-wide breadth indicators:
- Advance/Decline ratios
- New Highs/New Lows
- McClellan Oscillator
- Arms Index (TRIN)
- Percent of stocks above moving averages
- Sector rotation analysis
- Market internals scoring
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class MarketCondition(Enum):
    """Overall market condition."""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


class BreadthSignal(Enum):
    """Breadth signal types."""
    BULLISH_DIVERGENCE = "bullish_divergence"
    BEARISH_DIVERGENCE = "bearish_divergence"
    CONFIRMATION = "confirmation"
    OVERBOUGHT = "overbought"
    OVERSOLD = "oversold"
    NEUTRAL = "neutral"


class SectorStrength(Enum):
    """Sector strength levels."""
    LEADING = "leading"
    STRONG = "strong"
    NEUTRAL = "neutral"
    WEAK = "weak"
    LAGGING = "lagging"


@dataclass
class BreadthReading:
    """Single breadth reading."""
    timestamp: datetime
    advances: int
    declines: int
    unchanged: int
    new_highs: int
    new_lows: int
    up_volume: int
    down_volume: int
    total_issues: int
    
    @property
    def ad_ratio(self) -> float:
        """Advance/Decline ratio."""
        try:
            if self.declines > 0:
                return self.advances / self.declines
            return self.advances if self.advances > 0 else 1.0
        except Exception as e:
            logger.error(f"Error in ad_ratio: {e}")
            raise
    
    @property
    def ad_line(self) -> int:
        """Advance/Decline line value."""
        return self.advances - self.declines
    
    @property
    def ad_percent(self) -> float:
        """Percent advancing."""
        try:
            total = self.advances + self.declines + self.unchanged
            if total > 0:
                return self.advances / total
            return 0.5
        except Exception as e:
            logger.error(f"Error in ad_percent: {e}")
            raise
    
    @property
    def nh_nl_ratio(self) -> float:
        """New Highs / New Lows ratio."""
        try:
            if self.new_lows > 0:
                return self.new_highs / self.new_lows
            return self.new_highs if self.new_highs > 0 else 1.0
        except Exception as e:
            logger.error(f"Error in nh_nl_ratio: {e}")
            raise
    
    @property
    def nh_nl_diff(self) -> int:
        """New Highs - New Lows."""
        return self.new_highs - self.new_lows
    
    @property
    def trin(self) -> float:
        """Arms Index (TRIN)."""
        # TRIN = (Advances/Declines) / (Up Volume/Down Volume)
        try:
            if self.declines > 0 and self.down_volume > 0:
                ad_ratio = self.advances / self.declines
                vol_ratio = self.up_volume / self.down_volume
                if vol_ratio > 0:
                    return ad_ratio / vol_ratio
            return 1.0
        except Exception as e:
            logger.error(f"Error in trin: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'advances': self.advances,
            'declines': self.declines,
            'unchanged': self.unchanged,
            'new_highs': self.new_highs,
            'new_lows': self.new_lows,
            'ad_ratio': self.ad_ratio,
            'ad_line': self.ad_line,
            'nh_nl_diff': self.nh_nl_diff,
            'trin': self.trin
        }


@dataclass
class SectorData:
    """Sector performance data."""
    sector: str
    change_pct: float
    volume: int
    relative_strength: float
    stocks_above_50ma: float
    stocks_above_200ma: float
    
    @property
    def strength(self) -> SectorStrength:
        try:
            if self.relative_strength > 1.1:
                return SectorStrength.LEADING
            elif self.relative_strength > 1.02:
                return SectorStrength.STRONG
            elif self.relative_strength > 0.98:
                return SectorStrength.NEUTRAL
            elif self.relative_strength > 0.9:
                return SectorStrength.WEAK
            else:
                return SectorStrength.LAGGING
        except Exception as e:
            logger.error(f"Error in strength: {e}")
            raise


@dataclass
class MarketBreadthSignal:
    """Market breadth trading signal."""
    timestamp: datetime
    condition: MarketCondition
    signal: BreadthSignal
    confidence: float
    ad_ratio: float
    ad_line: int
    ad_line_trend: str  # 'rising', 'falling', 'flat'
    mcclellan_oscillator: float
    mcclellan_summation: float
    trin: float
    nh_nl_diff: int
    pct_above_50ma: float
    pct_above_200ma: float
    sector_rotation: Dict[str, SectorStrength]
    internals_score: float  # -100 to +100
    analysis: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'condition': self.condition.value,
            'signal': self.signal.value,
            'confidence': self.confidence,
            'ad_ratio': self.ad_ratio,
            'ad_line': self.ad_line,
            'ad_line_trend': self.ad_line_trend,
            'mcclellan_oscillator': self.mcclellan_oscillator,
            'mcclellan_summation': self.mcclellan_summation,
            'trin': self.trin,
            'nh_nl_diff': self.nh_nl_diff,
            'pct_above_50ma': self.pct_above_50ma,
            'pct_above_200ma': self.pct_above_200ma,
            'sector_rotation': {k: v.value for k, v in self.sector_rotation.items()},
            'internals_score': self.internals_score,
            'analysis': self.analysis
        }


class McClellanCalculator:
    """
    Calculates McClellan Oscillator and Summation Index.
    
    McClellan Oscillator = 19-day EMA of AD - 39-day EMA of AD
    McClellan Summation = Cumulative sum of McClellan Oscillator
    """
    
    def __init__(self):
        try:
            self.ad_values: deque = deque(maxlen=100)
            self.ema_19: Optional[float] = None
            self.ema_39: Optional[float] = None
            self.summation: float = 0.0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_reading(self, ad_value: int):
        """Add A/D reading and update calculations."""
        try:
            self.ad_values.append(ad_value)
        
            # Calculate EMAs
            if len(self.ad_values) >= 19:
                if self.ema_19 is None:
                    self.ema_19 = statistics.mean(list(self.ad_values)[-19:])
                else:
                    k = 2 / (19 + 1)
                    self.ema_19 = ad_value * k + self.ema_19 * (1 - k)
        
            if len(self.ad_values) >= 39:
                if self.ema_39 is None:
                    self.ema_39 = statistics.mean(list(self.ad_values)[-39:])
                else:
                    k = 2 / (39 + 1)
                    self.ema_39 = ad_value * k + self.ema_39 * (1 - k)
        
            # Update summation
            oscillator = self.get_oscillator()
            if oscillator is not None:
                self.summation += oscillator
        except Exception as e:
            logger.error(f"Error in add_reading: {e}")
            raise
    
    def get_oscillator(self) -> Optional[float]:
        """Get current McClellan Oscillator value."""
        try:
            if self.ema_19 is not None and self.ema_39 is not None:
                return self.ema_19 - self.ema_39
            return None
        except Exception as e:
            logger.error(f"Error in get_oscillator: {e}")
            raise
    
    def get_summation(self) -> float:
        """Get current McClellan Summation Index."""
        return self.summation


class MarketBreadthAnalyzer:
    """
    Complete market breadth analysis system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Historical data
            self.readings: deque = deque(maxlen=252)  # ~1 year of daily data
            self.mcclellan = McClellanCalculator()
        
            # Sector data
            self.sectors: Dict[str, SectorData] = {}
        
            # Moving average tracking
            self.stocks_above_50ma: float = 0.5
            self.stocks_above_200ma: float = 0.5
        
            # Index price for divergence detection
            self.index_prices: deque = deque(maxlen=50)
        
            logger.info("MarketBreadthAnalyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_reading(self, reading: BreadthReading):
        """
        Add a breadth reading.
        
        Args:
            reading: BreadthReading to add
        """
        try:
            self.readings.append(reading)
            self.mcclellan.add_reading(reading.ad_line)
        except Exception as e:
            logger.error(f"Error in add_reading: {e}")
            raise
    
    def update_sector(self, sector_data: SectorData):
        """Update sector data."""
        try:
            self.sectors[sector_data.sector] = sector_data
        except Exception as e:
            logger.error(f"Error in update_sector: {e}")
            raise
    
    def update_ma_percentages(self, pct_above_50ma: float, pct_above_200ma: float):
        """Update percentage of stocks above moving averages."""
        try:
            self.stocks_above_50ma = pct_above_50ma
            self.stocks_above_200ma = pct_above_200ma
        except Exception as e:
            logger.error(f"Error in update_ma_percentages: {e}")
            raise
    
    def add_index_price(self, price: float):
        """Add index price for divergence detection."""
        try:
            self.index_prices.append(price)
        except Exception as e:
            logger.error(f"Error in add_index_price: {e}")
            raise
    
    def generate_signal(self) -> MarketBreadthSignal:
        """
        Generate comprehensive market breadth signal.
        
        Returns:
            MarketBreadthSignal with analysis
        """
        try:
            if not self.readings:
                return self._empty_signal()
        
            latest = self.readings[-1]
        
            # Calculate metrics
            ad_ratio = latest.ad_ratio
            ad_line = latest.ad_line
            ad_line_trend = self._calculate_ad_trend()
        
            mcclellan_osc = self.mcclellan.get_oscillator() or 0.0
            mcclellan_sum = self.mcclellan.get_summation()
        
            trin = latest.trin
            nh_nl_diff = latest.nh_nl_diff
        
            # Sector rotation
            sector_rotation = {s: d.strength for s, d in self.sectors.items()}
        
            # Calculate internals score
            internals_score = self._calculate_internals_score(
                ad_ratio, mcclellan_osc, trin, nh_nl_diff,
                self.stocks_above_50ma, self.stocks_above_200ma
            )
        
            # Determine condition and signal
            condition = self._determine_condition(internals_score)
            signal, confidence = self._determine_signal(
                ad_line_trend, mcclellan_osc, trin, internals_score
            )
        
            # Generate analysis
            analysis = self._generate_analysis(
                ad_ratio, ad_line_trend, mcclellan_osc, trin, nh_nl_diff, internals_score
            )
        
            return MarketBreadthSignal(
                timestamp=datetime.now(),
                condition=condition,
                signal=signal,
                confidence=confidence,
                ad_ratio=ad_ratio,
                ad_line=ad_line,
                ad_line_trend=ad_line_trend,
                mcclellan_oscillator=mcclellan_osc,
                mcclellan_summation=mcclellan_sum,
                trin=trin,
                nh_nl_diff=nh_nl_diff,
                pct_above_50ma=self.stocks_above_50ma,
                pct_above_200ma=self.stocks_above_200ma,
                sector_rotation=sector_rotation,
                internals_score=internals_score,
                analysis=analysis
            )
        except Exception as e:
            logger.error(f"Error in generate_signal: {e}")
            raise
    
    def _empty_signal(self) -> MarketBreadthSignal:
        """Return empty signal when no data."""
        return MarketBreadthSignal(
            timestamp=datetime.now(),
            condition=MarketCondition.NEUTRAL,
            signal=BreadthSignal.NEUTRAL,
            confidence=0.0,
            ad_ratio=1.0,
            ad_line=0,
            ad_line_trend='flat',
            mcclellan_oscillator=0.0,
            mcclellan_summation=0.0,
            trin=1.0,
            nh_nl_diff=0,
            pct_above_50ma=0.5,
            pct_above_200ma=0.5,
            sector_rotation={},
            internals_score=0.0,
            analysis="Insufficient data"
        )
    
    def _calculate_ad_trend(self) -> str:
        """Calculate A/D line trend."""
        try:
            if len(self.readings) < 5:
                return 'flat'
        
            recent = [r.ad_line for r in list(self.readings)[-5:]]
        
            # Simple linear regression slope
            n = len(recent)
            x_mean = (n - 1) / 2
            y_mean = statistics.mean(recent)
        
            numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(recent))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
        
            if denominator > 0:
                slope = numerator / denominator
            
                if slope > 50:
                    return 'rising'
                elif slope < -50:
                    return 'falling'
        
            return 'flat'
        except Exception as e:
            logger.error(f"Error in _calculate_ad_trend: {e}")
            raise
    
    def _calculate_internals_score(
        self,
        ad_ratio: float,
        mcclellan: float,
        trin: float,
        nh_nl: int,
        pct_50ma: float,
        pct_200ma: float
    ) -> float:
        """
        Calculate market internals score (-100 to +100).
        
        Components:
        - A/D ratio: 25 points
        - McClellan: 25 points
        - TRIN: 15 points
        - NH/NL: 15 points
        - % above MAs: 20 points
        """
        try:
            score = 0.0
        
            # A/D ratio (25 points)
            if ad_ratio > 2.0:
                score += 25
            elif ad_ratio > 1.5:
                score += 20
            elif ad_ratio > 1.0:
                score += 10
            elif ad_ratio > 0.67:
                score -= 10
            elif ad_ratio > 0.5:
                score -= 20
            else:
                score -= 25
        
            # McClellan Oscillator (25 points)
            if mcclellan > 100:
                score += 25
            elif mcclellan > 50:
                score += 15
            elif mcclellan > 0:
                score += 5
            elif mcclellan > -50:
                score -= 5
            elif mcclellan > -100:
                score -= 15
            else:
                score -= 25
        
            # TRIN (15 points) - inverted, low TRIN is bullish
            if trin < 0.7:
                score += 15
            elif trin < 0.9:
                score += 10
            elif trin < 1.1:
                score += 0
            elif trin < 1.3:
                score -= 10
            else:
                score -= 15
        
            # NH/NL (15 points)
            if nh_nl > 200:
                score += 15
            elif nh_nl > 100:
                score += 10
            elif nh_nl > 0:
                score += 5
            elif nh_nl > -100:
                score -= 5
            elif nh_nl > -200:
                score -= 10
            else:
                score -= 15
        
            # % above MAs (20 points)
            ma_score = (pct_50ma - 0.5) * 20 + (pct_200ma - 0.5) * 20
            score += max(-20, min(20, ma_score))
        
            return max(-100, min(100, score))
        except Exception as e:
            logger.error(f"Error in _calculate_internals_score: {e}")
            raise
    
    def _determine_condition(self, internals_score: float) -> MarketCondition:
        """Determine market condition from internals score."""
        try:
            if internals_score > 60:
                return MarketCondition.STRONG_BULLISH
            elif internals_score > 20:
                return MarketCondition.BULLISH
            elif internals_score > -20:
                return MarketCondition.NEUTRAL
            elif internals_score > -60:
                return MarketCondition.BEARISH
            else:
                return MarketCondition.STRONG_BEARISH
        except Exception as e:
            logger.error(f"Error in _determine_condition: {e}")
            raise
    
    def _determine_signal(
        self,
        ad_trend: str,
        mcclellan: float,
        trin: float,
        internals_score: float
    ) -> Tuple[BreadthSignal, float]:
        """Determine breadth signal and confidence."""
        try:
            confidence = 0.5
        
            # Check for divergence
            if len(self.index_prices) >= 10:
                price_trend = self.index_prices[-1] > self.index_prices[-10]
                ad_positive = ad_trend == 'rising'
            
                if price_trend and not ad_positive:
                    return BreadthSignal.BEARISH_DIVERGENCE, 0.7
                elif not price_trend and ad_positive:
                    return BreadthSignal.BULLISH_DIVERGENCE, 0.7
        
            # Check for overbought/oversold
            if mcclellan > 150 or internals_score > 80:
                return BreadthSignal.OVERBOUGHT, 0.6
            elif mcclellan < -150 or internals_score < -80:
                return BreadthSignal.OVERSOLD, 0.6
        
            # Check for confirmation
            if internals_score > 40 and ad_trend == 'rising':
                return BreadthSignal.CONFIRMATION, 0.7
            elif internals_score < -40 and ad_trend == 'falling':
                return BreadthSignal.CONFIRMATION, 0.7
        
            return BreadthSignal.NEUTRAL, 0.5
        except Exception as e:
            logger.error(f"Error in _determine_signal: {e}")
            raise
    
    def _generate_analysis(
        self,
        ad_ratio: float,
        ad_trend: str,
        mcclellan: float,
        trin: float,
        nh_nl: int,
        internals_score: float
    ) -> str:
        """Generate analysis text."""
        try:
            parts = []
        
            # A/D analysis
            if ad_ratio > 1.5:
                parts.append(f"Strong breadth (A/D: {ad_ratio:.2f})")
            elif ad_ratio < 0.67:
                parts.append(f"Weak breadth (A/D: {ad_ratio:.2f})")
            else:
                parts.append(f"Mixed breadth (A/D: {ad_ratio:.2f})")
        
            # Trend
            parts.append(f"A/D line {ad_trend}")
        
            # McClellan
            if mcclellan > 100:
                parts.append("McClellan bullish")
            elif mcclellan < -100:
                parts.append("McClellan bearish")
        
            # TRIN
            if trin < 0.8:
                parts.append("TRIN bullish")
            elif trin > 1.2:
                parts.append("TRIN bearish")
        
            # NH/NL
            if nh_nl > 100:
                parts.append(f"New highs dominating (+{nh_nl})")
            elif nh_nl < -100:
                parts.append(f"New lows dominating ({nh_nl})")
        
            # Overall score
            parts.append(f"Internals: {internals_score:+.0f}")
        
            return " | ".join(parts)
        except Exception as e:
            logger.error(f"Error in _generate_analysis: {e}")
            raise
    
    def get_sector_rotation(self) -> Dict[str, Any]:
        """Get sector rotation analysis."""
        try:
            if not self.sectors:
                return {'status': 'No sector data'}
        
            # Sort sectors by strength
            sorted_sectors = sorted(
                self.sectors.items(),
                key=lambda x: x[1].relative_strength,
                reverse=True
            )
        
            leading = [s for s, d in sorted_sectors if d.strength == SectorStrength.LEADING]
            lagging = [s for s, d in sorted_sectors if d.strength == SectorStrength.LAGGING]
        
            return {
                'leading_sectors': leading,
                'lagging_sectors': lagging,
                'rotation_phase': self._determine_rotation_phase(leading, lagging),
                'all_sectors': {s: {'strength': d.strength.value, 'rs': d.relative_strength} 
                              for s, d in sorted_sectors}
            }
        except Exception as e:
            logger.error(f"Error in get_sector_rotation: {e}")
            raise
    
    def _determine_rotation_phase(self, leading: List[str], lagging: List[str]) -> str:
        """Determine market cycle phase from sector rotation."""
        # Simplified sector rotation model
        try:
            early_cycle = ['Financials', 'Consumer Discretionary', 'Industrials']
            mid_cycle = ['Technology', 'Communication Services', 'Materials']
            late_cycle = ['Energy', 'Healthcare']
            defensive = ['Utilities', 'Consumer Staples', 'Real Estate']
        
            leading_set = set(leading)
        
            if leading_set & set(early_cycle):
                return "EARLY_CYCLE"
            elif leading_set & set(mid_cycle):
                return "MID_CYCLE"
            elif leading_set & set(late_cycle):
                return "LATE_CYCLE"
            elif leading_set & set(defensive):
                return "DEFENSIVE"
            else:
                return "TRANSITIONAL"
        except Exception as e:
            logger.error(f"Error in _determine_rotation_phase: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status."""
        return {
            'readings_count': len(self.readings),
            'sectors_tracked': len(self.sectors),
            'mcclellan_oscillator': self.mcclellan.get_oscillator(),
            'mcclellan_summation': self.mcclellan.get_summation(),
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_breadth_analyzer(config: Optional[Dict] = None) -> MarketBreadthAnalyzer:
    """Create MarketBreadthAnalyzer instance."""
    return MarketBreadthAnalyzer(config)


# Example usage
if __name__ == "__main__":
    import random
    
    analyzer = create_breadth_analyzer()
    
    # Simulate historical readings
    for i in range(50):
        # Simulate bullish market
        advances = random.randint(1500, 2500)
        declines = random.randint(1000, 2000)
        
        reading = BreadthReading(
            timestamp=datetime.now() - timedelta(days=50-i),
            advances=advances,
            declines=declines,
            unchanged=random.randint(100, 300),
            new_highs=random.randint(50, 200),
            new_lows=random.randint(20, 100),
            up_volume=advances * random.randint(500, 1500),
            down_volume=declines * random.randint(400, 1200),
            total_issues=4000
        )
        
        analyzer.add_reading(reading)
        analyzer.add_index_price(4500 + i * 10 + random.uniform(-20, 20))
    
    # Add sector data
    sectors = [
        ("Technology", 0.02, 1.15),
        ("Healthcare", 0.01, 1.05),
        ("Financials", 0.015, 1.08),
        ("Consumer Discretionary", -0.005, 0.95),
        ("Utilities", -0.01, 0.88),
        ("Energy", 0.025, 1.12),
    ]
    
    for sector, change, rs in sectors:
        analyzer.update_sector(SectorData(
            sector=sector,
            change_pct=change,
            volume=random.randint(100000000, 500000000),
            relative_strength=rs,
            stocks_above_50ma=random.uniform(0.4, 0.8),
            stocks_above_200ma=random.uniform(0.5, 0.85)
        ))
    
    # Update MA percentages
    analyzer.update_ma_percentages(0.65, 0.72)
    
    # Generate signal
    signal = analyzer.generate_signal()
    
    print("=" * 60)
    print("MARKET BREADTH ANALYSIS")
    print("=" * 60)
    print(f"\nCondition: {signal.condition.value}")
    print(f"Signal: {signal.signal.value}")
    print(f"Confidence: {signal.confidence:.1%}")
    print(f"\nA/D Ratio: {signal.ad_ratio:.2f}")
    print(f"A/D Line: {signal.ad_line:,}")
    print(f"A/D Trend: {signal.ad_line_trend}")
    print(f"\nMcClellan Oscillator: {signal.mcclellan_oscillator:.1f}")
    print(f"McClellan Summation: {signal.mcclellan_summation:.1f}")
    print(f"TRIN: {signal.trin:.2f}")
    print(f"NH-NL: {signal.nh_nl_diff:+d}")
    print(f"\n% Above 50 MA: {signal.pct_above_50ma:.1%}")
    print(f"% Above 200 MA: {signal.pct_above_200ma:.1%}")
    print(f"\nInternals Score: {signal.internals_score:+.0f}")
    print(f"\nAnalysis: {signal.analysis}")
    
    # Sector rotation
    print("\n" + "=" * 60)
    print("SECTOR ROTATION")
    print("=" * 60)
    
    rotation = analyzer.get_sector_rotation()
    print(f"\nPhase: {rotation['rotation_phase']}")
    print(f"Leading: {', '.join(rotation['leading_sectors'])}")
    print(f"Lagging: {', '.join(rotation['lagging_sectors'])}")
