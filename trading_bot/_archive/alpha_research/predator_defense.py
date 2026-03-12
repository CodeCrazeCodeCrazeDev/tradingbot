"""
Predator Defense System
=======================
Advanced detection and defense against algorithmic predators.

Detection:
- Spread flickering
- Microsecond volume spikes
- Latency arbitrage signatures
- Momentum ignition
- Spoofing bursts
- Quote stuffing behavior

Mapping:
- Stop zone clustering
- Liquidity voids
- Order block patterns
- Fair value gaps
- High/Low volume nodes
- Algorithmic sweep zones

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.signal import find_peaks
    from scipy.cluster.hierarchy import fcluster, linkage
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.cluster import DBSCAN
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class PredatorType(Enum):
    """Types of predatory behavior"""
    SPREAD_FLICKER = auto()
    VOLUME_SPIKE = auto()
    LATENCY_ARB = auto()
    MOMENTUM_IGNITION = auto()
    SPOOFING = auto()
    QUOTE_STUFFING = auto()
    STOP_HUNTING = auto()
    LAYERING = auto()
    PINGING = auto()


class ZoneType(Enum):
    """Market structure zone types"""
    STOP_CLUSTER = auto()
    LIQUIDITY_VOID = auto()
    ORDER_BLOCK = auto()
    FAIR_VALUE_GAP = auto()
    HIGH_VOLUME_NODE = auto()
    LOW_VOLUME_NODE = auto()
    SWEEP_ZONE = auto()


@dataclass
class PredatorSignal:
    """Detected predator activity signal"""
    signal_id: str
    timestamp: datetime
    predator_type: PredatorType
    
    # Detection details
    confidence: float = 0.0
    severity: str = "low"  # low, medium, high, critical
    
    # Evidence
    evidence: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Recommendations
    action: str = ""
    avoid_until: Optional[datetime] = None


@dataclass
class MarketZone:
    """Identified market structure zone"""
    zone_id: str
    zone_type: ZoneType
    
    # Price range
    price_low: float
    price_high: float
    
    # Strength
    strength: float = 0.0
    touch_count: int = 0
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    last_touched: Optional[datetime] = None
    
    # Status
    is_active: bool = True
    breached: bool = False


@dataclass
class VolumeProfile:
    """Volume profile analysis"""
    price_levels: List[float] = field(default_factory=list)
    volumes: List[float] = field(default_factory=list)
    
    # Key levels
    poc: float = 0.0  # Point of Control
    vah: float = 0.0  # Value Area High
    val: float = 0.0  # Value Area Low
    
    # Nodes
    hvn_levels: List[float] = field(default_factory=list)
    lvn_levels: List[float] = field(default_factory=list)


class SpreadFlickerDetector:
    """Detect spread flickering"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.spread_history: deque = deque(maxlen=1000)
        self.flicker_threshold = self.config.get('flicker_threshold', 5)
        
    def update(self, bid: float, ask: float, timestamp: datetime):
        """Update spread history"""
        spread = ask - bid
        self.spread_history.append({
            'timestamp': timestamp,
            'spread': spread,
            'bid': bid,
            'ask': ask
        })
    
    def detect(self) -> Optional[PredatorSignal]:
        """Detect spread flickering"""
        
        if len(self.spread_history) < 50:
            return None
        
        recent = list(self.spread_history)[-50:]
        spreads = [r['spread'] for r in recent]
        
        # Count rapid spread changes
        changes = np.diff(spreads)
        sign_changes = np.sum(np.diff(np.sign(changes)) != 0)
        
        # Calculate flicker rate
        time_span = (recent[-1]['timestamp'] - recent[0]['timestamp']).total_seconds()
        flicker_rate = sign_changes / max(time_span, 0.001)
        
        if flicker_rate > self.flicker_threshold:
            return PredatorSignal(
                signal_id=f"flicker_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                predator_type=PredatorType.SPREAD_FLICKER,
                confidence=min(flicker_rate / 10, 1.0),
                severity='medium' if flicker_rate < 10 else 'high',
                evidence=[f"Flicker rate: {flicker_rate:.1f}/sec"],
                metrics={'flicker_rate': flicker_rate},
                action="Avoid market orders, use limit orders with buffer"
            )
        
        return None


class VolumeSpikeDetector:
    """Detect microsecond volume spikes"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.volume_history: deque = deque(maxlen=5000)
        self.spike_threshold = self.config.get('spike_threshold', 5.0)
        
    def add_trade(self, size: float, timestamp: datetime):
        """Add trade to history"""
        self.volume_history.append({
            'timestamp': timestamp,
            'size': size
        })
    
    def detect(self) -> Optional[PredatorSignal]:
        """Detect volume spikes"""
        
        if len(self.volume_history) < 100:
            return None
        
        recent = list(self.volume_history)
        
        # Calculate volume in small time windows
        window_ms = 100  # 100ms windows
        windows = {}
        
        for trade in recent:
            window_key = int(trade['timestamp'].timestamp() * 1000 / window_ms)
            if window_key not in windows:
                windows[window_key] = 0
            windows[window_key] += trade['size']
        
        if len(windows) < 10:
            return None
        
        volumes = list(windows.values())
        mean_vol = np.mean(volumes)
        std_vol = np.std(volumes)
        
        # Check for spikes
        max_vol = max(volumes)
        z_score = (max_vol - mean_vol) / (std_vol + 1e-10)
        
        if z_score > self.spike_threshold:
            return PredatorSignal(
                signal_id=f"spike_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                predator_type=PredatorType.VOLUME_SPIKE,
                confidence=min(z_score / 10, 1.0),
                severity='high' if z_score > 7 else 'medium',
                evidence=[f"Volume spike z-score: {z_score:.1f}"],
                metrics={'z_score': z_score, 'max_volume': max_vol},
                action="Pause execution, wait for normalization"
            )
        
        return None


class LatencyArbDetector:
    """Detect latency arbitrage signatures"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.quote_history: deque = deque(maxlen=1000)
        self.trade_history: deque = deque(maxlen=1000)
        
    def add_quote(self, bid: float, ask: float, timestamp: datetime):
        """Add quote update"""
        self.quote_history.append({
            'timestamp': timestamp,
            'bid': bid,
            'ask': ask,
            'mid': (bid + ask) / 2
        })
    
    def add_trade(self, price: float, size: float, side: str, timestamp: datetime):
        """Add trade"""
        self.trade_history.append({
            'timestamp': timestamp,
            'price': price,
            'size': size,
            'side': side
        })
    
    def detect(self) -> Optional[PredatorSignal]:
        """Detect latency arbitrage"""
        
        if len(self.quote_history) < 50 or len(self.trade_history) < 50:
            return None
        
        # Look for trades that consistently beat quote updates
        beat_count = 0
        total_checked = 0
        
        trades = list(self.trade_history)[-50:]
        quotes = list(self.quote_history)
        
        for trade in trades:
            # Find quote just before trade
            prev_quotes = [q for q in quotes if q['timestamp'] < trade['timestamp']]
            if not prev_quotes:
                continue
            
            prev_quote = prev_quotes[-1]
            
            # Check if trade price was better than quote
            if trade['side'] == 'buy' and trade['price'] < prev_quote['ask']:
                beat_count += 1
            elif trade['side'] == 'sell' and trade['price'] > prev_quote['bid']:
                beat_count += 1
            
            total_checked += 1
        
        if total_checked < 20:
            return None
        
        beat_ratio = beat_count / total_checked
        
        if beat_ratio > 0.3:  # More than 30% beat the quote
            return PredatorSignal(
                signal_id=f"latarb_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                predator_type=PredatorType.LATENCY_ARB,
                confidence=beat_ratio,
                severity='high',
                evidence=[f"Quote beat ratio: {beat_ratio:.1%}"],
                metrics={'beat_ratio': beat_ratio},
                action="Increase latency buffer, avoid aggressive orders"
            )
        
        return None


class MomentumIgnitionDetector:
    """Detect momentum ignition attempts"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.trade_history: deque = deque(maxlen=1000)
        
    def add_trade(self, price: float, size: float, side: str, timestamp: datetime):
        """Add trade"""
        self.trade_history.append({
            'timestamp': timestamp,
            'price': price,
            'size': size,
            'side': side
        })
    
    def detect(self) -> Optional[PredatorSignal]:
        """Detect momentum ignition"""
        
        if len(self.trade_history) < 50:
            return None
        
        recent = list(self.trade_history)[-50:]
        
        # Look for sudden directional burst followed by reversal
        buy_count = sum(1 for t in recent[:25] if t['side'] == 'buy')
        sell_count = 25 - buy_count
        
        initial_imbalance = abs(buy_count - sell_count) / 25
        
        # Check for reversal in second half
        buy_count_2 = sum(1 for t in recent[25:] if t['side'] == 'buy')
        sell_count_2 = 25 - buy_count_2
        
        # Reversal if direction flipped
        initial_direction = 'buy' if buy_count > sell_count else 'sell'
        second_direction = 'buy' if buy_count_2 > sell_count_2 else 'sell'
        
        reversal = initial_direction != second_direction
        
        # Price movement
        prices = [t['price'] for t in recent]
        price_move = (max(prices) - min(prices)) / prices[0]
        
        if initial_imbalance > 0.6 and reversal and price_move > 0.002:
            return PredatorSignal(
                signal_id=f"ignition_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                predator_type=PredatorType.MOMENTUM_IGNITION,
                confidence=initial_imbalance,
                severity='high',
                evidence=[
                    f"Initial imbalance: {initial_imbalance:.1%}",
                    f"Price move: {price_move:.2%}",
                    "Direction reversal detected"
                ],
                metrics={'imbalance': initial_imbalance, 'price_move': price_move},
                action="Do not chase momentum, wait for stabilization",
                avoid_until=datetime.now() + timedelta(seconds=30)
            )
        
        return None


class SpoofingDetector:
    """Detect spoofing behavior"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.order_history: deque = deque(maxlen=5000)
        
    def add_order_event(
        self,
        event_type: str,
        price: float,
        size: float,
        side: str,
        timestamp: datetime
    ):
        """Add order event (new, cancel, fill)"""
        self.order_history.append({
            'timestamp': timestamp,
            'event': event_type,
            'price': price,
            'size': size,
            'side': side
        })
    
    def detect(self) -> Optional[PredatorSignal]:
        """Detect spoofing"""
        
        if len(self.order_history) < 100:
            return None
        
        recent = list(self.order_history)[-100:]
        
        # Calculate cancel ratio for large orders
        large_orders = [o for o in recent if o['size'] > np.median([r['size'] for r in recent]) * 2]
        
        if len(large_orders) < 10:
            return None
        
        cancelled = sum(1 for o in large_orders if o['event'] == 'cancel')
        cancel_ratio = cancelled / len(large_orders)
        
        # Check if cancels happen quickly
        cancel_events = [o for o in recent if o['event'] == 'cancel']
        new_events = [o for o in recent if o['event'] == 'new']
        
        if cancel_events and new_events:
            # Average time between new and cancel
            quick_cancels = 0
            for cancel in cancel_events:
                matching_new = [n for n in new_events 
                               if abs(n['price'] - cancel['price']) < 0.0001
                               and n['timestamp'] < cancel['timestamp']]
                if matching_new:
                    time_diff = (cancel['timestamp'] - matching_new[-1]['timestamp']).total_seconds()
                    if time_diff < 1.0:  # Less than 1 second
                        quick_cancels += 1
            
            quick_cancel_ratio = quick_cancels / len(cancel_events) if cancel_events else 0
        else:
            quick_cancel_ratio = 0
        
        if cancel_ratio > 0.8 and quick_cancel_ratio > 0.5:
            return PredatorSignal(
                signal_id=f"spoof_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                predator_type=PredatorType.SPOOFING,
                confidence=cancel_ratio * quick_cancel_ratio,
                severity='critical',
                evidence=[
                    f"Large order cancel ratio: {cancel_ratio:.1%}",
                    f"Quick cancel ratio: {quick_cancel_ratio:.1%}"
                ],
                metrics={'cancel_ratio': cancel_ratio, 'quick_cancel_ratio': quick_cancel_ratio},
                action="Ignore displayed depth, trade cautiously"
            )
        
        return None


class QuoteStuffingDetector:
    """Detect quote stuffing"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.quote_history: deque = deque(maxlen=10000)
        self.stuffing_threshold = self.config.get('stuffing_threshold', 1000)
        
    def add_quote(self, timestamp: datetime):
        """Add quote update timestamp"""
        self.quote_history.append(timestamp)
    
    def detect(self) -> Optional[PredatorSignal]:
        """Detect quote stuffing"""
        
        if len(self.quote_history) < 100:
            return None
        
        recent = list(self.quote_history)[-100:]
        
        # Calculate quote rate
        time_span = (recent[-1] - recent[0]).total_seconds()
        quote_rate = len(recent) / max(time_span, 0.001)
        
        if quote_rate > self.stuffing_threshold:
            return PredatorSignal(
                signal_id=f"stuffing_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                predator_type=PredatorType.QUOTE_STUFFING,
                confidence=min(quote_rate / 2000, 1.0),
                severity='high' if quote_rate > 2000 else 'medium',
                evidence=[f"Quote rate: {quote_rate:.0f}/sec"],
                metrics={'quote_rate': quote_rate},
                action="Increase processing latency tolerance"
            )
        
        return None


class StopZoneMapper:
    """Map stop loss clustering zones"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.price_history: deque = deque(maxlen=10000)
        self.zones: List[MarketZone] = []
        
    def update(self, high: float, low: float, close: float):
        """Update with price data"""
        self.price_history.append({
            'high': high,
            'low': low,
            'close': close,
            'timestamp': datetime.now()
        })
    
    def find_stop_zones(self) -> List[MarketZone]:
        """Find potential stop clustering zones"""
        
        if len(self.price_history) < 100:
            return []
        
        prices = list(self.price_history)
        
        # Find swing highs and lows
        highs = [p['high'] for p in prices]
        lows = [p['low'] for p in prices]
        
        # Find local extremes
        if SCIPY_AVAILABLE:
            high_peaks, _ = find_peaks(highs, distance=5)
            low_peaks, _ = find_peaks([-l for l in lows], distance=5)
        else:
            high_peaks = []
            low_peaks = []
        
        zones = []
        
        # Create zones around swing points
        for idx in high_peaks:
            zone = MarketZone(
                zone_id=f"stop_high_{idx}",
                zone_type=ZoneType.STOP_CLUSTER,
                price_low=highs[idx] * 0.999,
                price_high=highs[idx] * 1.002,
                strength=0.7,
                touch_count=1
            )
            zones.append(zone)
        
        for idx in low_peaks:
            zone = MarketZone(
                zone_id=f"stop_low_{idx}",
                zone_type=ZoneType.STOP_CLUSTER,
                price_low=lows[idx] * 0.998,
                price_high=lows[idx] * 1.001,
                strength=0.7,
                touch_count=1
            )
            zones.append(zone)
        
        self.zones = zones
        return zones


class VolumeProfileAnalyzer:
    """Analyze volume profile for HVN/LVN"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.trade_history: deque = deque(maxlen=50000)
        
    def add_trade(self, price: float, size: float):
        """Add trade"""
        self.trade_history.append({
            'price': price,
            'size': size,
            'timestamp': datetime.now()
        })
    
    def calculate_profile(self, num_levels: int = 50) -> VolumeProfile:
        """Calculate volume profile"""
        
        if len(self.trade_history) < 100:
            return VolumeProfile()
        
        trades = list(self.trade_history)
        prices = [t['price'] for t in trades]
        sizes = [t['size'] for t in trades]
        
        # Create price bins
        min_price = min(prices)
        max_price = max(prices)
        bin_size = (max_price - min_price) / num_levels
        
        profile_levels = []
        profile_volumes = []
        
        for i in range(num_levels):
            level_low = min_price + i * bin_size
            level_high = level_low + bin_size
            level_mid = (level_low + level_high) / 2
            
            # Sum volume in this bin
            volume = sum(
                s for p, s in zip(prices, sizes)
                if level_low <= p < level_high
            )
            
            profile_levels.append(level_mid)
            profile_volumes.append(volume)
        
        # Find POC (Point of Control)
        poc_idx = np.argmax(profile_volumes)
        poc = profile_levels[poc_idx]
        
        # Find Value Area (70% of volume)
        total_volume = sum(profile_volumes)
        target_volume = total_volume * 0.7
        
        # Expand from POC
        included = {poc_idx}
        current_volume = profile_volumes[poc_idx]
        
        while current_volume < target_volume:
            # Check neighbors
            candidates = []
            for idx in included:
                if idx > 0 and idx - 1 not in included:
                    candidates.append((idx - 1, profile_volumes[idx - 1]))
                if idx < len(profile_volumes) - 1 and idx + 1 not in included:
                    candidates.append((idx + 1, profile_volumes[idx + 1]))
            
            if not candidates:
                break
            
            # Add highest volume neighbor
            best = max(candidates, key=lambda x: x[1])
            included.add(best[0])
            current_volume += best[1]
        
        val = min(profile_levels[i] for i in included)
        vah = max(profile_levels[i] for i in included)
        
        # Find HVN and LVN
        mean_vol = np.mean(profile_volumes)
        std_vol = np.std(profile_volumes)
        
        hvn_levels = [
            profile_levels[i] for i in range(len(profile_volumes))
            if profile_volumes[i] > mean_vol + std_vol
        ]
        
        lvn_levels = [
            profile_levels[i] for i in range(len(profile_volumes))
            if profile_volumes[i] < mean_vol - std_vol * 0.5
        ]
        
        return VolumeProfile(
            price_levels=profile_levels,
            volumes=profile_volumes,
            poc=poc,
            vah=vah,
            val=val,
            hvn_levels=hvn_levels,
            lvn_levels=lvn_levels
        )


class OrderBlockDetector:
    """Detect order blocks and fair value gaps"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.candle_history: deque = deque(maxlen=500)
        
    def add_candle(self, open_: float, high: float, low: float, close: float, volume: float):
        """Add candle"""
        self.candle_history.append({
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'timestamp': datetime.now()
        })
    
    def find_order_blocks(self) -> List[MarketZone]:
        """Find order blocks"""
        
        if len(self.candle_history) < 20:
            return []
        
        candles = list(self.candle_history)
        zones = []
        
        for i in range(2, len(candles) - 1):
            prev = candles[i - 1]
            curr = candles[i]
            next_ = candles[i + 1]
            
            # Bullish order block: down candle followed by strong up move
            if prev['close'] < prev['open']:  # Down candle
                if next_['close'] > curr['high']:  # Strong up move
                    zone = MarketZone(
                        zone_id=f"ob_bull_{i}",
                        zone_type=ZoneType.ORDER_BLOCK,
                        price_low=prev['low'],
                        price_high=prev['high'],
                        strength=0.8
                    )
                    zones.append(zone)
            
            # Bearish order block: up candle followed by strong down move
            if prev['close'] > prev['open']:  # Up candle
                if next_['close'] < curr['low']:  # Strong down move
                    zone = MarketZone(
                        zone_id=f"ob_bear_{i}",
                        zone_type=ZoneType.ORDER_BLOCK,
                        price_low=prev['low'],
                        price_high=prev['high'],
                        strength=0.8
                    )
                    zones.append(zone)
        
        return zones
    
    def find_fair_value_gaps(self) -> List[MarketZone]:
        """Find fair value gaps (imbalances)"""
        
        if len(self.candle_history) < 3:
            return []
        
        candles = list(self.candle_history)
        zones = []
        
        for i in range(1, len(candles) - 1):
            prev = candles[i - 1]
            next_ = candles[i + 1]
            
            # Bullish FVG: gap between prev high and next low
            if next_['low'] > prev['high']:
                zone = MarketZone(
                    zone_id=f"fvg_bull_{i}",
                    zone_type=ZoneType.FAIR_VALUE_GAP,
                    price_low=prev['high'],
                    price_high=next_['low'],
                    strength=0.7
                )
                zones.append(zone)
            
            # Bearish FVG: gap between prev low and next high
            if next_['high'] < prev['low']:
                zone = MarketZone(
                    zone_id=f"fvg_bear_{i}",
                    zone_type=ZoneType.FAIR_VALUE_GAP,
                    price_low=next_['high'],
                    price_high=prev['low'],
                    strength=0.7
                )
                zones.append(zone)
        
        return zones


class PredatorDefenseSystem:
    """
    Complete Predator Defense System.
    
    Detection:
    - Spread flickering
    - Microsecond volume spikes
    - Latency arbitrage signatures
    - Momentum ignition
    - Spoofing bursts
    - Quote stuffing behavior
    
    Mapping:
    - Stop zone clustering
    - Liquidity voids
    - Order block patterns
    - Fair value gaps
    - High/Low volume nodes
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Detectors
        self.spread_detector = SpreadFlickerDetector(config)
        self.volume_detector = VolumeSpikeDetector(config)
        self.latency_detector = LatencyArbDetector(config)
        self.momentum_detector = MomentumIgnitionDetector(config)
        self.spoofing_detector = SpoofingDetector(config)
        self.stuffing_detector = QuoteStuffingDetector(config)
        
        # Mappers
        self.stop_mapper = StopZoneMapper(config)
        self.volume_analyzer = VolumeProfileAnalyzer(config)
        self.order_block_detector = OrderBlockDetector(config)
        
        # State
        self.active_signals: List[PredatorSignal] = []
        self.market_zones: List[MarketZone] = []
        self.volume_profile: Optional[VolumeProfile] = None
        
        logger.info("PredatorDefenseSystem initialized")
    
    def update_quote(self, bid: float, ask: float, timestamp: datetime = None):
        """Update with quote data"""
        timestamp = timestamp or datetime.now()
        self.spread_detector.update(bid, ask, timestamp)
        self.latency_detector.add_quote(bid, ask, timestamp)
        self.stuffing_detector.add_quote(timestamp)
    
    def update_trade(
        self,
        price: float,
        size: float,
        side: str,
        timestamp: datetime = None
    ):
        """Update with trade data"""
        timestamp = timestamp or datetime.now()
        self.volume_detector.add_trade(size, timestamp)
        self.latency_detector.add_trade(price, size, side, timestamp)
        self.momentum_detector.add_trade(price, size, side, timestamp)
        self.volume_analyzer.add_trade(price, size)
    
    def update_order_event(
        self,
        event_type: str,
        price: float,
        size: float,
        side: str,
        timestamp: datetime = None
    ):
        """Update with order event"""
        timestamp = timestamp or datetime.now()
        self.spoofing_detector.add_order_event(event_type, price, size, side, timestamp)
    
    def update_candle(
        self,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float
    ):
        """Update with candle data"""
        self.stop_mapper.update(high, low, close)
        self.order_block_detector.add_candle(open_, high, low, close, volume)
    
    def detect_predators(self) -> List[PredatorSignal]:
        """Run all predator detection"""
        
        signals = []
        
        # Run all detectors
        detectors = [
            self.spread_detector,
            self.volume_detector,
            self.latency_detector,
            self.momentum_detector,
            self.spoofing_detector,
            self.stuffing_detector
        ]
        
        for detector in detectors:
            signal = detector.detect()
            if signal:
                signals.append(signal)
        
        self.active_signals = signals
        return signals
    
    def map_market_structure(self) -> Dict[str, Any]:
        """Map all market structure zones"""
        
        # Stop zones
        stop_zones = self.stop_mapper.find_stop_zones()
        
        # Order blocks and FVGs
        order_blocks = self.order_block_detector.find_order_blocks()
        fvgs = self.order_block_detector.find_fair_value_gaps()
        
        # Volume profile
        self.volume_profile = self.volume_analyzer.calculate_profile()
        
        # Combine all zones
        self.market_zones = stop_zones + order_blocks + fvgs
        
        # Add HVN/LVN as zones
        for hvn in self.volume_profile.hvn_levels:
            self.market_zones.append(MarketZone(
                zone_id=f"hvn_{hvn}",
                zone_type=ZoneType.HIGH_VOLUME_NODE,
                price_low=hvn * 0.999,
                price_high=hvn * 1.001,
                strength=0.6
            ))
        
        for lvn in self.volume_profile.lvn_levels:
            self.market_zones.append(MarketZone(
                zone_id=f"lvn_{lvn}",
                zone_type=ZoneType.LOW_VOLUME_NODE,
                price_low=lvn * 0.999,
                price_high=lvn * 1.001,
                strength=0.5
            ))
        
        return {
            'zones': self.market_zones,
            'volume_profile': self.volume_profile,
            'stop_zones': stop_zones,
            'order_blocks': order_blocks,
            'fair_value_gaps': fvgs
        }
    
    def get_threat_level(self) -> Tuple[str, float]:
        """Get overall threat level"""
        
        if not self.active_signals:
            return 'low', 0.1
        
        severities = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        max_severity = max(severities.get(s.severity, 1) for s in self.active_signals)
        avg_confidence = np.mean([s.confidence for s in self.active_signals])
        
        if max_severity >= 4:
            return 'critical', avg_confidence
        elif max_severity >= 3:
            return 'high', avg_confidence
        elif max_severity >= 2:
            return 'medium', avg_confidence
        else:
            return 'low', avg_confidence
    
    def should_trade(self, price: float) -> Tuple[bool, str]:
        """Determine if safe to trade at price"""
        
        threat_level, confidence = self.get_threat_level()
        
        if threat_level == 'critical':
            return False, "Critical predator activity detected"
        
        # Check if price is in dangerous zone
        for zone in self.market_zones:
            if zone.price_low <= price <= zone.price_high:
                if zone.zone_type == ZoneType.STOP_CLUSTER:
                    return False, f"Price in stop cluster zone"
                if zone.zone_type == ZoneType.LOW_VOLUME_NODE:
                    return False, f"Price in low volume node (liquidity void)"
        
        if threat_level == 'high' and confidence > 0.7:
            return False, "High threat level with high confidence"
        
        return True, "Safe to trade"


# Factory function
def create_predator_defense(config: Optional[Dict] = None) -> PredatorDefenseSystem:
    """Create and return a PredatorDefenseSystem instance"""
    return PredatorDefenseSystem(config)
