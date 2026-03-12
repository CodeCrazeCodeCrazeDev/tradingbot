"""
Skill #15: Sweep Detection System
=================================

Detects aggressive liquidity sweeps where large orders
take out multiple price levels rapidly.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SweepType(Enum):
    """Type of liquidity sweep."""
    BUY_SWEEP = "buy_sweep"  # Aggressive buying through asks
    SELL_SWEEP = "sell_sweep"  # Aggressive selling through bids
    STOP_SWEEP = "stop_sweep"  # Sweep targeting stops
    ICEBERG_SWEEP = "iceberg_sweep"  # Sweep through hidden liquidity


class SweepIntensity(Enum):
    """Intensity of the sweep."""
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    EXTREME = "extreme"


@dataclass
class LiquiditySweep:
    """Detected liquidity sweep."""
    timestamp: datetime
    sweep_type: SweepType
    intensity: SweepIntensity
    start_price: float
    end_price: float
    levels_swept: int
    volume_swept: float
    duration_bars: int
    is_reversal_likely: bool
    continuation_probability: float


@dataclass
class SweepAnalysisResult:
    """Complete sweep detection result."""
    detected_sweeps: List[LiquiditySweep]
    active_sweep: Optional[LiquiditySweep]
    sweep_direction: Optional[str]
    total_buy_sweeps: int
    total_sell_sweeps: int
    sweep_imbalance: float
    key_sweep_levels: List[float]
    post_sweep_bias: str
    trading_signal: str
    confidence: float


class SweepDetectionSystem:
    """
    Advanced Liquidity Sweep Detection System.
    
    Identifies aggressive liquidity taking through multiple levels.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_levels = self.config.get('min_levels', 3)
        self.volume_multiplier = self.config.get('volume_multiplier', 2.0)
        self.sweep_history: List[LiquiditySweep] = []
        
        logger.info("SweepDetectionSystem initialized")
    
    def analyze(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> SweepAnalysisResult:
        """
        Analyze for liquidity sweeps.
        
        Args:
            highs: Array of high prices
            lows: Array of low prices
            closes: Array of close prices
            volumes: Array of volumes
            timestamps: List of timestamps
            
        Returns:
            SweepAnalysisResult with detected sweeps
        """
        if len(closes) < 10:
            return self._create_empty_result()
        
        # Detect sweeps
        sweeps = self._detect_sweeps(highs, lows, closes, volumes, timestamps)
        
        # Update history
        self.sweep_history.extend(sweeps)
        if len(self.sweep_history) > 100:
            self.sweep_history = self.sweep_history[-100:]
        
        # Check for active sweep
        active_sweep = self._check_active_sweep(sweeps, closes[-1])
        
        # Determine sweep direction
        sweep_direction = None
        if active_sweep:
            sweep_direction = 'up' if active_sweep.sweep_type == SweepType.BUY_SWEEP else 'down'
        
        # Count sweeps
        buy_sweeps = sum(1 for s in sweeps if s.sweep_type == SweepType.BUY_SWEEP)
        sell_sweeps = sum(1 for s in sweeps if s.sweep_type == SweepType.SELL_SWEEP)
        
        # Calculate imbalance
        total = buy_sweeps + sell_sweeps
        imbalance = (buy_sweeps - sell_sweeps) / (total + 1e-10)
        
        # Find key levels
        key_levels = self._find_key_sweep_levels(sweeps)
        
        # Determine post-sweep bias
        bias = self._determine_post_sweep_bias(sweeps, closes)
        
        # Generate signal
        signal = self._generate_signal(
            sweeps, active_sweep, imbalance, bias
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(sweeps, active_sweep)
        
        return SweepAnalysisResult(
            detected_sweeps=sweeps,
            active_sweep=active_sweep,
            sweep_direction=sweep_direction,
            total_buy_sweeps=buy_sweeps,
            total_sell_sweeps=sell_sweeps,
            sweep_imbalance=imbalance,
            key_sweep_levels=key_levels,
            post_sweep_bias=bias,
            trading_signal=signal,
            confidence=confidence
        )
    
    def _detect_sweeps(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime]
    ) -> List[LiquiditySweep]:
        """Detect liquidity sweeps in the data."""
        sweeps = []
        avg_volume = np.mean(volumes)
        avg_range = np.mean(highs - lows)
        
        for i in range(5, len(closes)):
            # Check for buy sweep (aggressive move up)
            buy_sweep = self._check_buy_sweep(
                i, highs, lows, closes, volumes, avg_volume, avg_range, timestamps
            )
            if buy_sweep:
                sweeps.append(buy_sweep)
            
            # Check for sell sweep (aggressive move down)
            sell_sweep = self._check_sell_sweep(
                i, highs, lows, closes, volumes, avg_volume, avg_range, timestamps
            )
            if sell_sweep:
                sweeps.append(sell_sweep)
        
        return sweeps
    
    def _check_buy_sweep(
        self,
        idx: int,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        avg_volume: float,
        avg_range: float,
        timestamps: List[datetime]
    ) -> Optional[LiquiditySweep]:
        """Check for buy sweep at index."""
        # Look at recent bars
        window = 5
        start_idx = max(0, idx - window)
        
        window_highs = highs[start_idx:idx+1]
        window_lows = lows[start_idx:idx+1]
        window_volumes = volumes[start_idx:idx+1]
        window_closes = closes[start_idx:idx+1]
        
        # Calculate move
        price_move = np.max(window_highs) - np.min(window_lows)
        
        # Check for significant upward sweep
        if price_move > avg_range * 3:
            # High volume confirms sweep
            total_volume = np.sum(window_volumes)
            
            if total_volume > avg_volume * window * self.volume_multiplier:
                # Count levels swept
                levels = int(price_move / (avg_range / 3))
                
                # Determine intensity
                intensity = self._classify_intensity(
                    price_move / avg_range,
                    total_volume / (avg_volume * window)
                )
                
                # Check if reversal likely
                is_reversal = window_closes[-1] < np.max(window_highs) * 0.995
                
                # Continuation probability
                continuation = 0.6 if not is_reversal else 0.3
                
                return LiquiditySweep(
                    timestamp=timestamps[idx],
                    sweep_type=SweepType.BUY_SWEEP,
                    intensity=intensity,
                    start_price=np.min(window_lows),
                    end_price=np.max(window_highs),
                    levels_swept=levels,
                    volume_swept=total_volume,
                    duration_bars=window,
                    is_reversal_likely=is_reversal,
                    continuation_probability=continuation
                )
        
        return None
    
    def _check_sell_sweep(
        self,
        idx: int,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        avg_volume: float,
        avg_range: float,
        timestamps: List[datetime]
    ) -> Optional[LiquiditySweep]:
        """Check for sell sweep at index."""
        window = 5
        start_idx = max(0, idx - window)
        
        window_highs = highs[start_idx:idx+1]
        window_lows = lows[start_idx:idx+1]
        window_volumes = volumes[start_idx:idx+1]
        window_closes = closes[start_idx:idx+1]
        
        price_move = np.max(window_highs) - np.min(window_lows)
        
        # Check for significant downward sweep
        if price_move > avg_range * 3:
            total_volume = np.sum(window_volumes)
            
            if total_volume > avg_volume * window * self.volume_multiplier:
                # Confirm it's a down move
                if window_closes[-1] < window_closes[0]:
                    levels = int(price_move / (avg_range / 3))
                    
                    intensity = self._classify_intensity(
                        price_move / avg_range,
                        total_volume / (avg_volume * window)
                    )
                    
                    is_reversal = window_closes[-1] > np.min(window_lows) * 1.005
                    continuation = 0.6 if not is_reversal else 0.3
                    
                    return LiquiditySweep(
                        timestamp=timestamps[idx],
                        sweep_type=SweepType.SELL_SWEEP,
                        intensity=intensity,
                        start_price=np.max(window_highs),
                        end_price=np.min(window_lows),
                        levels_swept=levels,
                        volume_swept=total_volume,
                        duration_bars=window,
                        is_reversal_likely=is_reversal,
                        continuation_probability=continuation
                    )
        
        return None
    
    def _classify_intensity(
        self,
        price_ratio: float,
        volume_ratio: float
    ) -> SweepIntensity:
        """Classify sweep intensity."""
        combined = (price_ratio + volume_ratio) / 2
        
        if combined > 5:
            return SweepIntensity.EXTREME
        elif combined > 3:
            return SweepIntensity.HEAVY
        elif combined > 2:
            return SweepIntensity.MODERATE
        else:
            return SweepIntensity.LIGHT
    
    def _check_active_sweep(
        self,
        sweeps: List[LiquiditySweep],
        current_price: float
    ) -> Optional[LiquiditySweep]:
        """Check if a sweep is currently active."""
        if not sweeps:
            return None
        
        # Check most recent sweep
        latest = sweeps[-1]
        
        # Is price still within sweep range?
        if latest.sweep_type == SweepType.BUY_SWEEP:
            if current_price >= latest.start_price and current_price <= latest.end_price * 1.01:
                return latest
        else:
            if current_price <= latest.start_price and current_price >= latest.end_price * 0.99:
                return latest
        
        return None
    
    def _find_key_sweep_levels(
        self,
        sweeps: List[LiquiditySweep]
    ) -> List[float]:
        """Find key price levels from sweeps."""
        levels = []
        
        for sweep in sweeps:
            levels.append(sweep.start_price)
            levels.append(sweep.end_price)
        
        # Remove duplicates and sort
        levels = list(set(levels))
        levels.sort()
        
        return levels[:10]
    
    def _determine_post_sweep_bias(
        self,
        sweeps: List[LiquiditySweep],
        closes: np.ndarray
    ) -> str:
        """Determine bias after sweeps."""
        if not sweeps:
            return "neutral"
        
        # Look at recent sweeps
        recent = sweeps[-3:] if len(sweeps) >= 3 else sweeps
        
        # Count reversals
        reversals = sum(1 for s in recent if s.is_reversal_likely)
        
        if reversals > len(recent) / 2:
            # Most sweeps reversed - fade the sweep
            last_sweep = recent[-1]
            if last_sweep.sweep_type == SweepType.BUY_SWEEP:
                return "bearish_reversal"
            else:
                return "bullish_reversal"
        else:
            # Sweeps continued - follow the sweep
            last_sweep = recent[-1]
            if last_sweep.sweep_type == SweepType.BUY_SWEEP:
                return "bullish_continuation"
            else:
                return "bearish_continuation"
    
    def _generate_signal(
        self,
        sweeps: List[LiquiditySweep],
        active_sweep: Optional[LiquiditySweep],
        imbalance: float,
        bias: str
    ) -> str:
        """Generate trading signal."""
        signals = []
        
        if active_sweep:
            signals.append(
                f"ACTIVE {active_sweep.sweep_type.value.upper()}: "
                f"{active_sweep.levels_swept} levels, "
                f"{active_sweep.intensity.value} intensity"
            )
            
            if active_sweep.is_reversal_likely:
                signals.append("REVERSAL LIKELY - fade the sweep")
            else:
                signals.append("CONTINUATION LIKELY - follow the sweep")
        
        # Imbalance signal
        if imbalance > 0.3:
            signals.append("BUY SWEEP DOMINANT - bullish pressure")
        elif imbalance < -0.3:
            signals.append("SELL SWEEP DOMINANT - bearish pressure")
        
        # Bias signal
        if 'bullish' in bias:
            signals.append(f"BIAS: {bias.upper()}")
        elif 'bearish' in bias:
            signals.append(f"BIAS: {bias.upper()}")
        
        # Recent sweep count
        if sweeps:
            signals.append(f"SWEEPS DETECTED: {len(sweeps)}")
        
        return " | ".join(signals) if signals else "No significant sweeps detected"
    
    def _calculate_confidence(
        self,
        sweeps: List[LiquiditySweep],
        active_sweep: Optional[LiquiditySweep]
    ) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5
        
        # More sweeps = more confidence
        if len(sweeps) >= 5:
            confidence += 0.15
        elif len(sweeps) >= 3:
            confidence += 0.1
        
        # Active sweep adds confidence
        if active_sweep:
            confidence += 0.15
            
            # High intensity adds more
            if active_sweep.intensity in [SweepIntensity.HEAVY, SweepIntensity.EXTREME]:
                confidence += 0.1
        
        return min(1.0, confidence)
    
    def _create_empty_result(self) -> SweepAnalysisResult:
        """Create empty result for insufficient data."""
        return SweepAnalysisResult(
            detected_sweeps=[],
            active_sweep=None,
            sweep_direction=None,
            total_buy_sweeps=0,
            total_sell_sweeps=0,
            sweep_imbalance=0,
            key_sweep_levels=[],
            post_sweep_bias="neutral",
            trading_signal="Insufficient data",
            confidence=0
        )
