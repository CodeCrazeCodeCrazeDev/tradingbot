"""Complete Wyckoff Analysis Module.

Implements the full Wyckoff methodology including:
- Wyckoff Phase Detection (Accumulation, Markup, Distribution, Markdown)
- Spring and Upthrust patterns
- Composite Operator theory
- Wyckoff Schematic mapping
- Accumulation/Distribution phase recognition
- Wyckoff Events (PS, SC, AR, ST, Spring, Test, SOS, LPS, etc.)
- Effort vs Result analysis
- Volume Spread Analysis (VSA)
- Cause and Effect analysis
- Wyckoff Wave analysis

This module enables identification of institutional
accumulation/distribution phases for smart money tracking.
"""


from __future__ import annotations
import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from enum import Enum
import numpy
import pandas
from enum import auto

import logging
logger = logging.getLogger(__name__)



class WyckoffPhase(enum.Enum):
    """Wyckoff Market Cycle Phases."""
    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


class AccumulationEvent(enum.Enum):
    """Wyckoff Accumulation Events."""
    PS = "preliminary_support"  # Preliminary Support
    SC = "selling_climax"  # Selling Climax
    AR = "automatic_rally"  # Automatic Rally
    ST = "secondary_test"  # Secondary Test
    SPRING = "spring"  # Spring (shakeout)
    TEST = "test"  # Test of Spring
    SOS = "sign_of_strength"  # Sign of Strength
    LPS = "last_point_of_support"  # Last Point of Support
    BU = "backup"  # Backup to edge of TR
    JAC = "jump_across_creek"  # Jump Across the Creek


class DistributionEvent(enum.Enum):
    """Wyckoff Distribution Events."""
    PSY = "preliminary_supply"  # Preliminary Supply
    BC = "buying_climax"  # Buying Climax
    AR = "automatic_reaction"  # Automatic Reaction
    ST = "secondary_test"  # Secondary Test
    UT = "upthrust"  # Upthrust
    UTAD = "upthrust_after_distribution"  # Upthrust After Distribution
    SOW = "sign_of_weakness"  # Sign of Weakness
    LPSY = "last_point_of_supply"  # Last Point of Supply
    ICE = "ice"  # Ice (support becomes resistance)


class VSASignal(enum.Enum):
    """Volume Spread Analysis Signals."""
    NO_DEMAND = "no_demand"
    NO_SUPPLY = "no_supply"
    STOPPING_VOLUME = "stopping_volume"
    CLIMAX_VOLUME = "climax_volume"
    EFFORT_VS_RESULT = "effort_vs_result"
    ABSORPTION = "absorption"
    SHAKEOUT = "shakeout"
    TEST = "test"
    PUSHING_UP = "pushing_up"
    PUSHING_DOWN = "pushing_down"


class CompositeOperatorAction(enum.Enum):
    """Composite Operator Actions."""
    ACCUMULATING = "accumulating"
    DISTRIBUTING = "distributing"
    MARKING_UP = "marking_up"
    MARKING_DOWN = "marking_down"
    TESTING = "testing"
    SHAKING_OUT = "shaking_out"
    NEUTRAL = "neutral"


@dataclass
class WyckoffEvent:
    """Represents a Wyckoff event."""
    event_type: str  # AccumulationEvent or DistributionEvent value
    price: float
    volume: float
    idx: int
    timestamp: Optional[datetime]
    confidence: float  # 0-100
    description: str


@dataclass
class WyckoffSchematic:
    """Complete Wyckoff Schematic."""
    phase: WyckoffPhase
    events: List[WyckoffEvent]
    trading_range_high: float
    trading_range_low: float
    creek_level: Optional[float]  # Resistance in accumulation
    ice_level: Optional[float]  # Support in distribution
    current_position: str  # Where price is in the schematic
    completion_percent: float  # How complete the phase is
    next_expected_event: Optional[str]


@dataclass
class VSABar:
    """Volume Spread Analysis for a single bar."""
    idx: int
    spread: float  # High - Low
    close_position: float  # Where close is in the range (0-1)
    volume: float
    relative_volume: float  # Compared to average
    relative_spread: float  # Compared to average
    signal: Optional[VSASignal]
    interpretation: str


@dataclass
class EffortResult:
    """Effort vs Result Analysis."""
    idx: int
    effort: float  # Volume
    result: float  # Price movement
    ratio: float  # Result / Effort
    divergence: bool  # High effort, low result or vice versa
    interpretation: str


@dataclass
class CauseEffect:
    """Cause and Effect Analysis."""
    cause_start_idx: int
    cause_end_idx: int
    cause_width: int  # Number of bars in trading range
    point_figure_count: int  # P&F box count
    projected_move: float
    direction: str  # 'up' or 'down'
    target_price: float


@dataclass
class CompositeOperator:
    """Composite Operator Analysis."""
    action: CompositeOperatorAction
    accumulation_score: float  # 0-100
    distribution_score: float  # 0-100
    net_position_change: float
    smart_money_direction: str  # 'bullish', 'bearish', 'neutral'
    confidence: float


class WyckoffCompleteAnalyzer:
    """Complete Wyckoff Analysis Engine.
    
    Provides comprehensive Wyckoff methodology analysis for
    identifying institutional accumulation/distribution phases.
    """
    
    def __init__(
        self,
        swing_lookback: int = 5,
        volume_ma_period: int = 20,
        spread_ma_period: int = 20,
        climax_volume_threshold: float = 2.0,
        spring_penetration_pct: float = 0.02
    ):
        """Initialize Wyckoff Analyzer.
        
        Args:
            swing_lookback: Bars for swing detection
            volume_ma_period: Period for volume moving average
            spread_ma_period: Period for spread moving average
            climax_volume_threshold: Multiplier for climax volume detection
            spring_penetration_pct: Percentage penetration for spring detection
        """
        try:
            self.swing_lookback = swing_lookback
            self.volume_ma_period = volume_ma_period
            self.spread_ma_period = spread_ma_period
            self.climax_volume_threshold = climax_volume_threshold
            self.spring_penetration_pct = spring_penetration_pct
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def detect_phase(
        self,
        df: pd.DataFrame
    ) -> WyckoffPhase:
        """Detect current Wyckoff phase.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Current WyckoffPhase
        """
        try:
            if len(df) < 50:
                return WyckoffPhase.UNKNOWN
            
            # Calculate metrics
            recent = df.iloc[-50:]
        
            # Price trend
            price_change = (recent['close'].iloc[-1] - recent['close'].iloc[0]) / recent['close'].iloc[0]
        
            # Volatility (range as % of price)
            avg_range = (recent['high'] - recent['low']).mean() / recent['close'].mean()
        
            # Volume trend
            vol_first_half = recent['volume'].iloc[:25].mean()
            vol_second_half = recent['volume'].iloc[25:].mean()
            vol_trend = (vol_second_half - vol_first_half) / vol_first_half if vol_first_half > 0 else 0
        
            # Higher highs/lows analysis
            highs = recent['high'].values
            lows = recent['low'].values
        
            higher_highs = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
            lower_lows = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i-1])
        
            # Determine phase
            if price_change > 0.05 and higher_highs > lower_lows:
                return WyckoffPhase.MARKUP
            elif price_change < -0.05 and lower_lows > higher_highs:
                return WyckoffPhase.MARKDOWN
            elif abs(price_change) < 0.03:
                # Sideways - check if accumulation or distribution
                # Accumulation: price near lows, volume increasing on up moves
                # Distribution: price near highs, volume increasing on down moves
            
                range_position = (recent['close'].iloc[-1] - recent['low'].min()) / (recent['high'].max() - recent['low'].min())
            
                if range_position < 0.4:
                    return WyckoffPhase.ACCUMULATION
                elif range_position > 0.6:
                    return WyckoffPhase.DISTRIBUTION
                
            return WyckoffPhase.UNKNOWN
        except Exception as e:
            logger.error(f"Error in detect_phase: {e}")
            raise
        
    def detect_accumulation_events(
        self,
        df: pd.DataFrame
    ) -> List[WyckoffEvent]:
        """Detect Wyckoff accumulation events.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of detected accumulation events
        """
        try:
            events = []
        
            if len(df) < 30:
                return events
            
            # Calculate metrics
            df = df.copy()
            df['volume_ma'] = df['volume'].rolling(self.volume_ma_period).mean()
            df['spread'] = df['high'] - df['low']
            df['spread_ma'] = df['spread'].rolling(self.spread_ma_period).mean()
            df['close_position'] = (df['close'] - df['low']) / df['spread'].replace(0, np.nan)
        
            # Find trading range
            tr_high = df['high'].max()
            tr_low = df['low'].min()
        
            # Detect Selling Climax (SC)
            for i in range(self.volume_ma_period, len(df)):
                row = df.iloc[i]
            
                # SC: High volume, wide spread, close near low, new low
                if (row['volume'] > row['volume_ma'] * self.climax_volume_threshold and
                    row['spread'] > row['spread_ma'] * 1.5 and
                    row['close_position'] < 0.3 and
                    row['low'] <= df.iloc[:i]['low'].min()):
                
                    events.append(WyckoffEvent(
                        event_type=AccumulationEvent.SC.value,
                        price=row['low'],
                        volume=row['volume'],
                        idx=i,
                        timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None,
                        confidence=80,
                        description="Selling Climax: High volume capitulation at new low"
                    ))
                
            # Detect Automatic Rally (AR)
            sc_events = [e for e in events if e.event_type == AccumulationEvent.SC.value]
            for sc in sc_events:
                # Look for rally after SC
                for i in range(sc.idx + 1, min(sc.idx + 10, len(df))):
                    row = df.iloc[i]
                
                    # AR: Quick rally on decreasing volume
                    if (row['close'] > df.iloc[sc.idx]['close'] * 1.02 and
                        row['volume'] < df.iloc[sc.idx]['volume'] * 0.7):
                    
                        events.append(WyckoffEvent(
                            event_type=AccumulationEvent.AR.value,
                            price=row['high'],
                            volume=row['volume'],
                            idx=i,
                            timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None,
                            confidence=70,
                            description="Automatic Rally: Quick bounce after selling climax"
                        ))
                        break
                    
            # Detect Spring
            for i in range(self.volume_ma_period, len(df)):
                row = df.iloc[i]
                prev_low = df.iloc[:i]['low'].min()
            
                # Spring: Brief penetration below support with quick recovery
                if (row['low'] < prev_low and
                    row['close'] > prev_low and
                    row['volume'] < row['volume_ma']):
                
                    # Check for recovery in next bars
                    if i + 3 < len(df):
                        recovery = df.iloc[i+1:i+4]['close'].mean() > row['close']
                        if recovery:
                            events.append(WyckoffEvent(
                                event_type=AccumulationEvent.SPRING.value,
                                price=row['low'],
                                volume=row['volume'],
                                idx=i,
                                timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None,
                                confidence=85,
                                description="Spring: Shakeout below support with quick recovery"
                            ))
                        
            # Detect Sign of Strength (SOS)
            for i in range(self.volume_ma_period, len(df)):
                row = df.iloc[i]
            
                # SOS: Strong move up on high volume, wide spread, close near high
                if (row['volume'] > row['volume_ma'] * 1.5 and
                    row['spread'] > row['spread_ma'] * 1.3 and
                    row['close_position'] > 0.7 and
                    row['close'] > df.iloc[i-5:i]['high'].max()):
                
                    events.append(WyckoffEvent(
                        event_type=AccumulationEvent.SOS.value,
                        price=row['high'],
                        volume=row['volume'],
                        idx=i,
                        timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None,
                        confidence=75,
                        description="Sign of Strength: Strong up move breaking resistance"
                    ))
                
            # Detect Last Point of Support (LPS)
            sos_events = [e for e in events if e.event_type == AccumulationEvent.SOS.value]
            for sos in sos_events:
                # Look for pullback after SOS
                for i in range(sos.idx + 1, min(sos.idx + 15, len(df))):
                    row = df.iloc[i]
                
                    # LPS: Pullback on low volume that holds above previous support
                    if (row['close'] < df.iloc[sos.idx]['close'] and
                        row['volume'] < row['volume_ma'] * 0.8 and
                        row['low'] > tr_low):
                    
                        events.append(WyckoffEvent(
                            event_type=AccumulationEvent.LPS.value,
                            price=row['low'],
                            volume=row['volume'],
                            idx=i,
                            timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None,
                            confidence=70,
                            description="Last Point of Support: Low volume pullback holding support"
                        ))
                        break
                    
            return events
        except Exception as e:
            logger.error(f"Error in detect_accumulation_events: {e}")
            raise
        
    def detect_distribution_events(
        self,
        df: pd.DataFrame
    ) -> List[WyckoffEvent]:
        """Detect Wyckoff distribution events.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of detected distribution events
        """
        try:
            events = []
        
            if len(df) < 30:
                return events
            
            # Calculate metrics
            df = df.copy()
            df['volume_ma'] = df['volume'].rolling(self.volume_ma_period).mean()
            df['spread'] = df['high'] - df['low']
            df['spread_ma'] = df['spread'].rolling(self.spread_ma_period).mean()
            df['close_position'] = (df['close'] - df['low']) / df['spread'].replace(0, np.nan)
        
            # Find trading range
            tr_high = df['high'].max()
            tr_low = df['low'].min()
        
            # Detect Buying Climax (BC)
            for i in range(self.volume_ma_period, len(df)):
                row = df.iloc[i]
            
                # BC: High volume, wide spread, close near high, new high
                if (row['volume'] > row['volume_ma'] * self.climax_volume_threshold and
                    row['spread'] > row['spread_ma'] * 1.5 and
                    row['close_position'] > 0.7 and
                    row['high'] >= df.iloc[:i]['high'].max()):
                
                    events.append(WyckoffEvent(
                        event_type=DistributionEvent.BC.value,
                        price=row['high'],
                        volume=row['volume'],
                        idx=i,
                        timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None,
                        confidence=80,
                        description="Buying Climax: High volume euphoria at new high"
                    ))
                
            # Detect Automatic Reaction (AR)
            bc_events = [e for e in events if e.event_type == DistributionEvent.BC.value]
            for bc in bc_events:
                # Look for decline after BC
                for i in range(bc.idx + 1, min(bc.idx + 10, len(df))):
                    row = df.iloc[i]
                
                    # AR: Quick decline on decreasing volume
                    if (row['close'] < df.iloc[bc.idx]['close'] * 0.98 and
                        row['volume'] < df.iloc[bc.idx]['volume'] * 0.7):
                    
                        events.append(WyckoffEvent(
                            event_type=DistributionEvent.AR.value,
                            price=row['low'],
                            volume=row['volume'],
                            idx=i,
                            timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None,
                            confidence=70,
                            description="Automatic Reaction: Quick decline after buying climax"
                        ))
                        break
                    
            # Detect Upthrust (UT)
            for i in range(self.volume_ma_period, len(df)):
                row = df.iloc[i]
                prev_high = df.iloc[:i]['high'].max()
            
                # UT: Brief penetration above resistance with quick reversal
                if (row['high'] > prev_high and
                    row['close'] < prev_high and
                    row['close_position'] < 0.5):
                
                    events.append(WyckoffEvent(
                        event_type=DistributionEvent.UT.value,
                        price=row['high'],
                        volume=row['volume'],
                        idx=i,
                        timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None,
                        confidence=80,
                        description="Upthrust: Failed breakout above resistance"
                    ))
                
            # Detect Sign of Weakness (SOW)
            for i in range(self.volume_ma_period, len(df)):
                row = df.iloc[i]
            
                # SOW: Strong move down on high volume, wide spread, close near low
                if (row['volume'] > row['volume_ma'] * 1.5 and
                    row['spread'] > row['spread_ma'] * 1.3 and
                    row['close_position'] < 0.3 and
                    row['close'] < df.iloc[i-5:i]['low'].min()):
                
                    events.append(WyckoffEvent(
                        event_type=DistributionEvent.SOW.value,
                        price=row['low'],
                        volume=row['volume'],
                        idx=i,
                        timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None,
                        confidence=75,
                        description="Sign of Weakness: Strong down move breaking support"
                    ))
                
            # Detect Last Point of Supply (LPSY)
            sow_events = [e for e in events if e.event_type == DistributionEvent.SOW.value]
            for sow in sow_events:
                # Look for rally after SOW
                for i in range(sow.idx + 1, min(sow.idx + 15, len(df))):
                    row = df.iloc[i]
                
                    # LPSY: Rally on low volume that fails at resistance
                    if (row['close'] > df.iloc[sow.idx]['close'] and
                        row['volume'] < row['volume_ma'] * 0.8 and
                        row['high'] < tr_high):
                    
                        events.append(WyckoffEvent(
                            event_type=DistributionEvent.LPSY.value,
                            price=row['high'],
                            volume=row['volume'],
                            idx=i,
                            timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else None,
                            confidence=70,
                            description="Last Point of Supply: Low volume rally failing at resistance"
                        ))
                        break
                    
            return events
        except Exception as e:
            logger.error(f"Error in detect_distribution_events: {e}")
            raise
        
    def analyze_vsa(
        self,
        df: pd.DataFrame
    ) -> List[VSABar]:
        """Perform Volume Spread Analysis.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of VSABar analysis for each bar
        """
        try:
            vsa_bars = []
        
            if len(df) < self.volume_ma_period:
                return vsa_bars
            
            df = df.copy()
            df['volume_ma'] = df['volume'].rolling(self.volume_ma_period).mean()
            df['spread'] = df['high'] - df['low']
            df['spread_ma'] = df['spread'].rolling(self.spread_ma_period).mean()
        
            for i in range(self.volume_ma_period, len(df)):
                row = df.iloc[i]
            
                spread = row['spread']
                close_pos = (row['close'] - row['low']) / spread if spread > 0 else 0.5
                rel_volume = row['volume'] / row['volume_ma'] if row['volume_ma'] > 0 else 1
                rel_spread = spread / row['spread_ma'] if row['spread_ma'] > 0 else 1
            
                # Determine VSA signal
                signal = None
                interpretation = ""
            
                # No Demand: Narrow spread, low volume, close in upper half, up bar
                if (rel_spread < 0.7 and rel_volume < 0.7 and 
                    close_pos > 0.5 and row['close'] > row['open']):
                    signal = VSASignal.NO_DEMAND
                    interpretation = "Weak buying - potential reversal down"
                
                # No Supply: Narrow spread, low volume, close in lower half, down bar
                elif (rel_spread < 0.7 and rel_volume < 0.7 and 
                      close_pos < 0.5 and row['close'] < row['open']):
                    signal = VSASignal.NO_SUPPLY
                    interpretation = "Weak selling - potential reversal up"
                
                # Stopping Volume: Wide spread, high volume, close off lows
                elif (rel_spread > 1.3 and rel_volume > 1.5 and 
                      close_pos > 0.4 and row['close'] < row['open']):
                    signal = VSASignal.STOPPING_VOLUME
                    interpretation = "Absorption of selling - potential bottom"
                
                # Climax Volume: Very wide spread, very high volume
                elif rel_spread > 1.5 and rel_volume > 2.0:
                    signal = VSASignal.CLIMAX_VOLUME
                    interpretation = "Climax activity - potential exhaustion"
                
                # Effort vs Result divergence
                elif rel_volume > 1.5 and rel_spread < 0.7:
                    signal = VSASignal.EFFORT_VS_RESULT
                    interpretation = "High effort, low result - absorption"
                
                # Test: Low volume, narrow spread, close near high after down move
                elif (rel_volume < 0.6 and rel_spread < 0.8 and 
                      close_pos > 0.6 and i > 0 and df.iloc[i-1]['close'] < df.iloc[i-1]['open']):
                    signal = VSASignal.TEST
                    interpretation = "Successful test of supply"
                
                vsa_bars.append(VSABar(
                    idx=i,
                    spread=spread,
                    close_position=close_pos,
                    volume=row['volume'],
                    relative_volume=rel_volume,
                    relative_spread=rel_spread,
                    signal=signal,
                    interpretation=interpretation
                ))
            
            return vsa_bars
        except Exception as e:
            logger.error(f"Error in analyze_vsa: {e}")
            raise
        
    def analyze_effort_result(
        self,
        df: pd.DataFrame,
        lookback: int = 5
    ) -> List[EffortResult]:
        """Analyze Effort vs Result.
        
        Effort = Volume
        Result = Price movement
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Bars to analyze
            
        Returns:
            List of EffortResult analysis
        """
        try:
            results = []
        
            if len(df) < lookback + 1:
                return results
            
            for i in range(lookback, len(df)):
                # Effort: Sum of volume over lookback
                effort = df.iloc[i-lookback:i+1]['volume'].sum()
            
                # Result: Price change over lookback
                result = abs(df.iloc[i]['close'] - df.iloc[i-lookback]['close'])
            
                # Normalize
                avg_volume = df['volume'].mean()
                avg_price = df['close'].mean()
            
                norm_effort = effort / (avg_volume * lookback) if avg_volume > 0 else 1
                norm_result = result / (avg_price * 0.01) if avg_price > 0 else 1  # Result as % of price
            
                ratio = norm_result / norm_effort if norm_effort > 0 else 1
            
                # Divergence: High effort with low result or vice versa
                divergence = (norm_effort > 1.5 and norm_result < 0.5) or (norm_effort < 0.5 and norm_result > 1.5)
            
                if divergence:
                    if norm_effort > norm_result:
                        interpretation = "High effort, low result - absorption/accumulation"
                    else:
                        interpretation = "Low effort, high result - easy movement"
                else:
                    interpretation = "Normal effort/result relationship"
                
                results.append(EffortResult(
                    idx=i,
                    effort=effort,
                    result=result,
                    ratio=ratio,
                    divergence=divergence,
                    interpretation=interpretation
                ))
            
            return results
        except Exception as e:
            logger.error(f"Error in analyze_effort_result: {e}")
            raise
        
    def analyze_composite_operator(
        self,
        df: pd.DataFrame
    ) -> CompositeOperator:
        """Analyze Composite Operator activity.
        
        The Composite Operator represents the aggregate
        actions of large institutional traders.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            CompositeOperator analysis
        """
        try:
            if len(df) < 30:
                return CompositeOperator(
                    action=CompositeOperatorAction.NEUTRAL,
                    accumulation_score=50,
                    distribution_score=50,
                    net_position_change=0,
                    smart_money_direction='neutral',
                    confidence=0
                )
            
            # Detect accumulation signs
            acc_events = self.detect_accumulation_events(df)
            dist_events = self.detect_distribution_events(df)
            vsa = self.analyze_vsa(df)
        
            # Score accumulation
            acc_score = 0
            acc_score += len([e for e in acc_events if e.event_type == AccumulationEvent.SPRING.value]) * 20
            acc_score += len([e for e in acc_events if e.event_type == AccumulationEvent.SOS.value]) * 15
            acc_score += len([e for e in acc_events if e.event_type == AccumulationEvent.LPS.value]) * 10
            acc_score += len([v for v in vsa if v.signal == VSASignal.NO_SUPPLY]) * 5
            acc_score += len([v for v in vsa if v.signal == VSASignal.STOPPING_VOLUME]) * 10
        
            # Score distribution
            dist_score = 0
            dist_score += len([e for e in dist_events if e.event_type == DistributionEvent.UT.value]) * 20
            dist_score += len([e for e in dist_events if e.event_type == DistributionEvent.SOW.value]) * 15
            dist_score += len([e for e in dist_events if e.event_type == DistributionEvent.LPSY.value]) * 10
            dist_score += len([v for v in vsa if v.signal == VSASignal.NO_DEMAND]) * 5
        
            # Normalize scores
            acc_score = min(100, acc_score)
            dist_score = min(100, dist_score)
        
            # Determine action
            if acc_score > dist_score + 20:
                action = CompositeOperatorAction.ACCUMULATING
                direction = 'bullish'
            elif dist_score > acc_score + 20:
                action = CompositeOperatorAction.DISTRIBUTING
                direction = 'bearish'
            else:
                # Check price trend
                price_change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
                if price_change > 0.03:
                    action = CompositeOperatorAction.MARKING_UP
                    direction = 'bullish'
                elif price_change < -0.03:
                    action = CompositeOperatorAction.MARKING_DOWN
                    direction = 'bearish'
                else:
                    action = CompositeOperatorAction.NEUTRAL
                    direction = 'neutral'
                
            # Net position change estimate
            net_change = (acc_score - dist_score) / 100
        
            # Confidence
            confidence = abs(acc_score - dist_score)
        
            return CompositeOperator(
                action=action,
                accumulation_score=acc_score,
                distribution_score=dist_score,
                net_position_change=net_change,
                smart_money_direction=direction,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in analyze_composite_operator: {e}")
            raise
        
    def build_schematic(
        self,
        df: pd.DataFrame
    ) -> WyckoffSchematic:
        """Build complete Wyckoff schematic.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            WyckoffSchematic with all components
        """
        try:
            phase = self.detect_phase(df)
        
            if phase == WyckoffPhase.ACCUMULATION:
                events = self.detect_accumulation_events(df)
            elif phase == WyckoffPhase.DISTRIBUTION:
                events = self.detect_distribution_events(df)
            else:
                events = self.detect_accumulation_events(df) + self.detect_distribution_events(df)
            
            # Trading range
            tr_high = df['high'].max()
            tr_low = df['low'].min()
        
            # Creek (resistance in accumulation) / Ice (support in distribution)
            creek_level = None
            ice_level = None
        
            if phase == WyckoffPhase.ACCUMULATION:
                # Creek is typically the AR high
                ar_events = [e for e in events if e.event_type == AccumulationEvent.AR.value]
                if ar_events:
                    creek_level = ar_events[0].price
            elif phase == WyckoffPhase.DISTRIBUTION:
                # Ice is typically the AR low
                ar_events = [e for e in events if e.event_type == DistributionEvent.AR.value]
                if ar_events:
                    ice_level = ar_events[0].price
                
            # Current position in schematic
            current_price = df['close'].iloc[-1]
            range_position = (current_price - tr_low) / (tr_high - tr_low) if tr_high != tr_low else 0.5
        
            if range_position < 0.3:
                current_position = "Near support"
            elif range_position > 0.7:
                current_position = "Near resistance"
            else:
                current_position = "Middle of range"
            
            # Completion percentage based on events
            if phase == WyckoffPhase.ACCUMULATION:
                expected_events = [AccumulationEvent.SC, AccumulationEvent.AR, AccumulationEvent.ST, 
                                 AccumulationEvent.SPRING, AccumulationEvent.SOS, AccumulationEvent.LPS]
                found_types = set(e.event_type for e in events)
                completion = len(found_types.intersection(set(e.value for e in expected_events))) / len(expected_events) * 100
            elif phase == WyckoffPhase.DISTRIBUTION:
                expected_events = [DistributionEvent.BC, DistributionEvent.AR, DistributionEvent.ST,
                                 DistributionEvent.UT, DistributionEvent.SOW, DistributionEvent.LPSY]
                found_types = set(e.event_type for e in events)
                completion = len(found_types.intersection(set(e.value for e in expected_events))) / len(expected_events) * 100
            else:
                completion = 0
            
            # Next expected event
            next_event = None
            if phase == WyckoffPhase.ACCUMULATION:
                found_types = set(e.event_type for e in events)
                if AccumulationEvent.SC.value not in found_types:
                    next_event = "Selling Climax"
                elif AccumulationEvent.SPRING.value not in found_types:
                    next_event = "Spring"
                elif AccumulationEvent.SOS.value not in found_types:
                    next_event = "Sign of Strength"
                else:
                    next_event = "Markup phase"
                
            return WyckoffSchematic(
                phase=phase,
                events=events,
                trading_range_high=tr_high,
                trading_range_low=tr_low,
                creek_level=creek_level,
                ice_level=ice_level,
                current_position=current_position,
                completion_percent=completion,
                next_expected_event=next_event
            )
        except Exception as e:
            logger.error(f"Error in build_schematic: {e}")
            raise
        
    def calculate_cause_effect(
        self,
        df: pd.DataFrame,
        box_size: Optional[float] = None
    ) -> CauseEffect:
        """Calculate Cause and Effect (Point & Figure count).
        
        The width of a trading range (cause) projects
        the potential price move (effect).
        
        Args:
            df: DataFrame with OHLCV data
            box_size: P&F box size (auto-calculated if None)
            
        Returns:
            CauseEffect analysis
        """
        try:
            if len(df) < 20:
                return CauseEffect(
                    cause_start_idx=0,
                    cause_end_idx=len(df)-1,
                    cause_width=len(df),
                    point_figure_count=0,
                    projected_move=0,
                    direction='neutral',
                    target_price=df['close'].iloc[-1]
                )
            
            # Auto-calculate box size (1% of average price)
            if box_size is None:
                box_size = df['close'].mean() * 0.01
            
            # Find trading range boundaries
            tr_high = df['high'].max()
            tr_low = df['low'].min()
        
            # Count P&F boxes (simplified)
            # Each column represents a reversal
            columns = 0
            current_direction = None
            current_extreme = df['close'].iloc[0]
        
            for i in range(1, len(df)):
                price = df['close'].iloc[i]
            
                if current_direction is None:
                    if price > current_extreme + box_size:
                        current_direction = 'up'
                        current_extreme = price
                        columns = 1
                    elif price < current_extreme - box_size:
                        current_direction = 'down'
                        current_extreme = price
                        columns = 1
                elif current_direction == 'up':
                    if price > current_extreme:
                        current_extreme = price
                    elif price < current_extreme - 3 * box_size:  # 3-box reversal
                        current_direction = 'down'
                        current_extreme = price
                        columns += 1
                else:  # down
                    if price < current_extreme:
                        current_extreme = price
                    elif price > current_extreme + 3 * box_size:
                        current_direction = 'up'
                        current_extreme = price
                        columns += 1
                    
            # Projected move = box count * box size
            pf_count = columns
            projected_move = pf_count * box_size
        
            # Direction based on recent trend
            recent_change = df['close'].iloc[-1] - df['close'].iloc[-10]
            direction = 'up' if recent_change > 0 else 'down'
        
            # Target price
            if direction == 'up':
                target_price = tr_low + projected_move
            else:
                target_price = tr_high - projected_move
            
            return CauseEffect(
                cause_start_idx=0,
                cause_end_idx=len(df)-1,
                cause_width=len(df),
                point_figure_count=pf_count,
                projected_move=projected_move,
                direction=direction,
                target_price=target_price
            )
        except Exception as e:
            logger.error(f"Error in calculate_cause_effect: {e}")
            raise


# Convenience functions
def detect_wyckoff_phase(df: pd.DataFrame) -> WyckoffPhase:
    """Quick function to detect Wyckoff phase."""
    try:
        analyzer = WyckoffCompleteAnalyzer()
        return analyzer.detect_phase(df)
    except Exception as e:
        logger.error(f"Error in detect_wyckoff_phase: {e}")
        raise


def get_wyckoff_schematic(df: pd.DataFrame) -> WyckoffSchematic:
    """Quick function to get Wyckoff schematic."""
    try:
        analyzer = WyckoffCompleteAnalyzer()
        return analyzer.build_schematic(df)
    except Exception as e:
        logger.error(f"Error in get_wyckoff_schematic: {e}")
        raise


def analyze_composite_operator(df: pd.DataFrame) -> CompositeOperator:
    """Quick function to analyze Composite Operator."""
    try:
        analyzer = WyckoffCompleteAnalyzer()
        return analyzer.analyze_composite_operator(df)
    except Exception as e:
        logger.error(f"Error in analyze_composite_operator: {e}")
        raise
