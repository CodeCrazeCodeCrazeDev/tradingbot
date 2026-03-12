"""
Dark Pool Monitor

Monitors dark pool and off-exchange trading activity:
- FINRA ATS data analysis
- Dark pool print detection
- Block trade identification
- Institutional accumulation/distribution signals
- Hidden liquidity detection
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class DarkPoolVenue(Enum):
    """Dark pool venues."""
    SIGMA_X = "sigma_x"  # Goldman Sachs
    CROSSFINDER = "crossfinder"  # Credit Suisse
    LEVEL_ATS = "level_ats"  # Level ATS
    MS_POOL = "ms_pool"  # Morgan Stanley
    UBS_ATS = "ubs_ats"  # UBS
    INSTINET = "instinet"  # Nomura
    LIQUIDNET = "liquidnet"  # Liquidnet
    IEX = "iex"  # IEX (lit but with speed bumps)
    UNKNOWN = "unknown"


class PrintType(Enum):
    """Types of dark pool prints."""
    BLOCK = "block"  # Large block trade
    SWEEP = "sweep"  # Multi-venue sweep
    REGULAR = "regular"  # Regular dark pool print
    OPENING = "opening"  # Opening print
    CLOSING = "closing"  # Closing print


class SignalType(Enum):
    """Dark pool signal types."""
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    NEUTRAL = "neutral"
    BLOCK_BUY = "block_buy"
    BLOCK_SELL = "block_sell"


@dataclass
class DarkPoolPrint:
    """Represents a dark pool trade print."""
    timestamp: datetime
    symbol: str
    price: float
    size: int
    venue: DarkPoolVenue
    print_type: PrintType
    condition: str = ""  # Trade condition codes
    
    @property
    def notional_value(self) -> float:
        return self.price * self.size
    
    @property
    def is_block(self) -> bool:
        return self.size >= 10000 or self.notional_value >= 200000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'price': self.price,
            'size': self.size,
            'venue': self.venue.value,
            'print_type': self.print_type.value,
            'notional_value': self.notional_value,
            'is_block': self.is_block
        }


@dataclass
class DarkPoolLevel:
    """Represents a price level with dark pool activity."""
    price: float
    total_volume: int
    buy_volume: int
    sell_volume: int
    print_count: int
    avg_size: float
    
    @property
    def buy_ratio(self) -> float:
        try:
            if self.total_volume > 0:
                return self.buy_volume / self.total_volume
            return 0.5
        except Exception as e:
            logger.error(f"Error in buy_ratio: {e}")
            raise
    
    @property
    def is_accumulation_level(self) -> bool:
        return self.buy_ratio > 0.6 and self.total_volume > 50000
    
    @property
    def is_distribution_level(self) -> bool:
        return self.buy_ratio < 0.4 and self.total_volume > 50000


@dataclass
class DarkPoolSignal:
    """Dark pool trading signal."""
    symbol: str
    signal_type: SignalType
    confidence: float
    dark_pool_volume: int
    dark_pool_pct: float  # % of total volume
    block_count: int
    block_volume: int
    net_dark_flow: float  # Positive = buying, Negative = selling
    key_levels: List[DarkPoolLevel]
    venue_breakdown: Dict[str, int]
    analysis: str
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'dark_pool_volume': self.dark_pool_volume,
            'dark_pool_pct': self.dark_pool_pct,
            'block_count': self.block_count,
            'block_volume': self.block_volume,
            'net_dark_flow': self.net_dark_flow,
            'key_levels': [
                {'price': l.price, 'volume': l.total_volume, 'buy_ratio': l.buy_ratio}
                for l in self.key_levels
            ],
            'venue_breakdown': self.venue_breakdown,
            'analysis': self.analysis,
            'generated_at': self.generated_at.isoformat()
        }


class DarkPoolPrintClassifier:
    """
    Classifies dark pool prints as buys or sells.
    
    Uses multiple heuristics:
    - Price relative to NBBO
    - Trade condition codes
    - Time and sales context
    - Size patterns
    """
    
    def __init__(self):
        try:
            self.nbbo_cache: Dict[str, Tuple[float, float]] = {}  # symbol -> (bid, ask)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_nbbo(self, symbol: str, bid: float, ask: float):
        """Update NBBO for a symbol."""
        try:
            self.nbbo_cache[symbol] = (bid, ask)
        except Exception as e:
            logger.error(f"Error in update_nbbo: {e}")
            raise
    
    def classify(self, print_data: DarkPoolPrint) -> str:
        """
        Classify print as buy or sell.
        
        Returns:
            'buy', 'sell', or 'unknown'
        """
        try:
            if print_data.symbol not in self.nbbo_cache:
                return 'unknown'
        
            bid, ask = self.nbbo_cache[print_data.symbol]
            mid = (bid + ask) / 2
        
            # Price-based classification
            if print_data.price >= ask:
                return 'buy'  # Lifted the offer
            elif print_data.price <= bid:
                return 'sell'  # Hit the bid
            elif print_data.price > mid:
                return 'buy'  # Above mid, likely buy
            elif print_data.price < mid:
                return 'sell'  # Below mid, likely sell
        
            # At mid - use size heuristics
            if print_data.is_block:
                # Large blocks at mid are often institutional buys
                return 'buy'
        
            return 'unknown'
        except Exception as e:
            logger.error(f"Error in classify: {e}")
            raise


class BlockTradeDetector:
    """
    Detects and analyzes block trades.
    
    Block trade criteria:
    - Size >= 10,000 shares
    - Notional >= $200,000
    - Or significantly larger than average
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_block_shares = self.config.get('min_block_shares', 10000)
            self.min_block_notional = self.config.get('min_block_notional', 200000)
            self.size_multiplier = self.config.get('size_multiplier', 5.0)
        
            # Track average sizes
            self.avg_sizes: Dict[str, float] = defaultdict(lambda: 500)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_average(self, symbol: str, size: int):
        """Update running average size."""
        try:
            current = self.avg_sizes[symbol]
            self.avg_sizes[symbol] = current * 0.99 + size * 0.01
        except Exception as e:
            logger.error(f"Error in update_average: {e}")
            raise
    
    def is_block(self, print_data: DarkPoolPrint) -> bool:
        """Check if print is a block trade."""
        # Standard block criteria
        try:
            if print_data.size >= self.min_block_shares:
                return True
            if print_data.notional_value >= self.min_block_notional:
                return True
        
            # Relative size criteria
            avg = self.avg_sizes[print_data.symbol]
            if print_data.size >= avg * self.size_multiplier:
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in is_block: {e}")
            raise
    
    def analyze_block(self, print_data: DarkPoolPrint, side: str) -> Dict[str, Any]:
        """Analyze a block trade."""
        return {
            'timestamp': print_data.timestamp.isoformat(),
            'symbol': print_data.symbol,
            'size': print_data.size,
            'price': print_data.price,
            'notional': print_data.notional_value,
            'side': side,
            'venue': print_data.venue.value,
            'relative_size': print_data.size / self.avg_sizes[print_data.symbol],
            'significance': 'HIGH' if print_data.notional_value > 1000000 else 'MEDIUM'
        }


class AccumulationDistributionAnalyzer:
    """
    Analyzes dark pool flow for accumulation/distribution patterns.
    """
    
    def __init__(self, lookback_periods: int = 20):
        try:
            self.lookback_periods = lookback_periods
            self.flow_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_flow(self, symbol: str, net_flow: float, timestamp: Optional[datetime] = None):
        """Add net flow reading."""
        try:
            if timestamp is None:
                timestamp = datetime.now()
        
            self.flow_history[symbol].append((timestamp, net_flow))
        
            # Keep limited history
            if len(self.flow_history[symbol]) > self.lookback_periods * 10:
                self.flow_history[symbol] = self.flow_history[symbol][-self.lookback_periods * 10:]
        except Exception as e:
            logger.error(f"Error in add_flow: {e}")
            raise
    
    def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze accumulation/distribution pattern.
        
        Returns:
            Analysis dict with pattern and confidence
        """
        try:
            history = self.flow_history.get(symbol, [])
        
            if len(history) < 5:
                return {
                    'pattern': 'INSUFFICIENT_DATA',
                    'confidence': 0.0,
                    'trend': 'NEUTRAL'
                }
        
            flows = [f for _, f in history[-self.lookback_periods:]]
        
            # Calculate metrics
            total_flow = sum(flows)
            positive_periods = sum(1 for f in flows if f > 0)
            negative_periods = sum(1 for f in flows if f < 0)
        
            # Trend analysis
            if len(flows) >= 5:
                recent = flows[-5:]
                older = flows[-10:-5] if len(flows) >= 10 else flows[:5]
            
                recent_avg = statistics.mean(recent)
                older_avg = statistics.mean(older) if older else 0
            
                trend_strength = (recent_avg - older_avg) / (abs(older_avg) + 1)
            else:
                trend_strength = 0
        
            # Determine pattern
            if total_flow > 0 and positive_periods > negative_periods * 1.5:
                pattern = 'ACCUMULATION'
                confidence = min(1.0, positive_periods / len(flows))
            elif total_flow < 0 and negative_periods > positive_periods * 1.5:
                pattern = 'DISTRIBUTION'
                confidence = min(1.0, negative_periods / len(flows))
            else:
                pattern = 'NEUTRAL'
                confidence = 0.5
        
            # Trend direction
            if trend_strength > 0.1:
                trend = 'INCREASING_ACCUMULATION'
            elif trend_strength < -0.1:
                trend = 'INCREASING_DISTRIBUTION'
            else:
                trend = 'STABLE'
        
            return {
                'pattern': pattern,
                'confidence': confidence,
                'trend': trend,
                'total_flow': total_flow,
                'positive_periods': positive_periods,
                'negative_periods': negative_periods,
                'trend_strength': trend_strength
            }
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class DarkPoolMonitor:
    """
    Complete dark pool monitoring system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            self.classifier = DarkPoolPrintClassifier()
            self.block_detector = BlockTradeDetector(config)
            self.ad_analyzer = AccumulationDistributionAnalyzer()
        
            # Storage
            self.prints: Dict[str, List[DarkPoolPrint]] = defaultdict(list)
            self.classified_prints: Dict[str, List[Tuple[DarkPoolPrint, str]]] = defaultdict(list)
            self.blocks: Dict[str, List[Dict]] = defaultdict(list)
        
            # Aggregated data
            self.volume_by_level: Dict[str, Dict[float, DarkPoolLevel]] = defaultdict(dict)
            self.venue_volume: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
            logger.info("DarkPoolMonitor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_quote(self, symbol: str, bid: float, ask: float):
        """Update NBBO quote for classification."""
        try:
            self.classifier.update_nbbo(symbol, bid, ask)
        except Exception as e:
            logger.error(f"Error in update_quote: {e}")
            raise
    
    def process_print(self, print_data: DarkPoolPrint):
        """
        Process a dark pool print.
        
        Args:
            print_data: Dark pool print to process
        """
        try:
            symbol = print_data.symbol
        
            # Store print
            self.prints[symbol].append(print_data)
        
            # Classify
            side = self.classifier.classify(print_data)
            self.classified_prints[symbol].append((print_data, side))
        
            # Update average size
            self.block_detector.update_average(symbol, print_data.size)
        
            # Check for block
            if self.block_detector.is_block(print_data):
                block_analysis = self.block_detector.analyze_block(print_data, side)
                self.blocks[symbol].append(block_analysis)
        
            # Update volume by level
            price_level = round(print_data.price, 2)
            if price_level not in self.volume_by_level[symbol]:
                self.volume_by_level[symbol][price_level] = DarkPoolLevel(
                    price=price_level,
                    total_volume=0,
                    buy_volume=0,
                    sell_volume=0,
                    print_count=0,
                    avg_size=0
                )
        
            level = self.volume_by_level[symbol][price_level]
            level.total_volume += print_data.size
            level.print_count += 1
            level.avg_size = level.total_volume / level.print_count
        
            if side == 'buy':
                level.buy_volume += print_data.size
            elif side == 'sell':
                level.sell_volume += print_data.size
        
            # Update venue volume
            self.venue_volume[symbol][print_data.venue.value] += print_data.size
        
            # Update accumulation/distribution
            flow = print_data.size if side == 'buy' else -print_data.size if side == 'sell' else 0
            self.ad_analyzer.add_flow(symbol, flow, print_data.timestamp)
        
            # Cleanup old data
            self._cleanup_old_data(symbol)
        except Exception as e:
            logger.error(f"Error in process_print: {e}")
            raise
    
    def _cleanup_old_data(self, symbol: str, max_age_hours: int = 24):
        """Remove old data."""
        try:
            cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
            self.prints[symbol] = [p for p in self.prints[symbol] if p.timestamp >= cutoff]
            self.classified_prints[symbol] = [
                (p, s) for p, s in self.classified_prints[symbol] if p.timestamp >= cutoff
            ]
            self.blocks[symbol] = [
                b for b in self.blocks[symbol] 
                if datetime.fromisoformat(b['timestamp']) >= cutoff
            ]
        except Exception as e:
            logger.error(f"Error in _cleanup_old_data: {e}")
            raise
    
    def generate_signal(self, symbol: str, total_market_volume: int = 0) -> DarkPoolSignal:
        """
        Generate dark pool signal for a symbol.
        
        Args:
            symbol: Stock symbol
            total_market_volume: Total market volume for % calculation
            
        Returns:
            DarkPoolSignal with analysis
        """
        try:
            prints = self.prints.get(symbol, [])
            classified = self.classified_prints.get(symbol, [])
            blocks = self.blocks.get(symbol, [])
        
            if not prints:
                return DarkPoolSignal(
                    symbol=symbol,
                    signal_type=SignalType.NEUTRAL,
                    confidence=0.0,
                    dark_pool_volume=0,
                    dark_pool_pct=0.0,
                    block_count=0,
                    block_volume=0,
                    net_dark_flow=0.0,
                    key_levels=[],
                    venue_breakdown={},
                    analysis="No dark pool data available"
                )
        
            # Calculate volumes
            dark_pool_volume = sum(p.size for p in prints)
            dark_pool_pct = dark_pool_volume / total_market_volume if total_market_volume > 0 else 0
        
            # Block analysis
            block_count = len(blocks)
            block_volume = sum(b['size'] for b in blocks)
        
            # Net flow
            buy_volume = sum(p.size for p, s in classified if s == 'buy')
            sell_volume = sum(p.size for p, s in classified if s == 'sell')
            net_dark_flow = buy_volume - sell_volume
        
            # Key levels
            levels = list(self.volume_by_level.get(symbol, {}).values())
            key_levels = sorted(levels, key=lambda x: x.total_volume, reverse=True)[:5]
        
            # Venue breakdown
            venue_breakdown = dict(self.venue_volume.get(symbol, {}))
        
            # Accumulation/Distribution analysis
            ad_analysis = self.ad_analyzer.analyze(symbol)
        
            # Determine signal
            signal_type, confidence = self._determine_signal(
                net_dark_flow, dark_pool_volume, block_count, blocks, ad_analysis
            )
        
            # Generate analysis text
            analysis = self._generate_analysis(
                dark_pool_volume, dark_pool_pct, block_count, net_dark_flow, ad_analysis
            )
        
            return DarkPoolSignal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                dark_pool_volume=dark_pool_volume,
                dark_pool_pct=dark_pool_pct,
                block_count=block_count,
                block_volume=block_volume,
                net_dark_flow=net_dark_flow,
                key_levels=key_levels,
                venue_breakdown=venue_breakdown,
                analysis=analysis
            )
        except Exception as e:
            logger.error(f"Error in generate_signal: {e}")
            raise
    
    def _determine_signal(
        self,
        net_flow: float,
        total_volume: int,
        block_count: int,
        blocks: List[Dict],
        ad_analysis: Dict
    ) -> Tuple[SignalType, float]:
        """Determine signal type and confidence."""
        try:
            confidence = 0.5
        
            # Flow-based signal
            if total_volume > 0:
                flow_ratio = net_flow / total_volume
            
                if flow_ratio > 0.2:
                    signal_type = SignalType.ACCUMULATION
                    confidence = min(1.0, 0.5 + flow_ratio)
                elif flow_ratio < -0.2:
                    signal_type = SignalType.DISTRIBUTION
                    confidence = min(1.0, 0.5 + abs(flow_ratio))
                else:
                    signal_type = SignalType.NEUTRAL
                    confidence = 0.5
            else:
                signal_type = SignalType.NEUTRAL
        
            # Block trade signals
            if blocks:
                buy_blocks = [b for b in blocks if b['side'] == 'buy']
                sell_blocks = [b for b in blocks if b['side'] == 'sell']
            
                if len(buy_blocks) > len(sell_blocks) * 2:
                    signal_type = SignalType.BLOCK_BUY
                    confidence = min(1.0, confidence + 0.2)
                elif len(sell_blocks) > len(buy_blocks) * 2:
                    signal_type = SignalType.BLOCK_SELL
                    confidence = min(1.0, confidence + 0.2)
        
            # Adjust based on A/D analysis
            if ad_analysis['pattern'] == 'ACCUMULATION':
                if signal_type in [SignalType.ACCUMULATION, SignalType.BLOCK_BUY]:
                    confidence = min(1.0, confidence + 0.1)
            elif ad_analysis['pattern'] == 'DISTRIBUTION':
                if signal_type in [SignalType.DISTRIBUTION, SignalType.BLOCK_SELL]:
                    confidence = min(1.0, confidence + 0.1)
        
            return signal_type, confidence
        except Exception as e:
            logger.error(f"Error in _determine_signal: {e}")
            raise
    
    def _generate_analysis(
        self,
        volume: int,
        pct: float,
        block_count: int,
        net_flow: float,
        ad_analysis: Dict
    ) -> str:
        """Generate analysis text."""
        try:
            parts = []
        
            parts.append(f"Dark pool volume: {volume:,} shares ({pct:.1%} of total)")
        
            if block_count > 0:
                parts.append(f"Block trades: {block_count}")
        
            if net_flow > 0:
                parts.append(f"Net buying: {net_flow:,.0f} shares")
            elif net_flow < 0:
                parts.append(f"Net selling: {abs(net_flow):,.0f} shares")
        
            parts.append(f"Pattern: {ad_analysis['pattern']} ({ad_analysis['confidence']:.0%} confidence)")
        
            return " | ".join(parts)
        except Exception as e:
            logger.error(f"Error in _generate_analysis: {e}")
            raise
    
    def get_recent_blocks(self, symbol: str, hours: int = 1) -> List[Dict]:
        """Get recent block trades."""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
        
            return [
                b for b in self.blocks.get(symbol, [])
                if datetime.fromisoformat(b['timestamp']) >= cutoff
            ]
        except Exception as e:
            logger.error(f"Error in get_recent_blocks: {e}")
            raise
    
    def get_key_levels(self, symbol: str, top_n: int = 5) -> List[DarkPoolLevel]:
        """Get key dark pool levels by volume."""
        try:
            levels = list(self.volume_by_level.get(symbol, {}).values())
            return sorted(levels, key=lambda x: x.total_volume, reverse=True)[:top_n]
        except Exception as e:
            logger.error(f"Error in get_key_levels: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitor status."""
        return {
            'symbols_tracked': len(self.prints),
            'total_prints': sum(len(p) for p in self.prints.values()),
            'total_blocks': sum(len(b) for b in self.blocks.values()),
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_dark_pool_monitor(config: Optional[Dict] = None) -> DarkPoolMonitor:
    """Create DarkPoolMonitor instance."""
    return DarkPoolMonitor(config)


# Example usage
if __name__ == "__main__":
    monitor = create_dark_pool_monitor()
    
    # Update quote
    monitor.update_quote("AAPL", 149.95, 150.05)
    
    # Simulate some dark pool prints
    import random
    
    for i in range(50):
        price = 150.0 + random.uniform(-0.5, 0.5)
        size = random.choice([100, 500, 1000, 5000, 10000, 25000])
        venue = random.choice(list(DarkPoolVenue))
        
        print_data = DarkPoolPrint(
            timestamp=datetime.now() - timedelta(minutes=random.randint(0, 60)),
            symbol="AAPL",
            price=price,
            size=size,
            venue=venue,
            print_type=PrintType.BLOCK if size >= 10000 else PrintType.REGULAR
        )
        
        monitor.process_print(print_data)
    
    # Generate signal
    signal = monitor.generate_signal("AAPL", total_market_volume=1000000)
    
    print("=" * 60)
    print("DARK POOL ANALYSIS")
    print("=" * 60)
    print(f"\nSymbol: {signal.symbol}")
    print(f"Signal: {signal.signal_type.value}")
    print(f"Confidence: {signal.confidence:.1%}")
    print(f"\nDark Pool Volume: {signal.dark_pool_volume:,}")
    print(f"Dark Pool %: {signal.dark_pool_pct:.1%}")
    print(f"Block Count: {signal.block_count}")
    print(f"Net Flow: {signal.net_dark_flow:,.0f}")
    
    print(f"\nKey Levels:")
    for level in signal.key_levels:
        print(f"  ${level.price:.2f}: {level.total_volume:,} shares (Buy: {level.buy_ratio:.0%})")
    
    print(f"\nVenue Breakdown:")
    for venue, vol in signal.venue_breakdown.items():
        print(f"  {venue}: {vol:,}")
    
    print(f"\nAnalysis: {signal.analysis}")
