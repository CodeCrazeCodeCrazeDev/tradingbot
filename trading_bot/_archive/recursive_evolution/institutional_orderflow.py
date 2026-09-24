"""
Institutional Order Flow Analysis
==================================

Advanced order flow analysis system that detects and interprets institutional
trading activity including block trades, iceberg orders, spoofing, and other
sophisticated trading patterns.

CAPABILITIES:
- Real-time order flow imbalance detection
- Block trade identification
- Iceberg order detection
- Spoofing and layering detection
- Volume delta analysis
- Absorption and exhaustion patterns
- Institutional footprint tracking
- Smart money flow analysis
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class OrderFlowType(Enum):
    """Types of order flow patterns"""
    AGGRESSIVE_BUYING = "aggressive_buying"
    AGGRESSIVE_SELLING = "aggressive_selling"
    ABSORPTION = "absorption"
    EXHAUSTION = "exhaustion"
    BLOCK_TRADE = "block_trade"
    ICEBERG = "iceberg"
    SPOOFING = "spoofing"
    LAYERING = "layering"
    MOMENTUM = "momentum"
    REVERSAL = "reversal"


class InstitutionalActivityType(Enum):
    """Types of institutional activity"""
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    NEUTRAL = "neutral"
    MANIPULATION = "manipulation"


@dataclass
class OrderFlowSignal:
    """A detected order flow signal"""
    signal_id: str
    symbol: str
    timestamp: datetime
    flow_type: OrderFlowType
    strength: float  # 0-1
    price_level: float
    volume: float
    confidence: float
    evidence: List[str]
    expected_impact: str  # bullish, bearish, neutral
    timeframe: str  # immediate, short-term, medium-term


@dataclass
class BlockTradeDetection:
    """Detection of a block trade"""
    trade_id: str
    symbol: str
    timestamp: datetime
    size: float
    price: float
    side: str  # buy, sell
    is_institutional: bool
    confidence: float
    market_impact_estimate: float
    follow_through_expected: bool


@dataclass
class InstitutionalActivity:
    """Detected institutional activity"""
    activity_id: str
    symbol: str
    start_time: datetime
    end_time: Optional[datetime]
    activity_type: InstitutionalActivityType
    total_volume: float
    average_price: float
    confidence: float
    evidence: List[str]
    still_active: bool


class BlockTradeDetector:
    """
    Detects block trades and institutional-sized orders.
    """
    
    def __init__(self, min_block_size: float = 100000):
        self.min_block_size = min_block_size
        self.detected_blocks: List[BlockTradeDetection] = []
        
    def detect_block_trade(self, trade: Dict[str, Any], symbol: str) -> Optional[BlockTradeDetection]:
        """Detect if a trade is a block trade"""
        
        size = trade.get('size', 0)
        price = trade.get('price', 0)
        
        if size < self.min_block_size:
            return None
        
        # Calculate confidence based on size
        confidence = min(1.0, size / (self.min_block_size * 5))
        
        # Estimate market impact
        market_impact = (size / self.min_block_size) * 0.001  # 0.1% per 1x min size
        
        # Determine if follow-through expected
        follow_through = size > self.min_block_size * 2
        
        detection = BlockTradeDetection(
            trade_id=f"BLOCK-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            symbol=symbol,
            timestamp=datetime.utcnow(),
            size=size,
            price=price,
            side=trade.get('side', 'unknown'),
            is_institutional=True,
            confidence=confidence,
            market_impact_estimate=market_impact,
            follow_through_expected=follow_through
        )
        
        self.detected_blocks.append(detection)
        return detection


class InstitutionalOrderFlow:
    """
    Comprehensive institutional order flow analysis system.
    
    This system:
    1. Monitors real-time order flow
    2. Detects institutional trading patterns
    3. Identifies block trades and hidden orders
    4. Tracks volume delta and absorption
    5. Detects spoofing and manipulation
    6. Provides actionable signals
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Detection parameters
        self.min_block_size = self.config.get('min_block_size', 100000)
        self.iceberg_detection_window = self.config.get('iceberg_window', 60)  # seconds
        self.spoofing_cancel_ratio = self.config.get('spoofing_ratio', 0.8)
        
        # Detectors
        self.block_detector = BlockTradeDetector(self.min_block_size)
        
        # Order flow tracking
        self.volume_delta_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.order_flow_signals: List[OrderFlowSignal] = []
        self.institutional_activities: List[InstitutionalActivity] = []
        
        # Order tracking for iceberg/spoofing detection
        self.order_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.cancelled_orders: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        logger.info("InstitutionalOrderFlow initialized")
    
    def analyze_order_flow(self, symbol: str, market_data: Dict[str, Any],
                          context: Optional[Dict[str, Any]] = None) -> List[OrderFlowSignal]:
        """
        Analyze order flow and generate signals.
        """
        signals = []
        
        # 1. Volume delta analysis
        delta_signal = self._analyze_volume_delta(symbol, market_data)
        if delta_signal:
            signals.append(delta_signal)
        
        # 2. Block trade detection
        block_signals = self._detect_block_trades(symbol, market_data)
        signals.extend(block_signals)
        
        # 3. Iceberg order detection
        iceberg_signal = self._detect_iceberg_orders(symbol, market_data)
        if iceberg_signal:
            signals.append(iceberg_signal)
        
        # 4. Spoofing detection
        spoofing_signal = self._detect_spoofing(symbol, market_data)
        if spoofing_signal:
            signals.append(spoofing_signal)
        
        # 5. Absorption pattern detection
        absorption_signal = self._detect_absorption(symbol, market_data)
        if absorption_signal:
            signals.append(absorption_signal)
        
        # 6. Exhaustion pattern detection
        exhaustion_signal = self._detect_exhaustion(symbol, market_data)
        if exhaustion_signal:
            signals.append(exhaustion_signal)
        
        # Store signals
        self.order_flow_signals.extend(signals)
        
        return signals
    
    def _analyze_volume_delta(self, symbol: str, market_data: Dict[str, Any]) -> Optional[OrderFlowSignal]:
        """Analyze volume delta (buying vs selling pressure)"""
        
        if 'trades' not in market_data:
            return None
        
        trades = market_data['trades']
        
        # Calculate volume delta
        buy_volume = sum(t['size'] for t in trades if t.get('side') == 'buy')
        sell_volume = sum(t['size'] for t in trades if t.get('side') == 'sell')
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return None
        
        delta = (buy_volume - sell_volume) / total_volume
        
        # Store in history
        self.volume_delta_history[symbol].append((datetime.utcnow(), delta))
        
        # Check for significant imbalance
        if abs(delta) < 0.3:
            return None  # Not significant
        
        # Determine flow type
        if delta > 0.5:
            flow_type = OrderFlowType.AGGRESSIVE_BUYING
            expected_impact = "bullish"
        elif delta < -0.5:
            flow_type = OrderFlowType.AGGRESSIVE_SELLING
            expected_impact = "bearish"
        else:
            return None
        
        strength = abs(delta)
        confidence = min(1.0, abs(delta) * 1.5)
        
        return OrderFlowSignal(
            signal_id=f"FLOW-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            symbol=symbol,
            timestamp=datetime.utcnow(),
            flow_type=flow_type,
            strength=strength,
            price_level=market_data.get('price', 0),
            volume=total_volume,
            confidence=confidence,
            evidence=[f"Volume delta: {delta:.2f}", f"Buy: {buy_volume:.0f}, Sell: {sell_volume:.0f}"],
            expected_impact=expected_impact,
            timeframe="immediate"
        )
    
    def _detect_block_trades(self, symbol: str, market_data: Dict[str, Any]) -> List[OrderFlowSignal]:
        """Detect block trades"""
        
        signals = []
        
        if 'trades' not in market_data:
            return signals
        
        for trade in market_data['trades']:
            detection = self.block_detector.detect_block_trade(trade, symbol)
            
            if detection:
                # Convert to order flow signal
                signal = OrderFlowSignal(
                    signal_id=f"BLOCK-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    symbol=symbol,
                    timestamp=detection.timestamp,
                    flow_type=OrderFlowType.BLOCK_TRADE,
                    strength=detection.confidence,
                    price_level=detection.price,
                    volume=detection.size,
                    confidence=detection.confidence,
                    evidence=[
                        f"Block trade detected: {detection.size:.0f} at {detection.price:.5f}",
                        f"Side: {detection.side}",
                        f"Market impact: {detection.market_impact_estimate:.4f}"
                    ],
                    expected_impact="bullish" if detection.side == 'buy' else "bearish",
                    timeframe="short-term" if detection.follow_through_expected else "immediate"
                )
                signals.append(signal)
        
        return signals
    
    def _detect_iceberg_orders(self, symbol: str, market_data: Dict[str, Any]) -> Optional[OrderFlowSignal]:
        """Detect iceberg orders (large hidden orders executed in small chunks)"""
        
        if 'trades' not in market_data:
            return None
        
        trades = market_data['trades']
        
        # Look for repeated trades at similar prices
        price_clusters = defaultdict(list)
        for trade in trades:
            price_bucket = round(trade['price'], 4)  # Bucket by price
            price_clusters[price_bucket].append(trade)
        
        # Find clusters with many small trades
        for price, cluster_trades in price_clusters.items():
            if len(cluster_trades) < 5:
                continue
            
            # Check if trades are similar size
            sizes = [t['size'] for t in cluster_trades]
            avg_size = np.mean(sizes)
            size_std = np.std(sizes)
            
            # If sizes are consistent and total is large
            if size_std / avg_size < 0.3 and sum(sizes) > self.min_block_size:
                # Likely iceberg
                total_volume = sum(sizes)
                confidence = min(1.0, total_volume / (self.min_block_size * 2))
                
                # Determine side
                buy_count = sum(1 for t in cluster_trades if t.get('side') == 'buy')
                side = 'buy' if buy_count > len(cluster_trades) / 2 else 'sell'
                
                return OrderFlowSignal(
                    signal_id=f"ICEBERG-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    flow_type=OrderFlowType.ICEBERG,
                    strength=confidence,
                    price_level=price,
                    volume=total_volume,
                    confidence=confidence,
                    evidence=[
                        f"Iceberg detected: {len(cluster_trades)} trades totaling {total_volume:.0f}",
                        f"Average size: {avg_size:.0f}",
                        f"Price level: {price:.5f}"
                    ],
                    expected_impact="bullish" if side == 'buy' else "bearish",
                    timeframe="medium-term"
                )
        
        return None
    
    def _detect_spoofing(self, symbol: str, market_data: Dict[str, Any]) -> Optional[OrderFlowSignal]:
        """Detect spoofing (large orders placed and quickly cancelled)"""
        
        if 'cancelled_orders' not in market_data or 'placed_orders' not in market_data:
            return None
        
        cancelled = market_data['cancelled_orders']
        placed = market_data['placed_orders']
        
        # Track cancellations
        for order in cancelled:
            self.cancelled_orders[symbol].append({
                'timestamp': datetime.utcnow(),
                'size': order.get('size', 0),
                'price': order.get('price', 0),
                'side': order.get('side', 'unknown')
            })
        
        # Check for high cancellation rate of large orders
        recent_cancelled = [o for o in self.cancelled_orders[symbol]
                          if datetime.utcnow() - o['timestamp'] < timedelta(seconds=60)]
        
        if not recent_cancelled:
            return None
        
        large_cancelled = [o for o in recent_cancelled if o['size'] > self.min_block_size / 2]
        
        if len(large_cancelled) < 3:
            return None
        
        # Calculate cancellation ratio
        total_placed = len(placed) if placed else 1
        cancel_ratio = len(large_cancelled) / total_placed
        
        if cancel_ratio < self.spoofing_cancel_ratio:
            return None
        
        # Likely spoofing
        total_spoofed = sum(o['size'] for o in large_cancelled)
        avg_price = np.mean([o['price'] for o in large_cancelled])
        
        # Determine manipulation direction
        buy_spoof = sum(1 for o in large_cancelled if o['side'] == 'buy')
        sell_spoof = sum(1 for o in large_cancelled if o['side'] == 'sell')
        
        if buy_spoof > sell_spoof:
            expected_impact = "bearish"  # Fake buy pressure removed
        else:
            expected_impact = "bullish"  # Fake sell pressure removed
        
        return OrderFlowSignal(
            signal_id=f"SPOOF-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            symbol=symbol,
            timestamp=datetime.utcnow(),
            flow_type=OrderFlowType.SPOOFING,
            strength=0.8,
            price_level=avg_price,
            volume=total_spoofed,
            confidence=0.75,
            evidence=[
                f"Spoofing detected: {len(large_cancelled)} large orders cancelled",
                f"Total spoofed volume: {total_spoofed:.0f}",
                f"Cancel ratio: {cancel_ratio:.2f}"
            ],
            expected_impact=expected_impact,
            timeframe="immediate"
        )
    
    def _detect_absorption(self, symbol: str, market_data: Dict[str, Any]) -> Optional[OrderFlowSignal]:
        """Detect absorption (large orders absorbing market pressure)"""
        
        if 'order_book' not in market_data or 'trades' not in market_data:
            return None
        
        book = market_data['order_book']
        trades = market_data['trades']
        
        # Check for large orders in book that are absorbing trades
        if 'bids' in book and 'asks' in book:
            # Find largest bid/ask
            if book['bids']:
                largest_bid_price, largest_bid_size = max(book['bids'], key=lambda x: x[1])
                
                # Check if trades are hitting this level
                trades_at_bid = [t for t in trades 
                               if abs(t['price'] - largest_bid_price) < 0.0001 
                               and t.get('side') == 'sell']
                
                if len(trades_at_bid) > 5 and largest_bid_size > self.min_block_size:
                    # Absorption detected
                    absorbed_volume = sum(t['size'] for t in trades_at_bid)
                    
                    return OrderFlowSignal(
                        signal_id=f"ABSORB-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        symbol=symbol,
                        timestamp=datetime.utcnow(),
                        flow_type=OrderFlowType.ABSORPTION,
                        strength=0.75,
                        price_level=largest_bid_price,
                        volume=absorbed_volume,
                        confidence=0.70,
                        evidence=[
                            f"Absorption at {largest_bid_price:.5f}",
                            f"Large bid: {largest_bid_size:.0f}",
                            f"Absorbed: {absorbed_volume:.0f} from {len(trades_at_bid)} trades"
                        ],
                        expected_impact="bullish",
                        timeframe="short-term"
                    )
        
        return None
    
    def _detect_exhaustion(self, symbol: str, market_data: Dict[str, Any]) -> Optional[OrderFlowSignal]:
        """Detect exhaustion (buying/selling pressure running out)"""
        
        # Check volume delta history
        if symbol not in self.volume_delta_history:
            return None
        
        history = list(self.volume_delta_history[symbol])
        if len(history) < 10:
            return None
        
        # Get recent deltas
        recent_deltas = [d for _, d in history[-10:]]
        
        # Check for declining momentum
        if len(recent_deltas) >= 5:
            first_half = recent_deltas[:5]
            second_half = recent_deltas[5:]
            
            first_avg = np.mean([abs(d) for d in first_half])
            second_avg = np.mean([abs(d) for d in second_half])
            
            # If momentum is declining significantly
            if first_avg > 0.3 and second_avg < first_avg * 0.5:
                # Exhaustion detected
                direction = "bullish" if np.mean(first_half) > 0 else "bearish"
                
                # Exhaustion suggests reversal
                expected_impact = "bearish" if direction == "bullish" else "bullish"
                
                return OrderFlowSignal(
                    signal_id=f"EXHAUST-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    flow_type=OrderFlowType.EXHAUSTION,
                    strength=0.65,
                    price_level=market_data.get('price', 0),
                    volume=0,
                    confidence=0.65,
                    evidence=[
                        f"{direction.capitalize()} exhaustion detected",
                        f"Momentum declined from {first_avg:.2f} to {second_avg:.2f}",
                        "Potential reversal"
                    ],
                    expected_impact=expected_impact,
                    timeframe="short-term"
                )
        
        return None
    
    def track_institutional_activity(self, symbol: str, 
                                    signals: List[OrderFlowSignal]) -> List[InstitutionalActivity]:
        """Track ongoing institutional activity from signals"""
        
        new_activities = []
        
        # Group signals by type and time
        accumulation_signals = [s for s in signals 
                               if s.expected_impact == "bullish" 
                               and s.flow_type in [OrderFlowType.BLOCK_TRADE, 
                                                  OrderFlowType.ICEBERG,
                                                  OrderFlowType.ABSORPTION]]
        
        distribution_signals = [s for s in signals 
                               if s.expected_impact == "bearish"
                               and s.flow_type in [OrderFlowType.BLOCK_TRADE,
                                                  OrderFlowType.ICEBERG]]
        
        # Check for accumulation
        if len(accumulation_signals) >= 2:
            total_volume = sum(s.volume for s in accumulation_signals)
            avg_price = np.mean([s.price_level for s in accumulation_signals])
            
            activity = InstitutionalActivity(
                activity_id=f"INST-ACC-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                symbol=symbol,
                start_time=min(s.timestamp for s in accumulation_signals),
                end_time=None,
                activity_type=InstitutionalActivityType.ACCUMULATION,
                total_volume=total_volume,
                average_price=avg_price,
                confidence=np.mean([s.confidence for s in accumulation_signals]),
                evidence=[s.signal_id for s in accumulation_signals],
                still_active=True
            )
            new_activities.append(activity)
        
        # Check for distribution
        if len(distribution_signals) >= 2:
            total_volume = sum(s.volume for s in distribution_signals)
            avg_price = np.mean([s.price_level for s in distribution_signals])
            
            activity = InstitutionalActivity(
                activity_id=f"INST-DIST-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                symbol=symbol,
                start_time=min(s.timestamp for s in distribution_signals),
                end_time=None,
                activity_type=InstitutionalActivityType.DISTRIBUTION,
                total_volume=total_volume,
                average_price=avg_price,
                confidence=np.mean([s.confidence for s in distribution_signals]),
                evidence=[s.signal_id for s in distribution_signals],
                still_active=True
            )
            new_activities.append(activity)
        
        # Store activities
        self.institutional_activities.extend(new_activities)
        
        return new_activities
    
    def get_order_flow_summary(self, symbol: str, 
                              lookback_minutes: int = 60) -> Dict[str, Any]:
        """Get summary of order flow for a symbol"""
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
        
        # Filter recent signals
        recent_signals = [s for s in self.order_flow_signals 
                         if s.symbol == symbol and s.timestamp > cutoff_time]
        
        if not recent_signals:
            return {
                'symbol': symbol,
                'period_minutes': lookback_minutes,
                'signal_count': 0,
                'dominant_flow': 'neutral'
            }
        
        # Count signal types
        signal_counts = defaultdict(int)
        for signal in recent_signals:
            signal_counts[signal.flow_type.value] += 1
        
        # Determine dominant flow
        bullish_signals = sum(1 for s in recent_signals if s.expected_impact == "bullish")
        bearish_signals = sum(1 for s in recent_signals if s.expected_impact == "bearish")
        
        if bullish_signals > bearish_signals * 1.5:
            dominant_flow = "bullish"
        elif bearish_signals > bullish_signals * 1.5:
            dominant_flow = "bearish"
        else:
            dominant_flow = "neutral"
        
        # Calculate average strength
        avg_strength = np.mean([s.strength for s in recent_signals])
        
        # Get institutional activities
        recent_activities = [a for a in self.institutional_activities
                           if a.symbol == symbol and a.start_time > cutoff_time]
        
        return {
            'symbol': symbol,
            'period_minutes': lookback_minutes,
            'signal_count': len(recent_signals),
            'signal_types': dict(signal_counts),
            'dominant_flow': dominant_flow,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'average_strength': avg_strength,
            'institutional_activities': len(recent_activities),
            'block_trades_detected': len(self.block_detector.detected_blocks)
        }


def quick_start_orderflow(config: Optional[Dict[str, Any]] = None) -> InstitutionalOrderFlow:
    """Quick start function for order flow analysis"""
    return InstitutionalOrderFlow(config)
