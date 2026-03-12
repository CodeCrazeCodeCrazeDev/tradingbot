"""Wyckoff phase detection and market cycle analysis.

Simplified implementation of Wyckoff market cycle phases:
1. Accumulation (sideways, low volatility, absorption)
2. Markup (uptrend, higher highs, higher lows)
3. Distribution (sideways, high volatility, supply entering)
4. Markdown (downtrend, lower highs, lower lows)

Uses volume, price action, and volatility to identify phases.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd  # type: ignore

from trading_bot.analysis.market_structure import MarketStructureAnalyzer, SwingPoint
from enum import Enum
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class WyckoffPhase(enum.Enum):
    """Wyckoff market cycle phases."""

    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class PhaseChange:
    """Represents a change in Wyckoff phase."""

    idx: int  # bar index where phase changed
    old_phase: WyckoffPhase
    new_phase: WyckoffPhase
    confidence: float  # 0-100


class WyckoffAnalyzer:  # noqa: B024
    """Detect Wyckoff phases and market cycles."""

    def __init__(self, lookback: int = 50, volatility_window: int = 20) -> None:
        """Initialize with detection parameters.

        Args:
            lookback: Number of bars to analyze for phase detection
            volatility_window: Window for ATR calculation
        """
        try:
            self.lookback = lookback
            self.volatility_window = volatility_window
            self.msa = MarketStructureAnalyzer(swing_len=3)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_phase(self, df: pd.DataFrame) -> WyckoffPhase:
        """Detect current Wyckoff phase based on price action and volume."""
        try:
            if len(df) < self.lookback:
                return WyckoffPhase.UNKNOWN

            # Get recent data subset
            recent = df.iloc[-self.lookback:]
        
            # Calculate volatility (ATR)
            atr = self._calculate_atr(recent)
        
            # Get swing points
            highs, lows = self.msa.find_swings(recent)
        
            # Check for higher highs/lows and lower highs/lows
            higher_highs = self._check_higher_highs(highs)
            higher_lows = self._check_higher_lows(lows)
            lower_highs = self._check_lower_highs(highs)
            lower_lows = self._check_lower_lows(lows)
        
            # Check volume characteristics
            volume_increasing = self._is_volume_increasing(recent)
            volume_decreasing = self._is_volume_decreasing(recent)
        
            # Price range as percentage of average price
            price_range = (recent['high'].max() - recent['low'].min()) / recent['close'].mean()
        
            # Determine phase based on characteristics
            if higher_highs and higher_lows:
                return WyckoffPhase.MARKUP
            elif lower_highs and lower_lows:
                return WyckoffPhase.MARKDOWN
            elif price_range < 0.02 and not (higher_highs or lower_lows):  # tight range (2%)
                if recent['close'].iloc[-1] < recent['close'].mean():
                    return WyckoffPhase.ACCUMULATION
                else:
                    return WyckoffPhase.DISTRIBUTION
                
            # Default if no clear pattern
            return WyckoffPhase.UNKNOWN
        except Exception as e:
            logger.error(f"Error in detect_phase: {e}")
            raise

    def detect_phase_changes(self, df: pd.DataFrame, min_bars: int = 10) -> List[PhaseChange]:
        """Detect changes in Wyckoff phases over the entire dataset."""
        try:
            if len(df) < self.lookback:
                return []
            
            changes: List[PhaseChange] = []
            current_phase = WyckoffPhase.UNKNOWN
            phase_start_idx = 0
        
            # Step through data in chunks to detect phase changes
            for i in range(self.lookback, len(df), min_bars):
                chunk = df.iloc[:i]
                new_phase = self.detect_phase(chunk)
            
                if new_phase != current_phase and new_phase != WyckoffPhase.UNKNOWN:
                    # Calculate confidence based on how long we've been in the previous phase
                    confidence = min(100.0, (i - phase_start_idx) / 5)
                
                    changes.append(
                        PhaseChange(
                            idx=i,
                            old_phase=current_phase,
                            new_phase=new_phase,
                            confidence=confidence
                        )
                    )
                    current_phase = new_phase
                    phase_start_idx = i
                
            return changes
        except Exception as e:
            logger.error(f"Error in detect_phase_changes: {e}")
            raise

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    
    def _calculate_atr(self, df: pd.DataFrame) -> float:
        """Calculate Average True Range."""
        try:
            window = min(self.volatility_window, len(df))
        
            # True Range calculation
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
        
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
        
            # Average True Range
            atr = true_range.rolling(window=window).mean().iloc[-1]
            return float(atr) if not pd.isna(atr) else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_atr: {e}")
            raise
    
    def _check_higher_highs(self, highs: List[SwingPoint]) -> bool:
        """Check if we have higher swing highs."""
        try:
            if len(highs) < 2:
                return False
            return highs[-1].price > highs[-2].price
        except Exception as e:
            logger.error(f"Error in _check_higher_highs: {e}")
            raise
    
    def _check_higher_lows(self, lows: List[SwingPoint]) -> bool:
        """Check if we have higher swing lows."""
        try:
            if len(lows) < 2:
                return False
            return lows[-1].price > lows[-2].price
        except Exception as e:
            logger.error(f"Error in _check_higher_lows: {e}")
            raise
    
    def _check_lower_highs(self, highs: List[SwingPoint]) -> bool:
        """Check if we have lower swing highs."""
        try:
            if len(highs) < 2:
                return False
            return highs[-1].price < highs[-2].price
        except Exception as e:
            logger.error(f"Error in _check_lower_highs: {e}")
            raise
    
    def _check_lower_lows(self, lows: List[SwingPoint]) -> bool:
        """Check if we have lower swing lows."""
        try:
            if len(lows) < 2:
                return False
            return lows[-1].price < lows[-2].price
        except Exception as e:
            logger.error(f"Error in _check_lower_lows: {e}")
            raise
    
    def _is_volume_increasing(self, df: pd.DataFrame) -> bool:
        """Check if volume is generally increasing."""
        try:
            if 'volume' not in df.columns or len(df) < 10:
                return False
        
            recent_vol = df['volume'].iloc[-10:].mean()
            earlier_vol = df['volume'].iloc[-20:-10].mean()
        
            return recent_vol > earlier_vol * 1.1  # 10% increase
        except Exception as e:
            logger.error(f"Error in _is_volume_increasing: {e}")
            raise
    
    def _is_volume_decreasing(self, df: pd.DataFrame) -> bool:
        """Check if volume is generally decreasing."""
        try:
            if 'volume' not in df.columns or len(df) < 10:
                return False
        
            recent_vol = df['volume'].iloc[-10:].mean()
            earlier_vol = df['volume'].iloc[-20:-10].mean()
        
            return recent_vol < earlier_vol * 0.9  # 10% decrease
        except Exception as e:
            logger.error(f"Error in _is_volume_decreasing: {e}")
            raise
