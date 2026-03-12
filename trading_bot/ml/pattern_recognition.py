"""Pattern recognition module for technical analysis."""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from enum import Enum
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of technical patterns."""
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    HEAD_AND_SHOULDERS = "head_and_shoulders"
    INVERSE_HS = "inverse_head_and_shoulders"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    BULL_PENNANT = "bull_pennant"
    BEAR_PENNANT = "bear_pennant"
    RISING_WEDGE = "rising_wedge"
    FALLING_WEDGE = "falling_wedge"

class PatternRecognizer:
    """Advanced pattern recognition using ML techniques."""
    
    def __init__(self):
        """Initialize pattern recognizer."""
        try:
            self.patterns = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def detect_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect patterns in price data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of detected patterns with metadata
        """
        try:
            patterns = []
        
            # Detect double tops/bottoms
            double_patterns = self._detect_double_patterns(df)
            patterns.extend(double_patterns)
        
            # Detect head and shoulders
            hs_patterns = self._detect_head_and_shoulders(df)
            patterns.extend(hs_patterns)
        
            # Detect triangles
            triangle_patterns = self._detect_triangles(df)
            patterns.extend(triangle_patterns)
        
            # Detect flags and pennants
            flag_patterns = self._detect_flags_pennants(df)
            patterns.extend(flag_patterns)
        
            # Detect wedges
            wedge_patterns = self._detect_wedges(df)
            patterns.extend(wedge_patterns)
        
            return patterns
        except Exception as e:
            logger.error(f"Error in detect_patterns: {e}")
            raise
    
    def _detect_double_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect double top and double bottom patterns."""
        try:
            patterns = []
        
            # Get highs and lows
            highs = df['high'].values
            lows = df['low'].values
        
            # Look for double tops
            for i in range(1, len(highs)-1):
                # Look for similar highs
                if abs(highs[i] - highs[i-1]) < 0.0005:  # Within 5 pips
                    # Check for price drop between peaks
                    if min(lows[i-1:i+1]) < highs[i] - 0.001:  # At least 10 pips
                        patterns.append({
                            'type': PatternType.DOUBLE_TOP,
                            'direction': 'sell',
                            'confidence': 75.0,
                            'suggested_stop_pips': 15,
                            'suggested_rr': 2.0,
                            'name': 'Double Top'
                        })
        
            # Look for double bottoms
            for i in range(1, len(lows)-1):
                # Look for similar lows
                if abs(lows[i] - lows[i-1]) < 0.0005:  # Within 5 pips
                    # Check for price rise between troughs
                    if max(highs[i-1:i+1]) > lows[i] + 0.001:  # At least 10 pips
                        patterns.append({
                            'type': PatternType.DOUBLE_BOTTOM,
                            'direction': 'buy',
                            'confidence': 75.0,
                            'suggested_stop_pips': 15,
                            'suggested_rr': 2.0,
                            'name': 'Double Bottom'
                        })
        
            return patterns
        except Exception as e:
            logger.error(f"Error in _detect_double_patterns: {e}")
            raise
    
    def _detect_head_and_shoulders(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect head and shoulders patterns."""
        try:
            patterns = []
        
            # Get highs and lows
            highs = df['high'].values
            lows = df['low'].values
        
            # Look for head and shoulders
            for i in range(2, len(highs)-2):
                # Check for left shoulder, head, right shoulder formation
                if (highs[i] > highs[i-2] and highs[i] > highs[i+2] and  # Head higher than shoulders
                    abs(highs[i-2] - highs[i+2]) < 0.0005):  # Similar shoulder heights
                    patterns.append({
                        'type': PatternType.HEAD_AND_SHOULDERS,
                        'direction': 'sell',
                        'confidence': 80.0,
                        'suggested_stop_pips': 20,
                        'suggested_rr': 2.5,
                        'name': 'Head and Shoulders'
                    })
        
            # Look for inverse head and shoulders
            for i in range(2, len(lows)-2):
                # Check for left shoulder, head, right shoulder formation
                if (lows[i] < lows[i-2] and lows[i] < lows[i+2] and  # Head lower than shoulders
                    abs(lows[i-2] - lows[i+2]) < 0.0005):  # Similar shoulder heights
                    patterns.append({
                        'type': PatternType.INVERSE_HS,
                        'direction': 'buy',
                        'confidence': 80.0,
                        'suggested_stop_pips': 20,
                        'suggested_rr': 2.5,
                        'name': 'Inverse Head and Shoulders'
                    })
        
            return patterns
        except Exception as e:
            logger.error(f"Error in _detect_head_and_shoulders: {e}")
            raise
    
    def _detect_triangles(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect triangle patterns."""
        try:
            patterns = []
        
            # Get highs and lows
            highs = df['high'].values
            lows = df['low'].values
        
            # Look for ascending triangles
            for i in range(5, len(df)):
                window = df.iloc[i-5:i]
                resistance = window['high'].mean()
            
                # Check for flat resistance and rising support
                if (max(abs(window['high'] - resistance)) < 0.0005 and  # Flat resistance
                    window['low'].is_monotonic_increasing):  # Rising support
                    patterns.append({
                        'type': PatternType.ASCENDING_TRIANGLE,
                        'direction': 'buy',
                        'confidence': 70.0,
                        'suggested_stop_pips': 15,
                        'suggested_rr': 2.0,
                        'name': 'Ascending Triangle'
                    })
        
            # Look for descending triangles
            for i in range(5, len(df)):
                window = df.iloc[i-5:i]
                support = window['low'].mean()
            
                # Check for flat support and falling resistance
                if (max(abs(window['low'] - support)) < 0.0005 and  # Flat support
                    window['high'].is_monotonic_decreasing):  # Falling resistance
                    patterns.append({
                        'type': PatternType.DESCENDING_TRIANGLE,
                        'direction': 'sell',
                        'confidence': 70.0,
                        'suggested_stop_pips': 15,
                        'suggested_rr': 2.0,
                        'name': 'Descending Triangle'
                    })
        
            return patterns
        except Exception as e:
            logger.error(f"Error in _detect_triangles: {e}")
            raise
    
    def _detect_flags_pennants(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect flag and pennant patterns."""
        try:
            patterns = []
        
            # Get price data
            closes = df['close'].values
        
            # Look for bull flags
            for i in range(10, len(df)):
                # Check for strong uptrend followed by consolidation
                if (closes[i-10:i-5].mean() < closes[i-5:i].mean() and  # Uptrend
                    max(closes[i-5:i]) - min(closes[i-5:i]) < 0.001):  # Tight consolidation
                    patterns.append({
                        'type': PatternType.BULL_FLAG,
                        'direction': 'buy',
                        'confidence': 65.0,
                        'suggested_stop_pips': 12,
                        'suggested_rr': 2.0,
                        'name': 'Bull Flag'
                    })
        
            # Look for bear flags
            for i in range(10, len(df)):
                # Check for strong downtrend followed by consolidation
                if (closes[i-10:i-5].mean() > closes[i-5:i].mean() and  # Downtrend
                    max(closes[i-5:i]) - min(closes[i-5:i]) < 0.001):  # Tight consolidation
                    patterns.append({
                        'type': PatternType.BEAR_FLAG,
                        'direction': 'sell',
                        'confidence': 65.0,
                        'suggested_stop_pips': 12,
                        'suggested_rr': 2.0,
                        'name': 'Bear Flag'
                    })
        
            return patterns
        except Exception as e:
            logger.error(f"Error in _detect_flags_pennants: {e}")
            raise
    
    def _detect_wedges(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect wedge patterns."""
        try:
            patterns = []
        
            # Get highs and lows
            highs = df['high'].values
            lows = df['low'].values
        
            # Look for rising wedges
            for i in range(10, len(df)):
                window = df.iloc[i-10:i]
            
                # Check for rising support and resistance with converging lines
                if (window['high'].is_monotonic_increasing and 
                    window['low'].is_monotonic_increasing and
                    (window['high'] - window['low']).is_monotonic_decreasing):
                    patterns.append({
                        'type': PatternType.RISING_WEDGE,
                        'direction': 'sell',
                        'confidence': 75.0,
                        'suggested_stop_pips': 18,
                        'suggested_rr': 2.5,
                        'name': 'Rising Wedge'
                    })
        
            # Look for falling wedges
            for i in range(10, len(df)):
                window = df.iloc[i-10:i]
            
                # Check for falling support and resistance with converging lines
                if (window['high'].is_monotonic_decreasing and 
                    window['low'].is_monotonic_decreasing and
                    (window['high'] - window['low']).is_monotonic_decreasing):
                    patterns.append({
                        'type': PatternType.FALLING_WEDGE,
                        'direction': 'buy',
                        'confidence': 75.0,
                        'suggested_stop_pips': 18,
                        'suggested_rr': 2.5,
                        'name': 'Falling Wedge'
                    })
        
            return patterns
        except Exception as e:
            logger.error(f"Error in _detect_wedges: {e}")
            raise
