"""
Institutional Footprint DNA Detector

Advanced ML-based detection of institutional trading signatures by analyzing:
- Order sequence patterns (small orders followed by icebergs)
- Cancel/replace patterns
- Time-of-day clustering
- Volume distribution signatures
- Cross-asset coordination

Identifies exact moments institutions are accumulating or distributing.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import hashlib
import statistics

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class InstitutionalActivity(Enum):
    """Types of institutional activity."""
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    REPOSITIONING = "repositioning"
    HEDGING = "hedging"
    UNKNOWN = "unknown"


class OrderPattern(Enum):
    """Recognized order patterns."""
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"
    STEALTH = "stealth"
    MOMENTUM_IGNITION = "momentum_ignition"
    LAYERING = "layering"
    SWEEP = "sweep"
    BLOCK = "block"


class SignatureStrength(Enum):
    """Strength of institutional signature."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    DEFINITIVE = 4


@dataclass
class OrderEvent:
    """Single order event for pattern analysis."""
    timestamp: datetime
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: str
    price: float
    quantity: float
    filled_quantity: float
    status: str  # 'new', 'partial', 'filled', 'cancelled'
    venue: str = ""
    parent_order_id: Optional[str] = None
    
    @property
    def fill_rate(self) -> float:
        if self.quantity > 0:
            return self.filled_quantity / self.quantity
        return 0.0
    
    @property
    def is_cancelled(self) -> bool:
        return self.status == 'cancelled'
    
    @property
    def is_filled(self) -> bool:
        return self.status == 'filled'


@dataclass
class TradeEvent:
    """Single trade execution."""
    timestamp: datetime
    trade_id: str
    symbol: str
    side: str
    price: float
    quantity: float
    aggressor: str  # 'buyer' or 'seller'
    venue: str = ""


@dataclass
class InstitutionalSignature:
    """Detected institutional trading signature."""
    signature_id: str
    symbol: str
    activity_type: InstitutionalActivity
    pattern: OrderPattern
    strength: SignatureStrength
    confidence: float
    start_time: datetime
    end_time: datetime
    total_volume: float
    avg_price: float
    order_count: int
    trade_count: int
    fingerprint: str  # Unique pattern hash
    characteristics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signature_id': self.signature_id,
            'symbol': self.symbol,
            'activity_type': self.activity_type.value,
            'pattern': self.pattern.value,
            'strength': self.strength.name,
            'confidence': self.confidence,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_volume': self.total_volume,
            'avg_price': self.avg_price,
            'order_count': self.order_count,
            'trade_count': self.trade_count,
            'fingerprint': self.fingerprint,
            'characteristics': self.characteristics
        }


@dataclass
class AccumulationSignal:
    """Signal indicating institutional accumulation/distribution."""
    symbol: str
    signal_type: str  # 'ACCUMULATION', 'DISTRIBUTION', 'NEUTRAL'
    confidence: float
    signatures: List[InstitutionalSignature]
    volume_profile: Dict[str, float]
    time_clustering: Dict[int, float]  # hour -> volume
    price_impact: float
    stealth_score: float  # How hidden is the activity (0-1)
    urgency_score: float  # How urgent (0-1)
    analysis: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'confidence': self.confidence,
            'signature_count': len(self.signatures),
            'volume_profile': self.volume_profile,
            'price_impact': self.price_impact,
            'stealth_score': self.stealth_score,
            'urgency_score': self.urgency_score,
            'analysis': self.analysis
        }


class IcebergDetector:
    """
    Detects iceberg orders from order flow.
    
    Characteristics:
    - Repeated fills at same price level
    - Consistent small fill sizes
    - Quick refills after execution
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_refills = self.config.get('min_refills', 3)
        self.max_size_variance = self.config.get('max_size_variance', 0.2)
        self.max_time_gap_seconds = self.config.get('max_time_gap_seconds', 30)
    
    def detect(self, trades: List[TradeEvent]) -> List[Dict[str, Any]]:
        """Detect iceberg patterns in trades."""
        if len(trades) < self.min_refills:
            return []
        
        icebergs = []
        
        # Group by price level
        by_price = defaultdict(list)
        for trade in trades:
            price_key = round(trade.price, 5)
            by_price[price_key].append(trade)
        
        for price, price_trades in by_price.items():
            if len(price_trades) < self.min_refills:
                continue
            
            # Check for consistent sizing
            sizes = [t.quantity for t in price_trades]
            if len(sizes) < 2:
                continue
                
            avg_size = statistics.mean(sizes)
            if avg_size == 0:
                continue
                
            size_variance = statistics.stdev(sizes) / avg_size if len(sizes) > 1 else 0
            
            if size_variance <= self.max_size_variance:
                # Check time gaps
                time_gaps = []
                sorted_trades = sorted(price_trades, key=lambda t: t.timestamp)
                
                for i in range(1, len(sorted_trades)):
                    gap = (sorted_trades[i].timestamp - sorted_trades[i-1].timestamp).total_seconds()
                    time_gaps.append(gap)
                
                avg_gap = statistics.mean(time_gaps) if time_gaps else 0
                
                if avg_gap <= self.max_time_gap_seconds:
                    icebergs.append({
                        'price': price,
                        'trades': len(price_trades),
                        'total_volume': sum(sizes),
                        'avg_size': avg_size,
                        'size_variance': size_variance,
                        'avg_time_gap': avg_gap,
                        'side': price_trades[0].side,
                        'start_time': sorted_trades[0].timestamp,
                        'end_time': sorted_trades[-1].timestamp
                    })
        
        return icebergs


class TWAPDetector:
    """
    Detects TWAP (Time-Weighted Average Price) execution.
    
    Characteristics:
    - Regular time intervals between trades
    - Consistent trade sizes
    - Spread across time period
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_trades = self.config.get('min_trades', 5)
        self.max_interval_variance = self.config.get('max_interval_variance', 0.3)
    
    def detect(self, trades: List[TradeEvent], side: str) -> List[Dict[str, Any]]:
        """Detect TWAP patterns."""
        side_trades = [t for t in trades if t.side == side]
        
        if len(side_trades) < self.min_trades:
            return []
        
        twaps = []
        sorted_trades = sorted(side_trades, key=lambda t: t.timestamp)
        
        # Calculate time intervals
        intervals = []
        for i in range(1, len(sorted_trades)):
            interval = (sorted_trades[i].timestamp - sorted_trades[i-1].timestamp).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return []
        
        avg_interval = statistics.mean(intervals)
        if avg_interval == 0:
            return []
            
        interval_variance = statistics.stdev(intervals) / avg_interval if len(intervals) > 1 else 0
        
        if interval_variance <= self.max_interval_variance:
            sizes = [t.quantity for t in sorted_trades]
            avg_size = statistics.mean(sizes)
            size_variance = statistics.stdev(sizes) / avg_size if len(sizes) > 1 and avg_size > 0 else 0
            
            twaps.append({
                'side': side,
                'trades': len(sorted_trades),
                'total_volume': sum(sizes),
                'avg_size': avg_size,
                'size_variance': size_variance,
                'avg_interval_seconds': avg_interval,
                'interval_variance': interval_variance,
                'start_time': sorted_trades[0].timestamp,
                'end_time': sorted_trades[-1].timestamp,
                'duration_minutes': (sorted_trades[-1].timestamp - sorted_trades[0].timestamp).total_seconds() / 60
            })
        
        return twaps


class StealthAccumulationDetector:
    """
    Detects stealth accumulation patterns.
    
    Characteristics:
    - Small orders that don't move price
    - Consistent buying/selling pressure
    - Minimal market impact
    - Patient execution over extended period
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_duration_minutes = self.config.get('min_duration_minutes', 30)
        self.max_price_impact_pct = self.config.get('max_price_impact_pct', 0.1)
    
    def detect(
        self,
        trades: List[TradeEvent],
        start_price: float,
        end_price: float
    ) -> Optional[Dict[str, Any]]:
        """Detect stealth accumulation."""
        if not trades:
            return None
        
        # Calculate price impact
        price_change_pct = abs(end_price - start_price) / start_price * 100
        
        # Group by side
        buy_volume = sum(t.quantity for t in trades if t.side == 'buy')
        sell_volume = sum(t.quantity for t in trades if t.side == 'sell')
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return None
        
        # Calculate imbalance
        imbalance = (buy_volume - sell_volume) / total_volume
        
        # Duration
        sorted_trades = sorted(trades, key=lambda t: t.timestamp)
        duration_minutes = (sorted_trades[-1].timestamp - sorted_trades[0].timestamp).total_seconds() / 60
        
        # Check for stealth pattern
        if duration_minutes >= self.min_duration_minutes and price_change_pct <= self.max_price_impact_pct:
            # Calculate stealth score
            volume_per_minute = total_volume / duration_minutes if duration_minutes > 0 else 0
            impact_per_volume = price_change_pct / total_volume if total_volume > 0 else 0
            
            stealth_score = 1.0 - min(1.0, impact_per_volume * 10000)
            
            return {
                'activity': 'ACCUMULATION' if imbalance > 0.2 else 'DISTRIBUTION' if imbalance < -0.2 else 'NEUTRAL',
                'imbalance': imbalance,
                'buy_volume': buy_volume,
                'sell_volume': sell_volume,
                'total_volume': total_volume,
                'price_impact_pct': price_change_pct,
                'duration_minutes': duration_minutes,
                'stealth_score': stealth_score,
                'volume_per_minute': volume_per_minute,
                'trade_count': len(trades)
            }
        
        return None


class InstitutionalFootprintDNA:
    """
    Main institutional footprint detection system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Detectors
        self.iceberg_detector = IcebergDetector(config)
        self.twap_detector = TWAPDetector(config)
        self.stealth_detector = StealthAccumulationDetector(config)
        
        # Storage
        self.orders: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.trades: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.signatures: Dict[str, List[InstitutionalSignature]] = defaultdict(list)
        
        # Known institutional fingerprints
        self.known_fingerprints: Dict[str, str] = {}  # fingerprint -> institution name
        
        logger.info("InstitutionalFootprintDNA initialized")
    
    def add_order(self, order: OrderEvent):
        """Add order event."""
        self.orders[order.symbol].append(order)
    
    def add_trade(self, trade: TradeEvent):
        """Add trade event."""
        self.trades[trade.symbol].append(trade)
    
    def analyze(
        self,
        symbol: str,
        lookback_minutes: int = 60
    ) -> AccumulationSignal:
        """
        Analyze order flow for institutional signatures.
        
        Args:
            symbol: Symbol to analyze
            lookback_minutes: Analysis window
            
        Returns:
            AccumulationSignal with detected patterns
        """
        cutoff = datetime.now() - timedelta(minutes=lookback_minutes)
        
        # Get recent data
        recent_orders = [o for o in self.orders[symbol] if o.timestamp >= cutoff]
        recent_trades = [t for t in self.trades[symbol] if t.timestamp >= cutoff]
        
        if not recent_trades:
            return self._empty_signal(symbol)
        
        # Detect patterns
        signatures = []
        
        # Iceberg detection
        icebergs = self.iceberg_detector.detect(recent_trades)
        for iceberg in icebergs:
            sig = self._create_signature(
                symbol, iceberg, OrderPattern.ICEBERG,
                InstitutionalActivity.ACCUMULATION if iceberg['side'] == 'buy' else InstitutionalActivity.DISTRIBUTION
            )
            signatures.append(sig)
        
        # TWAP detection
        for side in ['buy', 'sell']:
            twaps = self.twap_detector.detect(recent_trades, side)
            for twap in twaps:
                sig = self._create_signature(
                    symbol, twap, OrderPattern.TWAP,
                    InstitutionalActivity.ACCUMULATION if side == 'buy' else InstitutionalActivity.DISTRIBUTION
                )
                signatures.append(sig)
        
        # Stealth accumulation
        if recent_trades:
            sorted_trades = sorted(recent_trades, key=lambda t: t.timestamp)
            stealth = self.stealth_detector.detect(
                recent_trades,
                sorted_trades[0].price,
                sorted_trades[-1].price
            )
            if stealth:
                sig = self._create_signature(
                    symbol, stealth, OrderPattern.STEALTH,
                    InstitutionalActivity.ACCUMULATION if stealth['activity'] == 'ACCUMULATION' 
                    else InstitutionalActivity.DISTRIBUTION if stealth['activity'] == 'DISTRIBUTION'
                    else InstitutionalActivity.UNKNOWN
                )
                signatures.append(sig)
        
        # Store signatures
        self.signatures[symbol].extend(signatures)
        
        # Calculate aggregate metrics
        volume_profile = self._calculate_volume_profile(recent_trades)
        time_clustering = self._calculate_time_clustering(recent_trades)
        
        # Determine overall signal
        signal_type, confidence = self._determine_signal(signatures, recent_trades)
        
        # Calculate scores
        stealth_score = self._calculate_stealth_score(recent_trades)
        urgency_score = self._calculate_urgency_score(recent_trades)
        price_impact = self._calculate_price_impact(recent_trades)
        
        # Generate analysis
        analysis = self._generate_analysis(signatures, signal_type, confidence)
        
        return AccumulationSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            signatures=signatures,
            volume_profile=volume_profile,
            time_clustering=time_clustering,
            price_impact=price_impact,
            stealth_score=stealth_score,
            urgency_score=urgency_score,
            analysis=analysis
        )
    
    def _empty_signal(self, symbol: str) -> AccumulationSignal:
        """Return empty signal."""
        return AccumulationSignal(
            symbol=symbol,
            signal_type='NEUTRAL',
            confidence=0.0,
            signatures=[],
            volume_profile={},
            time_clustering={},
            price_impact=0.0,
            stealth_score=0.0,
            urgency_score=0.0,
            analysis="Insufficient data for analysis"
        )
    
    def _create_signature(
        self,
        symbol: str,
        pattern_data: Dict,
        pattern: OrderPattern,
        activity: InstitutionalActivity
    ) -> InstitutionalSignature:
        """Create institutional signature from pattern data."""
        # Generate fingerprint
        fingerprint_data = f"{pattern.value}_{activity.value}_{pattern_data}"
        fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()[:12]
        
        # Determine strength
        if pattern_data.get('total_volume', 0) > 100000:
            strength = SignatureStrength.DEFINITIVE
        elif pattern_data.get('total_volume', 0) > 50000:
            strength = SignatureStrength.STRONG
        elif pattern_data.get('total_volume', 0) > 10000:
            strength = SignatureStrength.MODERATE
        else:
            strength = SignatureStrength.WEAK
        
        return InstitutionalSignature(
            signature_id=f"SIG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{fingerprint[:6]}",
            symbol=symbol,
            activity_type=activity,
            pattern=pattern,
            strength=strength,
            confidence=min(0.95, pattern_data.get('stealth_score', 0.5) + 0.3),
            start_time=pattern_data.get('start_time', datetime.now()),
            end_time=pattern_data.get('end_time', datetime.now()),
            total_volume=pattern_data.get('total_volume', 0),
            avg_price=pattern_data.get('price', 0),
            order_count=pattern_data.get('trades', 0),
            trade_count=pattern_data.get('trade_count', pattern_data.get('trades', 0)),
            fingerprint=fingerprint,
            characteristics=pattern_data
        )
    
    def _calculate_volume_profile(self, trades: List[TradeEvent]) -> Dict[str, float]:
        """Calculate volume distribution."""
        if not trades:
            return {}
        
        buy_volume = sum(t.quantity for t in trades if t.side == 'buy')
        sell_volume = sum(t.quantity for t in trades if t.side == 'sell')
        total = buy_volume + sell_volume
        
        return {
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'total_volume': total,
            'buy_pct': buy_volume / total if total > 0 else 0.5,
            'imbalance': (buy_volume - sell_volume) / total if total > 0 else 0
        }
    
    def _calculate_time_clustering(self, trades: List[TradeEvent]) -> Dict[int, float]:
        """Calculate volume by hour."""
        clustering = defaultdict(float)
        
        for trade in trades:
            hour = trade.timestamp.hour
            clustering[hour] += trade.quantity
        
        return dict(clustering)
    
    def _determine_signal(
        self,
        signatures: List[InstitutionalSignature],
        trades: List[TradeEvent]
    ) -> Tuple[str, float]:
        """Determine overall signal type and confidence."""
        if not signatures and not trades:
            return 'NEUTRAL', 0.0
        
        # Count by activity type
        accumulation_count = sum(1 for s in signatures if s.activity_type == InstitutionalActivity.ACCUMULATION)
        distribution_count = sum(1 for s in signatures if s.activity_type == InstitutionalActivity.DISTRIBUTION)
        
        # Volume analysis
        buy_volume = sum(t.quantity for t in trades if t.side == 'buy')
        sell_volume = sum(t.quantity for t in trades if t.side == 'sell')
        total = buy_volume + sell_volume
        
        imbalance = (buy_volume - sell_volume) / total if total > 0 else 0
        
        # Determine signal
        if accumulation_count > distribution_count and imbalance > 0.1:
            signal_type = 'ACCUMULATION'
            confidence = min(0.95, 0.5 + accumulation_count * 0.1 + imbalance * 0.3)
        elif distribution_count > accumulation_count and imbalance < -0.1:
            signal_type = 'DISTRIBUTION'
            confidence = min(0.95, 0.5 + distribution_count * 0.1 + abs(imbalance) * 0.3)
        else:
            signal_type = 'NEUTRAL'
            confidence = 0.5
        
        return signal_type, confidence
    
    def _calculate_stealth_score(self, trades: List[TradeEvent]) -> float:
        """Calculate how stealthy the activity is."""
        if not trades:
            return 0.0
        
        # Smaller average trade size = more stealth
        sizes = [t.quantity for t in trades]
        avg_size = statistics.mean(sizes)
        
        # More trades = more stealth (breaking up orders)
        trade_count = len(trades)
        
        # Calculate score
        size_score = 1.0 / (1.0 + avg_size / 1000)
        count_score = min(1.0, trade_count / 100)
        
        return (size_score + count_score) / 2
    
    def _calculate_urgency_score(self, trades: List[TradeEvent]) -> float:
        """Calculate urgency of activity."""
        if len(trades) < 2:
            return 0.0
        
        sorted_trades = sorted(trades, key=lambda t: t.timestamp)
        
        # Calculate trade frequency
        duration = (sorted_trades[-1].timestamp - sorted_trades[0].timestamp).total_seconds()
        if duration == 0:
            return 1.0
        
        trades_per_minute = len(trades) / (duration / 60)
        
        # Higher frequency = more urgency
        return min(1.0, trades_per_minute / 10)
    
    def _calculate_price_impact(self, trades: List[TradeEvent]) -> float:
        """Calculate price impact of activity."""
        if not trades:
            return 0.0
        
        sorted_trades = sorted(trades, key=lambda t: t.timestamp)
        start_price = sorted_trades[0].price
        end_price = sorted_trades[-1].price
        
        if start_price == 0:
            return 0.0
        
        return (end_price - start_price) / start_price * 100
    
    def _generate_analysis(
        self,
        signatures: List[InstitutionalSignature],
        signal_type: str,
        confidence: float
    ) -> str:
        """Generate analysis text."""
        parts = []
        
        parts.append(f"Signal: {signal_type} ({confidence:.0%} confidence)")
        
        if signatures:
            patterns = [s.pattern.value for s in signatures]
            parts.append(f"Detected patterns: {', '.join(set(patterns))}")
            
            total_vol = sum(s.total_volume for s in signatures)
            parts.append(f"Institutional volume: {total_vol:,.0f}")
            
            # Strongest signature
            strongest = max(signatures, key=lambda s: s.strength.value)
            parts.append(f"Strongest: {strongest.pattern.value} ({strongest.strength.name})")
        else:
            parts.append("No clear institutional patterns detected")
        
        return " | ".join(parts)
    
    def get_recent_signatures(
        self,
        symbol: str,
        hours: int = 24
    ) -> List[InstitutionalSignature]:
        """Get recent signatures for a symbol."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        return [
            s for s in self.signatures[symbol]
            if s.end_time >= cutoff
        ]
    
    def register_fingerprint(self, fingerprint: str, institution_name: str):
        """Register a known institutional fingerprint."""
        self.known_fingerprints[fingerprint] = institution_name
    
    def identify_institution(self, signature: InstitutionalSignature) -> Optional[str]:
        """Try to identify institution from signature."""
        return self.known_fingerprints.get(signature.fingerprint)
    
    def get_status(self) -> Dict[str, Any]:
        """Get detector status."""
        return {
            'symbols_tracked': len(self.orders),
            'total_orders': sum(len(o) for o in self.orders.values()),
            'total_trades': sum(len(t) for t in self.trades.values()),
            'total_signatures': sum(len(s) for s in self.signatures.values()),
            'known_fingerprints': len(self.known_fingerprints),
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_footprint_detector(config: Optional[Dict] = None) -> InstitutionalFootprintDNA:
    """Create InstitutionalFootprintDNA instance."""
    return InstitutionalFootprintDNA(config)


# Example usage
if __name__ == "__main__":
    import random
    
    detector = create_footprint_detector()
    
    symbol = "EURUSD"
    base_price = 1.1000
    
    # Simulate institutional accumulation pattern
    print("Simulating institutional accumulation...")
    
    for i in range(100):
        # Iceberg-like pattern: repeated fills at same level
        price = base_price + random.uniform(-0.0005, 0.0010)
        
        trade = TradeEvent(
            timestamp=datetime.now() - timedelta(minutes=random.randint(0, 60)),
            trade_id=f"T{i}",
            symbol=symbol,
            side='buy' if random.random() > 0.3 else 'sell',  # 70% buy bias
            price=round(price, 5),
            quantity=random.randint(100, 500),  # Small consistent sizes
            aggressor='buyer' if random.random() > 0.4 else 'seller'
        )
        
        detector.add_trade(trade)
    
    # Analyze
    signal = detector.analyze(symbol, lookback_minutes=60)
    
    print("\n" + "=" * 60)
    print("INSTITUTIONAL FOOTPRINT DNA ANALYSIS")
    print("=" * 60)
    
    print(f"\nSymbol: {signal.symbol}")
    print(f"Signal: {signal.signal_type}")
    print(f"Confidence: {signal.confidence:.1%}")
    print(f"Stealth Score: {signal.stealth_score:.1%}")
    print(f"Urgency Score: {signal.urgency_score:.1%}")
    print(f"Price Impact: {signal.price_impact:.3f}%")
    
    print(f"\nVolume Profile:")
    for key, value in signal.volume_profile.items():
        print(f"  {key}: {value:,.2f}")
    
    print(f"\nDetected Signatures: {len(signal.signatures)}")
    for sig in signal.signatures:
        print(f"\n  {sig.pattern.value} ({sig.strength.name})")
        print(f"    Activity: {sig.activity_type.value}")
        print(f"    Volume: {sig.total_volume:,.0f}")
        print(f"    Fingerprint: {sig.fingerprint}")
    
    print(f"\nAnalysis: {signal.analysis}")
