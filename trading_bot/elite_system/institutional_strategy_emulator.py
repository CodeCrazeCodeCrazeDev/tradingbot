"""
Institutional Strategy Emulator - Wyckoff and ICT Integration

This module implements institutional-grade strategy emulation including:
1. Wyckoff Accumulation Detector with phase analysis
2. Market Maker Mind Model with premium/discount zones
3. FVG hunter with time-sensitive validation
4. ICT Power of 3 Engine with triple-timeframe confirmation
5. Volume-spread confirmation and institutional order flow tracking
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
from scipy.signal import find_peaks
from sklearn.cluster import DBSCAN
from datetime import datetime, timedelta
import warnings
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

class WyckoffPhase(Enum):
    """Wyckoff market phases"""
    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"
    PHASE_A = "phase_a"  # Stopping action
    PHASE_B = "phase_b"  # Building cause
    PHASE_C = "phase_c"  # Testing
    PHASE_D = "phase_d"  # Evidence of supply/demand
    PHASE_E = "phase_e"  # Effort vs result

class ICTConcept(Enum):
    """ICT trading concepts"""
    FAIR_VALUE_GAP = "fair_value_gap"
    ORDER_BLOCK = "order_block"
    BREAKER_BLOCK = "breaker_block"
    MITIGATION_BLOCK = "mitigation_block"
    LIQUIDITY_VOID = "liquidity_void"
    PREMIUM_DISCOUNT = "premium_discount"
    POWER_OF_3 = "power_of_3"
    SILVER_BULLET = "silver_bullet"

class MarketMakerModel(Enum):
    """Market maker behavior models"""
    ACCUMULATION_MODEL = "accumulation"
    DISTRIBUTION_MODEL = "distribution"
    MANIPULATION_MODEL = "manipulation"
    REBALANCING_MODEL = "rebalancing"
    HEDGING_MODEL = "hedging"

@dataclass
class WyckoffAnalysis:
    """Wyckoff phase analysis result"""
    current_phase: WyckoffPhase
    phase_confidence: float
    volume_confirmation: bool
    spread_confirmation: bool
    effort_vs_result: float
    cause_building: bool
    spring_action: bool
    upthrust_action: bool
    strength_weakness: str

@dataclass
class FairValueGap:
    """Fair Value Gap structure"""
    start_index: int
    end_index: int
    high_price: float
    low_price: float
    gap_size: float
    direction: str  # bullish or bearish
    filled_percentage: float
    mitigation_level: float
    time_sensitivity: float
    institutional_origin: bool

@dataclass
class OrderBlock:
    """Order Block structure"""
    price_high: float
    price_low: float
    timestamp: datetime
    block_type: str  # bullish or bearish
    strength: float
    volume_confirmation: bool
    mitigation_count: int
    breaker_status: bool
    institutional_signature: bool

@dataclass
class PremiumDiscountZone:
    """Premium/Discount zone analysis"""
    current_level: float
    premium_threshold: float
    discount_threshold: float
    equilibrium: float
    zone_type: str  # premium, discount, equilibrium
    reversion_probability: float
    institutional_interest: float

@dataclass
class PowerOf3Analysis:
    """ICT Power of 3 analysis"""
    accumulation_phase: bool
    manipulation_phase: bool
    distribution_phase: bool
    current_phase: str
    phase_completion: float
    next_phase_probability: float
    timeframe_alignment: Dict[str, bool]

@dataclass
class InstitutionalStrategy:
    """Complete institutional strategy analysis"""
    wyckoff_analysis: WyckoffAnalysis
    fair_value_gaps: List[FairValueGap]
    order_blocks: List[OrderBlock]
    premium_discount: PremiumDiscountZone
    power_of_3: PowerOf3Analysis
    market_maker_model: MarketMakerModel
    institutional_bias: str
    strategy_confidence: float

class WyckoffAccumulationDetector:
    """Advanced Wyckoff accumulation/distribution detector"""
    
    def __init__(self):
        self.phase_history = []
        self.volume_analysis = {}
        self.spread_analysis = {}
        
    def detect_wyckoff_phase(self, df: pd.DataFrame) -> WyckoffAnalysis:
        """
        Detect current Wyckoff phase with volume-spread confirmation
        
        Args:
            df: OHLCV data
            
        Returns:
            Wyckoff phase analysis
        """
        if len(df) < 50:
            return self._default_analysis()
        
        # Calculate volume and spread metrics
        volume_analysis = self._analyze_volume_patterns(df)
        spread_analysis = self._analyze_spread_patterns(df)
        
        # Detect specific phases
        phase_scores = self._calculate_phase_scores(df, volume_analysis, spread_analysis)
        
        # Determine current phase
        current_phase = max(phase_scores, key=phase_scores.get)
        phase_confidence = phase_scores[current_phase]
        
        # Check for specific Wyckoff events
        spring_action = self._detect_spring_action(df, volume_analysis)
        upthrust_action = self._detect_upthrust_action(df, volume_analysis)
        
        # Analyze effort vs result
        effort_vs_result = self._analyze_effort_vs_result(df, volume_analysis, spread_analysis)
        
        # Check cause building
        cause_building = self._detect_cause_building(df, volume_analysis)
        
        # Determine strength/weakness
        strength_weakness = self._determine_strength_weakness(df, volume_analysis, spread_analysis)
        
        return WyckoffAnalysis(
            current_phase=current_phase,
            phase_confidence=phase_confidence,
            volume_confirmation=volume_analysis['confirmation'],
            spread_confirmation=spread_analysis['confirmation'],
            effort_vs_result=effort_vs_result,
            cause_building=cause_building,
            spring_action=spring_action,
            upthrust_action=upthrust_action,
            strength_weakness=strength_weakness
        )
    
    def _analyze_volume_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns for Wyckoff confirmation"""
        if 'volume' not in df.columns:
            return {'confirmation': False, 'trend': 'unknown', 'climax': False}
        
        volume = df['volume']
        prices = df['close']
        
        # Volume trend analysis
        volume_ma_short = volume.rolling(10).mean()
        volume_ma_long = volume.rolling(30).mean()
        volume_trend = 'increasing' if volume_ma_short.iloc[-1] > volume_ma_long.iloc[-1] else 'decreasing'
        
        # Climax volume detection
        volume_std = volume.rolling(20).std()
        volume_mean = volume.rolling(20).mean()
        recent_volume = volume.iloc[-5:]
        
        climax_volume = any(vol > vol_mean + 2 * vol_std for vol, vol_mean, vol_std in 
                           zip(recent_volume, volume_mean.iloc[-5:], volume_std.iloc[-5:]))
        
        # Volume-price confirmation
        price_changes = prices.pct_change()
        volume_changes = volume.pct_change()
        
        # Correlation between volume and price movement
        correlation = price_changes.rolling(20).corr(volume_changes).iloc[-1]
        confirmation = not np.isnan(correlation) and abs(correlation) > 0.3
        
        return {
            'confirmation': confirmation,
            'trend': volume_trend,
            'climax': climax_volume,
            'correlation': correlation if not np.isnan(correlation) else 0
        }
    
    def _analyze_spread_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze spread (range) patterns for Wyckoff confirmation"""
        # Calculate true range and spread
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        spread = df['high'] - df['low']
        
        # Spread trend analysis
        spread_ma_short = spread.rolling(10).mean()
        spread_ma_long = spread.rolling(30).mean()
        spread_trend = 'widening' if spread_ma_short.iloc[-1] > spread_ma_long.iloc[-1] else 'narrowing'
        
        # Narrow spread detection (potential accumulation/distribution)
        spread_std = spread.rolling(20).std()
        spread_mean = spread.rolling(20).mean()
        
        narrow_spread = spread.iloc[-1] < spread_mean.iloc[-1] - spread_std.iloc[-1]
        wide_spread = spread.iloc[-1] > spread_mean.iloc[-1] + spread_std.iloc[-1]
        
        # Spread confirmation
        confirmation = spread_trend == 'narrowing' and narrow_spread
        
        return {
            'confirmation': confirmation,
            'trend': spread_trend,
            'narrow': narrow_spread,
            'wide': wide_spread,
            'current_spread': spread.iloc[-1]
        }
    
    def _calculate_phase_scores(self, df: pd.DataFrame, volume_analysis: Dict, 
                              spread_analysis: Dict) -> Dict[WyckoffPhase, float]:
        """Calculate scores for each Wyckoff phase"""
        scores = {phase: 0.0 for phase in WyckoffPhase}
        
        # Price action analysis
        prices = df['close']
        highs = df['high']
        lows = df['low']
        
        # Recent price trend
        price_trend = np.polyfit(range(20), prices.iloc[-20:], 1)[0] if len(prices) >= 20 else 0
        
        # Volatility analysis
        volatility = prices.rolling(20).std().iloc[-1]
        avg_volatility = prices.rolling(50).std().mean()
        
        # Phase A (Stopping Action) - High volume, wide spreads, little progress
        if volume_analysis['climax'] and spread_analysis['wide']:
            scores[WyckoffPhase.PHASE_A] += 0.6
            scores[WyckoffPhase.ACCUMULATION] += 0.3
            scores[WyckoffPhase.DISTRIBUTION] += 0.3
        
        # Phase B (Building Cause) - Lower volume, narrower spreads, sideways movement
        if (volume_analysis['trend'] == 'decreasing' and 
            spread_analysis['trend'] == 'narrowing' and 
            abs(price_trend) < avg_volatility * 0.1):
            scores[WyckoffPhase.PHASE_B] += 0.7
            scores[WyckoffPhase.ACCUMULATION] += 0.4
        
        # Phase C (Testing) - Low volume test of lows/highs
        recent_low = lows.rolling(20).min().iloc[-1]
        recent_high = highs.rolling(20).max().iloc[-1]
        current_price = prices.iloc[-1]
        
        if (current_price <= recent_low * 1.01 and 
            volume_analysis['trend'] == 'decreasing'):
            scores[WyckoffPhase.PHASE_C] += 0.6
            scores[WyckoffPhase.ACCUMULATION] += 0.5
        
        # Phase D (Evidence of Supply/Demand) - Volume increase with price movement
        if (volume_analysis['confirmation'] and 
            volume_analysis['trend'] == 'increasing'):
            scores[WyckoffPhase.PHASE_D] += 0.7
            if price_trend > 0:
                scores[WyckoffPhase.MARKUP] += 0.6
            else:
                scores[WyckoffPhase.MARKDOWN] += 0.6
        
        # Phase E (Effort vs Result) - Strong volume with strong price movement
        if (volume_analysis['climax'] and abs(price_trend) > avg_volatility):
            scores[WyckoffPhase.PHASE_E] += 0.8
            if price_trend > 0:
                scores[WyckoffPhase.MARKUP] += 0.7
            else:
                scores[WyckoffPhase.MARKDOWN] += 0.7
        
        # Normalize scores
        max_score = max(scores.values()) if scores.values() else 1
        if max_score > 0:
            scores = {phase: score/max_score for phase, score in scores.items()}
        
        return scores
    
    def _detect_spring_action(self, df: pd.DataFrame, volume_analysis: Dict) -> bool:
        """Detect spring action (test of support with low volume)"""
        if len(df) < 30:
            return False
        
        prices = df['close']
        lows = df['low']
        
        # Find recent support level
        support_level = lows.rolling(20).min().iloc[-20]
        
        # Check for test of support
        recent_lows = lows.iloc[-10:]
        support_test = any(low <= support_level * 1.005 for low in recent_lows)  # 0.5% tolerance
        
        # Check for low volume during test
        low_volume = volume_analysis['trend'] == 'decreasing'
        
        # Check for recovery
        current_price = prices.iloc[-1]
        recovery = current_price > support_level * 1.01
        
        return support_test and low_volume and recovery
    
    def _detect_upthrust_action(self, df: pd.DataFrame, volume_analysis: Dict) -> bool:
        """Detect upthrust action (test of resistance with high volume failure)"""
        if len(df) < 30:
            return False
        
        prices = df['close']
        highs = df['high']
        
        # Find recent resistance level
        resistance_level = highs.rolling(20).max().iloc[-20]
        
        # Check for test of resistance
        recent_highs = highs.iloc[-10:]
        resistance_test = any(high >= resistance_level * 0.995 for high in recent_highs)  # 0.5% tolerance
        
        # Check for high volume during test
        high_volume = volume_analysis['climax']
        
        # Check for failure to break through
        current_price = prices.iloc[-1]
        failure = current_price < resistance_level * 0.99
        
        return resistance_test and high_volume and failure
    
    def _analyze_effort_vs_result(self, df: pd.DataFrame, volume_analysis: Dict, 
                                spread_analysis: Dict) -> float:
        """Analyze effort vs result relationship"""
        if 'volume' not in df.columns:
            return 0.5
        
        # Calculate effort (volume + spread)
        volume = df['volume'].iloc[-10:]  # Last 10 bars
        spread = (df['high'] - df['low']).iloc[-10:]
        
        effort = (volume / volume.mean()) * (spread / spread.mean())
        
        # Calculate result (price movement)
        price_changes = df['close'].pct_change().iloc[-10:]
        result = abs(price_changes).mean()
        
        # Effort vs Result ratio
        avg_effort = effort.mean()
        
        if avg_effort > 0 and result > 0:
            effort_result_ratio = result / (avg_effort / 10)  # Normalize
            return min(effort_result_ratio, 1.0)
        
        return 0.5
    
    def _detect_cause_building(self, df: pd.DataFrame, volume_analysis: Dict) -> bool:
        """Detect cause building (accumulation/distribution)"""
        if len(df) < 50:
            return False
        
        # Check for sideways price action
        prices = df['close'].iloc[-30:]
        price_range = prices.max() - prices.min()
        avg_price = prices.mean()
        
        sideways_action = price_range / avg_price < 0.05  # Less than 5% range
        
        # Check for consistent volume
        consistent_volume = volume_analysis['trend'] != 'unknown'
        
        return sideways_action and consistent_volume
    
    def _determine_strength_weakness(self, df: pd.DataFrame, volume_analysis: Dict, 
                                   spread_analysis: Dict) -> str:
        """Determine market strength or weakness"""
        # Price momentum
        prices = df['close']
        price_momentum = prices.iloc[-1] / prices.iloc[-20] - 1 if len(prices) >= 20 else 0
        
        # Volume confirmation
        volume_confirmation = volume_analysis['confirmation']
        
        # Spread analysis
        spread_confirmation = spread_analysis['confirmation']
        
        if price_momentum > 0.02 and volume_confirmation:
            return "strength"
        elif price_momentum < -0.02 and volume_confirmation:
            return "weakness"
        elif spread_confirmation:
            return "accumulation"
        else:
            return "neutral"
    
    def _default_analysis(self) -> WyckoffAnalysis:
        """Return default analysis when insufficient data"""
        return WyckoffAnalysis(
            current_phase=WyckoffPhase.PHASE_B,
            phase_confidence=0.3,
            volume_confirmation=False,
            spread_confirmation=False,
            effort_vs_result=0.5,
            cause_building=False,
            spring_action=False,
            upthrust_action=False,
            strength_weakness="neutral"
        )

class FairValueGapHunter:
    """Advanced Fair Value Gap detection with time-sensitive validation"""
    
    def __init__(self, min_gap_size: float = 0.0001):
        self.min_gap_size = min_gap_size
        self.detected_gaps = []
        
    def hunt_fair_value_gaps(self, df: pd.DataFrame) -> List[FairValueGap]:
        """
        Hunt for Fair Value Gaps with institutional validation
        
        Args:
            df: OHLCV data
            
        Returns:
            List of detected Fair Value Gaps
        """
        gaps = []
        
        if len(df) < 3:
            return gaps
        
        for i in range(1, len(df) - 1):
            # Check for bullish FVG
            bullish_gap = self._detect_bullish_fvg(df, i)
            if bullish_gap:
                gaps.append(bullish_gap)
            
            # Check for bearish FVG
            bearish_gap = self._detect_bearish_fvg(df, i)
            if bearish_gap:
                gaps.append(bearish_gap)
        
        # Validate and update gaps
        validated_gaps = self._validate_gaps(gaps, df)
        
        return validated_gaps
    
    def _detect_bullish_fvg(self, df: pd.DataFrame, index: int) -> Optional[FairValueGap]:
        """Detect bullish Fair Value Gap"""
        if index < 1 or index >= len(df) - 1:
            return None
        
        # Three consecutive candles
        candle1 = df.iloc[index - 1]  # First candle
        candle2 = df.iloc[index]      # Middle candle (gap candle)
        candle3 = df.iloc[index + 1]  # Third candle
        
        # Bullish FVG: candle1 high < candle3 low
        if candle1['high'] < candle3['low']:
            gap_high = candle3['low']
            gap_low = candle1['high']
            gap_size = gap_high - gap_low
            
            # Check minimum gap size
            if gap_size >= self.min_gap_size:
                # Calculate time sensitivity
                time_sensitivity = self._calculate_time_sensitivity(df, index)
                
                # Check institutional origin
                institutional_origin = self._check_institutional_origin(df, index)
                
                return FairValueGap(
                    start_index=index - 1,
                    end_index=index + 1,
                    high_price=gap_high,
                    low_price=gap_low,
                    gap_size=gap_size,
                    direction="bullish",
                    filled_percentage=0.0,
                    mitigation_level=gap_low + gap_size * 0.5,  # 50% mitigation
                    time_sensitivity=time_sensitivity,
                    institutional_origin=institutional_origin
                )
        
        return None
    
    def _detect_bearish_fvg(self, df: pd.DataFrame, index: int) -> Optional[FairValueGap]:
        """Detect bearish Fair Value Gap"""
        if index < 1 or index >= len(df) - 1:
            return None
        
        # Three consecutive candles
        candle1 = df.iloc[index - 1]  # First candle
        candle2 = df.iloc[index]      # Middle candle (gap candle)
        candle3 = df.iloc[index + 1]  # Third candle
        
        # Bearish FVG: candle1 low > candle3 high
        if candle1['low'] > candle3['high']:
            gap_high = candle1['low']
            gap_low = candle3['high']
            gap_size = gap_high - gap_low
            
            # Check minimum gap size
            if gap_size >= self.min_gap_size:
                # Calculate time sensitivity
                time_sensitivity = self._calculate_time_sensitivity(df, index)
                
                # Check institutional origin
                institutional_origin = self._check_institutional_origin(df, index)
                
                return FairValueGap(
                    start_index=index - 1,
                    end_index=index + 1,
                    high_price=gap_high,
                    low_price=gap_low,
                    gap_size=gap_size,
                    direction="bearish",
                    filled_percentage=0.0,
                    mitigation_level=gap_high - gap_size * 0.5,  # 50% mitigation
                    time_sensitivity=time_sensitivity,
                    institutional_origin=institutional_origin
                )
        
        return None
    
    def _calculate_time_sensitivity(self, df: pd.DataFrame, index: int) -> float:
        """Calculate time sensitivity of the gap"""
        # Time sensitivity decreases over time
        bars_since_creation = len(df) - index - 1
        
        # Exponential decay with half-life of 20 bars
        time_sensitivity = np.exp(-bars_since_creation / 20)
        
        return max(time_sensitivity, 0.1)  # Minimum 10% sensitivity
    
    def _check_institutional_origin(self, df: pd.DataFrame, index: int) -> bool:
        """Check if gap has institutional origin"""
        if 'volume' not in df.columns:
            return False
        
        # Check volume around gap formation
        gap_volume = df['volume'].iloc[index]
        avg_volume = df['volume'].rolling(20).mean().iloc[index]
        
        # High volume suggests institutional involvement
        high_volume = gap_volume > avg_volume * 1.5
        
        # Check for rapid price movement
        price_movement = abs(df['close'].iloc[index] - df['open'].iloc[index])
        avg_range = (df['high'] - df['low']).rolling(20).mean().iloc[index]
        
        rapid_movement = price_movement > avg_range * 0.8
        
        return high_volume and rapid_movement
    
    def _validate_gaps(self, gaps: List[FairValueGap], df: pd.DataFrame) -> List[FairValueGap]:
        """Validate and update gap information"""
        validated_gaps = []
        
        for gap in gaps:
            # Update filled percentage
            gap.filled_percentage = self._calculate_filled_percentage(gap, df)
            
            # Update time sensitivity
            gap.time_sensitivity = self._calculate_time_sensitivity(df, gap.end_index)
            
            # Only keep gaps that are not fully filled
            if gap.filled_percentage < 1.0:
                validated_gaps.append(gap)
        
        return validated_gaps
    
    def _calculate_filled_percentage(self, gap: FairValueGap, df: pd.DataFrame) -> float:
        """Calculate how much of the gap has been filled"""
        # Look at price action after gap creation
        post_gap_data = df.iloc[gap.end_index + 1:]
        
        if post_gap_data.empty:
            return 0.0
        
        if gap.direction == "bullish":
            # Check how much price has retraced into the gap
            lowest_retrace = post_gap_data['low'].min()
            
            if lowest_retrace >= gap.high_price:
                return 0.0  # No fill
            elif lowest_retrace <= gap.low_price:
                return 1.0  # Fully filled
            else:
                # Partially filled
                filled_amount = gap.high_price - lowest_retrace
                return filled_amount / gap.gap_size
        
        else:  # bearish gap
            # Check how much price has retraced into the gap
            highest_retrace = post_gap_data['high'].max()
            
            if highest_retrace <= gap.low_price:
                return 0.0  # No fill
            elif highest_retrace >= gap.high_price:
                return 1.0  # Fully filled
            else:
                # Partially filled
                filled_amount = highest_retrace - gap.low_price
                return filled_amount / gap.gap_size
        
        return 0.0

class MarketMakerMindModel:
    """Market Maker behavior model with premium/discount zones"""
    
    def __init__(self):
        self.equilibrium_levels = []
        self.premium_discount_history = []
        
    def analyze_premium_discount_zones(self, df: pd.DataFrame) -> PremiumDiscountZone:
        """
        Analyze premium and discount zones from market maker perspective
        
        Args:
            df: OHLCV data
            
        Returns:
            Premium/Discount zone analysis
        """
        if len(df) < 50:
            return self._default_premium_discount()
        
        # Calculate equilibrium (fair value)
        equilibrium = self._calculate_equilibrium(df)
        
        # Calculate premium and discount thresholds
        premium_threshold, discount_threshold = self._calculate_thresholds(df, equilibrium)
        
        # Determine current zone
        current_price = df['close'].iloc[-1]
        zone_type = self._determine_zone_type(current_price, equilibrium, 
                                            premium_threshold, discount_threshold)
        
        # Calculate reversion probability
        reversion_probability = self._calculate_reversion_probability(
            df, current_price, equilibrium, zone_type
        )
        
        # Assess institutional interest
        institutional_interest = self._assess_institutional_interest(df, zone_type)
        
        return PremiumDiscountZone(
            current_level=current_price,
            premium_threshold=premium_threshold,
            discount_threshold=discount_threshold,
            equilibrium=equilibrium,
            zone_type=zone_type,
            reversion_probability=reversion_probability,
            institutional_interest=institutional_interest
        )
    
    def _calculate_equilibrium(self, df: pd.DataFrame) -> float:
        """Calculate market equilibrium (fair value)"""
        # Use multiple methods to determine equilibrium
        
        # Method 1: Volume-weighted average price (VWAP)
        if 'volume' in df.columns:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            vwap = (typical_price * df['volume']).sum() / df['volume'].sum()
        else:
            vwap = df['close'].mean()
        
        # Method 2: Time-weighted average
        time_weighted = df['close'].rolling(50).mean().iloc[-1]
        
        # Method 3: Median price
        median_price = df['close'].median()
        
        # Combine methods
        equilibrium = (vwap * 0.5 + time_weighted * 0.3 + median_price * 0.2)
        
        return equilibrium
    
    def _calculate_thresholds(self, df: pd.DataFrame, equilibrium: float) -> Tuple[float, float]:
        """Calculate premium and discount thresholds"""
        # Use standard deviation to determine thresholds
        price_std = df['close'].rolling(50).std().iloc[-1]
        
        # Premium: 1 standard deviation above equilibrium
        premium_threshold = equilibrium + price_std
        
        # Discount: 1 standard deviation below equilibrium
        discount_threshold = equilibrium - price_std
        
        return premium_threshold, discount_threshold
    
    def _determine_zone_type(self, current_price: float, equilibrium: float,
                           premium_threshold: float, discount_threshold: float) -> str:
        """Determine if current price is in premium, discount, or equilibrium zone"""
        if current_price >= premium_threshold:
            return "premium"
        elif current_price <= discount_threshold:
            return "discount"
        else:
            return "equilibrium"
    
    def _calculate_reversion_probability(self, df: pd.DataFrame, current_price: float,
                                       equilibrium: float, zone_type: str) -> float:
        """Calculate probability of mean reversion"""
        # Base probability
        base_prob = 0.6
        
        # Distance from equilibrium
        distance = abs(current_price - equilibrium) / equilibrium
        
        # Higher distance = higher reversion probability
        distance_factor = min(distance * 10, 0.3)  # Max 30% boost
        
        # Time factor (how long in extreme zone)
        recent_prices = df['close'].iloc[-10:]
        extreme_bars = 0
        
        if zone_type == "premium":
            extreme_bars = sum(1 for price in recent_prices if price >= current_price * 0.99)
        elif zone_type == "discount":
            extreme_bars = sum(1 for price in recent_prices if price <= current_price * 1.01)
        
        time_factor = min(extreme_bars / 10, 0.2)  # Max 20% boost
        
        # Volume factor
        volume_factor = 0
        if 'volume' in df.columns:
            recent_volume = df['volume'].iloc[-5:].mean()
            avg_volume = df['volume'].mean()
            if recent_volume > avg_volume * 1.2:
                volume_factor = 0.1  # High volume increases reversion probability
        
        total_probability = base_prob + distance_factor + time_factor + volume_factor
        
        return min(total_probability, 0.95)  # Max 95% probability
    
    def _assess_institutional_interest(self, df: pd.DataFrame, zone_type: str) -> float:
        """Assess institutional interest in current zone"""
        interest_score = 0.5  # Base interest
        
        # Volume analysis
        if 'volume' in df.columns:
            recent_volume = df['volume'].iloc[-10:].mean()
            avg_volume = df['volume'].mean()
            
            if recent_volume > avg_volume * 1.5:
                interest_score += 0.2  # High volume = high interest
        
        # Price action analysis
        recent_volatility = df['close'].rolling(10).std().iloc[-1]
        avg_volatility = df['close'].rolling(50).std().mean()
        
        if recent_volatility < avg_volatility * 0.7:
            interest_score += 0.1  # Low volatility in extreme zones = accumulation
        
        # Zone-specific adjustments
        if zone_type == "discount":
            interest_score += 0.1  # Institutions prefer buying at discount
        elif zone_type == "premium":
            interest_score += 0.05  # Some interest in selling at premium
        
        return min(interest_score, 1.0)
    
    def _default_premium_discount(self) -> PremiumDiscountZone:
        """Return default premium/discount analysis"""
        return PremiumDiscountZone(
            current_level=0.0,
            premium_threshold=0.0,
            discount_threshold=0.0,
            equilibrium=0.0,
            zone_type="equilibrium",
            reversion_probability=0.5,
            institutional_interest=0.5
        )

class ICTPowerOf3Engine:
    """ICT Power of 3 engine with triple-timeframe confirmation"""
    
    def __init__(self):
        self.power_of_3_history = []
        self.timeframe_data = {}
        
    def analyze_power_of_3(self, df_dict: Dict[str, pd.DataFrame]) -> PowerOf3Analysis:
        """
        Analyze ICT Power of 3 across multiple timeframes
        
        Args:
            df_dict: Dictionary of timeframe data {timeframe: dataframe}
            
        Returns:
            Power of 3 analysis
        """
        # Get primary timeframe (H1 if available)
        primary_tf = 'H1' if 'H1' in df_dict else list(df_dict.keys())[0]
        primary_df = df_dict[primary_tf]
        
        if len(primary_df) < 30:
            return self._default_power_of_3()
        
        # Analyze each phase
        accumulation_phase = self._detect_accumulation_phase(primary_df)
        manipulation_phase = self._detect_manipulation_phase(primary_df)
        distribution_phase = self._detect_distribution_phase(primary_df)
        
        # Determine current phase
        current_phase = self._determine_current_phase(
            accumulation_phase, manipulation_phase, distribution_phase
        )
        
        # Calculate phase completion
        phase_completion = self._calculate_phase_completion(primary_df, current_phase)
        
        # Calculate next phase probability
        next_phase_probability = self._calculate_next_phase_probability(
            current_phase, phase_completion
        )
        
        # Check timeframe alignment
        timeframe_alignment = self._check_timeframe_alignment(df_dict, current_phase)
        
        return PowerOf3Analysis(
            accumulation_phase=accumulation_phase,
            manipulation_phase=manipulation_phase,
            distribution_phase=distribution_phase,
            current_phase=current_phase,
            phase_completion=phase_completion,
            next_phase_probability=next_phase_probability,
            timeframe_alignment=timeframe_alignment
        )
    
    def _detect_accumulation_phase(self, df: pd.DataFrame) -> bool:
        """Detect accumulation phase characteristics"""
        # Accumulation: Sideways price action, decreasing volume
        
        # Price range analysis
        recent_prices = df['close'].iloc[-20:]
        price_range = recent_prices.max() - recent_prices.min()
        avg_price = recent_prices.mean()
        
        sideways_action = price_range / avg_price < 0.03  # Less than 3% range
        
        # Volume analysis
        volume_decreasing = True
        if 'volume' in df.columns:
            recent_volume = df['volume'].iloc[-10:].mean()
            older_volume = df['volume'].iloc[-20:-10].mean()
            volume_decreasing = recent_volume < older_volume
        
        # Low volatility
        volatility = df['close'].rolling(20).std().iloc[-1]
        avg_volatility = df['close'].rolling(50).std().mean()
        low_volatility = volatility < avg_volatility * 0.8
        
        return sideways_action and volume_decreasing and low_volatility
    
    def _detect_manipulation_phase(self, df: pd.DataFrame) -> bool:
        """Detect manipulation phase characteristics"""
        # Manipulation: Sharp moves, stop hunts, false breakouts
        
        # Sharp price movements
        price_changes = df['close'].pct_change().iloc[-10:]
        sharp_moves = any(abs(change) > 0.01 for change in price_changes)  # 1% moves
        
        # Volume spikes during moves
        volume_spikes = False
        if 'volume' in df.columns:
            volume = df['volume'].iloc[-10:]
            avg_volume = df['volume'].rolling(20).mean().iloc[-10:]
            volume_spikes = any(vol > avg_vol * 2 for vol, avg_vol in zip(volume, avg_volume))
        
        # Quick reversals (false breakouts)
        highs = df['high'].iloc[-5:]
        lows = df['low'].iloc[-5:]
        
        recent_high = highs.max()
        recent_low = lows.min()
        current_price = df['close'].iloc[-1]
        
        # Check for quick reversal from extremes
        quick_reversal = (
            (current_price < recent_high * 0.995 and current_price > recent_high * 0.98) or
            (current_price > recent_low * 1.005 and current_price < recent_low * 1.02)
        )
        
        return sharp_moves and (volume_spikes or quick_reversal)
    
    def _detect_distribution_phase(self, df: pd.DataFrame) -> bool:
        """Detect distribution phase characteristics"""
        # Distribution: Sustained move in one direction, increasing volume
        
        # Sustained directional move
        prices = df['close'].iloc[-15:]
        price_trend = np.polyfit(range(len(prices)), prices, 1)[0]
        
        sustained_move = abs(price_trend) > prices.std() * 0.1
        
        # Increasing volume during move
        volume_increasing = True
        if 'volume' in df.columns:
            volume_trend = np.polyfit(range(10), df['volume'].iloc[-10:], 1)[0]
            volume_increasing = volume_trend > 0
        
        # Consistent direction
        recent_changes = df['close'].pct_change().iloc[-10:]
        positive_changes = sum(1 for change in recent_changes if change > 0)
        negative_changes = sum(1 for change in recent_changes if change < 0)
        
        consistent_direction = max(positive_changes, negative_changes) >= 7  # 70% consistency
        
        return sustained_move and volume_increasing and consistent_direction
    
    def _determine_current_phase(self, accumulation: bool, manipulation: bool, 
                               distribution: bool) -> str:
        """Determine current Power of 3 phase"""
        if accumulation and not manipulation and not distribution:
            return "accumulation"
        elif manipulation:
            return "manipulation"
        elif distribution:
            return "distribution"
        elif accumulation and manipulation:
            return "accumulation_to_manipulation"
        elif manipulation and distribution:
            return "manipulation_to_distribution"
        else:
            return "transition"
    
    def _calculate_phase_completion(self, df: pd.DataFrame, current_phase: str) -> float:
        """Calculate how complete the current phase is"""
        # This is a simplified calculation
        # In practice, this would involve more sophisticated analysis
        
        if current_phase == "accumulation":
            # Measure how long price has been sideways
            sideways_bars = 0
            recent_prices = df['close'].iloc[-30:]
            
            for i in range(1, len(recent_prices)):
                change = abs(recent_prices.iloc[i] - recent_prices.iloc[i-1]) / recent_prices.iloc[i-1]
                if change < 0.005:  # Less than 0.5% change
                    sideways_bars += 1
            
            completion = min(sideways_bars / 20, 1.0)  # Max completion at 20 bars
            
        elif current_phase == "manipulation":
            # Measure volatility and sharp moves
            volatility = df['close'].rolling(10).std().iloc[-1]
            avg_volatility = df['close'].rolling(50).std().mean()
            
            completion = min(volatility / (avg_volatility * 2), 1.0)
            
        elif current_phase == "distribution":
            # Measure trend strength and duration
            prices = df['close'].iloc[-20:]
            trend_strength = abs(np.polyfit(range(len(prices)), prices, 1)[0])
            
            completion = min(trend_strength * 1000, 1.0)  # Scale appropriately
            
        else:
            completion = 0.5  # Default for transition phases
        
        return completion
    
    def _calculate_next_phase_probability(self, current_phase: str, completion: float) -> float:
        """Calculate probability of moving to next phase"""
        base_probability = completion * 0.8  # Higher completion = higher probability
        
        # Phase-specific adjustments
        if current_phase == "accumulation":
            # Accumulation can last long, so lower probability
            return min(base_probability * 0.7, 0.8)
        elif current_phase == "manipulation":
            # Manipulation is usually quick, so higher probability
            return min(base_probability * 1.3, 0.9)
        elif current_phase == "distribution":
            # Distribution can vary, moderate probability
            return min(base_probability, 0.85)
        else:
            return base_probability
    
    def _check_timeframe_alignment(self, df_dict: Dict[str, pd.DataFrame], 
                                 current_phase: str) -> Dict[str, bool]:
        """Check phase alignment across timeframes"""
        alignment = {}
        
        for timeframe, df in df_dict.items():
            if len(df) < 20:
                alignment[timeframe] = False
                continue
            
            # Simplified alignment check
            if current_phase == "accumulation":
                # Check for sideways action
                recent_range = df['high'].iloc[-10:].max() - df['low'].iloc[-10:].min()
                avg_price = df['close'].iloc[-10:].mean()
                alignment[timeframe] = recent_range / avg_price < 0.05
                
            elif current_phase == "manipulation":
                # Check for volatility
                volatility = df['close'].rolling(10).std().iloc[-1]
                avg_volatility = df['close'].rolling(30).std().mean()
                alignment[timeframe] = volatility > avg_volatility * 1.2
                
            elif current_phase == "distribution":
                # Check for trend
                prices = df['close'].iloc[-10:]
                trend_strength = abs(np.polyfit(range(len(prices)), prices, 1)[0])
                alignment[timeframe] = trend_strength > prices.std() * 0.05
                
            else:
                alignment[timeframe] = False
        
        return alignment
    
    def _default_power_of_3(self) -> PowerOf3Analysis:
        """Return default Power of 3 analysis"""
        return PowerOf3Analysis(
            accumulation_phase=False,
            manipulation_phase=False,
            distribution_phase=False,
            current_phase="transition",
            phase_completion=0.0,
            next_phase_probability=0.5,
            timeframe_alignment={}
        )

class InstitutionalStrategyEmulator:
    """Main emulator combining all institutional strategy components"""
    
    def __init__(self):
        self.wyckoff_detector = WyckoffAccumulationDetector()
        self.fvg_hunter = FairValueGapHunter()
        self.mm_model = MarketMakerMindModel()
        self.power_of_3_engine = ICTPowerOf3Engine()
        
    def emulate_institutional_strategy(self, df: pd.DataFrame, 
                                     df_dict: Optional[Dict[str, pd.DataFrame]] = None) -> InstitutionalStrategy:
        """
        Comprehensive institutional strategy emulation
        
        Args:
            df: Primary timeframe OHLCV data
            df_dict: Optional multi-timeframe data
            
        Returns:
            Complete institutional strategy analysis
        """
        # Wyckoff analysis
        wyckoff_analysis = self.wyckoff_detector.detect_wyckoff_phase(df)
        
        # Fair Value Gap hunting
        fair_value_gaps = self.fvg_hunter.hunt_fair_value_gaps(df)
        
        # Order block detection (simplified - would be more complex in practice)
        order_blocks = self._detect_order_blocks(df)
        
        # Premium/Discount analysis
        premium_discount = self.mm_model.analyze_premium_discount_zones(df)
        
        # Power of 3 analysis
        if df_dict:
            power_of_3 = self.power_of_3_engine.analyze_power_of_3(df_dict)
        else:
            power_of_3 = self.power_of_3_engine.analyze_power_of_3({'primary': df})
        
        # Determine market maker model
        market_maker_model = self._determine_market_maker_model(
            wyckoff_analysis, premium_discount, power_of_3
        )
        
        # Determine institutional bias
        institutional_bias = self._determine_institutional_bias(
            wyckoff_analysis, fair_value_gaps, premium_discount, power_of_3
        )
        
        # Calculate strategy confidence
        strategy_confidence = self._calculate_strategy_confidence(
            wyckoff_analysis, fair_value_gaps, premium_discount, power_of_3
        )
        
        return InstitutionalStrategy(
            wyckoff_analysis=wyckoff_analysis,
            fair_value_gaps=fair_value_gaps,
            order_blocks=order_blocks,
            premium_discount=premium_discount,
            power_of_3=power_of_3,
            market_maker_model=market_maker_model,
            institutional_bias=institutional_bias,
            strategy_confidence=strategy_confidence
        )
    
    def _detect_order_blocks(self, df: pd.DataFrame) -> List[OrderBlock]:
        """Detect order blocks (simplified implementation)"""
        order_blocks = []
        
        if len(df) < 10:
            return order_blocks
        
        # Look for significant candles followed by moves
        for i in range(5, len(df) - 5):
            candle = df.iloc[i]
            
            # Check for large candle
            candle_size = candle['high'] - candle['low']
            avg_size = (df['high'] - df['low']).rolling(20).mean().iloc[i]
            
            if candle_size > avg_size * 1.5:  # 50% larger than average
                # Check for subsequent move
                future_prices = df['close'].iloc[i+1:i+6]
                
                if len(future_prices) > 0:
                    price_move = future_prices.iloc[-1] - candle['close']
                    
                    # Determine block type
                    if price_move > candle_size * 0.5:  # Bullish move
                        block_type = "bullish"
                    elif price_move < -candle_size * 0.5:  # Bearish move
                        block_type = "bearish"
                    else:
                        continue  # Not significant enough
                    
                    # Volume confirmation
                    volume_confirmation = True
                    if 'volume' in df.columns:
                        avg_volume = df['volume'].rolling(20).mean().iloc[i]
                        volume_confirmation = candle['volume'] > avg_volume * 1.2
                    
                    order_block = OrderBlock(
                        price_high=candle['high'],
                        price_low=candle['low'],
                        timestamp=pd.to_datetime(candle.name) if hasattr(candle.name, 'to_pydatetime') else datetime.now(),
                        block_type=block_type,
                        strength=candle_size / avg_size,
                        volume_confirmation=volume_confirmation,
                        mitigation_count=0,
                        breaker_status=False,
                        institutional_signature=volume_confirmation and candle_size > avg_size * 2
                    )
                    
                    order_blocks.append(order_block)
        
        return order_blocks
    
    def _determine_market_maker_model(self, wyckoff: WyckoffAnalysis, 
                                    premium_discount: PremiumDiscountZone,
                                    power_of_3: PowerOf3Analysis) -> MarketMakerModel:
        """Determine active market maker model"""
        
        # Accumulation model
        if (wyckoff.current_phase in [WyckoffPhase.ACCUMULATION, WyckoffPhase.PHASE_B] or
            power_of_3.accumulation_phase):
            return MarketMakerModel.ACCUMULATION_MODEL
        
        # Distribution model
        if (wyckoff.current_phase in [WyckoffPhase.DISTRIBUTION, WyckoffPhase.PHASE_D] or
            power_of_3.distribution_phase):
            return MarketMakerModel.DISTRIBUTION_MODEL
        
        # Manipulation model
        if power_of_3.manipulation_phase or wyckoff.spring_action or wyckoff.upthrust_action:
            return MarketMakerModel.MANIPULATION_MODEL
        
        # Rebalancing model
        if premium_discount.zone_type == "equilibrium":
            return MarketMakerModel.REBALANCING_MODEL
        
        # Default to hedging
        return MarketMakerModel.HEDGING_MODEL
    
    def _determine_institutional_bias(self, wyckoff: WyckoffAnalysis,
                                    fair_value_gaps: List[FairValueGap],
                                    premium_discount: PremiumDiscountZone,
                                    power_of_3: PowerOf3Analysis) -> str:
        """Determine overall institutional bias"""
        
        bullish_signals = 0
        bearish_signals = 0
        
        # Wyckoff signals
        if wyckoff.strength_weakness == "strength":
            bullish_signals += 1
        elif wyckoff.strength_weakness == "weakness":
            bearish_signals += 1
        
        if wyckoff.spring_action:
            bullish_signals += 1
        if wyckoff.upthrust_action:
            bearish_signals += 1
        
        # FVG signals
        recent_fvgs = fair_value_gaps[-3:] if len(fair_value_gaps) >= 3 else fair_value_gaps
        for fvg in recent_fvgs:
            if fvg.direction == "bullish" and fvg.filled_percentage < 0.5:
                bullish_signals += 1
            elif fvg.direction == "bearish" and fvg.filled_percentage < 0.5:
                bearish_signals += 1
        
        # Premium/Discount signals
        if premium_discount.zone_type == "discount":
            bullish_signals += 1
        elif premium_discount.zone_type == "premium":
            bearish_signals += 1
        
        # Power of 3 signals
        if power_of_3.current_phase == "distribution" and power_of_3.phase_completion > 0.7:
            # Distribution phase nearing completion suggests reversal
            if power_of_3.accumulation_phase:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Determine bias
        if bullish_signals > bearish_signals + 1:
            return "bullish"
        elif bearish_signals > bullish_signals + 1:
            return "bearish"
        else:
            return "neutral"
    
    def _calculate_strategy_confidence(self, wyckoff: WyckoffAnalysis,
                                     fair_value_gaps: List[FairValueGap],
                                     premium_discount: PremiumDiscountZone,
                                     power_of_3: PowerOf3Analysis) -> float:
        """Calculate overall strategy confidence"""
        
        confidence_factors = []
        
        # Wyckoff confidence
        confidence_factors.append(wyckoff.phase_confidence)
        
        # Volume and spread confirmation
        if wyckoff.volume_confirmation:
            confidence_factors.append(0.8)
        if wyckoff.spread_confirmation:
            confidence_factors.append(0.7)
        
        # FVG confidence
        if fair_value_gaps:
            avg_fvg_confidence = np.mean([fvg.time_sensitivity for fvg in fair_value_gaps])
            confidence_factors.append(avg_fvg_confidence)
        
        # Premium/Discount confidence
        confidence_factors.append(premium_discount.reversion_probability)
        
        # Power of 3 confidence
        confidence_factors.append(power_of_3.next_phase_probability)
        
        # Timeframe alignment
        if power_of_3.timeframe_alignment:
            alignment_ratio = sum(power_of_3.timeframe_alignment.values()) / len(power_of_3.timeframe_alignment)
            confidence_factors.append(alignment_ratio)
        
        # Calculate weighted average
        if confidence_factors:
            overall_confidence = np.mean(confidence_factors)
        else:
            overall_confidence = 0.5
        
        return min(overall_confidence, 0.95)  # Max 95% confidence
    
    def get_trading_signals(self, strategy: InstitutionalStrategy) -> Dict[str, Any]:
        """Generate trading signals from institutional strategy analysis"""
        
        signals = {
            'wyckoff_signal': self._generate_wyckoff_signal(strategy.wyckoff_analysis),
            'fvg_signal': self._generate_fvg_signal(strategy.fair_value_gaps),
            'premium_discount_signal': self._generate_premium_discount_signal(strategy.premium_discount),
            'power_of_3_signal': self._generate_power_of_3_signal(strategy.power_of_3),
            'overall_signal': None
        }
        
        # Generate overall signal
        signals['overall_signal'] = self._generate_overall_institutional_signal(strategy, signals)
        
        return signals
    
    def _generate_wyckoff_signal(self, wyckoff: WyckoffAnalysis) -> Dict[str, Any]:
        """Generate signal from Wyckoff analysis"""
        
        if wyckoff.spring_action:
            signal = 'buy'
            strength = 0.8
        elif wyckoff.upthrust_action:
            signal = 'sell'
            strength = 0.8
        elif wyckoff.strength_weakness == "strength":
            signal = 'bullish_bias'
            strength = 0.6
        elif wyckoff.strength_weakness == "weakness":
            signal = 'bearish_bias'
            strength = 0.6
        else:
            signal = 'neutral'
            strength = 0.3
        
        return {
            'signal': signal,
            'strength': strength,
            'phase': wyckoff.current_phase.value,
            'confidence': wyckoff.phase_confidence,
            'volume_confirmation': wyckoff.volume_confirmation
        }
    
    def _generate_fvg_signal(self, fair_value_gaps: List[FairValueGap]) -> Dict[str, Any]:
        """Generate signal from Fair Value Gaps"""
        
        if not fair_value_gaps:
            return {'signal': 'neutral', 'strength': 0}
        
        # Find most relevant FVG
        active_fvgs = [fvg for fvg in fair_value_gaps if fvg.filled_percentage < 0.8]
        
        if not active_fvgs:
            return {'signal': 'neutral', 'strength': 0}
        
        # Get most recent or strongest FVG
        best_fvg = max(active_fvgs, key=lambda x: x.time_sensitivity * (1 - x.filled_percentage))
        
        if best_fvg.direction == "bullish":
            signal = 'buy_fvg_retest'
        else:
            signal = 'sell_fvg_retest'
        
        strength = best_fvg.time_sensitivity * (1 - best_fvg.filled_percentage)
        
        return {
            'signal': signal,
            'strength': strength,
            'fvg_price': best_fvg.mitigation_level,
            'gap_size': best_fvg.gap_size,
            'institutional_origin': best_fvg.institutional_origin
        }
    
    def _generate_premium_discount_signal(self, premium_discount: PremiumDiscountZone) -> Dict[str, Any]:
        """Generate signal from Premium/Discount analysis"""
        
        if premium_discount.zone_type == "discount":
            signal = 'buy_discount'
            strength = premium_discount.institutional_interest
        elif premium_discount.zone_type == "premium":
            signal = 'sell_premium'
            strength = premium_discount.institutional_interest
        else:
            signal = 'equilibrium'
            strength = 0.5
        
        return {
            'signal': signal,
            'strength': strength,
            'zone_type': premium_discount.zone_type,
            'reversion_probability': premium_discount.reversion_probability,
            'equilibrium': premium_discount.equilibrium
        }
    
    def _generate_power_of_3_signal(self, power_of_3: PowerOf3Analysis) -> Dict[str, Any]:
        """Generate signal from Power of 3 analysis"""
        
        if power_of_3.current_phase == "accumulation":
            signal = 'accumulation_phase'
            strength = 0.6
        elif power_of_3.current_phase == "manipulation":
            signal = 'manipulation_phase'
            strength = 0.8  # High importance
        elif power_of_3.current_phase == "distribution":
            signal = 'distribution_phase'
            strength = 0.7
        else:
            signal = 'transition_phase'
            strength = 0.4
        
        return {
            'signal': signal,
            'strength': strength,
            'phase_completion': power_of_3.phase_completion,
            'next_phase_probability': power_of_3.next_phase_probability,
            'timeframe_alignment': power_of_3.timeframe_alignment
        }
    
    def _generate_overall_institutional_signal(self, strategy: InstitutionalStrategy,
                                             signals: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall institutional signal"""
        
        # Extract signal strengths
        wyckoff_strength = signals['wyckoff_signal']['strength']
        fvg_strength = signals['fvg_signal']['strength']
        premium_discount_strength = signals['premium_discount_signal']['strength']
        power_of_3_strength = signals['power_of_3_signal']['strength']
        
        # Weighted combination
        overall_strength = (
            wyckoff_strength * 0.3 +
            fvg_strength * 0.25 +
            premium_discount_strength * 0.25 +
            power_of_3_strength * 0.2
        )
        
        # Determine direction from institutional bias
        direction = strategy.institutional_bias
        
        # Quality assessment
        if overall_strength > 0.7 and strategy.strategy_confidence > 0.7:
            quality = 'high'
        elif overall_strength > 0.5 and strategy.strategy_confidence > 0.5:
            quality = 'medium'
        else:
            quality = 'low'
        
        return {
            'direction': direction,
            'strength': overall_strength,
            'quality': quality,
            'confidence': strategy.strategy_confidence,
            'market_maker_model': strategy.market_maker_model.value,
            'components': {
                'wyckoff': wyckoff_strength,
                'fvg': fvg_strength,
                'premium_discount': premium_discount_strength,
                'power_of_3': power_of_3_strength
            }
        }
