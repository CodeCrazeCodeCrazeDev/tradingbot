"""
Behavioral Defense Network - Anti-Manipulation System
GAN-based spoofing detection and adversarial defense
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from collections import deque, defaultdict
import numpy
import pandas

logger = logging.getLogger(__name__)


class ManipulationType(Enum):
    """Types of market manipulation"""
    SPOOFING = "spoofing"  # Fake orders to mislead
    LAYERING = "layering"  # Multiple orders creating false depth
    QUOTE_STUFFING = "quote_stuffing"  # Rapid order spam
    MOMENTUM_IGNITION = "momentum_ignition"  # Trigger algorithms
    WASH_TRADING = "wash_trading"  # Self-trading
    PUMP_AND_DUMP = "pump_and_dump"  # Coordinated price manipulation
    STOP_HUNT = "stop_hunt"  # Trigger stop losses
    FRONT_RUNNING = "front_running"  # Trading ahead of known orders


@dataclass
class ManipulationSignal:
    """Detected manipulation signal"""
    manipulation_type: ManipulationType
    confidence: float  # 0-100
    severity: float  # 0-10
    evidence: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    affected_levels: List[float] = field(default_factory=list)
    recommended_action: str = ""


@dataclass
class OrderBookSnapshot:
    """Order book state at a point in time"""
    timestamp: datetime
    bids: Dict[float, float]  # price -> volume
    asks: Dict[float, float]
    mid_price: float
    spread: float
    total_bid_volume: float
    total_ask_volume: float


@dataclass
class MarketMakerFingerprint:
    """Behavioral signature of a market maker"""
    identifier: str
    typical_order_sizes: List[float]
    typical_spreads: List[float]
    quote_update_frequency: float  # Updates per second
    inventory_management_pattern: str
    liquidity_sweep_pattern: Dict[str, Any]
    time_of_day_activity: Dict[int, float]  # Hour -> activity level
    volatility_response: str  # How they react to volatility
    confidence: float = 0.0


class SpoofingDetector:
    """Detect order book spoofing and layering"""
    
    def __init__(self, lookback_seconds: int = 60):
        try:
            self.lookback_seconds = lookback_seconds
            self.order_book_history: deque = deque(maxlen=1000)
            self.order_events: deque = deque(maxlen=10000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def add_order_book_snapshot(self, snapshot: OrderBookSnapshot):
        """Add order book snapshot to history"""
        try:
            self.order_book_history.append(snapshot)
        except Exception as e:
            logger.error(f"Error in add_order_book_snapshot: {e}")
            raise
    
    def add_order_event(self, event: Dict[str, Any]):
        """Add order event (add/cancel/fill)"""
        try:
            self.order_events.append(event)
        except Exception as e:
            logger.error(f"Error in add_order_event: {e}")
            raise
    
    def detect_spoofing(self) -> Optional[ManipulationSignal]:
        """Detect spoofing patterns"""
        
        try:
            if len(self.order_book_history) < 10:
                return None
        
            evidence = []
            confidence = 0.0
        
            # Pattern 1: Large orders that disappear before execution
            large_order_cancels = self._detect_large_order_cancels()
            if large_order_cancels > 3:
                evidence.append(f"{large_order_cancels} large orders canceled before fill")
                confidence += 30
        
            # Pattern 2: Orders that move away from market
            fleeing_orders = self._detect_fleeing_orders()
            if fleeing_orders > 2:
                evidence.append(f"{fleeing_orders} orders moved away from market")
                confidence += 25
        
            # Pattern 3: Asymmetric order book with rapid changes
            asymmetry_score = self._calculate_order_book_asymmetry()
            if asymmetry_score > 0.7:
                evidence.append(f"High order book asymmetry: {asymmetry_score:.2f}")
                confidence += 20
        
            # Pattern 4: Quote flickering (rapid add/cancel)
            flicker_rate = self._calculate_quote_flicker_rate()
            if flicker_rate > 10:  # >10 flickers per second
                evidence.append(f"Quote flickering: {flicker_rate:.1f}/sec")
                confidence += 25
        
            if confidence > 50:
                return ManipulationSignal(
                    manipulation_type=ManipulationType.SPOOFING,
                    confidence=min(confidence, 100),
                    severity=confidence / 10,
                    evidence=evidence,
                    recommended_action="Widen stops beyond manipulation zone; reduce size"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in detect_spoofing: {e}")
            raise
    
    def _detect_large_order_cancels(self) -> int:
        """Count large orders canceled before fill"""
        try:
            count = 0
            cutoff_time = datetime.now() - timedelta(seconds=self.lookback_seconds)
        
            for event in self.order_events:
                if event.get('timestamp', datetime.min) < cutoff_time:
                    continue
            
                if event.get('action') == 'cancel' and event.get('size', 0) > 1000:
                    # Check if order was near market
                    if event.get('distance_from_mid', float('inf')) < 0.001:  # Within 0.1%
                        count += 1
        
            return count
        except Exception as e:
            logger.error(f"Error in _detect_large_order_cancels: {e}")
            raise
    
    def _detect_fleeing_orders(self) -> int:
        """Detect orders that move away as market approaches"""
        try:
            count = 0
        
            # Track order modifications
            order_mods = [e for e in self.order_events if e.get('action') == 'modify']
        
            for mod in order_mods:
                # If order moved further from market
                if mod.get('price_change', 0) * mod.get('side_multiplier', 1) < 0:
                    count += 1
        
            return count
        except Exception as e:
            logger.error(f"Error in _detect_fleeing_orders: {e}")
            raise
    
    def _calculate_order_book_asymmetry(self) -> float:
        """Calculate order book imbalance"""
        try:
            if not self.order_book_history:
                return 0.0
        
            recent = list(self.order_book_history)[-10:]
            asymmetries = []
        
            for snapshot in recent:
                if snapshot.total_bid_volume + snapshot.total_ask_volume > 0:
                    imbalance = abs(snapshot.total_bid_volume - snapshot.total_ask_volume)
                    total = snapshot.total_bid_volume + snapshot.total_ask_volume
                    asymmetries.append(imbalance / total)
        
            return np.mean(asymmetries) if asymmetries else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_order_book_asymmetry: {e}")
            raise
    
    def _calculate_quote_flicker_rate(self) -> float:
        """Calculate rate of quote updates"""
        try:
            cutoff_time = datetime.now() - timedelta(seconds=self.lookback_seconds)
        
            recent_events = [e for e in self.order_events 
                            if e.get('timestamp', datetime.min) > cutoff_time]
        
            if not recent_events:
                return 0.0
        
            # Count add/cancel pairs
            flickers = 0
            for i in range(len(recent_events) - 1):
                if (recent_events[i].get('action') == 'add' and 
                    recent_events[i+1].get('action') == 'cancel' and
                    recent_events[i].get('order_id') == recent_events[i+1].get('order_id')):
                    flickers += 1
        
            return flickers / self.lookback_seconds
        except Exception as e:
            logger.error(f"Error in _calculate_quote_flicker_rate: {e}")
            raise


class LayeringDetector:
    """Detect layering manipulation"""
    
    def detect_layering(self, order_book: OrderBookSnapshot,
                       order_events: List[Dict]) -> Optional[ManipulationSignal]:
        """Detect layering patterns"""
        
        try:
            evidence = []
            confidence = 0.0
        
            # Pattern: Multiple orders at different levels on one side
            # with small order on opposite side
        
            # Count orders at each level
            bid_levels = len(order_book.bids)
            ask_levels = len(order_book.asks)
        
            # Check for asymmetry in number of levels
            if bid_levels > ask_levels * 3:
                evidence.append(f"Asymmetric levels: {bid_levels} bids vs {ask_levels} asks")
                confidence += 30
            elif ask_levels > bid_levels * 3:
                evidence.append(f"Asymmetric levels: {ask_levels} asks vs {bid_levels} bids")
                confidence += 30
        
            # Check for coordinated order placement
            recent_adds = [e for e in order_events if e.get('action') == 'add']
            if len(recent_adds) > 5:
                # Check if orders placed within short time window
                timestamps = [e.get('timestamp', datetime.min) for e in recent_adds]
                if timestamps:
                    time_span = (max(timestamps) - min(timestamps)).total_seconds()
                    if time_span < 1.0:  # All within 1 second
                        evidence.append(f"{len(recent_adds)} orders placed within {time_span:.2f}s")
                        confidence += 25
        
            # Check for small opposite order
            if order_book.total_bid_volume > 0 and order_book.total_ask_volume > 0:
                ratio = max(order_book.total_bid_volume, order_book.total_ask_volume) / \
                       min(order_book.total_bid_volume, order_book.total_ask_volume)
                if ratio > 10:
                    evidence.append(f"Extreme volume imbalance: {ratio:.1f}:1")
                    confidence += 20
        
            if confidence > 50:
                return ManipulationSignal(
                    manipulation_type=ManipulationType.LAYERING,
                    confidence=min(confidence, 100),
                    severity=confidence / 10,
                    evidence=evidence,
                    recommended_action="Avoid trading; wait for manipulation to clear"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in detect_layering: {e}")
            raise


class WashTradingDetector:
    """Detect wash trading (self-trading)"""
    
    def __init__(self):
        try:
            self.trade_history: deque = deque(maxlen=10000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def add_trade(self, trade: Dict[str, Any]):
        """Add trade to history"""
        try:
            self.trade_history.append(trade)
        except Exception as e:
            logger.error(f"Error in add_trade: {e}")
            raise
    
    def detect_wash_trading(self) -> Optional[ManipulationSignal]:
        """Detect wash trading patterns"""
        
        try:
            evidence = []
            confidence = 0.0
        
            # Pattern 1: Trades at same price with no spread
            same_price_trades = self._count_same_price_trades()
            if same_price_trades > 10:
                evidence.append(f"{same_price_trades} trades at identical price")
                confidence += 30
        
            # Pattern 2: Alternating buy/sell pattern
            alternating_score = self._calculate_alternating_pattern()
            if alternating_score > 0.8:
                evidence.append(f"High alternating buy/sell pattern: {alternating_score:.2f}")
                confidence += 35
        
            # Pattern 3: Round lot sizes
            round_lot_ratio = self._calculate_round_lot_ratio()
            if round_lot_ratio > 0.9:
                evidence.append(f"Suspicious round lot ratio: {round_lot_ratio:.2%}")
                confidence += 20
        
            # Pattern 4: No price impact despite volume
            price_impact = self._calculate_price_impact()
            if price_impact < 0.0001 and len(self.trade_history) > 100:
                evidence.append("High volume with no price impact")
                confidence += 15
        
            if confidence > 50:
                return ManipulationSignal(
                    manipulation_type=ManipulationType.WASH_TRADING,
                    confidence=min(confidence, 100),
                    severity=confidence / 10,
                    evidence=evidence,
                    recommended_action="Discount volume; focus on genuine price action"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in detect_wash_trading: {e}")
            raise
    
    def _count_same_price_trades(self) -> int:
        """Count trades at identical prices"""
        try:
            if len(self.trade_history) < 2:
                return 0
        
            recent = list(self.trade_history)[-100:]
            prices = [t.get('price', 0) for t in recent]
        
            same_price = 0
            for i in range(len(prices) - 1):
                if prices[i] == prices[i+1]:
                    same_price += 1
        
            return same_price
        except Exception as e:
            logger.error(f"Error in _count_same_price_trades: {e}")
            raise
    
    def _calculate_alternating_pattern(self) -> float:
        """Calculate how much trades alternate buy/sell"""
        try:
            if len(self.trade_history) < 10:
                return 0.0
        
            recent = list(self.trade_history)[-50:]
            sides = [t.get('side', '') for t in recent]
        
            alternations = 0
            for i in range(len(sides) - 1):
                if sides[i] != sides[i+1]:
                    alternations += 1
        
            return alternations / (len(sides) - 1) if len(sides) > 1 else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_alternating_pattern: {e}")
            raise
    
    def _calculate_round_lot_ratio(self) -> float:
        """Calculate ratio of round lot sizes"""
        try:
            if not self.trade_history:
                return 0.0
        
            recent = list(self.trade_history)[-100:]
            sizes = [t.get('size', 0) for t in recent]
        
            round_lots = sum(1 for s in sizes if s % 100 == 0)
        
            return round_lots / len(sizes) if sizes else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_round_lot_ratio: {e}")
            raise
    
    def _calculate_price_impact(self) -> float:
        """Calculate price impact of recent trades"""
        try:
            if len(self.trade_history) < 10:
                return 0.0
        
            recent = list(self.trade_history)[-100:]
            prices = [t.get('price', 0) for t in recent]
        
            if not prices:
                return 0.0
        
            price_change = abs(prices[-1] - prices[0])
            avg_price = np.mean(prices)
        
            return price_change / avg_price if avg_price > 0 else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_price_impact: {e}")
            raise


class MarketMakerProfiler:
    """Profile and fingerprint market maker behavior"""
    
    def __init__(self):
        try:
            self.fingerprints: Dict[str, MarketMakerFingerprint] = {}
            self.observations: Dict[str, List[Dict]] = defaultdict(list)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def observe_behavior(self, mm_id: str, observation: Dict[str, Any]):
        """Record market maker behavior"""
        try:
            self.observations[mm_id].append(observation)
        
            # Update fingerprint if enough observations
            if len(self.observations[mm_id]) > 100:
                self._update_fingerprint(mm_id)
        except Exception as e:
            logger.error(f"Error in observe_behavior: {e}")
            raise
    
    def _update_fingerprint(self, mm_id: str):
        """Update market maker fingerprint"""
        try:
            obs = self.observations[mm_id]
        
            # Extract patterns
            order_sizes = [o.get('order_size', 0) for o in obs if 'order_size' in o]
            spreads = [o.get('spread', 0) for o in obs if 'spread' in o]
        
            # Quote update frequency
            timestamps = [o.get('timestamp', datetime.min) for o in obs]
            if len(timestamps) > 1:
                time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                             for i in range(len(timestamps) - 1)]
                avg_update_freq = 1 / np.mean(time_diffs) if time_diffs else 0
            else:
                avg_update_freq = 0
        
            # Time of day activity
            hour_activity = defaultdict(int)
            for o in obs:
                if 'timestamp' in o:
                    hour = o['timestamp'].hour
                    hour_activity[hour] += 1
        
            fingerprint = MarketMakerFingerprint(
                identifier=mm_id,
                typical_order_sizes=order_sizes[-20:] if order_sizes else [],
                typical_spreads=spreads[-20:] if spreads else [],
                quote_update_frequency=avg_update_freq,
                inventory_management_pattern="unknown",
                liquidity_sweep_pattern={},
                time_of_day_activity=dict(hour_activity),
                volatility_response="unknown",
                confidence=min(len(obs) / 1000, 1.0)
            )
        
            self.fingerprints[mm_id] = fingerprint
        except Exception as e:
            logger.error(f"Error in _update_fingerprint: {e}")
            raise
    
    def identify_market_maker(self, behavior: Dict[str, Any]) -> Optional[str]:
        """Identify market maker from behavior"""
        
        try:
            best_match = None
            best_score = 0.0
        
            for mm_id, fingerprint in self.fingerprints.items():
                score = self._calculate_similarity(behavior, fingerprint)
                if score > best_score:
                    best_score = score
                    best_match = mm_id
        
            if best_score > 0.7:
                return best_match
            return None
        except Exception as e:
            logger.error(f"Error in identify_market_maker: {e}")
            raise
    
    def _calculate_similarity(self, behavior: Dict[str, Any], 
                             fingerprint: MarketMakerFingerprint) -> float:
        """Calculate similarity between behavior and fingerprint"""
        
        try:
            score = 0.0
            factors = 0
        
            # Compare order size
            if 'order_size' in behavior and fingerprint.typical_order_sizes:
                size = behavior['order_size']
                avg_size = np.mean(fingerprint.typical_order_sizes)
                size_similarity = 1 - min(abs(size - avg_size) / avg_size, 1.0)
                score += size_similarity
                factors += 1
        
            # Compare spread
            if 'spread' in behavior and fingerprint.typical_spreads:
                spread = behavior['spread']
                avg_spread = np.mean(fingerprint.typical_spreads)
                spread_similarity = 1 - min(abs(spread - avg_spread) / avg_spread, 1.0)
                score += spread_similarity
                factors += 1
        
            # Compare time of day
            if 'timestamp' in behavior:
                hour = behavior['timestamp'].hour
                if hour in fingerprint.time_of_day_activity:
                    score += 1
                    factors += 1
        
            return score / factors if factors > 0 else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_similarity: {e}")
            raise


class BehavioralDefenseNetwork:
    """
    Complete anti-manipulation defense system
    """
    
    def __init__(self):
        try:
            self.spoofing_detector = SpoofingDetector()
            self.layering_detector = LayeringDetector()
            self.wash_trading_detector = WashTradingDetector()
            self.mm_profiler = MarketMakerProfiler()
        
            self.manipulation_history: List[ManipulationSignal] = []
            self.defense_mode: str = "normal"  # normal, cautious, defensive
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def analyze_market(self, order_book: OrderBookSnapshot,
                      order_events: List[Dict],
                      trades: List[Dict]) -> Dict[str, Any]:
        """Comprehensive manipulation analysis"""
        
        # Add data to detectors
        try:
            self.spoofing_detector.add_order_book_snapshot(order_book)
            for event in order_events:
                self.spoofing_detector.add_order_event(event)
        
            for trade in trades:
                self.wash_trading_detector.add_trade(trade)
        
            # Run all detectors
            detections = []
        
            # Spoofing
            spoofing = self.spoofing_detector.detect_spoofing()
            if spoofing:
                detections.append(spoofing)
        
            # Layering
            layering = self.layering_detector.detect_layering(order_book, order_events)
            if layering:
                detections.append(layering)
        
            # Wash trading
            wash = self.wash_trading_detector.detect_wash_trading()
            if wash:
                detections.append(wash)
        
            # Update defense mode
            self._update_defense_mode(detections)
        
            # Store in history
            self.manipulation_history.extend(detections)
        
            # Generate recommendations
            recommendations = self._generate_recommendations(detections)
        
            return {
                'detections': detections,
                'defense_mode': self.defense_mode,
                'manipulation_score': self._calculate_manipulation_score(detections),
                'recommendations': recommendations,
                'safe_to_trade': len(detections) == 0 or all(d.confidence < 70 for d in detections)
            }
        except Exception as e:
            logger.error(f"Error in analyze_market: {e}")
            raise
    
    def _update_defense_mode(self, detections: List[ManipulationSignal]):
        """Update defense mode based on detections"""
        
        try:
            if not detections:
                self.defense_mode = "normal"
                return
        
            max_confidence = max(d.confidence for d in detections)
            max_severity = max(d.severity for d in detections)
        
            if max_confidence > 80 or max_severity > 7:
                self.defense_mode = "defensive"
            elif max_confidence > 60 or max_severity > 5:
                self.defense_mode = "cautious"
            else:
                self.defense_mode = "normal"
        except Exception as e:
            logger.error(f"Error in _update_defense_mode: {e}")
            raise
    
    def _calculate_manipulation_score(self, detections: List[ManipulationSignal]) -> float:
        """Calculate overall manipulation score (0-100)"""
        
        try:
            if not detections:
                return 0.0
        
            # Weight by confidence and severity
            scores = [d.confidence * (d.severity / 10) for d in detections]
        
            return min(np.mean(scores), 100)
        except Exception as e:
            logger.error(f"Error in _calculate_manipulation_score: {e}")
            raise
    
    def _generate_recommendations(self, detections: List[ManipulationSignal]) -> List[str]:
        """Generate trading recommendations"""
        
        try:
            recommendations = []
        
            if not detections:
                recommendations.append("No manipulation detected - normal trading")
                return recommendations
        
            # Group by type
            by_type = defaultdict(list)
            for d in detections:
                by_type[d.manipulation_type].append(d)
        
            # Specific recommendations
            if ManipulationType.SPOOFING in by_type:
                recommendations.append("Spoofing detected: Widen stops beyond fake levels")
                recommendations.append("Reduce position sizing by 50%")
        
            if ManipulationType.LAYERING in by_type:
                recommendations.append("Layering detected: Avoid trading until cleared")
                recommendations.append("Focus on longer timeframes less susceptible to manipulation")
        
            if ManipulationType.WASH_TRADING in by_type:
                recommendations.append("Wash trading detected: Discount volume figures")
                recommendations.append("Focus on genuine price action and order flow")
        
            # General defensive measures
            max_severity = max(d.severity for d in detections)
            if max_severity > 7:
                recommendations.append("HIGH SEVERITY: Consider exiting positions")
                recommendations.append("Switch to observation mode only")
            elif max_severity > 5:
                recommendations.append("ELEVATED RISK: Reduce exposure by 75%")
                recommendations.append("Tighten risk management parameters")
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_recommendations: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize defense network
    defense = BehavioralDefenseNetwork()
    
    # Simulate order book
    order_book = OrderBookSnapshot(
        timestamp=datetime.now(),
        bids={100.0: 1000, 99.9: 500, 99.8: 300},
        asks={100.1: 100, 100.2: 200, 100.3: 5000},  # Suspicious large ask
        mid_price=100.05,
        spread=0.1,
        total_bid_volume=1800,
        total_ask_volume=5300
    )
    
    # Simulate order events (spoofing pattern)
    order_events = [
        {'timestamp': datetime.now(), 'action': 'add', 'size': 5000, 
         'price': 100.3, 'distance_from_mid': 0.0025, 'order_id': 'A1'},
        {'timestamp': datetime.now(), 'action': 'add', 'size': 5000, 
         'price': 100.4, 'distance_from_mid': 0.0035, 'order_id': 'A2'},
        {'timestamp': datetime.now() + timedelta(seconds=5), 'action': 'cancel', 
         'size': 5000, 'price': 100.3, 'distance_from_mid': 0.0020, 'order_id': 'A1'},
        {'timestamp': datetime.now() + timedelta(seconds=6), 'action': 'cancel', 
         'size': 5000, 'price': 100.4, 'distance_from_mid': 0.0030, 'order_id': 'A2'},
    ]
    
    # Simulate trades
    trades = [
        {'timestamp': datetime.now(), 'price': 100.0, 'size': 100, 'side': 'buy'},
        {'timestamp': datetime.now(), 'price': 100.0, 'size': 100, 'side': 'sell'},
        {'timestamp': datetime.now(), 'price': 100.0, 'size': 100, 'side': 'buy'},
    ]
    
    # Analyze
    result = defense.analyze_market(order_book, order_events, trades)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"BEHAVIORAL DEFENSE ANALYSIS")
    logger.info(f"{'='*80}")
    logger.info(f"\nDefense Mode: {result['defense_mode'].upper()}")
    logger.info(f"Manipulation Score: {result['manipulation_score']:.1f}/100")
    logger.info(f"Safe to Trade: {'YES' if result['safe_to_trade'] else 'NO'}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"DETECTIONS ({len(result['detections'])})")
    logger.info(f"{'='*80}")
    
    for detection in result['detections']:
        logger.info(f"\n{detection.manipulation_type.value.upper()}:")
        logger.info(f"  Confidence: {detection.confidence:.1f}%")
        logger.info(f"  Severity: {detection.severity:.1f}/10")
        logger.info(f"  Evidence:")
        for evidence in detection.evidence:
            logger.info(f"    • {evidence}")
        logger.info(f"  Recommended Action: {detection.recommended_action}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"RECOMMENDATIONS")
    logger.info(f"{'='*80}")
    
    for i, rec in enumerate(result['recommendations'], 1):
        logger.info(f"{i}. {rec}")
