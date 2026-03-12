"""Market Structure & Swing-point detection utilities.

This module provides a comprehensive market structure analysis system that
operates on iterables of OHLC dictionaries **or** on `pandas.DataFrame` objects.
It focuses on advanced structure mapping and detection of key market events:

    • BOS   – Break of Structure
    • CHOCH – Change of Character (trend flip)
    • COS   – Change of Structure (trend flip on internal structure)
    • Swing structure analysis across multiple timeframes
    • Structure mapping for optimal entry/exit points

The implementation follows the specifications in the Elite Trading Bot framework.
"""

from __future__ import annotations
import enum
import itertools
import statistics
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Sequence, Tuple

import pandas as pd  # type: ignore

# ---------------------------------------------------------------------------
# Dataclasses & Enums
# ---------------------------------------------------------------------------


import logging

logger = logging.getLogger(__name__)

@dataclass(slots=True)
class OHLC:
    """Simple, immutable representation of an OHLC bar."""

    time: float  # POSIX timestamp (seconds)
    open: float
    high: float
    low: float
    close: float


class TimeFrame(enum.Enum):
    """Standard timeframes for market analysis."""
    M1 = "1m"  # 1 minute
    M5 = "5m"  # 5 minutes
    M15 = "15m"  # 15 minutes
    M30 = "30m"  # 30 minutes
    H1 = "1h"  # 1 hour
    H4 = "4h"  # 4 hours
    D1 = "1d"  # 1 day
    W1 = "1w"  # 1 week
    MN = "1M"  # 1 month


class Trend(enum.Enum):
    """Market trend direction."""
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class SwingPoint:
    """Represents a swing high or swing low with enhanced properties."""

    idx: int  # numeric position in original series
    time: float
    price: float
    kind: str  # "high" | "low"
    strength: float = 1.0  # relative strength of the swing point (1.0 = normal)
    volume: float = 0.0  # volume at the swing point
    confirmed: bool = False  # whether this swing point is confirmed
    timeframe: TimeFrame = TimeFrame.M15  # timeframe this swing was detected on


class StructureType(enum.Enum):
    BOS = "BOS"  # Break of Structure
    CHOCH = "CHOCH"  # Change of Character
    COS = "COS"  # Change of Structure


@dataclass(slots=True)
class StructureEvent:
    """Encapsulates a market-structure event (BOS / CHOCH / COS) with enhanced properties."""

    idx: int  # index at which event occurred (bar that broke structure)
    event: StructureType
    broken_swing: SwingPoint
    new_close: float
    strength: float = 1.0  # relative strength/significance of the event
    volume_delta: float = 0.0  # volume change compared to average
    confirmed: bool = False  # whether this event is confirmed
    timeframe: TimeFrame = TimeFrame.M15  # timeframe this event was detected on
    correlated_events: List["StructureEvent"] = None  # related events on other timeframes


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _to_ohlc_series(data: pd.DataFrame | Sequence[dict[str, float]]) -> List[OHLC]:
    try:
        if isinstance(data, pd.DataFrame):
            required = {"open", "high", "low", "close"}
            if not required.issubset(data.columns):
                raise ValueError(f"DataFrame must contain {required} columns.")

            def _index_to_ts(idx) -> float:
                if hasattr(idx, 'timestamp'):
                    return idx.timestamp()
                if isinstance(idx, (int, float)):
                    return float(idx)
                return 0.0

            return [
                OHLC(_index_to_ts(row.Index),
                     row.open, row.high, row.low, row.close)  # type: ignore[attr-defined]
                for row in data.itertuples()
            ]
        # Assume iterable of dicts
        return [OHLC(d.get("time", 0), d["open"], d["high"], d["low"], d["close"]) for d in data]
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Error in _to_ohlc_series: {e}")
        raise


# ---------------------------------------------------------------------------
# Core Analyzer
# ---------------------------------------------------------------------------


class MarketStructureAnalyzer:
    """Advanced market structure analyzer with multi-timeframe capabilities.
    
    This class provides comprehensive market structure analysis including:
    - Swing point detection with strength evaluation
    - Structure event identification (BOS, CHOCH, COS)
    - Multi-timeframe correlation and confirmation
    - Structure mapping for optimal entry/exit points
    - Trend strength and momentum analysis
    """

    def __init__(self, *, 
                 swing_len: int = 3, 
                 default_timeframe: TimeFrame = TimeFrame.M15,
                 volume_weight: float = 0.3,
                 multi_timeframe: bool = True) -> None:
        """Initialize the market structure analyzer.
        
        Args:
            swing_len: Number of bars to look left/right for swing detection
            default_timeframe: Default timeframe for analysis
            volume_weight: Weight of volume in strength calculations (0.0-1.0)
            multi_timeframe: Whether to perform multi-timeframe analysis
        """
        try:
            if swing_len < 1:
                raise ValueError("swing_len must be >=1")
            if not 0.0 <= volume_weight <= 1.0:
                raise ValueError("volume_weight must be between 0.0 and 1.0")
            
            self.swing_len = swing_len
            self.default_timeframe = default_timeframe
            self.volume_weight = volume_weight
            self.multi_timeframe = multi_timeframe
            self.timeframe_data = {}
            self.correlated_events = []
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_swings(
        self,
        data: pd.DataFrame | Sequence[dict[str, float]],
        timeframe: TimeFrame = None,
        calculate_strength: bool = True,
    ) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """Return lists of swing-highs and swing-lows with strength evaluation.
        
        Args:
            data: OHLC data as DataFrame or sequence of dicts
            timeframe: Timeframe of the data (defaults to self.default_timeframe)
            calculate_strength: Whether to calculate swing point strength
            
        Returns:
            Tuple of (swing_highs, swing_lows)
        """
        try:
            series = _to_ohlc_series(data)
            highs: list[SwingPoint] = []
            lows: list[SwingPoint] = []
        
            # Use provided timeframe or default
            tf = timeframe or self.default_timeframe
        
            # Calculate average volume if available for strength evaluation
            has_volume = False
            avg_volume = 0.0
            if isinstance(data, pd.DataFrame) and "volume" in data.columns:
                has_volume = True
                avg_volume = data["volume"].mean()

            for i in range(self.swing_len, len(series) - self.swing_len):
                pivot = series[i]
                left = series[i - self.swing_len : i]
                right = series[i + 1 : i + 1 + self.swing_len]

                # Check for swing high
                if all(pivot.high > b.high for b in itertools.chain(left, right)):
                    # Calculate strength based on price difference and volume
                    strength = 1.0
                    volume = 0.0
                
                    if calculate_strength:
                        # Price component: how much higher than surrounding bars
                        avg_high = statistics.mean(b.high for b in itertools.chain(left, right))
                        price_strength = (pivot.high - avg_high) / avg_high * 100
                        strength = 1.0 + min(price_strength, 5.0) / 5.0  # Cap at 2.0
                    
                        # Volume component if available
                        if has_volume and isinstance(data, pd.DataFrame):
                            volume = float(data.iloc[i]["volume"])
                            vol_ratio = volume / avg_volume if avg_volume > 0 else 1.0
                            # Blend price and volume components
                            strength = (strength * (1 - self.volume_weight) + 
                                       min(vol_ratio, 3.0) / 3.0 * self.volume_weight)
                
                    # Create swing point with calculated properties
                    swing = SwingPoint(
                        i, pivot.time, pivot.high, "high", 
                        strength=strength, volume=volume, 
                        confirmed=True, timeframe=tf
                    )
                    highs.append(swing)
                
                # Check for swing low
                if all(pivot.low < b.low for b in itertools.chain(left, right)):
                    # Calculate strength based on price difference and volume
                    strength = 1.0
                    volume = 0.0
                
                    if calculate_strength:
                        # Price component: how much lower than surrounding bars
                        avg_low = statistics.mean(b.low for b in itertools.chain(left, right))
                        price_strength = (avg_low - pivot.low) / avg_low * 100
                        strength = 1.0 + min(price_strength, 5.0) / 5.0  # Cap at 2.0
                    
                        # Volume component if available
                        if has_volume and isinstance(data, pd.DataFrame):
                            volume = float(data.iloc[i]["volume"])
                            vol_ratio = volume / avg_volume if avg_volume > 0 else 1.0
                            # Blend price and volume components
                            strength = (strength * (1 - self.volume_weight) + 
                                       min(vol_ratio, 3.0) / 3.0 * self.volume_weight)
                
                    # Create swing point with calculated properties
                    swing = SwingPoint(
                        i, pivot.time, pivot.low, "low", 
                        strength=strength, volume=volume, 
                        confirmed=True, timeframe=tf
                    )
                    lows.append(swing)
                
            return highs, lows
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in find_swings: {e}")
            raise

    def detect_structure(
        self,
        data: pd.DataFrame | Sequence[dict[str, float]],
        timeframe: TimeFrame = None,
        calculate_strength: bool = True,
    ) -> List[StructureEvent]:
        """Detect advanced market structure events with strength evaluation.

        This enhanced algorithm detects:
        1. Break of Structure (BOS) - when price breaks a significant swing point
        2. Change of Character (CHOCH) - when trend direction changes
        3. Change of Structure (COS) - internal structure changes within a trend
        
        The method evaluates the strength of each event based on:
        - Price movement magnitude
        - Volume confirmation (if available)
        - Timeframe significance
        - Historical context
        
        Args:
            data: OHLC data as DataFrame or sequence of dicts
            timeframe: Timeframe of the data (defaults to self.default_timeframe)
            calculate_strength: Whether to calculate event strength
            
        Returns:
            List of structure events with strength evaluation
        """
        # Use provided timeframe or default
        try:
            tf = timeframe or self.default_timeframe
        
            # Find swing points with strength evaluation
            swings_high, swings_low = self.find_swings(data, timeframe=tf, calculate_strength=calculate_strength)
            series = _to_ohlc_series(data)
            events: list[StructureEvent] = []
            trend: Trend = Trend.UNKNOWN
            last_choc_idx: int | None = None
            sideways_count = 0  # Counter for sideways market detection

            # Calculate average volume if available for strength evaluation
            has_volume = False
            avg_volume = 0.0
            if isinstance(data, pd.DataFrame) and "volume" in data.columns:
                has_volume = True
                avg_volume = data["volume"].mean()

            # Build quick lookup by idx for fast access
            high_by_idx = {s.idx: s for s in swings_high}
            low_by_idx = {s.idx: s for s in swings_low}
            swing_idxs_sorted = sorted([s.idx for s in itertools.chain(swings_high, swings_low)])

            # Iterate forward bar by bar and check for breaks
            hi_pointer, lo_pointer = 0, 0  # Indexes in the swing lists
            last_high = swings_high[0] if swings_high else None
            last_low = swings_low[0] if swings_low else None
            last_event_idx = -20  # To prevent too many events too close together

            for i in range(len(series)):
                bar = series[i]
                # Advance last_high/low pointers if we've passed them
                while hi_pointer + 1 < len(swings_high) and swings_high[hi_pointer + 1].idx <= i:
                    hi_pointer += 1
                    last_high = swings_high[hi_pointer]
                while lo_pointer + 1 < len(swings_low) and swings_low[lo_pointer + 1].idx <= i:
                    lo_pointer += 1
                    last_low = swings_low[lo_pointer]

                # Skip if we just had an event (prevents noise)
                if i - last_event_idx < 3:
                    continue

                # Check for structure breaks
                if last_high and bar.close > last_high.price and i > last_high.idx:
                    # Upside break
                    ev_type = StructureType.BOS if trend in {Trend.UP, Trend.UNKNOWN} else StructureType.CHOCH
                    if ev_type == StructureType.CHOCH:
                        last_choc_idx = i
                        sideways_count = 0  # Reset sideways counter on trend change
                
                    # Determine trend based on context
                    if trend == Trend.SIDEWAYS and ev_type == StructureType.BOS:
                        # Coming out of sideways into a trend
                        trend = Trend.UP
                        sideways_count = 0
                    elif trend != Trend.UP:
                        trend = Trend.UP
                        sideways_count = 0
                
                    # Calculate event strength
                    strength = last_high.strength  # Base on swing point strength
                    volume_delta = 0.0
                
                    if calculate_strength and has_volume and isinstance(data, pd.DataFrame):
                        # Volume confirmation component
                        if i < len(data):
                            current_vol = float(data.iloc[i]["volume"])
                            volume_delta = (current_vol - avg_volume) / avg_volume if avg_volume > 0 else 0.0
                            # Stronger if volume confirms the break
                            if volume_delta > 0.2:  # 20% above average
                                strength *= 1.2
                
                    # Create structure event with calculated properties
                    event = StructureEvent(
                        i, ev_type, last_high, bar.close,
                        strength=strength,
                        volume_delta=volume_delta,
                        confirmed=True,
                        timeframe=tf
                    )
                    events.append(event)
                    last_event_idx = i
                
                elif last_low and bar.close < last_low.price and i > last_low.idx:
                    # Downside break
                    ev_type = StructureType.BOS if trend in {Trend.DOWN, Trend.UNKNOWN} else StructureType.CHOCH
                    if ev_type == StructureType.CHOCH:
                        last_choc_idx = i
                        sideways_count = 0  # Reset sideways counter on trend change
                
                    # Determine trend based on context
                    if trend == Trend.SIDEWAYS and ev_type == StructureType.BOS:
                        # Coming out of sideways into a trend
                        trend = Trend.DOWN
                        sideways_count = 0
                    elif trend != Trend.DOWN:
                        trend = Trend.DOWN
                        sideways_count = 0
                
                    # Calculate event strength
                    strength = last_low.strength  # Base on swing point strength
                    volume_delta = 0.0
                
                    if calculate_strength and has_volume and isinstance(data, pd.DataFrame):
                        # Volume confirmation component
                        if i < len(data):
                            current_vol = float(data.iloc[i]["volume"])
                            volume_delta = (current_vol - avg_volume) / avg_volume if avg_volume > 0 else 0.0
                            # Stronger if volume confirms the break
                            if volume_delta > 0.2:  # 20% above average
                                strength *= 1.2
                
                    # Create structure event with calculated properties
                    event = StructureEvent(
                        i, ev_type, last_low, bar.close,
                        strength=strength,
                        volume_delta=volume_delta,
                        confirmed=True,
                        timeframe=tf
                    )
                    events.append(event)
                    last_event_idx = i
            
                # Detect sideways market (no clear breaks for a while)
                elif i > 20 and i - last_event_idx > 15:
                    sideways_count += 1
                    if sideways_count > 10 and trend != Trend.SIDEWAYS:
                        trend = Trend.SIDEWAYS

                # Enhanced COS detection: first BOS after CHOCH with specific characteristics
                if (
                    last_choc_idx is not None
                    and events
                    and events[-1].idx == i
                    and events[-1].event == StructureType.BOS
                    and events[-1].idx - last_choc_idx <= 15  # within 15 bars after CHOCH
                ):
                    events[-1].event = StructureType.COS
                    # COS events are typically more significant
                    events[-1].strength *= 1.25  # Increase strength for COS events
                    last_choc_idx = None

            return events
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect_structure: {e}")
            raise

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------

    def analyse_dataframe(self, df: pd.DataFrame, timeframe: TimeFrame = None) -> List[StructureEvent]:
        """Shortcut for DataFrame input with timeframe specification."""
        return self.detect_structure(df, timeframe=timeframe)
        
    def analyze_multi_timeframe(self, data_dict: dict[TimeFrame, pd.DataFrame]) -> dict[TimeFrame, List[StructureEvent]]:
        """Analyze market structure across multiple timeframes.
        
        Args:
            data_dict: Dictionary mapping timeframes to their respective DataFrames
            
        Returns:
            Dictionary mapping timeframes to their structure events
        """
        try:
            if not self.multi_timeframe:
                raise ValueError("Multi-timeframe analysis is disabled. Initialize with multi_timeframe=True")
            
            # Store results for each timeframe
            results = {}
        
            # Analyze each timeframe individually
            for tf, df in data_dict.items():
                results[tf] = self.detect_structure(df, timeframe=tf)
            
            # Store for correlation analysis
            self.timeframe_data = results
        
            # Correlate events across timeframes
            if len(data_dict) > 1:
                self._correlate_timeframes()
            
            return results
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze_multi_timeframe: {e}")
            raise
    
    def _correlate_timeframes(self) -> None:
        """Correlate structure events across timeframes.
        
        This method identifies relationships between structure events on different
        timeframes, enhancing the significance of events that align across multiple
        timeframes.
        """
        try:
            if not self.timeframe_data or len(self.timeframe_data) <= 1:
                return
            
            # Sort timeframes from higher to lower
            timeframes = sorted(self.timeframe_data.keys(), 
                               key=lambda tf: [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, 
                                              TimeFrame.M30, TimeFrame.H1, TimeFrame.H4, 
                                              TimeFrame.D1, TimeFrame.W1, TimeFrame.MN].index(tf),
                               reverse=True)
        
            # For each higher timeframe, find correlated events in lower timeframes
            for i, higher_tf in enumerate(timeframes[:-1]):
                higher_events = self.timeframe_data[higher_tf]
            
                for j, lower_tf in enumerate(timeframes[i+1:]):
                    lower_events = self.timeframe_data[lower_tf]
                
                    # Find correlations between these two timeframes
                    self._find_correlated_events(higher_events, lower_events, higher_tf, lower_tf)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _correlate_timeframes: {e}")
            raise
    
    def _find_correlated_events(self, 
                              higher_events: List[StructureEvent], 
                              lower_events: List[StructureEvent],
                              higher_tf: TimeFrame,
                              lower_tf: TimeFrame) -> None:
        """Find correlations between events on different timeframes.
        
        Args:
            higher_events: Events from the higher timeframe
            lower_events: Events from the lower timeframe
            higher_tf: The higher timeframe
            lower_tf: The lower timeframe
        """
        # For each event in the higher timeframe
        try:
            for h_event in higher_events:
                # Find lower timeframe events that occurred around the same time
                correlated = []
            
                # Time window for correlation (wider for higher timeframes)
                time_window = 3600  # 1 hour in seconds
                if higher_tf in {TimeFrame.H4, TimeFrame.D1}:
                    time_window = 14400  # 4 hours
                elif higher_tf in {TimeFrame.W1, TimeFrame.MN}:
                    time_window = 86400  # 24 hours
                
                for l_event in lower_events:
                    # Check if events are close in time
                    if abs(l_event.broken_swing.time - h_event.broken_swing.time) <= time_window:
                        # Check if they're the same type of event
                        if l_event.event == h_event.event:
                            correlated.append(l_event)
                        
                            # Enhance the strength of the lower timeframe event
                            # when it aligns with a higher timeframe event
                            l_event.strength *= 1.5
                        
                            # Store correlation in both events
                            if h_event.correlated_events is None:
                                h_event.correlated_events = []
                            if l_event.correlated_events is None:
                                l_event.correlated_events = []
                            
                            h_event.correlated_events.append(l_event)
                            l_event.correlated_events.append(h_event)
            
                # If we found correlations, increase the higher event's strength
                if correlated and h_event.correlated_events:
                    h_event.strength *= 1.2
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _find_correlated_events: {e}")
            raise
                
    def get_significant_events(self, min_strength: float = 1.5) -> List[StructureEvent]:
        """Get the most significant structure events across all timeframes.
        
        Args:
            min_strength: Minimum strength threshold for events
            
        Returns:
            List of significant structure events sorted by strength
        """
        try:
            all_events = []
        
            # Collect events from all timeframes
            for tf, events in self.timeframe_data.items():
                all_events.extend([e for e in events if e.strength >= min_strength])
            
            # Sort by strength (descending)
            return sorted(all_events, key=lambda e: e.strength, reverse=True)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in get_significant_events: {e}")
            raise


    # ------------------------------------------------------------------
    # Structure Mapping for Entry/Exit Points
    # ------------------------------------------------------------------
    
    def map_structure(self, data: pd.DataFrame, timeframe: TimeFrame = None) -> dict:
        """Map market structure to identify optimal entry and exit points.
        
        This method analyzes the market structure to identify:
        - Key support and resistance levels
        - Optimal entry zones based on structure breaks
        - Potential exit points (take profit and stop loss)
        - Structure-based risk-reward ratios
        
        Args:
            data: OHLC data as DataFrame
            timeframe: Timeframe of the data
            
        Returns:
            Dictionary containing structure mapping information
        """
        # Use provided timeframe or default
        try:
            tf = timeframe or self.default_timeframe
        
            # Detect structure events
            events = self.detect_structure(data, timeframe=tf)
        
            # Find swing points
            swings_high, swings_low = self.find_swings(data, timeframe=tf)
        
            # Identify current trend
            current_trend = self._identify_current_trend(events)
        
            # Identify key levels
            support_levels = self._identify_support_levels(swings_low, data)
            resistance_levels = self._identify_resistance_levels(swings_high, data)
        
            # Identify entry zones based on structure
            entry_zones = self._identify_entry_zones(events, current_trend, data)
        
            # Identify exit points
            exit_points = self._identify_exit_points(entry_zones, support_levels, resistance_levels, current_trend)
        
            # Calculate structure-based risk-reward ratios
            risk_reward = self._calculate_risk_reward(entry_zones, exit_points)
        
            return {
                "timeframe": tf,
                "current_trend": current_trend,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "entry_zones": entry_zones,
                "exit_points": exit_points,
                "risk_reward": risk_reward
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in map_structure: {e}")
            raise
    
    def _identify_current_trend(self, events: List[StructureEvent]) -> Trend:
        """Identify the current market trend based on recent structure events."""
        try:
            if not events:
                return Trend.UNKNOWN
            
            # Look at the most recent events
            recent_events = events[-min(5, len(events)):]
        
            # Count trend directions in recent events
            up_count = sum(1 for e in recent_events if 
                          (e.event == StructureType.BOS and e.broken_swing.kind == "high") or
                          (e.event == StructureType.CHOCH and e.broken_swing.kind == "low"))
                      
            down_count = sum(1 for e in recent_events if 
                            (e.event == StructureType.BOS and e.broken_swing.kind == "low") or
                            (e.event == StructureType.CHOCH and e.broken_swing.kind == "high"))
        
            # Determine trend based on counts
            if up_count > down_count:
                return Trend.UP
            elif down_count > up_count:
                return Trend.DOWN
            elif up_count == down_count and up_count > 0:
                # Equal counts but non-zero - likely sideways
                return Trend.SIDEWAYS
            else:
                return Trend.UNKNOWN
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _identify_current_trend: {e}")
            raise
    
    def _identify_support_levels(self, swings_low: List[SwingPoint], data: pd.DataFrame) -> List[dict]:
        """Identify key support levels from swing lows."""
        try:
            if not swings_low:
                return []
            
            # Group nearby swing lows (clustering)
            clusters = []
            current_cluster = [swings_low[0]]
        
            # Price threshold for clustering (as percentage)
            threshold = 0.0015  # 0.15%
        
            for i in range(1, len(swings_low)):
                current_swing = swings_low[i]
                prev_swing = current_cluster[-1]
            
                # Check if price is close enough to be in the same cluster
                price_diff_pct = abs(current_swing.price - prev_swing.price) / prev_swing.price
            
                if price_diff_pct <= threshold:
                    # Add to current cluster
                    current_cluster.append(current_swing)
                else:
                    # Start a new cluster
                    if current_cluster:
                        clusters.append(current_cluster)
                    current_cluster = [current_swing]
                
            # Add the last cluster if not empty
            if current_cluster:
                clusters.append(current_cluster)
            
            # Process clusters into support levels
            support_levels = []
        
            for cluster in clusters:
                # Calculate average price and strength
                avg_price = statistics.mean(s.price for s in cluster)
                avg_strength = statistics.mean(s.strength for s in cluster)
            
                # More points in a cluster means stronger support
                cluster_strength = avg_strength * (1 + 0.1 * (len(cluster) - 1))
            
                # Check if level was recently tested
                recent_test = False
                if len(data) > 0:
                    last_low = float(data.iloc[-1]["low"])
                    # If price came within 0.2% of the level recently
                    if abs(last_low - avg_price) / avg_price < 0.002:
                        recent_test = True
            
                support_levels.append({
                    "price": avg_price,
                    "strength": cluster_strength,
                    "num_tests": len(cluster),
                    "recent_test": recent_test,
                    "swings": cluster
                })
            
            # Sort by strength (descending)
            return sorted(support_levels, key=lambda x: x["strength"], reverse=True)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _identify_support_levels: {e}")
            raise
    
    def _identify_resistance_levels(self, swings_high: List[SwingPoint], data: pd.DataFrame) -> List[dict]:
        """Identify key resistance levels from swing highs."""
        try:
            if not swings_high:
                return []
            
            # Group nearby swing highs (clustering)
            clusters = []
            current_cluster = [swings_high[0]]
        
            # Price threshold for clustering (as percentage)
            threshold = 0.0015  # 0.15%
        
            for i in range(1, len(swings_high)):
                current_swing = swings_high[i]
                prev_swing = current_cluster[-1]
            
                # Check if price is close enough to be in the same cluster
                price_diff_pct = abs(current_swing.price - prev_swing.price) / prev_swing.price
            
                if price_diff_pct <= threshold:
                    # Add to current cluster
                    current_cluster.append(current_swing)
                else:
                    # Start a new cluster
                    if current_cluster:
                        clusters.append(current_cluster)
                    current_cluster = [current_swing]
                
            # Add the last cluster if not empty
            if current_cluster:
                clusters.append(current_cluster)
            
            # Process clusters into resistance levels
            resistance_levels = []
        
            for cluster in clusters:
                # Calculate average price and strength
                avg_price = statistics.mean(s.price for s in cluster)
                avg_strength = statistics.mean(s.strength for s in cluster)
            
                # More points in a cluster means stronger resistance
                cluster_strength = avg_strength * (1 + 0.1 * (len(cluster) - 1))
            
                # Check if level was recently tested
                recent_test = False
                if len(data) > 0:
                    last_high = float(data.iloc[-1]["high"])
                    # If price came within 0.2% of the level recently
                    if abs(last_high - avg_price) / avg_price < 0.002:
                        recent_test = True
            
                resistance_levels.append({
                    "price": avg_price,
                    "strength": cluster_strength,
                    "num_tests": len(cluster),
                    "recent_test": recent_test,
                    "swings": cluster
                })
            
            # Sort by strength (descending)
            return sorted(resistance_levels, key=lambda x: x["strength"], reverse=True)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _identify_resistance_levels: {e}")
            raise
    
    def _identify_entry_zones(self, events: List[StructureEvent], current_trend: Trend, data: pd.DataFrame) -> List[dict]:
        """Identify potential entry zones based on structure events."""
        try:
            if not events or len(data) == 0:
                return []
            
            entry_zones = []
            last_price = float(data.iloc[-1]["close"])
        
            # Look at recent structure events for entry opportunities
            recent_events = events[-min(10, len(events)):]
        
            for event in recent_events:
                # Skip older events
                if event.idx < len(data) - 30:  # Only consider last 30 bars
                    continue
                
                # BOS and COS events are good for entries in trend direction
                if event.event in {StructureType.BOS, StructureType.COS}:
                    # For uptrend, look for BOS/COS of swing lows
                    if current_trend == Trend.UP and event.broken_swing.kind == "low":
                        # Entry zone slightly above the broken level
                        entry_price = event.broken_swing.price * 1.001  # 0.1% above
                    
                        # Only include if price is still above the entry
                        if last_price >= entry_price:
                            entry_zones.append({
                                "price": entry_price,
                                "type": "long",
                                "strength": event.strength,
                                "event": event,
                                "description": f"{event.event.value} Long Entry"
                            })
                        
                    # For downtrend, look for BOS/COS of swing highs
                    elif current_trend == Trend.DOWN and event.broken_swing.kind == "high":
                        # Entry zone slightly below the broken level
                        entry_price = event.broken_swing.price * 0.999  # 0.1% below
                    
                        # Only include if price is still below the entry
                        if last_price <= entry_price:
                            entry_zones.append({
                                "price": entry_price,
                                "type": "short",
                                "strength": event.strength,
                                "event": event,
                                "description": f"{event.event.value} Short Entry"
                            })
            
                # CHOCH events can signal reversals - potential counter-trend entries
                elif event.event == StructureType.CHOCH and event.strength >= 1.5:
                    if event.broken_swing.kind == "high":
                        # Potential short entry below the broken high
                        entry_price = event.broken_swing.price * 0.998  # 0.2% below
                    
                        if last_price <= entry_price:
                            entry_zones.append({
                                "price": entry_price,
                                "type": "short",
                                "strength": event.strength * 0.8,  # Lower strength for counter-trend
                                "event": event,
                                "description": "CHOCH Short Entry (Reversal)"
                            })
                    else:  # Low
                        # Potential long entry above the broken low
                        entry_price = event.broken_swing.price * 1.002  # 0.2% above
                    
                        if last_price >= entry_price:
                            entry_zones.append({
                                "price": entry_price,
                                "type": "long",
                                "strength": event.strength * 0.8,  # Lower strength for counter-trend
                                "event": event,
                                "description": "CHOCH Long Entry (Reversal)"
                            })
        
            # Sort by strength (descending)
            return sorted(entry_zones, key=lambda x: x["strength"], reverse=True)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _identify_entry_zones: {e}")
            raise
    
    def _identify_exit_points(self, entry_zones: List[dict], 
                            support_levels: List[dict], 
                            resistance_levels: List[dict],
                            current_trend: Trend) -> dict:
        """Identify potential exit points (take profit and stop loss) for entries."""
        try:
            exits = {}
        
            for i, entry in enumerate(entry_zones):
                entry_price = entry["price"]
                entry_type = entry["type"]
            
                # Initialize exit points for this entry
                exits[f"entry_{i}"] = {
                    "entry": entry,
                    "take_profits": [],
                    "stop_loss": None
                }
            
                # For long entries
                if entry_type == "long":
                    # Stop loss: Use closest support level below entry
                    suitable_supports = [s for s in support_levels if s["price"] < entry_price]
                    if suitable_supports:
                        # Use the strongest nearby support for stop loss
                        stop_price = suitable_supports[0]["price"]
                        # Add small buffer (0.1% below support)
                        stop_price *= 0.999
                    
                        exits[f"entry_{i}"]["stop_loss"] = {
                            "price": stop_price,
                            "type": "support",
                            "risk_pct": (entry_price - stop_price) / entry_price * 100
                        }
                    
                    # Take profits: Use resistance levels above entry
                    suitable_resistances = [r for r in resistance_levels if r["price"] > entry_price]
                    for j, res in enumerate(suitable_resistances[:3]):  # Use top 3 resistances
                        # Calculate reward based on distance from entry
                        reward_pct = (res["price"] - entry_price) / entry_price * 100
                    
                        exits[f"entry_{i}"]["take_profits"].append({
                            "price": res["price"],
                            "type": "resistance",
                            "reward_pct": reward_pct,
                            "strength": res["strength"]
                        })
            
                # For short entries
                elif entry_type == "short":
                    # Stop loss: Use closest resistance level above entry
                    suitable_resistances = [r for r in resistance_levels if r["price"] > entry_price]
                    if suitable_resistances:
                        # Use the strongest nearby resistance for stop loss
                        stop_price = suitable_resistances[0]["price"]
                        # Add small buffer (0.1% above resistance)
                        stop_price *= 1.001
                    
                        exits[f"entry_{i}"]["stop_loss"] = {
                            "price": stop_price,
                            "type": "resistance",
                            "risk_pct": (stop_price - entry_price) / entry_price * 100
                        }
                    
                    # Take profits: Use support levels below entry
                    suitable_supports = [s for s in support_levels if s["price"] < entry_price]
                    for j, sup in enumerate(suitable_supports[:3]):  # Use top 3 supports
                        # Calculate reward based on distance from entry
                        reward_pct = (entry_price - sup["price"]) / entry_price * 100
                    
                        exits[f"entry_{i}"]["take_profits"].append({
                            "price": sup["price"],
                            "type": "support",
                            "reward_pct": reward_pct,
                            "strength": sup["strength"]
                        })
        
            return exits
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _identify_exit_points: {e}")
            raise
    
    def _calculate_risk_reward(self, entry_zones: List[dict], exit_points: dict) -> List[dict]:
        """Calculate risk-reward ratios for potential trades."""
        try:
            risk_reward_data = []
        
            for i, entry in enumerate(entry_zones):
                entry_key = f"entry_{i}"
                if entry_key not in exit_points:
                    continue
                
                exit_data = exit_points[entry_key]
                stop_loss = exit_data["stop_loss"]
                take_profits = exit_data["take_profits"]
            
                if not stop_loss or not take_profits:
                    continue
                
                # Calculate risk in percentage
                risk_pct = stop_loss["risk_pct"]
            
                # Calculate weighted average reward
                total_weight = sum(tp["strength"] for tp in take_profits)
                if total_weight == 0:
                    continue
                
                weighted_reward = sum(tp["reward_pct"] * tp["strength"] for tp in take_profits) / total_weight
            
                # Calculate risk-reward ratio
                if risk_pct > 0:
                    rr_ratio = weighted_reward / risk_pct
                else:
                    continue
                
                risk_reward_data.append({
                    "entry": entry,
                    "risk_pct": risk_pct,
                    "reward_pct": weighted_reward,
                    "risk_reward_ratio": rr_ratio,
                    "quality_score": rr_ratio * entry["strength"]
                })
            
            # Sort by quality score (descending)
            return sorted(risk_reward_data, key=lambda x: x["quality_score"], reverse=True)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _calculate_risk_reward: {e}")
            raise


# ---------------------------------------------------------------------------
# Quick & dirty self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    import random
    import time

    random.seed(42)
    prices = [1.1000]
    for _ in range(500):
        prices.append(prices[-1] + random.uniform(-0.003, 0.003))
    df = pd.DataFrame(
        {
            "time": [time.time() + i * 60 for i in range(len(prices))],
            "open": prices,
            "high": [p + random.uniform(0, 0.001) for p in prices],
            "low": [p - random.uniform(0, 0.001) for p in prices],
            "close": prices,
            "volume": [random.uniform(100, 1000) for _ in range(len(prices))]
        }
    )

    # Test the enhanced analyzer
    msa = MarketStructureAnalyzer(swing_len=3, multi_timeframe=True)
    evts = msa.analyse_dataframe(df)
    print("\nStructure Events:")
    for e in evts[-5:]:
        print(f"{e.event.value} at idx {e.idx}, strength: {e.strength:.2f}")
        
    # Test structure mapping
    print("\nStructure Mapping:")
    mapping = msa.map_structure(df)
    print(f"Current Trend: {mapping['current_trend'].value}")
    print(f"Found {len(mapping['support_levels'])} support levels")
    print(f"Found {len(mapping['resistance_levels'])} resistance levels")
    print(f"Found {len(mapping['entry_zones'])} potential entry zones")
    
    # Print top entry with risk/reward
    if mapping['entry_zones'] and mapping['risk_reward']:
        top_trade = mapping['risk_reward'][0]
        print(f"\nTop Trade: {top_trade['entry']['description']}")
        print(f"Entry: {top_trade['entry']['price']:.4f}")
        print(f"Risk: {top_trade['risk_pct']:.2f}%")
        print(f"Reward: {top_trade['reward_pct']:.2f}%")
        print(f"R/R Ratio: {top_trade['risk_reward_ratio']:.2f}")
        print(f"Quality Score: {top_trade['quality_score']:.2f}")
