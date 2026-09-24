"""
Market Manipulation Detector
=============================

Detects signs of market manipulation:
- Wash trading (buyer = seller, unusual volume without price move)
- Pump & dump (coordinated social media + volume spike + crash)
- Spoofing (large orders placed/cancelled to move price)
- Layering (multiple fake orders at different levels)
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ManipulationType(Enum):
    """Types of market manipulation."""
    WASH_TRADING = "wash_trading"
    PUMP_AND_DUMP = "pump_and_dump"
    SPOOFING = "spoofing"
    LAYERING = "layering"
    FRONT_RUNNING = "front_running"
    UNKNOWN = "unknown"


@dataclass
class ManipulationAlert:
    """Detected manipulation attempt."""
    asset: str
    manipulation_type: ManipulationType
    confidence: float
    evidence: List[str]
    affected_volume: float
    estimated_impact: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset': self.asset,
            'manipulation_type': self.manipulation_type.value,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'affected_volume': self.affected_volume,
            'estimated_impact': self.estimated_impact,
            'timestamp': self.timestamp.isoformat(),
        }


class MarketManipulationDetector:
    """
    Detects various forms of market manipulation.
    
    Critical for avoiding traps and protecting capital from
    coordinated manipulation schemes.
    """
    
    def __init__(self,
                 volume_anomaly_threshold: float = 3.0,
                 order_cancel_threshold: float = 0.8,
                 social_spike_threshold: float = 5.0):
        """
        Initialize detector.
        
        Args:
            volume_anomaly_threshold: Volume spike threshold (x normal)
            order_cancel_threshold: Cancellation rate threshold
            social_spike_threshold: Social media spike threshold
        """
        self.volume_anomaly_threshold = volume_anomaly_threshold
        self.order_cancel_threshold = order_cancel_threshold
        self.social_spike_threshold = social_spike_threshold
        
        self.order_history: Dict[str, List[Dict]] = {}
        self.volume_history: Dict[str, List[float]] = {}
        self.social_history: Dict[str, List[float]] = {}
        
        logger.info("MarketManipulationDetector initialized")
    
    def detect_wash_trading(self,
                         asset: str,
                         trades: List[Dict[str, Any]]) -> Optional[ManipulationAlert]:
        """
        Detect wash trading patterns.
        
        Wash trading signs:
        - Circular trading (A buys from B, B buys from A)
        - Volume without price movement
        - Same entities on both sides
        """
        if len(trades) < 10:
            return None
        
        # Analyze trade patterns
        volume = sum(t.get('size', 0) for t in trades)
        prices = [t.get('price', 0) for t in trades]
        
        # Check for low price variance despite high volume
        if len(prices) > 1:
            price_range = max(prices) - min(prices)
            avg_price = sum(prices) / len(prices)
            
            if avg_price > 0 and price_range / avg_price < 0.001:  # Less than 0.1% range
                # High volume, flat price = suspicious
                confidence = min(1.0, volume / 1000000)  # Higher volume = higher confidence
                
                return ManipulationAlert(
                    asset=asset,
                    manipulation_type=ManipulationType.WASH_TRADING,
                    confidence=confidence,
                    evidence=[
                        f"High volume ({volume:.0f}) with minimal price movement ({price_range/avg_price:.4%})",
                        "Price range less than 0.1% despite active trading",
                    ],
                    affected_volume=volume,
                    estimated_impact=0.01,  # Artificial volume can mislead
                    timestamp=datetime.now(),
                )
        
        return None
    
    def detect_pump_and_dump(self,
                            asset: str,
                            price_data: List[float],
                            volume_data: List[float],
                            social_sentiment: List[float]) -> Optional[ManipulationAlert]:
        """
        Detect pump and dump schemes.
        
        Pump & dump pattern:
        1. Coordinated social media activity
        2. Volume spike
        3. Price spike
        4. Rapid price collapse
        """
        if len(price_data) < 20 or len(volume_data) < 20:
            return None
        
        # Calculate recent metrics
        recent_prices = price_data[-20:]
        recent_volumes = volume_data[-20:]
        
        # Volume spike
        avg_volume = np.mean(volume_data[:-20]) if len(volume_data) > 20 else np.mean(volume_data)
        recent_avg_volume = np.mean(recent_volumes)
        volume_spike = recent_avg_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Price spike
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] if recent_prices[0] > 0 else 0
        
        # Social sentiment spike
        social_spike = False
        if social_sentiment and len(social_sentiment) >= 20:
            recent_social = np.mean(social_sentiment[-20:])
            historical_social = np.mean(social_sentiment[:-20]) if len(social_sentiment) > 20 else 0
            if historical_social > 0:
                social_spike = recent_social / historical_social > self.social_spike_threshold
        
        # Detect pump pattern
        is_pump = (
            volume_spike > self.volume_anomaly_threshold and
            price_change > 0.10 and  # 10% price spike
            social_spike
        )
        
        # Detect dump pattern (if we have more data)
        is_dump = False
        if len(price_data) >= 30:
            post_prices = price_data[-10:]
            post_change = (post_prices[-1] - post_prices[0]) / post_prices[0] if post_prices[0] > 0 else 0
            is_dump = post_change < -0.05  # 5% drop after pump
        
        if is_pump:
            confidence = min(1.0, (volume_spike / self.volume_anomaly_threshold) * 0.7 + 
                           (abs(price_change) / 0.20) * 0.3)
            
            evidence = [
                f"Volume spike: {volume_spike:.1f}x normal",
                f"Price spike: {price_change:.1%}",
            ]
            if social_spike:
                evidence.append("Coordinated social media activity detected")
            if is_dump:
                evidence.append("Dump phase confirmed: rapid price decline after spike")
            
            return ManipulationAlert(
                asset=asset,
                manipulation_type=ManipulationType.PUMP_AND_DUMP,
                confidence=confidence,
                evidence=evidence,
                affected_volume=sum(recent_volumes),
                estimated_impact=abs(price_change),
                timestamp=datetime.now(),
            )
        
        return None
    
    def detect_spoofing(self,
                       asset: str,
                       order_book: Dict[str, List[Tuple[float, float]]]) -> Optional[ManipulationAlert]:
        """
        Detect spoofing (layering fake orders).
        
        Spoofing signs:
        - Large orders placed and quickly cancelled
        - Orders far from best bid/ask
        - Repetitive placement/cancellation patterns
        """
        if 'bids' not in order_book or 'asks' not in order_book:
            return None
        
        # Track order history for this asset
        if asset not in self.order_history:
            self.order_history[asset] = []
        
        # Record current state
        snapshot = {
            'timestamp': datetime.now(),
            'bids': order_book['bids'],
            'asks': order_book['asks'],
        }
        self.order_history[asset].append(snapshot)
        
        # Keep only recent history
        cutoff = datetime.now() - timedelta(minutes=5)
        self.order_history[asset] = [
            h for h in self.order_history[asset]
            if h['timestamp'] > cutoff
        ]
        
        # Need at least 10 snapshots to detect pattern
        if len(self.order_history[asset]) < 10:
            return None
        
        # Analyze for spoofing patterns
        large_orders_cancelled = 0
        total_large_orders = 0
        
        for i in range(1, len(self.order_history[asset])):
            prev = self.order_history[asset][i-1]
            curr = self.order_history[asset][i]
            
            # Check for disappeared large orders
            prev_large_bids = [b for b in prev['bids'] if b[1] > 10000]  # Size > 10000
            curr_bids = [b[0] for b in curr['bids']]  # Price levels
            
            for order in prev_large_bids:
                if order[0] not in curr_bids:  # Price level gone
                    large_orders_cancelled += 1
                total_large_orders += 1
        
        if total_large_orders > 0:
            cancel_rate = large_orders_cancelled / total_large_orders
            
            if cancel_rate > self.order_cancel_threshold:
                confidence = min(1.0, cancel_rate)
                
                return ManipulationAlert(
                    asset=asset,
                    manipulation_type=ManipulationType.SPOOFING,
                    confidence=confidence,
                    evidence=[
                        f"High cancellation rate: {cancel_rate:.1%} of large orders",
                        f"{large_orders_cancelled} large orders cancelled in 5 minutes",
                    ],
                    affected_volume=total_large_orders * 10000,
                    estimated_impact=0.005,  # Can move price by 0.5%
                    timestamp=datetime.now(),
                )
        
        return None
    
    def get_manipulation_summary(self, asset: str) -> Dict[str, Any]:
        """Get summary of manipulation risk for asset."""
        # Check historical alerts
        # This would integrate with a database in production
        
        return {
            'asset': asset,
            'risk_level': 'unknown',
            'recent_alerts': 0,
            'recommended_action': 'monitor',
        }
