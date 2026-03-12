import logging
logger = logging.getLogger(__name__)
"""
Order Flow Analysis Module

This module provides advanced order flow analysis capabilities for the Elite Trading Bot,
including footprint charts, delta volume analysis, cumulative delta, market depth analysis,
and order flow imbalances detection.

The module integrates with market structure and liquidity analysis to provide a comprehensive
view of market dynamics and institutional activity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union
import time

import numpy as np
import pandas as pd
from loguru import logger

from trading_bot.analysis.market_structure import TimeFrame


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ImbalanceType(Enum):
    """Types of order flow imbalances."""
    BUY = auto()  # More buying pressure than selling
    SELL = auto()  # More selling pressure than buying
    NEUTRAL = auto()  # Balanced buying and selling


class DeltaSignal(Enum):
    """Signal types from delta analysis."""
    BULLISH = auto()  # Positive delta, buying pressure
    BEARISH = auto()  # Negative delta, selling pressure
    NEUTRAL = auto()  # Balanced delta, no clear direction


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class FootprintBar:
    """Represents a footprint chart bar with buy/sell volume at each price level."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    total_volume: float
    buy_volume: float
    sell_volume: float
    delta: float  # buy_volume - sell_volume
    price_levels: Dict[float, Tuple[float, float]]  # price -> (buy_vol, sell_vol)
    poc_price: float  # Point of control price (highest volume price)
    imbalance_levels: List[Tuple[float, ImbalanceType, float]]  # (price, type, strength)
    timeframe: TimeFrame = None


@dataclass
class DeltaBar:
    """Represents a delta volume bar with cumulative metrics."""
    timestamp: datetime
    price: float
    delta: float  # Current bar's delta (buy - sell)
    cumulative_delta: float  # Running sum of delta
    delta_strength: float  # Normalized delta relative to recent bars
    signal: DeltaSignal
    divergence: bool = False  # True if delta diverges from price
    timeframe: TimeFrame = None


@dataclass
class MarketDepth:
    """Represents market depth data at a point in time."""
    timestamp: datetime
    bids: Dict[float, float]  # price -> volume
    asks: Dict[float, float]  # price -> volume
    bid_total: float
    ask_total: float
    imbalance_ratio: float  # bid_total / ask_total
    signal: DeltaSignal
    timeframe: TimeFrame = None


@dataclass
class OrderFlowImbalance:
    """Represents a significant order flow imbalance."""
    timestamp: datetime
    price_level: float
    imbalance_type: ImbalanceType
    strength: float  # 0.0 to 2.0, higher is stronger
    volume_ratio: float  # ratio of buy/sell or sell/buy volume
    confirmed: bool = False
    timeframe: TimeFrame = None


# ---------------------------------------------------------------------------
# Main Analyzer Class
# ---------------------------------------------------------------------------


class OrderFlowAnalyzer:
    """Analyzes order flow data to identify institutional activity and market bias."""

    def __init__(
        self,
        imbalance_threshold: float = 2.0,  # Minimum ratio to consider an imbalance
        delta_lookback: int = 20,  # Bars to look back for delta context
        volume_profile_levels: int = 20,  # Number of price levels in volume profile
        multi_timeframe: bool = False,
        default_timeframe: TimeFrame = TimeFrame.M15,
        real_time_mode: bool = False,
        cache_size: int = 1000  # Maximum number of bars to keep in cache
    ):
        """Initialize the order flow analyzer.
        
        Args:
            imbalance_threshold: Minimum buy/sell ratio to consider an imbalance
            delta_lookback: Number of bars to look back for delta context
            volume_profile_levels: Number of price levels to use in volume profiles
            multi_timeframe: Whether to enable multi-timeframe analysis
            default_timeframe: Default timeframe to use when none is specified
            real_time_mode: Enable optimizations for real-time trading
            cache_size: Maximum number of bars to keep in cache
        """
        try:
            self.imbalance_threshold = imbalance_threshold
            self.delta_lookback = delta_lookback
            self.volume_profile_levels = volume_profile_levels
            self.multi_timeframe = multi_timeframe
            self.default_timeframe = default_timeframe
            self.real_time_mode = real_time_mode
            self.cache_size = cache_size
        
            # Caches for multi-timeframe analysis
            self._footprint_bars: Dict[TimeFrame, List[FootprintBar]] = {}
            self._delta_bars: Dict[TimeFrame, List[DeltaBar]] = {}
            self._imbalances: Dict[TimeFrame, List[OrderFlowImbalance]] = {}
            self._market_depth: Dict[TimeFrame, List[MarketDepth]] = {}
            self._timeframe_data: Dict[TimeFrame, pd.DataFrame] = {}
        
            # Real-time optimization caches
            self._last_processed_timestamp: Dict[TimeFrame, datetime] = {}
            self._cumulative_delta: Dict[TimeFrame, float] = {}
            self._recent_deltas: Dict[TimeFrame, List[float]] = {}
            self._signal_cache: Dict[TimeFrame, pd.DataFrame] = {}
        
            # Performance metrics
            self._processing_times: List[float] = []
            self._last_processing_time: float = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    # ------------------------------------------------------------------
    # Footprint Chart Analysis
    # ------------------------------------------------------------------

    def create_footprint_chart(
        self, 
        data: pd.DataFrame,
        bid_ask_data: Optional[pd.DataFrame] = None,
        timeframe: TimeFrame = None
    ) -> List[FootprintBar]:
        """Create footprint chart data from OHLCV and optional bid-ask data.
        
        Args:
            data: OHLCV DataFrame
            bid_ask_data: Optional DataFrame with bid/ask volumes
            timeframe: Timeframe for analysis
            
        Returns:
            List of FootprintBar objects
        """
        try:
            if timeframe is None:
                timeframe = self.default_timeframe
            
            footprint_bars = []
        
            # If we have actual bid-ask data, use it
            if bid_ask_data is not None:
                for i in range(len(data)):
                    timestamp = data.index[i]
                
                    # Get bid-ask data for this bar's time range
                    if i < len(data) - 1:
                        next_timestamp = data.index[i+1]
                        mask = (bid_ask_data.index >= timestamp) & (bid_ask_data.index < next_timestamp)
                    else:
                        mask = bid_ask_data.index >= timestamp
                    
                    period_data = bid_ask_data[mask]
                
                    if len(period_data) == 0:
                        continue
                    
                    # Calculate price levels and volumes
                    price_levels = {}
                    for price in np.linspace(data.loc[timestamp, 'low'], data.loc[timestamp, 'high'], 
                                            self.volume_profile_levels):
                        price = round(price, 5)  # Round to avoid floating point issues
                    
                        # Find trades near this price level
                        price_mask = (period_data['price'] >= price - 0.0001) & (period_data['price'] < price + 0.0001)
                        price_data = period_data[price_mask]
                    
                        if len(price_data) > 0:
                            buy_vol = price_data[price_data['side'] == 'buy']['volume'].sum()
                            sell_vol = price_data[price_data['side'] == 'sell']['volume'].sum()
                            price_levels[price] = (buy_vol, sell_vol)
                
                    # Calculate totals
                    buy_volume = sum(bv for bv, _ in price_levels.values())
                    sell_volume = sum(sv for _, sv in price_levels.values())
                    delta = buy_volume - sell_volume
                
                    # Find point of control (price level with highest volume)
                    poc_price = max(price_levels.keys(), 
                                   key=lambda p: price_levels[p][0] + price_levels[p][1], 
                                   default=data.loc[timestamp, 'close'])
                
                    # Find imbalance levels
                    imbalance_levels = []
                    for price, (buy_vol, sell_vol) in price_levels.items():
                        if buy_vol > 0 and sell_vol > 0:
                            ratio = buy_vol / sell_vol if buy_vol > sell_vol else sell_vol / buy_vol
                            if ratio >= self.imbalance_threshold:
                                imbalance_type = ImbalanceType.BUY if buy_vol > sell_vol else ImbalanceType.SELL
                                strength = min(2.0, ratio / self.imbalance_threshold)
                                imbalance_levels.append((price, imbalance_type, strength))
                
                    # Create footprint bar
                    footprint_bar = FootprintBar(
                        timestamp=timestamp,
                        open=data.loc[timestamp, 'open'],
                        high=data.loc[timestamp, 'high'],
                        low=data.loc[timestamp, 'low'],
                        close=data.loc[timestamp, 'close'],
                        total_volume=buy_volume + sell_volume,
                        buy_volume=buy_volume,
                        sell_volume=sell_volume,
                        delta=delta,
                        price_levels=price_levels,
                        poc_price=poc_price,
                        imbalance_levels=imbalance_levels,
                        timeframe=timeframe
                    )
                
                    footprint_bars.append(footprint_bar)
            else:
                # Estimate buy/sell volume from price action if bid-ask data is not available
                logger.info("No bid-ask data provided, estimating buy/sell volume from price action")
            
                for i in range(len(data)):
                    timestamp = data.index[i]
                    row = data.iloc[i]
                
                    # Estimate buy/sell volume based on price movement
                    # This is a simple heuristic - in real trading, use actual bid-ask data
                    close_position = (row['close'] - row['low']) / (row['high'] - row['low']) if row['high'] != row['low'] else 0.5
                    buy_volume = row['volume'] * close_position
                    sell_volume = row['volume'] - buy_volume
                    delta = buy_volume - sell_volume
                
                    # Create synthetic price levels
                    price_levels = {}
                    price_range = np.linspace(row['low'], row['high'], self.volume_profile_levels)
                
                    # Distribute volume across price levels based on proximity to close
                    for price in price_range:
                        price = round(price, 5)
                        # More volume near the close
                        price_position = (price - row['low']) / (row['high'] - row['low']) if row['high'] != row['low'] else 0.5
                        weight = 1 - abs(price_position - close_position)
                    
                        # Assign buy/sell volume based on price position and weight
                        level_volume = row['volume'] * weight / sum(
                            1 - abs((p - row['low']) / (row['high'] - row['low']) - close_position) 
                            for p in price_range if row['high'] != row['low']
                        ) if row['high'] != row['low'] else row['volume'] / len(price_range)
                    
                        buy_level = level_volume * (price_position if price >= row['open'] else 0.3)
                        sell_level = level_volume - buy_level
                    
                        price_levels[price] = (buy_level, sell_level)
                
                    # Find point of control (price level with highest volume)
                    poc_price = max(price_levels.keys(), 
                                   key=lambda p: price_levels[p][0] + price_levels[p][1], 
                                   default=row['close'])
                
                    # Find imbalance levels
                    imbalance_levels = []
                    for price, (buy_vol, sell_vol) in price_levels.items():
                        if buy_vol > 0 and sell_vol > 0:
                            ratio = buy_vol / sell_vol if buy_vol > sell_vol else sell_vol / buy_vol
                            if ratio >= self.imbalance_threshold:
                                imbalance_type = ImbalanceType.BUY if buy_vol > sell_vol else ImbalanceType.SELL
                                strength = min(2.0, ratio / self.imbalance_threshold)
                                imbalance_levels.append((price, imbalance_type, strength))
                
                    # Create footprint bar
                    footprint_bar = FootprintBar(
                        timestamp=timestamp,
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        total_volume=row['volume'],
                        buy_volume=buy_volume,
                        sell_volume=sell_volume,
                        delta=delta,
                        price_levels=price_levels,
                        poc_price=poc_price,
                        imbalance_levels=imbalance_levels,
                        timeframe=timeframe
                    )
                
                    footprint_bars.append(footprint_bar)
        
            # Cache results for multi-timeframe analysis
            self._footprint_bars[timeframe] = footprint_bars
        
            return footprint_bars
        except Exception as e:
            logger.error(f"Error in create_footprint_chart: {e}")
            raise

    # ------------------------------------------------------------------
    # Delta Volume Analysis
    # ------------------------------------------------------------------

    def analyze_delta(
        self, 
        data: pd.DataFrame,
        footprint_bars: Optional[List[FootprintBar]] = None,
        timeframe: TimeFrame = None
    ) -> List[DeltaBar]:
        """Analyze delta volume and cumulative delta.
        
        Args:
            data: OHLCV DataFrame
            footprint_bars: Optional pre-computed footprint bars
            timeframe: Timeframe for analysis
            
        Returns:
            List of DeltaBar objects
        """
        try:
            if timeframe is None:
                timeframe = self.default_timeframe
            
            # Use existing footprint bars or create new ones
            if footprint_bars is None:
                if timeframe in self._footprint_bars:
                    footprint_bars = self._footprint_bars[timeframe]
                else:
                    footprint_bars = self.create_footprint_chart(data, timeframe=timeframe)
        
            delta_bars = []
            cumulative_delta = 0
        
            # Calculate delta metrics
            for i, fb in enumerate(footprint_bars):
                cumulative_delta += fb.delta
            
                # Calculate delta strength relative to recent bars
                lookback = min(i, self.delta_lookback)
                if lookback > 0:
                    recent_deltas = [footprint_bars[j].delta for j in range(i - lookback, i)]
                    mean_delta = sum(recent_deltas) / len(recent_deltas)
                    std_delta = np.std(recent_deltas) if len(recent_deltas) > 1 else 1.0
                
                    # Z-score of current delta
                    delta_strength = (fb.delta - mean_delta) / std_delta if std_delta > 0 else 0
                    delta_strength = min(max(delta_strength, -2), 2)  # Clamp to [-2, 2]
                else:
                    delta_strength = 0
            
                # Determine signal
                if fb.delta > 0 and delta_strength > 0.5:
                    signal = DeltaSignal.BULLISH
                elif fb.delta < 0 and delta_strength < -0.5:
                    signal = DeltaSignal.BEARISH
                else:
                    signal = DeltaSignal.NEUTRAL
            
                # Check for divergence
                divergence = False
                if i > 0:
                    prev_close = footprint_bars[i-1].close
                    price_up = fb.close > prev_close
                    delta_up = fb.delta > footprint_bars[i-1].delta
                
                    # Divergence when price and delta move in opposite directions
                    divergence = (price_up and not delta_up) or (not price_up and delta_up)
            
                # Create delta bar
                delta_bar = DeltaBar(
                    timestamp=fb.timestamp,
                    price=fb.close,
                    delta=fb.delta,
                    cumulative_delta=cumulative_delta,
                    delta_strength=delta_strength,
                    signal=signal,
                    divergence=divergence,
                    timeframe=timeframe
                )
            
                delta_bars.append(delta_bar)
        
            # Cache results for multi-timeframe analysis
            self._delta_bars[timeframe] = delta_bars
        
            return delta_bars
        except Exception as e:
            logger.error(f"Error in analyze_delta: {e}")
            raise

    # ------------------------------------------------------------------
    # Market Depth Analysis
    # ------------------------------------------------------------------

    def analyze_market_depth(
        self, 
        depth_data: pd.DataFrame,
        timeframe: TimeFrame = None
    ) -> List[MarketDepth]:
        """Analyze market depth data to identify imbalances and signals.
        
        Args:
            depth_data: DataFrame with bid/ask data by price level
            timeframe: Timeframe for analysis
            
        Returns:
            List of MarketDepth objects
        """
        try:
            if timeframe is None:
                timeframe = self.default_timeframe
            
            market_depths = []
        
            # Group by timestamp
            grouped = depth_data.groupby(depth_data.index)
        
            for timestamp, group in grouped:
                bids = {}
                asks = {}
            
                # Extract bid and ask data
                for _, row in group.iterrows():
                    if 'bid_price' in row and 'bid_volume' in row:
                        bids[row['bid_price']] = row['bid_volume']
                    if 'ask_price' in row and 'ask_volume' in row:
                        asks[row['ask_price']] = row['ask_volume']
            
                # Calculate totals
                bid_total = sum(bids.values())
                ask_total = sum(asks.values())
            
                # Calculate imbalance ratio
                imbalance_ratio = bid_total / ask_total if ask_total > 0 else float('inf')
            
                # Determine signal
                if imbalance_ratio > 1.5:
                    signal = DeltaSignal.BULLISH
                elif imbalance_ratio < 0.67:
                    signal = DeltaSignal.BEARISH
                else:
                    signal = DeltaSignal.NEUTRAL
            
                # Create market depth object
                depth = MarketDepth(
                    timestamp=timestamp,
                    bids=bids,
                    asks=asks,
                    bid_total=bid_total,
                    ask_total=ask_total,
                    imbalance_ratio=imbalance_ratio,
                    signal=signal,
                    timeframe=timeframe
                )
            
                market_depths.append(depth)
        
            # Cache results for multi-timeframe analysis
            self._market_depth[timeframe] = market_depths
        
            return market_depths
        except Exception as e:
            logger.error(f"Error in analyze_market_depth: {e}")
            raise

    # ------------------------------------------------------------------
    # Order Flow Imbalance Detection
    # ------------------------------------------------------------------

    def detect_imbalances(
        self, 
        footprint_bars: List[FootprintBar],
        timeframe: TimeFrame = None
    ) -> List[OrderFlowImbalance]:
        """Detect significant order flow imbalances from footprint data.
        
        Args:
            footprint_bars: List of FootprintBar objects
            timeframe: Timeframe for analysis
            
        Returns:
            List of OrderFlowImbalance objects
        """
        try:
            if timeframe is None:
                timeframe = self.default_timeframe
            
            imbalances = []
        
            for fb in footprint_bars:
                # Process significant imbalances
                for price, imbalance_type, strength in fb.imbalance_levels:
                    if strength >= 1.0:  # Only include strong imbalances
                        # Calculate volume ratio
                        buy_vol, sell_vol = fb.price_levels.get(price, (0, 0))
                        volume_ratio = buy_vol / sell_vol if imbalance_type == ImbalanceType.BUY else sell_vol / buy_vol
                    
                        # Create imbalance object
                        imbalance = OrderFlowImbalance(
                            timestamp=fb.timestamp,
                            price_level=price,
                            imbalance_type=imbalance_type,
                            strength=strength,
                            volume_ratio=volume_ratio,
                            confirmed=False,  # Will be confirmed by price action later
                            timeframe=timeframe
                        )
                    
                        imbalances.append(imbalance)
        
            # Confirm imbalances based on subsequent price action
            for i, imb in enumerate(imbalances):
                # Find the next bar after this imbalance
                next_bars = [fb for fb in footprint_bars if fb.timestamp > imb.timestamp]
            
                if next_bars:
                    next_bar = next_bars[0]
                
                    # Check if price respected the imbalance level
                    if imb.imbalance_type == ImbalanceType.BUY:
                        # Buy imbalance should act as support
                        if next_bar.low <= imb.price_level <= next_bar.high and next_bar.close > imb.price_level:
                            imb.confirmed = True
                    else:  # SELL imbalance
                        # Sell imbalance should act as resistance
                        if next_bar.low <= imb.price_level <= next_bar.high and next_bar.close < imb.price_level:
                            imb.confirmed = True
        
            # Cache results for multi-timeframe analysis
            self._imbalances[timeframe] = imbalances
        
            return imbalances
        except Exception as e:
            logger.error(f"Error in detect_imbalances: {e}")
            raise

    # ------------------------------------------------------------------
    # Multi-Timeframe Analysis
    # ------------------------------------------------------------------

    def analyze_multi_timeframe(
        self, 
        data_dict: Dict[TimeFrame, pd.DataFrame],
        depth_dict: Optional[Dict[TimeFrame, pd.DataFrame]] = None
    ) -> Dict[str, Dict[TimeFrame, List]]:
        """Perform multi-timeframe order flow analysis.
        
        Args:
            data_dict: Dictionary mapping timeframes to OHLCV DataFrames
            depth_dict: Optional dictionary mapping timeframes to depth data
            
        Returns:
            Dictionary of analysis results by type and timeframe
        """
        try:
            if not self.multi_timeframe:
                logger.warning("Multi-timeframe analysis is disabled. Enable with multi_timeframe=True")
                return {}
            
            # Store data for later reference
            self._timeframe_data = data_dict
        
            # Analyze each timeframe
            for tf, data in data_dict.items():
                # Create footprint chart
                footprint_bars = self.create_footprint_chart(data, timeframe=tf)
            
                # Analyze delta
                self.analyze_delta(data, footprint_bars, timeframe=tf)
            
                # Detect imbalances
                self.detect_imbalances(footprint_bars, timeframe=tf)
            
                # Analyze market depth if available
                if depth_dict and tf in depth_dict:
                    self.analyze_market_depth(depth_dict[tf], timeframe=tf)
        
            # Correlate findings across timeframes
            self._correlate_imbalances()
        
            # Return all analysis results
            return {
                "footprint_bars": self._footprint_bars,
                "delta_bars": self._delta_bars,
                "imbalances": self._imbalances,
                "market_depth": self._market_depth
            }
        except Exception as e:
            logger.error(f"Error in analyze_multi_timeframe: {e}")
            raise

    def _correlate_imbalances(self) -> None:
        """Correlate imbalances across timeframes to enhance strength."""
        try:
            if len(self._imbalances) <= 1:
                return
            
            # Sort timeframes from smallest to largest
            timeframes = sorted(self._imbalances.keys(), 
                               key=lambda tf: TimeFrame[tf.name].value if isinstance(tf, TimeFrame) else 0)
        
            # For each larger timeframe, check if its imbalances are confirmed by smaller timeframes
            for i in range(1, len(timeframes)):
                larger_tf = timeframes[i]
                larger_imbalances = self._imbalances[larger_tf]
            
                # Check each larger timeframe imbalance against smaller timeframe imbalances
                for imb in larger_imbalances:
                    for j in range(i):
                        smaller_tf = timeframes[j]
                        smaller_imbalances = self._imbalances[smaller_tf]
                    
                        # Find confirming imbalances of the same type
                        confirming_imbalances = []
                        for simb in smaller_imbalances:
                            if simb.imbalance_type == imb.imbalance_type:
                                # Check if price levels are close
                                if abs(simb.price_level - imb.price_level) / imb.price_level < 0.001:  # 0.1% tolerance
                                    confirming_imbalances.append(simb)
                    
                        # Enhance strength based on confirmations
                        if confirming_imbalances:
                            # More confirmations = stronger
                            confirmation_boost = min(0.5, 0.1 * len(confirming_imbalances))
                            imb.strength = min(2.0, imb.strength + confirmation_boost)
        except Exception as e:
            logger.error(f"Error in _correlate_imbalances: {e}")
            raise

    # ------------------------------------------------------------------
    # Signal Generation
    # ------------------------------------------------------------------

    def generate_signals(
        self, 
        data: pd.DataFrame,
        timeframe: TimeFrame = None
    ) -> pd.DataFrame:
        """Generate trading signals based on order flow analysis.
        
        Args:
            data: OHLCV DataFrame
            timeframe: Timeframe for analysis
            
        Returns:
            DataFrame with signals
        """
        try:
            if timeframe is None:
                timeframe = self.default_timeframe
            
            # Ensure we have all required analysis
            if timeframe not in self._footprint_bars:
                self.create_footprint_chart(data, timeframe=timeframe)
            
            if timeframe not in self._delta_bars:
                self.analyze_delta(data, timeframe=timeframe)
            
            if timeframe not in self._imbalances:
                self.detect_imbalances(self._footprint_bars[timeframe], timeframe=timeframe)
        
            # Use cached signals if in real-time mode and we have them
            if self.real_time_mode and timeframe in self._signal_cache:
                cached_signals = self._signal_cache[timeframe]
                # Only generate signals for new timestamps
                new_timestamps = [ts for ts in data.index if ts not in cached_signals.index]
                if not new_timestamps:
                    return cached_signals
            
                # Create signals only for new data
                new_data = data.loc[new_timestamps]
                new_signals = self._generate_signals_internal(new_data, timeframe)
            
                # Combine with cached signals
                signals = pd.concat([cached_signals, new_signals])
            
                # Limit cache size
                if len(signals) > self.cache_size:
                    signals = signals.iloc[-self.cache_size:]
                
                # Update cache
                self._signal_cache[timeframe] = signals
                return signals
            else:
                # Generate signals for all data
                signals = self._generate_signals_internal(data, timeframe)
            
                # Cache if in real-time mode
                if self.real_time_mode:
                    self._signal_cache[timeframe] = signals
                
                return signals
        except Exception as e:
            logger.error(f"Error in generate_signals: {e}")
            raise
    
    def _generate_signals_internal(
        self,
        data: pd.DataFrame,
        timeframe: TimeFrame
    ) -> pd.DataFrame:
        """Internal method to generate signals from analyzed data."""
        try:
            start_time = time.time()
        
            # Create signal DataFrame
            signals = pd.DataFrame(index=data.index)
            signals['bullish'] = 0
            signals['bearish'] = 0
            signals['strength'] = 0
        
            # Add delta signals
            for db in self._delta_bars[timeframe]:
                if db.timestamp in signals.index:
                    if db.signal == DeltaSignal.BULLISH:
                        signals.loc[db.timestamp, 'bullish'] += 1
                        signals.loc[db.timestamp, 'strength'] += abs(db.delta_strength)
                    elif db.signal == DeltaSignal.BEARISH:
                        signals.loc[db.timestamp, 'bearish'] += 1
                        signals.loc[db.timestamp, 'strength'] += abs(db.delta_strength)
                
                    # Add divergence as a stronger signal
                    if db.divergence:
                        if db.delta > 0:  # Positive delta divergence
                            signals.loc[db.timestamp, 'bullish'] += 2
                        else:  # Negative delta divergence
                            signals.loc[db.timestamp, 'bearish'] += 2
        
            # Add imbalance signals
            for imb in self._imbalances[timeframe]:
                if imb.timestamp in signals.index and imb.confirmed:
                    if imb.imbalance_type == ImbalanceType.BUY:
                        signals.loc[db.timestamp, 'bullish'] += 1
                        signals.loc[db.timestamp, 'strength'] += imb.strength
                    elif imb.imbalance_type == ImbalanceType.SELL:
                        signals.loc[db.timestamp, 'bearish'] += 1
                        signals.loc[db.timestamp, 'strength'] += imb.strength
        
            # Calculate net signal
            signals['net_signal'] = signals['bullish'] - signals['bearish']
        
            # Normalize strength to 0-1 range
            max_strength = signals['strength'].max()
            if max_strength > 0:
                signals['strength'] = signals['strength'] / max_strength
        
            # Record processing time
            processing_time = time.time() - start_time
            self._processing_times.append(processing_time)
            self._last_processing_time = processing_time
        
            return signals
        except Exception as e:
            logger.error(f"Error in _generate_signals_internal: {e}")
            raise
        
    # ------------------------------------------------------------------
    # Real-time Processing Methods
    # ------------------------------------------------------------------
    
    def process_tick(self, tick_data: Dict[str, Any], timeframe: TimeFrame = None) -> Optional[Dict[str, Any]]:
        """Process a single tick of data in real-time.
        
        Args:
            tick_data: Dictionary with tick data (price, volume, etc.)
            timeframe: Timeframe for analysis
            
        Returns:
            Dictionary with analysis results if a bar is completed, None otherwise
        """
        try:
            if not self.real_time_mode:
                logger.warning("Real-time processing is disabled. Enable with real_time_mode=True")
                return None
            
            if timeframe is None:
                timeframe = self.default_timeframe
            
            # Implementation depends on data source format
            # This is a placeholder for tick processing logic
            # In a real implementation, you would:
            # 1. Aggregate ticks into bars
            # 2. When a bar is complete, update the analysis
            # 3. Return updated signals
        
            # For now, we'll just log the tick
            logger.debug(f"Processed tick: {tick_data}")
            return None
        except Exception as e:
            logger.error(f"Error in process_tick: {e}")
            raise
        
    def update_with_new_bar(self, 
                           bar_data: Dict[str, Any], 
                           bid_ask_data: Optional[Dict[str, Any]] = None,
                           timeframe: TimeFrame = None) -> Dict[str, Any]:
        """Update analysis with a new price bar in real-time.
        
        Args:
            bar_data: Dictionary with OHLCV data for the new bar
            bid_ask_data: Optional dictionary with bid/ask data
            timeframe: Timeframe for analysis
            
        Returns:
            Dictionary with updated analysis results
        """
        try:
            start_time = time.time()
        
            if not self.real_time_mode:
                logger.warning("Real-time processing is disabled. Enable with real_time_mode=True")
                return {}
            
            if timeframe is None:
                timeframe = self.default_timeframe
            
            # Initialize timeframe data if needed
            if timeframe not in self._timeframe_data:
                self._timeframe_data[timeframe] = pd.DataFrame()
                self._footprint_bars[timeframe] = []
                self._delta_bars[timeframe] = []
                self._imbalances[timeframe] = []
                self._last_processed_timestamp[timeframe] = None
                self._cumulative_delta[timeframe] = 0
                self._recent_deltas[timeframe] = []
            
            # Convert bar_data to DataFrame
            timestamp = bar_data.get('timestamp', datetime.now())
            new_bar = pd.DataFrame({
                'open': [bar_data.get('open', 0)],
                'high': [bar_data.get('high', 0)],
                'low': [bar_data.get('low', 0)],
                'close': [bar_data.get('close', 0)],
                'volume': [bar_data.get('volume', 0)]
            }, index=[timestamp])
        
            # Append to timeframe data
            self._timeframe_data[timeframe] = pd.concat([self._timeframe_data[timeframe], new_bar])
        
            # Limit cache size
            if len(self._timeframe_data[timeframe]) > self.cache_size:
                self._timeframe_data[timeframe] = self._timeframe_data[timeframe].iloc[-self.cache_size:]
            
            # Create footprint bar for the new bar
            if bid_ask_data:
                # Convert bid_ask_data to DataFrame if needed
                bid_ask_df = pd.DataFrame(bid_ask_data) if not isinstance(bid_ask_data, pd.DataFrame) else bid_ask_data
                footprint_bar = self._create_single_footprint_bar(new_bar.iloc[0], timestamp, bid_ask_df, timeframe)
            else:
                footprint_bar = self._create_single_footprint_bar(new_bar.iloc[0], timestamp, None, timeframe)
            
            # Add to footprint bars
            self._footprint_bars[timeframe].append(footprint_bar)
        
            # Limit cache size
            if len(self._footprint_bars[timeframe]) > self.cache_size:
                self._footprint_bars[timeframe] = self._footprint_bars[timeframe][-self.cache_size:]
            
            # Update delta analysis
            delta_bar = self._update_delta_analysis(footprint_bar, timeframe)
        
            # Update imbalances
            imbalances = self._update_imbalance_detection(footprint_bar, timeframe)
        
            # Generate signals for the new bar
            signals = self.generate_signals(self._timeframe_data[timeframe].iloc[-20:], timeframe)
            latest_signal = signals.iloc[-1].to_dict() if not signals.empty else {}
        
            # Update last processed timestamp
            self._last_processed_timestamp[timeframe] = timestamp
        
            # Record processing time
            processing_time = time.time() - start_time
            self._processing_times.append(processing_time)
            self._last_processing_time = processing_time
        
            # Return analysis results
            return {
                'timestamp': timestamp,
                'footprint_bar': footprint_bar,
                'delta_bar': delta_bar,
                'imbalances': imbalances,
                'signal': latest_signal,
                'processing_time_ms': processing_time * 1000
            }
        except Exception as e:
            logger.error(f"Error in update_with_new_bar: {e}")
            raise
        
    def _create_single_footprint_bar(
        self,
        bar_data: pd.Series,
        timestamp: datetime,
        bid_ask_data: Optional[pd.DataFrame],
        timeframe: TimeFrame
    ) -> FootprintBar:
        """Create a single footprint bar from bar data."""
        # If we have bid-ask data
        try:
            if bid_ask_data is not None:
                # Calculate price levels and volumes
                price_levels = {}
                for price in np.linspace(bar_data['low'], bar_data['high'], self.volume_profile_levels):
                    price = round(price, 5)  # Round to avoid floating point issues
                
                    # Find trades near this price level
                    price_mask = (bid_ask_data['price'] >= price - 0.0001) & (bid_ask_data['price'] < price + 0.0001)
                    price_data = bid_ask_data[price_mask]
                
                    if len(price_data) > 0:
                        buy_vol = price_data[price_data['side'] == 'buy']['volume'].sum()
                        sell_vol = price_data[price_data['side'] == 'sell']['volume'].sum()
                        price_levels[price] = (buy_vol, sell_vol)
            
                # Calculate totals
                buy_volume = sum(bv for bv, _ in price_levels.values()) if price_levels else 0
                sell_volume = sum(sv for _, sv in price_levels.values()) if price_levels else 0
                delta = buy_volume - sell_volume
            
                # Find point of control
                poc_price = max(price_levels.keys(), 
                               key=lambda p: price_levels[p][0] + price_levels[p][1], 
                               default=bar_data['close']) if price_levels else bar_data['close']
            else:
                # Estimate buy/sell volume based on price movement
                close_position = (bar_data['close'] - bar_data['low']) / (bar_data['high'] - bar_data['low']) if bar_data['high'] != bar_data['low'] else 0.5
                buy_volume = bar_data['volume'] * close_position
                sell_volume = bar_data['volume'] - buy_volume
                delta = buy_volume - sell_volume
            
                # Create synthetic price levels
                price_levels = {}
                price_range = np.linspace(bar_data['low'], bar_data['high'], self.volume_profile_levels)
            
                # Distribute volume across price levels
                for price in price_range:
                    price = round(price, 5)
                    price_position = (price - bar_data['low']) / (bar_data['high'] - bar_data['low']) if bar_data['high'] != bar_data['low'] else 0.5
                    weight = 1 - abs(price_position - close_position)
                
                    # Assign buy/sell volume based on price position and weight
                    level_volume = bar_data['volume'] * weight / sum(
                        1 - abs((p - bar_data['low']) / (bar_data['high'] - bar_data['low']) - close_position) 
                        for p in price_range if bar_data['high'] != bar_data['low']
                    ) if bar_data['high'] != bar_data['low'] else bar_data['volume'] / len(price_range)
                
                    buy_level = level_volume * (price_position if price >= bar_data['open'] else 0.3)
                    sell_level = level_volume - buy_level
                
                    price_levels[price] = (buy_level, sell_level)
            
                # Find point of control
                poc_price = max(price_levels.keys(), 
                               key=lambda p: price_levels[p][0] + price_levels[p][1], 
                               default=bar_data['close'])
        
            # Find imbalance levels
            imbalance_levels = []
            for price, (buy_vol, sell_vol) in price_levels.items():
                if buy_vol > 0 and sell_vol > 0:
                    ratio = buy_vol / sell_vol if buy_vol > sell_vol else sell_vol / buy_vol
                    if ratio >= self.imbalance_threshold:
                        imbalance_type = ImbalanceType.BUY if buy_vol > sell_vol else ImbalanceType.SELL
                        strength = min(2.0, ratio / self.imbalance_threshold)
                        imbalance_levels.append((price, imbalance_type, strength))
        
            # Create footprint bar
            return FootprintBar(
                timestamp=timestamp,
                open=bar_data['open'],
                high=bar_data['high'],
                low=bar_data['low'],
                close=bar_data['close'],
                total_volume=bar_data['volume'],
                buy_volume=buy_volume,
                sell_volume=sell_volume,
                delta=delta,
                price_levels=price_levels,
                poc_price=poc_price,
                imbalance_levels=imbalance_levels,
                timeframe=timeframe
            )
        except Exception as e:
            logger.error(f"Error in _create_single_footprint_bar: {e}")
            raise
        
    def _update_delta_analysis(self, footprint_bar: FootprintBar, timeframe: TimeFrame) -> DeltaBar:
        """Update delta analysis with a new footprint bar."""
        # Update cumulative delta
        try:
            if timeframe not in self._cumulative_delta:
                self._cumulative_delta[timeframe] = 0
            self._cumulative_delta[timeframe] += footprint_bar.delta
        
            # Update recent deltas
            if timeframe not in self._recent_deltas:
                self._recent_deltas[timeframe] = []
            self._recent_deltas[timeframe].append(footprint_bar.delta)
        
            # Keep only the most recent deltas
            if len(self._recent_deltas[timeframe]) > self.delta_lookback:
                self._recent_deltas[timeframe] = self._recent_deltas[timeframe][-self.delta_lookback:]
        
            # Calculate delta strength
            if len(self._recent_deltas[timeframe]) > 1:
                mean_delta = sum(self._recent_deltas[timeframe]) / len(self._recent_deltas[timeframe])
                std_delta = np.std(self._recent_deltas[timeframe])
                delta_strength = (footprint_bar.delta - mean_delta) / std_delta if std_delta > 0 else 0
                delta_strength = min(max(delta_strength, -2), 2)  # Clamp to [-2, 2]
            else:
                delta_strength = 0
        
            # Determine signal
            if footprint_bar.delta > 0 and delta_strength > 0.5:
                signal = DeltaSignal.BULLISH
            elif footprint_bar.delta < 0 and delta_strength < -0.5:
                signal = DeltaSignal.BEARISH
            else:
                signal = DeltaSignal.NEUTRAL
        
            # Check for divergence
            divergence = False
            if timeframe in self._delta_bars and self._delta_bars[timeframe]:
                prev_bar = self._delta_bars[timeframe][-1]
                price_up = footprint_bar.close > prev_bar.price
                delta_up = footprint_bar.delta > prev_bar.delta
                divergence = (price_up and not delta_up) or (not price_up and delta_up)
        
            # Create delta bar
            delta_bar = DeltaBar(
                timestamp=footprint_bar.timestamp,
                price=footprint_bar.close,
                delta=footprint_bar.delta,
                cumulative_delta=self._cumulative_delta[timeframe],
                delta_strength=delta_strength,
                signal=signal,
                divergence=divergence,
                timeframe=timeframe
            )
        
            # Add to delta bars
            if timeframe not in self._delta_bars:
                self._delta_bars[timeframe] = []
            self._delta_bars[timeframe].append(delta_bar)
        
            # Limit cache size
            if len(self._delta_bars[timeframe]) > self.cache_size:
                self._delta_bars[timeframe] = self._delta_bars[timeframe][-self.cache_size:]
            
            return delta_bar
        except Exception as e:
            logger.error(f"Error in _update_delta_analysis: {e}")
            raise
        
    def _update_imbalance_detection(self, footprint_bar: FootprintBar, timeframe: TimeFrame) -> List[OrderFlowImbalance]:
        """Update imbalance detection with a new footprint bar."""
        try:
            new_imbalances = []
        
            # Process significant imbalances
            for price, imbalance_type, strength in footprint_bar.imbalance_levels:
                if strength >= 1.0:  # Only include strong imbalances
                    # Calculate volume ratio
                    buy_vol, sell_vol = footprint_bar.price_levels.get(price, (0, 0))
                    volume_ratio = buy_vol / sell_vol if imbalance_type == ImbalanceType.BUY else sell_vol / buy_vol
                
                    # Create imbalance object
                    imbalance = OrderFlowImbalance(
                        timestamp=footprint_bar.timestamp,
                        price_level=price,
                        imbalance_type=imbalance_type,
                        strength=strength,
                        volume_ratio=volume_ratio,
                        confirmed=False,  # Will be confirmed by price action later
                        timeframe=timeframe
                    )
                
                    new_imbalances.append(imbalance)
        
            # Add to imbalances
            if timeframe not in self._imbalances:
                self._imbalances[timeframe] = []
            self._imbalances[timeframe].extend(new_imbalances)
        
            # Limit cache size
            if len(self._imbalances[timeframe]) > self.cache_size:
                self._imbalances[timeframe] = self._imbalances[timeframe][-self.cache_size:]
            
            # Update confirmation status of previous imbalances
            self._update_imbalance_confirmations(footprint_bar, timeframe)
            
            return new_imbalances
        except Exception as e:
            logger.error(f"Error in _update_imbalance_detection: {e}")
            raise
        
    def _update_imbalance_confirmations(self, current_bar: FootprintBar, timeframe: TimeFrame) -> None:
        """Update confirmation status of imbalances based on new price action."""
        try:
            if timeframe not in self._imbalances:
                return
            
            # Check unconfirmed imbalances from previous bars
            for imb in self._imbalances[timeframe]:
                if not imb.confirmed and imb.timestamp < current_bar.timestamp:
                    # Check if price respected the imbalance level
                    if imb.imbalance_type == ImbalanceType.BUY:
                        # Buy imbalance should act as support
                        if current_bar.low <= imb.price_level <= current_bar.high and current_bar.close > imb.price_level:
                            imb.confirmed = True
                    else:  # SELL imbalance
                        # Sell imbalance should act as resistance
                        if current_bar.low <= imb.price_level <= current_bar.high and current_bar.close < imb.price_level:
                            imb.confirmed = True
        except Exception as e:
            logger.error(f"Error in _update_imbalance_confirmations: {e}")
            raise
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for the analyzer."""
        try:
            if not self._processing_times:
                return {
                    'avg_processing_time_ms': 0,
                    'last_processing_time_ms': 0,
                    'max_processing_time_ms': 0,
                    'min_processing_time_ms': 0
                }
            
            return {
                'avg_processing_time_ms': sum(self._processing_times) / len(self._processing_times) * 1000,
                'last_processing_time_ms': self._last_processing_time * 1000,
                'max_processing_time_ms': max(self._processing_times) * 1000,
                'min_processing_time_ms': min(self._processing_times) * 1000
            }
        except Exception as e:
            logger.error(f"Error in get_performance_metrics: {e}")
            raise


# Alias for backward compatibility
AdvancedOrderFlowAnalyzer = OrderFlowAnalyzer


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    # Create sample data
    
    # Generate sample OHLCV data
    np.random.seed(42)
    n = 100
    dates = pd.date_range('2023-01-01', periods=n, freq='15min')
    
    # Create a trending price series with some volatility
    close = np.cumsum(np.random.normal(0, 1, n)) + 100
    # Add some mean reversion
    close = close * 0.99 + 100 * 0.01
    
    # Create OHLCV data
    high = close + np.random.uniform(0, 2, n)
    low = close - np.random.uniform(0, 2, n)
    open_price = low + np.random.uniform(0, high - low, n)
    volume = np.random.uniform(100, 1000, n)
    
    # Create DataFrame
    df = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    # Create smaller timeframe data
    df_m5 = df.copy()
    df_m5.index = pd.date_range('2023-01-01', periods=n*3, freq='5min')[:n]
    
    # Create larger timeframe data
    df_h1 = df.iloc[:4].copy()
    
    # Create analyzer
    analyzer = OrderFlowAnalyzer(multi_timeframe=True)
    
    # Test footprint chart creation
    footprint_bars = analyzer.create_footprint_chart(df)
    logger.info(f"\nCreated {len(footprint_bars)} footprint bars")
    
    # Test delta analysis
    delta_bars = analyzer.analyze_delta(df, footprint_bars)
    logger.info(f"Created {len(delta_bars)} delta bars")
    
    # Test imbalance detection
    imbalances = analyzer.detect_imbalances(footprint_bars)
    logger.info(f"Detected {len(imbalances)} order flow imbalances")
    
    # Test multi-timeframe analysis
    results = analyzer.analyze_multi_timeframe({
        TimeFrame.M5: df_m5,
        TimeFrame.M15: df,
        TimeFrame.H1: df_h1
    })
    
    # Test signal generation
    signals = analyzer.generate_signals(df)
    logger.info("\nSignal summary:")
    logger.info(f"Bullish signals: {signals['bullish'].sum()}")
    logger.info(f"Bearish signals: {signals['bearish'].sum()}")
    logger.info(f"Average signal strength: {signals['strength'].mean():.2f}")
