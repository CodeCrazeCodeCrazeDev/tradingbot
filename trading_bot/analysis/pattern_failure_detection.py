"""Pattern Failure Detection Module.

Implements comprehensive pattern failure analysis including:
- Head and Shoulders failure patterns
- Double top/bottom traps
- Triangle breakout failures
- Flag pattern collapses
- Channel break invalidations
- Time-based invalidation rules
- Pattern completion time requirements
- Maximum pattern duration limits
- Failed breakout detection
- Bull/Bear trap identification

This module enables detection of failed patterns for
contrarian entries and stop-loss optimization.
"""


from __future__ import annotations
import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from enum import Enum
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class PatternType(enum.Enum):
    """Types of chart patterns."""
    HEAD_SHOULDERS = "head_shoulders"
    INVERSE_HEAD_SHOULDERS = "inverse_head_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_TOP = "triple_top"
    TRIPLE_BOTTOM = "triple_bottom"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRICAL_TRIANGLE = "symmetrical_triangle"
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    ASCENDING_CHANNEL = "ascending_channel"
    DESCENDING_CHANNEL = "descending_channel"
    RECTANGLE = "rectangle"
    WEDGE_RISING = "wedge_rising"
    WEDGE_FALLING = "wedge_falling"


class FailureType(enum.Enum):
    """Types of pattern failures."""
    FALSE_BREAKOUT = "false_breakout"  # Breakout that reverses
    FAILED_PATTERN = "failed_pattern"  # Pattern that doesn't complete
    TIME_EXPIRATION = "time_expiration"  # Pattern took too long
    INVALIDATION = "invalidation"  # Key level broken
    TRAP = "trap"  # Bull/Bear trap
    FAKEOUT = "fakeout"  # Quick reversal after breakout


class TrapType(enum.Enum):
    """Types of traps."""
    BULL_TRAP = "bull_trap"  # False bullish breakout
    BEAR_TRAP = "bear_trap"  # False bearish breakout


@dataclass
class Pattern:
    """Detected chart pattern."""
    pattern_type: PatternType
    start_idx: int
    end_idx: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    key_levels: Dict[str, float]  # neckline, resistance, support, etc.
    expected_direction: str  # 'bullish' or 'bearish'
    expected_target: float
    invalidation_level: float
    confidence: float
    duration_bars: int
    max_duration_bars: int


@dataclass
class PatternFailure:
    """Detected pattern failure."""
    pattern: Pattern
    failure_type: FailureType
    failure_idx: int
    failure_time: Optional[datetime]
    failure_price: float
    reversal_magnitude: float  # How far price reversed
    time_to_failure: int  # Bars from breakout to failure
    contrarian_signal: str  # 'long' or 'short'
    signal_strength: float  # 0-100
    stop_loss: float
    take_profit: float


@dataclass
class Trap:
    """Bull/Bear trap detection."""
    trap_type: TrapType
    trigger_idx: int
    trigger_time: Optional[datetime]
    trigger_price: float
    reversal_idx: int
    reversal_price: float
    trapped_direction: str  # Direction that got trapped
    magnitude: float  # Size of the trap
    volume_confirmation: bool
    signal_strength: float


@dataclass
class InvalidationRule:
    """Pattern invalidation rule."""
    rule_name: str
    invalidation_level: float
    invalidation_type: str  # 'price', 'time', 'structure'
    current_status: str  # 'valid', 'warning', 'invalidated'
    distance_to_invalidation: float


class PatternFailureDetector:
    """Pattern Failure Detection Engine.
    
    Detects failed chart patterns and traps for
    contrarian trading opportunities.
    """
    
    # Default pattern duration limits (in bars)
    PATTERN_DURATION_LIMITS = {
        PatternType.HEAD_SHOULDERS: 100,
        PatternType.INVERSE_HEAD_SHOULDERS: 100,
        PatternType.DOUBLE_TOP: 60,
        PatternType.DOUBLE_BOTTOM: 60,
        PatternType.TRIPLE_TOP: 80,
        PatternType.TRIPLE_BOTTOM: 80,
        PatternType.ASCENDING_TRIANGLE: 50,
        PatternType.DESCENDING_TRIANGLE: 50,
        PatternType.SYMMETRICAL_TRIANGLE: 50,
        PatternType.BULL_FLAG: 30,
        PatternType.BEAR_FLAG: 30,
        PatternType.ASCENDING_CHANNEL: 100,
        PatternType.DESCENDING_CHANNEL: 100,
        PatternType.RECTANGLE: 60,
        PatternType.WEDGE_RISING: 50,
        PatternType.WEDGE_FALLING: 50,
    }
    
    # Minimum confirmation bars after breakout
    MIN_CONFIRMATION_BARS = 3
    
    # False breakout threshold (% reversal)
    FALSE_BREAKOUT_THRESHOLD = 0.02  # 2%
    
    def __init__(
        self,
        swing_lookback: int = 5,
        false_breakout_threshold: float = 0.02,
        min_confirmation_bars: int = 3,
        trap_threshold: float = 0.015
    ):
        """Initialize Pattern Failure Detector.
        
        Args:
            swing_lookback: Bars for swing detection
            false_breakout_threshold: Threshold for false breakout (%)
            min_confirmation_bars: Minimum bars for breakout confirmation
            trap_threshold: Threshold for trap detection (%)
        """
        try:
            self.swing_lookback = swing_lookback
            self.false_breakout_threshold = false_breakout_threshold
            self.min_confirmation_bars = min_confirmation_bars
            self.trap_threshold = trap_threshold
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def detect_head_shoulders_failure(
        self,
        df: pd.DataFrame,
        pattern: Pattern
    ) -> Optional[PatternFailure]:
        """Detect Head and Shoulders pattern failure.
        
        Failure occurs when:
        1. Price breaks neckline but reverses back above
        2. Pattern takes too long to complete
        3. Right shoulder exceeds head level
        """
        try:
            if pattern.pattern_type not in [PatternType.HEAD_SHOULDERS, PatternType.INVERSE_HEAD_SHOULDERS]:
                return None
            
            neckline = pattern.key_levels.get('neckline', 0)
            head = pattern.key_levels.get('head', 0)
        
            if neckline == 0:
                return None
            
            # Check for false breakout
            subsequent_data = df.iloc[pattern.end_idx:]
        
            if len(subsequent_data) < self.min_confirmation_bars:
                return None
            
            if pattern.pattern_type == PatternType.HEAD_SHOULDERS:
                # Bearish pattern - failure if price goes back above neckline
                broke_neckline = any(subsequent_data['close'] < neckline)
            
                if broke_neckline:
                    # Find where it broke
                    break_idx = subsequent_data[subsequent_data['close'] < neckline].index[0]
                    break_bar = subsequent_data.loc[break_idx]
                
                    # Check for reversal back above
                    after_break = subsequent_data.loc[break_idx:]
                    if len(after_break) > self.min_confirmation_bars:
                        reversal = any(after_break['close'].iloc[self.min_confirmation_bars:] > neckline * 1.01)
                    
                        if reversal:
                            reversal_idx = after_break[after_break['close'] > neckline * 1.01].index[0]
                            reversal_bar = after_break.loc[reversal_idx]
                        
                            return PatternFailure(
                                pattern=pattern,
                                failure_type=FailureType.FALSE_BREAKOUT,
                                failure_idx=df.index.get_loc(reversal_idx),
                                failure_time=reversal_idx if isinstance(reversal_idx, datetime) else None,
                                failure_price=reversal_bar['close'],
                                reversal_magnitude=(reversal_bar['close'] - break_bar['close']) / break_bar['close'] * 100,
                                time_to_failure=df.index.get_loc(reversal_idx) - df.index.get_loc(break_idx),
                                contrarian_signal='long',
                                signal_strength=75,
                                stop_loss=break_bar['low'] * 0.99,
                                take_profit=head
                            )
                        
            else:  # Inverse H&S
                # Bullish pattern - failure if price goes back below neckline
                broke_neckline = any(subsequent_data['close'] > neckline)
            
                if broke_neckline:
                    break_idx = subsequent_data[subsequent_data['close'] > neckline].index[0]
                    break_bar = subsequent_data.loc[break_idx]
                
                    after_break = subsequent_data.loc[break_idx:]
                    if len(after_break) > self.min_confirmation_bars:
                        reversal = any(after_break['close'].iloc[self.min_confirmation_bars:] < neckline * 0.99)
                    
                        if reversal:
                            reversal_idx = after_break[after_break['close'] < neckline * 0.99].index[0]
                            reversal_bar = after_break.loc[reversal_idx]
                        
                            return PatternFailure(
                                pattern=pattern,
                                failure_type=FailureType.FALSE_BREAKOUT,
                                failure_idx=df.index.get_loc(reversal_idx),
                                failure_time=reversal_idx if isinstance(reversal_idx, datetime) else None,
                                failure_price=reversal_bar['close'],
                                reversal_magnitude=(break_bar['close'] - reversal_bar['close']) / break_bar['close'] * 100,
                                time_to_failure=df.index.get_loc(reversal_idx) - df.index.get_loc(break_idx),
                                contrarian_signal='short',
                                signal_strength=75,
                                stop_loss=break_bar['high'] * 1.01,
                                take_profit=head
                            )
                        
            return None
        except Exception as e:
            logger.error(f"Error in detect_head_shoulders_failure: {e}")
            raise
        
    def detect_double_top_bottom_trap(
        self,
        df: pd.DataFrame,
        pattern: Pattern
    ) -> Optional[PatternFailure]:
        """Detect Double Top/Bottom trap (failed pattern).
        
        Trap occurs when:
        1. Price breaks the pattern level
        2. Quickly reverses back
        3. Traps traders on wrong side
        """
        try:
            if pattern.pattern_type not in [PatternType.DOUBLE_TOP, PatternType.DOUBLE_BOTTOM]:
                return None
            
            subsequent_data = df.iloc[pattern.end_idx:]
        
            if len(subsequent_data) < self.min_confirmation_bars + 3:
                return None
            
            if pattern.pattern_type == PatternType.DOUBLE_TOP:
                # Bearish pattern - trap if price breaks support then reverses up
                support = pattern.key_levels.get('support', pattern.invalidation_level)
                resistance = pattern.key_levels.get('resistance', pattern.key_levels.get('top', 0))
            
                # Check for break below support
                broke_support = any(subsequent_data['close'] < support)
            
                if broke_support:
                    break_idx = subsequent_data[subsequent_data['close'] < support].index[0]
                
                    # Check for reversal back above
                    after_break = subsequent_data.loc[break_idx:]
                    if len(after_break) > 3:
                        # Strong reversal = closes above resistance
                        strong_reversal = any(after_break['close'].iloc[3:] > resistance * 0.99)
                    
                        if strong_reversal:
                            reversal_idx = after_break[after_break['close'] > resistance * 0.99].index[0]
                        
                            return PatternFailure(
                                pattern=pattern,
                                failure_type=FailureType.TRAP,
                                failure_idx=df.index.get_loc(reversal_idx),
                                failure_time=reversal_idx if isinstance(reversal_idx, datetime) else None,
                                failure_price=df.loc[reversal_idx, 'close'],
                                reversal_magnitude=(df.loc[reversal_idx, 'close'] - support) / support * 100,
                                time_to_failure=df.index.get_loc(reversal_idx) - df.index.get_loc(break_idx),
                                contrarian_signal='long',
                                signal_strength=85,
                                stop_loss=df.loc[break_idx:reversal_idx, 'low'].min() * 0.99,
                                take_profit=resistance * 1.05
                            )
                        
            else:  # Double Bottom
                # Bullish pattern - trap if price breaks resistance then reverses down
                resistance = pattern.key_levels.get('resistance', pattern.invalidation_level)
                support = pattern.key_levels.get('support', pattern.key_levels.get('bottom', 0))
            
                broke_resistance = any(subsequent_data['close'] > resistance)
            
                if broke_resistance:
                    break_idx = subsequent_data[subsequent_data['close'] > resistance].index[0]
                
                    after_break = subsequent_data.loc[break_idx:]
                    if len(after_break) > 3:
                        strong_reversal = any(after_break['close'].iloc[3:] < support * 1.01)
                    
                        if strong_reversal:
                            reversal_idx = after_break[after_break['close'] < support * 1.01].index[0]
                        
                            return PatternFailure(
                                pattern=pattern,
                                failure_type=FailureType.TRAP,
                                failure_idx=df.index.get_loc(reversal_idx),
                                failure_time=reversal_idx if isinstance(reversal_idx, datetime) else None,
                                failure_price=df.loc[reversal_idx, 'close'],
                                reversal_magnitude=(resistance - df.loc[reversal_idx, 'close']) / resistance * 100,
                                time_to_failure=df.index.get_loc(reversal_idx) - df.index.get_loc(break_idx),
                                contrarian_signal='short',
                                signal_strength=85,
                                stop_loss=df.loc[break_idx:reversal_idx, 'high'].max() * 1.01,
                                take_profit=support * 0.95
                            )
                        
            return None
        except Exception as e:
            logger.error(f"Error in detect_double_top_bottom_trap: {e}")
            raise
        
    def detect_triangle_failure(
        self,
        df: pd.DataFrame,
        pattern: Pattern
    ) -> Optional[PatternFailure]:
        """Detect triangle breakout failure."""
        try:
            if pattern.pattern_type not in [
                PatternType.ASCENDING_TRIANGLE,
                PatternType.DESCENDING_TRIANGLE,
                PatternType.SYMMETRICAL_TRIANGLE
            ]:
                return None
            
            subsequent_data = df.iloc[pattern.end_idx:]
        
            if len(subsequent_data) < self.min_confirmation_bars + 3:
                return None
            
            upper = pattern.key_levels.get('upper', pattern.key_levels.get('resistance', 0))
            lower = pattern.key_levels.get('lower', pattern.key_levels.get('support', 0))
        
            if upper == 0 or lower == 0:
                return None
            
            # Check for breakout in either direction
            broke_upper = any(subsequent_data['close'] > upper)
            broke_lower = any(subsequent_data['close'] < lower)
        
            if broke_upper:
                break_idx = subsequent_data[subsequent_data['close'] > upper].index[0]
                break_price = subsequent_data.loc[break_idx, 'close']
            
                # Check for failure (reversal back below upper)
                after_break = subsequent_data.loc[break_idx:]
                if len(after_break) > self.min_confirmation_bars:
                    failure = any(after_break['close'].iloc[self.min_confirmation_bars:] < lower)
                
                    if failure:
                        failure_idx = after_break[after_break['close'] < lower].index[0]
                    
                        return PatternFailure(
                            pattern=pattern,
                            failure_type=FailureType.FALSE_BREAKOUT,
                            failure_idx=df.index.get_loc(failure_idx),
                            failure_time=failure_idx if isinstance(failure_idx, datetime) else None,
                            failure_price=df.loc[failure_idx, 'close'],
                            reversal_magnitude=(break_price - df.loc[failure_idx, 'close']) / break_price * 100,
                            time_to_failure=df.index.get_loc(failure_idx) - df.index.get_loc(break_idx),
                            contrarian_signal='short',
                            signal_strength=80,
                            stop_loss=break_price * 1.01,
                            take_profit=lower - (upper - lower)
                        )
                    
            if broke_lower:
                break_idx = subsequent_data[subsequent_data['close'] < lower].index[0]
                break_price = subsequent_data.loc[break_idx, 'close']
            
                after_break = subsequent_data.loc[break_idx:]
                if len(after_break) > self.min_confirmation_bars:
                    failure = any(after_break['close'].iloc[self.min_confirmation_bars:] > upper)
                
                    if failure:
                        failure_idx = after_break[after_break['close'] > upper].index[0]
                    
                        return PatternFailure(
                            pattern=pattern,
                            failure_type=FailureType.FALSE_BREAKOUT,
                            failure_idx=df.index.get_loc(failure_idx),
                            failure_time=failure_idx if isinstance(failure_idx, datetime) else None,
                            failure_price=df.loc[failure_idx, 'close'],
                            reversal_magnitude=(df.loc[failure_idx, 'close'] - break_price) / break_price * 100,
                            time_to_failure=df.index.get_loc(failure_idx) - df.index.get_loc(break_idx),
                            contrarian_signal='long',
                            signal_strength=80,
                            stop_loss=break_price * 0.99,
                            take_profit=upper + (upper - lower)
                        )
                    
            return None
        except Exception as e:
            logger.error(f"Error in detect_triangle_failure: {e}")
            raise
        
    def detect_flag_failure(
        self,
        df: pd.DataFrame,
        pattern: Pattern
    ) -> Optional[PatternFailure]:
        """Detect flag pattern failure."""
        try:
            if pattern.pattern_type not in [PatternType.BULL_FLAG, PatternType.BEAR_FLAG]:
                return None
            
            subsequent_data = df.iloc[pattern.end_idx:]
        
            if len(subsequent_data) < self.min_confirmation_bars + 3:
                return None
            
            if pattern.pattern_type == PatternType.BULL_FLAG:
                # Bull flag should break up - failure if breaks down
                flag_low = pattern.key_levels.get('flag_low', pattern.invalidation_level)
                pole_high = pattern.key_levels.get('pole_high', 0)
            
                # Check for breakdown
                broke_down = any(subsequent_data['close'] < flag_low * 0.99)
            
                if broke_down:
                    break_idx = subsequent_data[subsequent_data['close'] < flag_low * 0.99].index[0]
                
                    return PatternFailure(
                        pattern=pattern,
                        failure_type=FailureType.FAILED_PATTERN,
                        failure_idx=df.index.get_loc(break_idx),
                        failure_time=break_idx if isinstance(break_idx, datetime) else None,
                        failure_price=df.loc[break_idx, 'close'],
                        reversal_magnitude=(flag_low - df.loc[break_idx, 'close']) / flag_low * 100,
                        time_to_failure=df.index.get_loc(break_idx) - pattern.end_idx,
                        contrarian_signal='short',
                        signal_strength=70,
                        stop_loss=flag_low * 1.01,
                        take_profit=flag_low - (pole_high - flag_low)
                    )
                
            else:  # Bear Flag
                flag_high = pattern.key_levels.get('flag_high', pattern.invalidation_level)
                pole_low = pattern.key_levels.get('pole_low', 0)
            
                broke_up = any(subsequent_data['close'] > flag_high * 1.01)
            
                if broke_up:
                    break_idx = subsequent_data[subsequent_data['close'] > flag_high * 1.01].index[0]
                
                    return PatternFailure(
                        pattern=pattern,
                        failure_type=FailureType.FAILED_PATTERN,
                        failure_idx=df.index.get_loc(break_idx),
                        failure_time=break_idx if isinstance(break_idx, datetime) else None,
                        failure_price=df.loc[break_idx, 'close'],
                        reversal_magnitude=(df.loc[break_idx, 'close'] - flag_high) / flag_high * 100,
                        time_to_failure=df.index.get_loc(break_idx) - pattern.end_idx,
                        contrarian_signal='long',
                        signal_strength=70,
                        stop_loss=flag_high * 0.99,
                        take_profit=flag_high + (flag_high - pole_low)
                    )
                
            return None
        except Exception as e:
            logger.error(f"Error in detect_flag_failure: {e}")
            raise
        
    def check_time_invalidation(
        self,
        pattern: Pattern,
        current_bar: int
    ) -> Optional[PatternFailure]:
        """Check if pattern has exceeded time limit."""
        try:
            max_duration = self.PATTERN_DURATION_LIMITS.get(
                pattern.pattern_type,
                pattern.max_duration_bars
            )
        
            current_duration = current_bar - pattern.start_idx
        
            if current_duration > max_duration:
                return PatternFailure(
                    pattern=pattern,
                    failure_type=FailureType.TIME_EXPIRATION,
                    failure_idx=current_bar,
                    failure_time=None,
                    failure_price=0,
                    reversal_magnitude=0,
                    time_to_failure=current_duration,
                    contrarian_signal='none',
                    signal_strength=30,
                    stop_loss=0,
                    take_profit=0
                )
            
            return None
        except Exception as e:
            logger.error(f"Error in check_time_invalidation: {e}")
            raise
        
    def detect_bull_trap(
        self,
        df: pd.DataFrame,
        resistance_level: float,
        lookback: int = 20
    ) -> Optional[Trap]:
        """Detect bull trap (false bullish breakout)."""
        try:
            if len(df) < lookback + 5:
                return None
            
            recent = df.iloc[-lookback:]
        
            # Find breakout above resistance
            breakout_mask = recent['close'] > resistance_level
        
            if not any(breakout_mask):
                return None
            
            # Find first breakout
            breakout_idx = recent[breakout_mask].index[0]
            breakout_bar = recent.loc[breakout_idx]
        
            # Check for reversal back below
            after_breakout = recent.loc[breakout_idx:]
        
            if len(after_breakout) < 3:
                return None
            
            # Reversal = closes below resistance
            reversal_mask = after_breakout['close'].iloc[1:] < resistance_level * 0.99
        
            if any(reversal_mask):
                reversal_idx = after_breakout[after_breakout['close'] < resistance_level * 0.99].index[0]
                reversal_bar = after_breakout.loc[reversal_idx]
            
                # Volume confirmation (high volume on reversal)
                if 'volume' in df.columns:
                    avg_vol = df['volume'].iloc[-lookback:].mean()
                    vol_confirm = reversal_bar['volume'] > avg_vol * 1.5
                else:
                    vol_confirm = False
                
                magnitude = (breakout_bar['high'] - reversal_bar['close']) / breakout_bar['high'] * 100
            
                return Trap(
                    trap_type=TrapType.BULL_TRAP,
                    trigger_idx=df.index.get_loc(breakout_idx),
                    trigger_time=breakout_idx if isinstance(breakout_idx, datetime) else None,
                    trigger_price=breakout_bar['high'],
                    reversal_idx=df.index.get_loc(reversal_idx),
                    reversal_price=reversal_bar['close'],
                    trapped_direction='long',
                    magnitude=magnitude,
                    volume_confirmation=vol_confirm,
                    signal_strength=min(100, 50 + magnitude * 10 + (20 if vol_confirm else 0))
                )
            
            return None
        except Exception as e:
            logger.error(f"Error in detect_bull_trap: {e}")
            raise
        
    def detect_bear_trap(
        self,
        df: pd.DataFrame,
        support_level: float,
        lookback: int = 20
    ) -> Optional[Trap]:
        """Detect bear trap (false bearish breakout)."""
        try:
            if len(df) < lookback + 5:
                return None
            
            recent = df.iloc[-lookback:]
        
            # Find breakdown below support
            breakdown_mask = recent['close'] < support_level
        
            if not any(breakdown_mask):
                return None
            
            breakdown_idx = recent[breakdown_mask].index[0]
            breakdown_bar = recent.loc[breakdown_idx]
        
            after_breakdown = recent.loc[breakdown_idx:]
        
            if len(after_breakdown) < 3:
                return None
            
            # Reversal = closes above support
            reversal_mask = after_breakdown['close'].iloc[1:] > support_level * 1.01
        
            if any(reversal_mask):
                reversal_idx = after_breakdown[after_breakdown['close'] > support_level * 1.01].index[0]
                reversal_bar = after_breakdown.loc[reversal_idx]
            
                if 'volume' in df.columns:
                    avg_vol = df['volume'].iloc[-lookback:].mean()
                    vol_confirm = reversal_bar['volume'] > avg_vol * 1.5
                else:
                    vol_confirm = False
                
                magnitude = (reversal_bar['close'] - breakdown_bar['low']) / breakdown_bar['low'] * 100
            
                return Trap(
                    trap_type=TrapType.BEAR_TRAP,
                    trigger_idx=df.index.get_loc(breakdown_idx),
                    trigger_time=breakdown_idx if isinstance(breakdown_idx, datetime) else None,
                    trigger_price=breakdown_bar['low'],
                    reversal_idx=df.index.get_loc(reversal_idx),
                    reversal_price=reversal_bar['close'],
                    trapped_direction='short',
                    magnitude=magnitude,
                    volume_confirmation=vol_confirm,
                    signal_strength=min(100, 50 + magnitude * 10 + (20 if vol_confirm else 0))
                )
            
            return None
        except Exception as e:
            logger.error(f"Error in detect_bear_trap: {e}")
            raise
        
    def get_invalidation_rules(
        self,
        pattern: Pattern,
        current_price: float
    ) -> List[InvalidationRule]:
        """Get invalidation rules for a pattern."""
        try:
            rules = []
        
            # Price invalidation
            if pattern.invalidation_level > 0:
                distance = abs(current_price - pattern.invalidation_level) / current_price * 100
            
                if pattern.expected_direction == 'bullish':
                    status = 'invalidated' if current_price < pattern.invalidation_level else (
                        'warning' if distance < 1 else 'valid'
                    )
                else:
                    status = 'invalidated' if current_price > pattern.invalidation_level else (
                        'warning' if distance < 1 else 'valid'
                    )
                
                rules.append(InvalidationRule(
                    rule_name="Price Invalidation",
                    invalidation_level=pattern.invalidation_level,
                    invalidation_type='price',
                    current_status=status,
                    distance_to_invalidation=distance
                ))
            
            # Time invalidation
            max_duration = self.PATTERN_DURATION_LIMITS.get(pattern.pattern_type, pattern.max_duration_bars)
            time_remaining = max_duration - pattern.duration_bars
            time_pct = pattern.duration_bars / max_duration * 100
        
            time_status = 'invalidated' if time_remaining <= 0 else (
                'warning' if time_pct > 80 else 'valid'
            )
        
            rules.append(InvalidationRule(
                rule_name="Time Invalidation",
                invalidation_level=max_duration,
                invalidation_type='time',
                current_status=time_status,
                distance_to_invalidation=time_remaining
            ))
        
            return rules
        except Exception as e:
            logger.error(f"Error in get_invalidation_rules: {e}")
            raise


# Convenience functions
def detect_bull_trap(df: pd.DataFrame, resistance: float) -> Optional[Dict[str, Any]]:
    """Quick function to detect bull trap."""
    try:
        detector = PatternFailureDetector()
        trap = detector.detect_bull_trap(df, resistance)
    
        if trap:
            return {
                'type': 'bull_trap',
                'trigger_price': trap.trigger_price,
                'reversal_price': trap.reversal_price,
                'magnitude': trap.magnitude,
                'signal_strength': trap.signal_strength,
                'volume_confirmed': trap.volume_confirmation
            }
        return None
    except Exception as e:
        logger.error(f"Error in detect_bull_trap: {e}")
        raise


def detect_bear_trap(df: pd.DataFrame, support: float) -> Optional[Dict[str, Any]]:
    """Quick function to detect bear trap."""
    try:
        detector = PatternFailureDetector()
        trap = detector.detect_bear_trap(df, support)
    
        if trap:
            return {
                'type': 'bear_trap',
                'trigger_price': trap.trigger_price,
                'reversal_price': trap.reversal_price,
                'magnitude': trap.magnitude,
                'signal_strength': trap.signal_strength,
                'volume_confirmed': trap.volume_confirmation
            }
        return None
    except Exception as e:
        logger.error(f"Error in detect_bear_trap: {e}")
        raise
