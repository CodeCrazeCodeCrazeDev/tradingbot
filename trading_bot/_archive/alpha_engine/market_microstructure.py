"""
Market Microstructure Module
=============================

Advanced market microstructure analysis:
- Order Flow Analysis
- Toxicity Detection (VPIN)
- Latency Arbitrage Defense
- Liquidity Analysis
- Anomaly Detection
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import numpy
import pandas

logger = logging.getLogger(__name__)


class OrderFlowType(Enum):
    """Types of order flow"""
    AGGRESSIVE_BUY = "aggressive_buy"
    AGGRESSIVE_SELL = "aggressive_sell"
    PASSIVE_BUY = "passive_buy"
    PASSIVE_SELL = "passive_sell"
    HIDDEN = "hidden"
    ICEBERG = "iceberg"


class ToxicityLevel(Enum):
    """Toxicity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class OrderFlowEvent:
    """Single order flow event"""
    timestamp: datetime
    price: float
    size: float
    side: str  # 'buy' or 'sell'
    flow_type: OrderFlowType
    aggressor: bool
    venue: str = ""
    
    @property
    def value(self) -> float:
        return self.price * self.size


@dataclass
class ToxicityMetrics:
    """Toxicity analysis metrics"""
    timestamp: datetime
    vpin: float  # Volume-synchronized probability of informed trading
    toxicity_level: ToxicityLevel
    buy_volume: float
    sell_volume: float
    imbalance: float
    adverse_selection_risk: float
    recommendation: str


@dataclass
class LiquidityMetrics:
    """Liquidity analysis metrics"""
    timestamp: datetime
    bid_depth: float
    ask_depth: float
    spread: float
    spread_bps: float
    depth_imbalance: float
    resilience: float  # How quickly liquidity replenishes
    hidden_liquidity_estimate: float


class OrderFlowAnalyzer:
    """
    Analyzes order flow for trading signals
    
    Features:
    - Volume delta analysis
    - Price absorption patterns
    - Exhaustion detection
    - Momentum signals
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Flow history
        self.flow_history: deque = deque(maxlen=10000)
        
        # Aggregated metrics
        self.volume_buckets: deque = deque(maxlen=1000)
        
        # Settings
        self.bucket_size = self.config.get('bucket_size', 1000)  # Volume per bucket
        self.lookback_buckets = self.config.get('lookback_buckets', 50)
    
    def process_trade(self, trade: Dict[str, Any]) -> Optional[OrderFlowEvent]:
        """
        Process a single trade
        
        Args:
            trade: Trade dictionary with price, size, side, timestamp
            
        Returns:
            OrderFlowEvent
        """
        # Determine flow type
        if trade.get('aggressor', True):
            if trade['side'] == 'buy':
                flow_type = OrderFlowType.AGGRESSIVE_BUY
            else:
                flow_type = OrderFlowType.AGGRESSIVE_SELL
        else:
            if trade['side'] == 'buy':
                flow_type = OrderFlowType.PASSIVE_BUY
            else:
                flow_type = OrderFlowType.PASSIVE_SELL
        
        event = OrderFlowEvent(
            timestamp=trade.get('timestamp', datetime.now()),
            price=trade['price'],
            size=trade['size'],
            side=trade['side'],
            flow_type=flow_type,
            aggressor=trade.get('aggressor', True),
            venue=trade.get('venue', ''),
        )
        
        self.flow_history.append(event)
        self._update_buckets(event)
        
        return event
    
    def _update_buckets(self, event: OrderFlowEvent):
        """Update volume buckets for VPIN calculation"""
        if not self.volume_buckets:
            self.volume_buckets.append({
                'buy_volume': 0,
                'sell_volume': 0,
                'total_volume': 0,
                'start_time': event.timestamp,
            })
        
        current_bucket = self.volume_buckets[-1]
        
        # Add to current bucket
        if event.side == 'buy':
            current_bucket['buy_volume'] += event.size
        else:
            current_bucket['sell_volume'] += event.size
        current_bucket['total_volume'] += event.size
        
        # Check if bucket is full
        if current_bucket['total_volume'] >= self.bucket_size:
            # Start new bucket
            self.volume_buckets.append({
                'buy_volume': 0,
                'sell_volume': 0,
                'total_volume': 0,
                'start_time': event.timestamp,
            })
    
    def calculate_volume_delta(self, lookback: int = 100) -> Dict[str, float]:
        """Calculate volume delta (buy - sell volume)"""
        recent = list(self.flow_history)[-lookback:]
        
        if not recent:
            return {'delta': 0, 'buy_volume': 0, 'sell_volume': 0}
        
        buy_volume = sum(e.size for e in recent if e.side == 'buy')
        sell_volume = sum(e.size for e in recent if e.side == 'sell')
        
        delta = buy_volume - sell_volume
        total = buy_volume + sell_volume
        
        return {
            'delta': delta,
            'delta_pct': delta / total if total > 0 else 0,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'imbalance': (buy_volume - sell_volume) / (buy_volume + sell_volume) if total > 0 else 0,
        }
    
    def detect_absorption(self, lookback: int = 50) -> Dict[str, Any]:
        """
        Detect price absorption patterns
        
        Absorption: Large volume with minimal price movement
        """
        recent = list(self.flow_history)[-lookback:]
        
        if len(recent) < 10:
            return {'absorption_detected': False}
        
        # Calculate volume and price change
        total_volume = sum(e.size for e in recent)
        price_change = abs(recent[-1].price - recent[0].price) / recent[0].price
        
        # Volume-weighted price impact
        expected_impact = total_volume * 0.00001  # Simplified impact model
        actual_impact = price_change
        
        # Absorption if actual impact much less than expected
        absorption_ratio = actual_impact / expected_impact if expected_impact > 0 else 1
        
        return {
            'absorption_detected': absorption_ratio < 0.5,
            'absorption_ratio': absorption_ratio,
            'total_volume': total_volume,
            'price_change': price_change,
            'interpretation': 'Strong buying absorbed' if absorption_ratio < 0.5 else 'Normal flow',
        }
    
    def detect_exhaustion(self, lookback: int = 100) -> Dict[str, Any]:
        """
        Detect exhaustion patterns
        
        Exhaustion: Decreasing volume with continued price movement
        """
        recent = list(self.flow_history)[-lookback:]
        
        if len(recent) < 20:
            return {'exhaustion_detected': False}
        
        # Split into halves
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]
        
        # Volume comparison
        first_volume = sum(e.size for e in first_half)
        second_volume = sum(e.size for e in second_half)
        
        # Price movement
        first_price_change = abs(first_half[-1].price - first_half[0].price)
        second_price_change = abs(second_half[-1].price - second_half[0].price)
        
        # Exhaustion: decreasing volume but continued price movement
        volume_declining = second_volume < first_volume * 0.7
        price_continuing = second_price_change > first_price_change * 0.5
        
        return {
            'exhaustion_detected': volume_declining and price_continuing,
            'volume_ratio': second_volume / first_volume if first_volume > 0 else 1,
            'price_ratio': second_price_change / first_price_change if first_price_change > 0 else 1,
            'interpretation': 'Trend exhaustion likely' if volume_declining and price_continuing else 'Trend healthy',
        }
    
    def get_momentum_signal(self) -> Dict[str, Any]:
        """Get momentum signal from order flow"""
        delta = self.calculate_volume_delta(100)
        absorption = self.detect_absorption(50)
        exhaustion = self.detect_exhaustion(100)
        
        # Combine signals
        imbalance = delta['imbalance']
        
        if exhaustion['exhaustion_detected']:
            # Potential reversal
            if imbalance > 0:
                signal = -0.5  # Bullish exhaustion, expect reversal down
            else:
                signal = 0.5  # Bearish exhaustion, expect reversal up
        elif absorption['absorption_detected']:
            # Continuation likely
            signal = imbalance * 0.3
        else:
            # Normal flow
            signal = imbalance * 0.5
        
        return {
            'signal': signal,
            'direction': 'long' if signal > 0.2 else ('short' if signal < -0.2 else 'neutral'),
            'confidence': min(abs(signal) + 0.3, 1.0),
            'delta': delta,
            'absorption': absorption,
            'exhaustion': exhaustion,
        }


class ToxicityDetector:
    """
    Detects toxic order flow using VPIN and other metrics
    
    VPIN: Volume-Synchronized Probability of Informed Trading
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # VPIN settings
        self.bucket_size = self.config.get('bucket_size', 1000)
        self.num_buckets = self.config.get('num_buckets', 50)
        
        # Volume buckets
        self.buckets: deque = deque(maxlen=self.num_buckets)
        self.current_bucket = {'buy': 0, 'sell': 0, 'total': 0}
        
        # Toxicity history
        self.toxicity_history: deque = deque(maxlen=1000)
        
        # Thresholds
        self.high_toxicity_threshold = self.config.get('high_toxicity', 0.7)
        self.extreme_toxicity_threshold = self.config.get('extreme_toxicity', 0.85)
    
    def process_trade(self, price: float, size: float, side: str):
        """Process trade for VPIN calculation"""
        # Bulk Volume Classification (BVC)
        # Simplified: use trade direction directly
        if side == 'buy':
            self.current_bucket['buy'] += size
        else:
            self.current_bucket['sell'] += size
        self.current_bucket['total'] += size
        
        # Check if bucket is full
        if self.current_bucket['total'] >= self.bucket_size:
            self.buckets.append(self.current_bucket.copy())
            self.current_bucket = {'buy': 0, 'sell': 0, 'total': 0}
    
    def calculate_vpin(self) -> float:
        """
        Calculate VPIN (Volume-synchronized Probability of Informed Trading)
        
        VPIN = Sum(|Buy_i - Sell_i|) / (n * V)
        """
        if len(self.buckets) < 10:
            return 0.5  # Default
        
        buckets = list(self.buckets)
        
        # Calculate order imbalance for each bucket
        imbalances = []
        for bucket in buckets:
            imbalance = abs(bucket['buy'] - bucket['sell'])
            imbalances.append(imbalance)
        
        # VPIN
        total_imbalance = sum(imbalances)
        total_volume = sum(b['total'] for b in buckets)
        
        vpin = total_imbalance / total_volume if total_volume > 0 else 0.5
        
        return min(vpin, 1.0)
    
    def get_toxicity_metrics(self) -> ToxicityMetrics:
        """Get comprehensive toxicity metrics"""
        vpin = self.calculate_vpin()
        
        # Determine toxicity level
        if vpin >= self.extreme_toxicity_threshold:
            level = ToxicityLevel.EXTREME
            recommendation = "Widen spreads significantly, reduce quote size"
        elif vpin >= self.high_toxicity_threshold:
            level = ToxicityLevel.HIGH
            recommendation = "Widen spreads, reduce exposure"
        elif vpin >= 0.5:
            level = ToxicityLevel.MEDIUM
            recommendation = "Monitor closely, normal operations"
        else:
            level = ToxicityLevel.LOW
            recommendation = "Safe to provide liquidity"
        
        # Calculate additional metrics
        if self.buckets:
            recent_buckets = list(self.buckets)[-10:]
            buy_volume = sum(b['buy'] for b in recent_buckets)
            sell_volume = sum(b['sell'] for b in recent_buckets)
            total = buy_volume + sell_volume
            imbalance = (buy_volume - sell_volume) / total if total > 0 else 0
        else:
            buy_volume = 0
            sell_volume = 0
            imbalance = 0
        
        # Adverse selection risk
        adverse_selection = vpin * 0.8 + abs(imbalance) * 0.2
        
        metrics = ToxicityMetrics(
            timestamp=datetime.now(),
            vpin=vpin,
            toxicity_level=level,
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            imbalance=imbalance,
            adverse_selection_risk=adverse_selection,
            recommendation=recommendation,
        )
        
        self.toxicity_history.append(metrics)
        
        return metrics
    
    def get_spread_adjustment(self) -> float:
        """Get recommended spread multiplier based on toxicity"""
        vpin = self.calculate_vpin()
        
        if vpin >= self.extreme_toxicity_threshold:
            return 2.0  # Double spreads
        elif vpin >= self.high_toxicity_threshold:
            return 1.5
        elif vpin >= 0.5:
            return 1.2
        else:
            return 1.0  # Normal spreads


class LatencyArbitrageDefense:
    """
    Defense against latency arbitrage
    
    Strategies:
    - Predictive quote updates
    - Quote fading
    - Strategic quote placement
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Quote state
        self.last_quote_update = datetime.now()
        self.quote_age_threshold = self.config.get('quote_age_threshold', 0.1)  # 100ms
        
        # Market data
        self.price_history: deque = deque(maxlen=1000)
        self.volatility_history: deque = deque(maxlen=100)
        
        # Defense settings
        self.fade_rate = self.config.get('fade_rate', 0.001)  # Quote fade per 100ms
        self.max_fade = self.config.get('max_fade', 0.005)  # Maximum fade
    
    def update_market_data(self, price: float, timestamp: datetime = None):
        """Update market data for staleness calculation"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.price_history.append({
            'price': price,
            'timestamp': timestamp,
        })
        
        # Update volatility
        if len(self.price_history) >= 10:
            recent_prices = [p['price'] for p in list(self.price_history)[-10:]]
            returns = np.diff(recent_prices) / recent_prices[:-1]
            volatility = np.std(returns)
            self.volatility_history.append(volatility)
    
    def calculate_staleness_risk(self) -> float:
        """
        Calculate risk of quote being stale
        
        Returns:
            Staleness risk (0-1)
        """
        time_since_update = (datetime.now() - self.last_quote_update).total_seconds()
        
        # Get current volatility
        if self.volatility_history:
            volatility = np.mean(list(self.volatility_history)[-10:])
        else:
            volatility = 0.001
        
        # Staleness risk increases with time and volatility
        staleness = time_since_update * volatility * 100
        
        return min(staleness, 1.0)
    
    def get_quote_fade(self) -> float:
        """
        Get quote fade amount based on staleness
        
        Returns:
            Fade amount (spread widening)
        """
        staleness = self.calculate_staleness_risk()
        
        fade = staleness * self.fade_rate
        fade = min(fade, self.max_fade)
        
        return fade
    
    def should_cancel_quotes(self) -> Tuple[bool, str]:
        """
        Determine if quotes should be cancelled
        
        Returns:
            Tuple of (should_cancel, reason)
        """
        staleness = self.calculate_staleness_risk()
        
        if staleness > 0.8:
            return True, f"High staleness risk: {staleness:.2f}"
        
        # Check for rapid price movement
        if len(self.price_history) >= 5:
            recent = list(self.price_history)[-5:]
            price_change = abs(recent[-1]['price'] - recent[0]['price']) / recent[0]['price']
            
            if price_change > 0.005:  # 0.5% move
                return True, f"Rapid price movement: {price_change*100:.2f}%"
        
        return False, "Quotes safe"
    
    def get_optimal_quote_level(self, mid_price: float, side: str) -> float:
        """
        Get optimal quote price level
        
        Args:
            mid_price: Current mid price
            side: 'bid' or 'ask'
            
        Returns:
            Optimal quote price
        """
        fade = self.get_quote_fade()
        
        if side == 'bid':
            return mid_price * (1 - fade)
        else:
            return mid_price * (1 + fade)
    
    def record_quote_update(self):
        """Record quote update timestamp"""
        self.last_quote_update = datetime.now()


class LiquidityAnalyzer:
    """
    Analyzes market liquidity
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Order book snapshots
        self.book_history: deque = deque(maxlen=1000)
        
        # Liquidity metrics history
        self.metrics_history: deque = deque(maxlen=1000)
    
    def update_order_book(self, bids: List[Tuple[float, float]], 
                         asks: List[Tuple[float, float]]):
        """
        Update order book snapshot
        
        Args:
            bids: List of (price, size) tuples
            asks: List of (price, size) tuples
        """
        self.book_history.append({
            'timestamp': datetime.now(),
            'bids': bids,
            'asks': asks,
        })
    
    def calculate_metrics(self) -> LiquidityMetrics:
        """Calculate liquidity metrics"""
        if not self.book_history:
            return LiquidityMetrics(
                timestamp=datetime.now(),
                bid_depth=0,
                ask_depth=0,
                spread=0,
                spread_bps=0,
                depth_imbalance=0,
                resilience=0,
                hidden_liquidity_estimate=0,
            )
        
        latest = self.book_history[-1]
        bids = latest['bids']
        asks = latest['asks']
        
        # Calculate depths
        bid_depth = sum(size for _, size in bids[:5]) if bids else 0
        ask_depth = sum(size for _, size in asks[:5]) if asks else 0
        
        # Calculate spread
        if bids and asks:
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            spread = best_ask - best_bid
            mid_price = (best_bid + best_ask) / 2
            spread_bps = spread / mid_price * 10000
        else:
            spread = 0
            spread_bps = 0
        
        # Depth imbalance
        total_depth = bid_depth + ask_depth
        depth_imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0
        
        # Resilience (how quickly depth replenishes)
        resilience = self._calculate_resilience()
        
        # Hidden liquidity estimate
        hidden_estimate = self._estimate_hidden_liquidity()
        
        metrics = LiquidityMetrics(
            timestamp=datetime.now(),
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            spread=spread,
            spread_bps=spread_bps,
            depth_imbalance=depth_imbalance,
            resilience=resilience,
            hidden_liquidity_estimate=hidden_estimate,
        )
        
        self.metrics_history.append(metrics)
        
        return metrics
    
    def _calculate_resilience(self) -> float:
        """Calculate liquidity resilience"""
        if len(self.book_history) < 10:
            return 0.5
        
        # Compare depth changes over time
        recent = list(self.book_history)[-10:]
        
        depths = []
        for snapshot in recent:
            bid_depth = sum(size for _, size in snapshot['bids'][:5]) if snapshot['bids'] else 0
            ask_depth = sum(size for _, size in snapshot['asks'][:5]) if snapshot['asks'] else 0
            depths.append(bid_depth + ask_depth)
        
        # Resilience = stability of depth
        if np.mean(depths) > 0:
            resilience = 1 - (np.std(depths) / np.mean(depths))
        else:
            resilience = 0
        
        return max(0, min(1, resilience))
    
    def _estimate_hidden_liquidity(self) -> float:
        """Estimate hidden liquidity from trade patterns"""
        # Simplified: based on depth imbalance and recent trades
        if not self.metrics_history:
            return 0
        
        recent_metrics = list(self.metrics_history)[-10:]
        avg_depth = np.mean([m.bid_depth + m.ask_depth for m in recent_metrics])
        
        # Estimate hidden as 20-50% of visible
        return avg_depth * 0.3
    
    def get_liquidity_score(self) -> float:
        """Get overall liquidity score (0-1)"""
        metrics = self.calculate_metrics()
        
        # Score components
        depth_score = min((metrics.bid_depth + metrics.ask_depth) / 10000, 1.0)
        spread_score = max(0, 1 - metrics.spread_bps / 50)
        resilience_score = metrics.resilience
        
        # Weighted average
        score = depth_score * 0.4 + spread_score * 0.4 + resilience_score * 0.2
        
        return score
    
    def is_liquid_enough(self, order_size: float) -> Tuple[bool, str]:
        """
        Check if market is liquid enough for order
        
        Args:
            order_size: Intended order size
            
        Returns:
            Tuple of (is_liquid, reason)
        """
        metrics = self.calculate_metrics()
        
        total_depth = metrics.bid_depth + metrics.ask_depth
        
        if order_size > total_depth * 0.5:
            return False, f"Order size ({order_size}) exceeds 50% of visible depth ({total_depth})"
        
        if metrics.spread_bps > 20:
            return False, f"Spread too wide: {metrics.spread_bps:.1f} bps"
        
        if metrics.resilience < 0.3:
            return False, f"Low liquidity resilience: {metrics.resilience:.2f}"
        
        return True, "Sufficient liquidity"
