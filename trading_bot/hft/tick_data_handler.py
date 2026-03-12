"""
High-Frequency Trading Components
==================================

Comprehensive HFT infrastructure:
- Tick data handler (microsecond processing)
- Order book imbalance signals
- Latency optimizer
- Market making engine
- Statistical arbitrage
- Pairs trading engine
- Mean reversion scalper
- Momentum ignition detector

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple
from enum import Enum, auto
from collections import deque, defaultdict
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import numpy

logger = logging.getLogger(__name__)


class TickType(Enum):
    """Tick types"""
    TRADE = "trade"
    BID = "bid"
    ASK = "ask"
    BID_SIZE = "bid_size"
    ASK_SIZE = "ask_size"
    LAST_SIZE = "last_size"


class SignalStrength(Enum):
    """Signal strength"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    NEUTRAL = "neutral"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class Tick:
    """Single tick data"""
    symbol: str
    timestamp: datetime
    timestamp_ns: int  # Nanosecond precision
    tick_type: TickType
    price: float
    size: float
    exchange: str = ""
    conditions: List[str] = field(default_factory=list)
    
    @property
    def timestamp_us(self) -> int:
        """Microsecond timestamp"""
        return self.timestamp_ns // 1000


@dataclass
class OrderBookLevel:
    """Single order book level"""
    price: float
    size: float
    order_count: int = 0


@dataclass
class OrderBook:
    """Order book snapshot"""
    symbol: str
    timestamp: datetime
    timestamp_ns: int
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    
    @property
    def best_bid(self) -> Optional[OrderBookLevel]:
        return self.bids[0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[OrderBookLevel]:
        return self.asks[0] if self.asks else None
    
    @property
    def mid_price(self) -> float:
        if self.best_bid and self.best_ask:
            return (self.best_bid.price + self.best_ask.price) / 2
        return 0.0
    
    @property
    def spread(self) -> float:
        if self.best_bid and self.best_ask:
            return self.best_ask.price - self.best_bid.price
        return 0.0
    
    @property
    def spread_bps(self) -> float:
        if self.mid_price > 0:
            return (self.spread / self.mid_price) * 10000
        return 0.0


@dataclass
class ImbalanceSignal:
    """Order book imbalance signal"""
    symbol: str
    timestamp: datetime
    
    # Imbalance metrics
    bid_size: float
    ask_size: float
    imbalance_ratio: float  # (bid - ask) / (bid + ask)
    
    # Signal
    signal: SignalStrength
    confidence: float
    
    # Price levels
    bid_pressure_levels: int
    ask_pressure_levels: int
    
    # Predicted direction
    predicted_direction: str  # "up", "down", "neutral"
    predicted_magnitude: float


@dataclass
class LatencyMetrics:
    """Latency metrics"""
    timestamp: datetime
    
    # Network latency
    network_latency_us: float
    
    # Processing latency
    tick_processing_us: float
    signal_generation_us: float
    order_preparation_us: float
    
    # Total
    total_latency_us: float
    
    # Percentiles
    p50_us: float = 0.0
    p95_us: float = 0.0
    p99_us: float = 0.0


class TickDataHandler:
    """
    High-performance tick data handler
    Processes ticks with microsecond precision
    """
    
    def __init__(
        self,
        buffer_size: int = 100000,
        processing_threads: int = 4
    ):
        self.buffer_size = buffer_size
        
        # Tick buffers per symbol
        self.tick_buffers: Dict[str, Deque[Tick]] = defaultdict(
            lambda: deque(maxlen=buffer_size)
        )
        
        # Aggregated data
        self.vwap: Dict[str, float] = {}
        self.twap: Dict[str, float] = {}
        self.volume: Dict[str, float] = defaultdict(float)
        
        # Processing
        self.executor = ThreadPoolExecutor(max_workers=processing_threads)
        
        # Callbacks
        self.on_tick: List[Callable] = []
        self.on_trade: List[Callable] = []
        self.on_quote: List[Callable] = []
        
        # Statistics
        self.stats = {
            'ticks_processed': 0,
            'avg_processing_time_us': 0.0,
            'max_processing_time_us': 0.0
        }
        
        self._lock = threading.RLock()
        
        logger.info("TickDataHandler initialized")
    
    def process_tick(self, tick: Tick):
        """Process a single tick"""
        start_ns = time.perf_counter_ns()
        
        with self._lock:
            # Store tick
            self.tick_buffers[tick.symbol].append(tick)
            
            # Update aggregates
            if tick.tick_type == TickType.TRADE:
                self._update_vwap(tick)
                self._update_twap(tick)
                self.volume[tick.symbol] += tick.size
        
        # Fire callbacks
        for callback in self.on_tick:
            try:
                callback(tick)
            except Exception as e:
                logger.error(f"Tick callback error: {e}")
        
        if tick.tick_type == TickType.TRADE:
            for callback in self.on_trade:
                try:
                    callback(tick)
                except Exception as e:
                    logger.error(f"Trade callback error: {e}")
        elif tick.tick_type in [TickType.BID, TickType.ASK]:
            for callback in self.on_quote:
                try:
                    callback(tick)
                except Exception as e:
                    logger.error(f"Quote callback error: {e}")
        
        # Update stats
        processing_time_us = (time.perf_counter_ns() - start_ns) / 1000
        self.stats['ticks_processed'] += 1
        self.stats['avg_processing_time_us'] = (
            (self.stats['avg_processing_time_us'] * (self.stats['ticks_processed'] - 1) + processing_time_us)
            / self.stats['ticks_processed']
        )
        self.stats['max_processing_time_us'] = max(
            self.stats['max_processing_time_us'],
            processing_time_us
        )
    
    def process_ticks_batch(self, ticks: List[Tick]):
        """Process multiple ticks in batch"""
        for tick in ticks:
            self.process_tick(tick)
    
    def _update_vwap(self, tick: Tick):
        """Update VWAP"""
        symbol = tick.symbol
        buffer = self.tick_buffers[symbol]
        
        trades = [t for t in buffer if t.tick_type == TickType.TRADE]
        if trades:
            total_value = sum(t.price * t.size for t in trades)
            total_volume = sum(t.size for t in trades)
            self.vwap[symbol] = total_value / total_volume if total_volume > 0 else 0
    
    def _update_twap(self, tick: Tick):
        """Update TWAP"""
        symbol = tick.symbol
        buffer = self.tick_buffers[symbol]
        
        trades = [t for t in buffer if t.tick_type == TickType.TRADE]
        if trades:
            self.twap[symbol] = np.mean([t.price for t in trades])
    
    def get_recent_ticks(
        self,
        symbol: str,
        count: int = 100,
        tick_type: Optional[TickType] = None
    ) -> List[Tick]:
        """Get recent ticks"""
        with self._lock:
            buffer = list(self.tick_buffers.get(symbol, []))
            
            if tick_type:
                buffer = [t for t in buffer if t.tick_type == tick_type]
            
            return buffer[-count:]
    
    def get_vwap(self, symbol: str) -> float:
        """Get current VWAP"""
        return self.vwap.get(symbol, 0.0)
    
    def get_twap(self, symbol: str) -> float:
        """Get current TWAP"""
        return self.twap.get(symbol, 0.0)
    
    def get_volume(self, symbol: str) -> float:
        """Get cumulative volume"""
        return self.volume.get(symbol, 0.0)
    
    def get_tick_stats(self, symbol: str) -> Dict[str, Any]:
        """Get tick statistics"""
        with self._lock:
            buffer = list(self.tick_buffers.get(symbol, []))
            
            if not buffer:
                return {}
            
            trades = [t for t in buffer if t.tick_type == TickType.TRADE]
            
            if not trades:
                return {}
            
            prices = [t.price for t in trades]
            sizes = [t.size for t in trades]
            
            return {
                'tick_count': len(buffer),
                'trade_count': len(trades),
                'vwap': self.vwap.get(symbol, 0),
                'twap': self.twap.get(symbol, 0),
                'volume': self.volume.get(symbol, 0),
                'price_high': max(prices),
                'price_low': min(prices),
                'price_last': prices[-1],
                'avg_trade_size': np.mean(sizes),
                'price_volatility': np.std(prices)
            }


class OrderBookImbalanceDetector:
    """
    Detects order book imbalances for trading signals
    """
    
    def __init__(
        self,
        imbalance_threshold: float = 0.3,
        levels_to_analyze: int = 5
    ):
        self.imbalance_threshold = imbalance_threshold
        self.levels_to_analyze = levels_to_analyze
        
        # Order book cache
        self.order_books: Dict[str, OrderBook] = {}
        
        # Signal history
        self.signal_history: Dict[str, Deque[ImbalanceSignal]] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        # Callbacks
        self.on_signal: List[Callable] = []
        
        self._lock = threading.RLock()
        
        logger.info("OrderBookImbalanceDetector initialized")
    
    def update_order_book(self, order_book: OrderBook) -> Optional[ImbalanceSignal]:
        """Update order book and check for imbalance"""
        with self._lock:
            self.order_books[order_book.symbol] = order_book
        
        return self.analyze(order_book)
    
    def analyze(self, order_book: OrderBook) -> Optional[ImbalanceSignal]:
        """Analyze order book for imbalance"""
        if not order_book.bids or not order_book.asks:
            return None
        
        # Calculate size at each level
        bid_sizes = [level.size for level in order_book.bids[:self.levels_to_analyze]]
        ask_sizes = [level.size for level in order_book.asks[:self.levels_to_analyze]]
        
        total_bid = sum(bid_sizes)
        total_ask = sum(ask_sizes)
        
        if total_bid + total_ask == 0:
            return None
        
        # Calculate imbalance ratio
        imbalance_ratio = (total_bid - total_ask) / (total_bid + total_ask)
        
        # Determine signal strength
        if abs(imbalance_ratio) < self.imbalance_threshold:
            signal = SignalStrength.NEUTRAL
            predicted_direction = "neutral"
        elif imbalance_ratio > 0.6:
            signal = SignalStrength.STRONG_BUY
            predicted_direction = "up"
        elif imbalance_ratio > self.imbalance_threshold:
            signal = SignalStrength.BUY
            predicted_direction = "up"
        elif imbalance_ratio < -0.6:
            signal = SignalStrength.STRONG_SELL
            predicted_direction = "down"
        elif imbalance_ratio < -self.imbalance_threshold:
            signal = SignalStrength.SELL
            predicted_direction = "down"
        else:
            signal = SignalStrength.NEUTRAL
            predicted_direction = "neutral"
        
        # Count pressure levels
        bid_pressure = sum(1 for s in bid_sizes if s > np.mean(bid_sizes) * 1.5)
        ask_pressure = sum(1 for s in ask_sizes if s > np.mean(ask_sizes) * 1.5)
        
        # Calculate confidence
        confidence = min(1.0, abs(imbalance_ratio) / 0.8)
        
        imbalance_signal = ImbalanceSignal(
            symbol=order_book.symbol,
            timestamp=order_book.timestamp,
            bid_size=total_bid,
            ask_size=total_ask,
            imbalance_ratio=imbalance_ratio,
            signal=signal,
            confidence=confidence,
            bid_pressure_levels=bid_pressure,
            ask_pressure_levels=ask_pressure,
            predicted_direction=predicted_direction,
            predicted_magnitude=abs(imbalance_ratio) * order_book.spread
        )
        
        # Store signal
        with self._lock:
            self.signal_history[order_book.symbol].append(imbalance_signal)
        
        # Fire callbacks
        if signal != SignalStrength.NEUTRAL:
            for callback in self.on_signal:
                try:
                    callback(imbalance_signal)
                except Exception as e:
                    logger.error(f"Imbalance signal callback error: {e}")
        
        return imbalance_signal
    
    def get_current_imbalance(self, symbol: str) -> Optional[ImbalanceSignal]:
        """Get current imbalance for a symbol"""
        with self._lock:
            history = self.signal_history.get(symbol)
            if history:
                return history[-1]
            return None
    
    def get_signal_history(self, symbol: str, count: int = 100) -> List[ImbalanceSignal]:
        """Get signal history"""
        with self._lock:
            history = list(self.signal_history.get(symbol, []))
            return history[-count:]


class LatencyOptimizer:
    """
    Optimizes and monitors system latency
    """
    
    def __init__(self, target_latency_us: float = 100):
        self.target_latency = target_latency_us
        
        # Latency tracking
        self.latency_samples: Deque[LatencyMetrics] = deque(maxlen=10000)
        
        # Component latencies
        self.component_latencies: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        # Optimization suggestions
        self.suggestions: List[str] = []
        
        self._lock = threading.RLock()
        
        logger.info("LatencyOptimizer initialized")
    
    def record_latency(
        self,
        network_us: float,
        tick_processing_us: float,
        signal_generation_us: float,
        order_preparation_us: float
    ) -> LatencyMetrics:
        """Record latency measurement"""
        total = network_us + tick_processing_us + signal_generation_us + order_preparation_us
        
        metrics = LatencyMetrics(
            timestamp=datetime.now(),
            network_latency_us=network_us,
            tick_processing_us=tick_processing_us,
            signal_generation_us=signal_generation_us,
            order_preparation_us=order_preparation_us,
            total_latency_us=total
        )
        
        with self._lock:
            self.latency_samples.append(metrics)
            
            # Update component tracking
            self.component_latencies['network'].append(network_us)
            self.component_latencies['tick_processing'].append(tick_processing_us)
            self.component_latencies['signal_generation'].append(signal_generation_us)
            self.component_latencies['order_preparation'].append(order_preparation_us)
            self.component_latencies['total'].append(total)
        
        # Check if optimization needed
        if total > self.target_latency:
            self._generate_suggestions(metrics)
        
        return metrics
    
    def _generate_suggestions(self, metrics: LatencyMetrics):
        """Generate optimization suggestions"""
        suggestions = []
        
        if metrics.network_latency_us > self.target_latency * 0.5:
            suggestions.append("Consider co-location or dedicated network connection")
        
        if metrics.tick_processing_us > self.target_latency * 0.2:
            suggestions.append("Optimize tick processing - consider batch processing or SIMD")
        
        if metrics.signal_generation_us > self.target_latency * 0.2:
            suggestions.append("Simplify signal generation or use pre-computed values")
        
        if metrics.order_preparation_us > self.target_latency * 0.1:
            suggestions.append("Pre-allocate order objects and use object pooling")
        
        self.suggestions = suggestions
    
    def get_percentiles(self) -> Dict[str, float]:
        """Get latency percentiles"""
        with self._lock:
            if not self.latency_samples:
                return {}
            
            totals = [m.total_latency_us for m in self.latency_samples]
            sorted_totals = sorted(totals)
            
            n = len(sorted_totals)
            
            return {
                'p50': sorted_totals[n // 2],
                'p90': sorted_totals[int(n * 0.9)],
                'p95': sorted_totals[int(n * 0.95)],
                'p99': sorted_totals[int(n * 0.99)],
                'min': sorted_totals[0],
                'max': sorted_totals[-1],
                'avg': np.mean(totals)
            }
    
    def get_component_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Get latency breakdown by component"""
        with self._lock:
            breakdown = {}
            
            for component, samples in self.component_latencies.items():
                if samples:
                    breakdown[component] = {
                        'avg': np.mean(samples),
                        'max': max(samples),
                        'min': min(samples),
                        'std': np.std(samples)
                    }
            
            return breakdown
    
    def is_meeting_target(self) -> bool:
        """Check if meeting latency target"""
        percentiles = self.get_percentiles()
        return percentiles.get('p95', float('inf')) <= self.target_latency


class MarketMakingEngine:
    """
    Market making engine with quote management
    """
    
    def __init__(
        self,
        spread_bps: float = 10,
        position_limit: float = 100,
        inventory_skew_factor: float = 0.5
    ):
        self.spread_bps = spread_bps
        self.position_limit = position_limit
        self.inventory_skew_factor = inventory_skew_factor
        
        # Current quotes
        self.quotes: Dict[str, Dict[str, float]] = {}
        
        # Inventory
        self.inventory: Dict[str, float] = defaultdict(float)
        
        # P&L tracking
        self.realized_pnl: Dict[str, float] = defaultdict(float)
        self.unrealized_pnl: Dict[str, float] = defaultdict(float)
        
        # Statistics
        self.stats = {
            'quotes_sent': 0,
            'fills_received': 0,
            'spread_captured': 0.0
        }
        
        self._lock = threading.RLock()
        
        logger.info("MarketMakingEngine initialized")
    
    def calculate_quotes(
        self,
        symbol: str,
        mid_price: float,
        volatility: float = 0.0
    ) -> Tuple[float, float, float, float]:
        """
        Calculate bid/ask quotes
        Returns: (bid_price, bid_size, ask_price, ask_size)
        """
        with self._lock:
            # Base spread
            half_spread = (self.spread_bps / 10000) * mid_price / 2
            
            # Adjust for volatility
            if volatility > 0:
                half_spread *= (1 + volatility)
            
            # Inventory skew
            inventory = self.inventory.get(symbol, 0)
            inventory_ratio = inventory / self.position_limit if self.position_limit > 0 else 0
            
            # Skew quotes based on inventory
            skew = inventory_ratio * self.inventory_skew_factor * half_spread
            
            bid_price = mid_price - half_spread - skew
            ask_price = mid_price + half_spread - skew
            
            # Size based on inventory
            base_size = self.position_limit / 10
            bid_size = base_size * (1 - max(0, inventory_ratio))
            ask_size = base_size * (1 + min(0, inventory_ratio))
            
            # Store quotes
            self.quotes[symbol] = {
                'bid_price': bid_price,
                'bid_size': bid_size,
                'ask_price': ask_price,
                'ask_size': ask_size,
                'mid_price': mid_price,
                'timestamp': datetime.now()
            }
            
            self.stats['quotes_sent'] += 1
            
            return (bid_price, bid_size, ask_price, ask_size)
    
    def record_fill(
        self,
        symbol: str,
        side: str,
        price: float,
        size: float
    ):
        """Record a fill"""
        with self._lock:
            if side == 'buy':
                self.inventory[symbol] += size
            else:
                self.inventory[symbol] -= size
            
            self.stats['fills_received'] += 1
            
            # Calculate spread captured
            quote = self.quotes.get(symbol, {})
            if quote:
                mid = quote.get('mid_price', price)
                if side == 'buy':
                    spread_captured = mid - price
                else:
                    spread_captured = price - mid
                
                self.stats['spread_captured'] += spread_captured * size
                self.realized_pnl[symbol] += spread_captured * size
    
    def update_unrealized_pnl(self, symbol: str, current_price: float):
        """Update unrealized P&L"""
        with self._lock:
            inventory = self.inventory.get(symbol, 0)
            quote = self.quotes.get(symbol, {})
            
            if quote:
                avg_price = quote.get('mid_price', current_price)
                self.unrealized_pnl[symbol] = inventory * (current_price - avg_price)
    
    def get_inventory(self, symbol: str) -> float:
        """Get current inventory"""
        return self.inventory.get(symbol, 0)
    
    def get_pnl(self, symbol: str) -> Dict[str, float]:
        """Get P&L for a symbol"""
        return {
            'realized': self.realized_pnl.get(symbol, 0),
            'unrealized': self.unrealized_pnl.get(symbol, 0),
            'total': self.realized_pnl.get(symbol, 0) + self.unrealized_pnl.get(symbol, 0)
        }


class StatisticalArbitrageEngine:
    """
    Statistical arbitrage engine
    """
    
    def __init__(
        self,
        lookback_period: int = 100,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5
    ):
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        
        # Price history
        self.price_history: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=lookback_period)
        )
        
        # Spread history
        self.spread_history: Dict[Tuple[str, str], Deque[float]] = defaultdict(
            lambda: deque(maxlen=lookback_period)
        )
        
        # Active positions
        self.positions: Dict[Tuple[str, str], Dict] = {}
        
        # Statistics
        self.stats = {
            'signals_generated': 0,
            'trades_entered': 0,
            'trades_exited': 0,
            'total_pnl': 0.0
        }
        
        self._lock = threading.RLock()
        
        logger.info("StatisticalArbitrageEngine initialized")
    
    def update_price(self, symbol: str, price: float):
        """Update price for a symbol"""
        with self._lock:
            self.price_history[symbol].append(price)
    
    def calculate_spread(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Calculate spread between two symbols"""
        with self._lock:
            prices1 = list(self.price_history.get(symbol1, []))
            prices2 = list(self.price_history.get(symbol2, []))
            
            if not prices1 or not prices2:
                return None
            
            # Use log prices for spread
            spread = np.log(prices1[-1]) - np.log(prices2[-1])
            
            self.spread_history[(symbol1, symbol2)].append(spread)
            
            return spread
    
    def calculate_zscore(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Calculate z-score of spread"""
        with self._lock:
            spreads = list(self.spread_history.get((symbol1, symbol2), []))
            
            if len(spreads) < self.lookback_period // 2:
                return None
            
            mean = np.mean(spreads)
            std = np.std(spreads)
            
            if std == 0:
                return 0.0
            
            return (spreads[-1] - mean) / std
    
    def check_entry_signal(
        self,
        symbol1: str,
        symbol2: str
    ) -> Optional[Dict[str, Any]]:
        """Check for entry signal"""
        zscore = self.calculate_zscore(symbol1, symbol2)
        
        if zscore is None:
            return None
        
        if abs(zscore) >= self.entry_threshold:
            self.stats['signals_generated'] += 1
            
            if zscore > 0:
                # Spread too high - short symbol1, long symbol2
                return {
                    'action': 'enter',
                    'symbol1': symbol1,
                    'symbol1_side': 'short',
                    'symbol2': symbol2,
                    'symbol2_side': 'long',
                    'zscore': zscore,
                    'timestamp': datetime.now()
                }
            else:
                # Spread too low - long symbol1, short symbol2
                return {
                    'action': 'enter',
                    'symbol1': symbol1,
                    'symbol1_side': 'long',
                    'symbol2': symbol2,
                    'symbol2_side': 'short',
                    'zscore': zscore,
                    'timestamp': datetime.now()
                }
        
        return None
    
    def check_exit_signal(
        self,
        symbol1: str,
        symbol2: str
    ) -> Optional[Dict[str, Any]]:
        """Check for exit signal"""
        pair = (symbol1, symbol2)
        
        if pair not in self.positions:
            return None
        
        zscore = self.calculate_zscore(symbol1, symbol2)
        
        if zscore is None:
            return None
        
        if abs(zscore) <= self.exit_threshold:
            return {
                'action': 'exit',
                'symbol1': symbol1,
                'symbol2': symbol2,
                'zscore': zscore,
                'timestamp': datetime.now()
            }
        
        return None


class PairsTradingEngine:
    """
    Pairs trading engine with cointegration analysis
    """
    
    def __init__(
        self,
        lookback_period: int = 252,
        entry_zscore: float = 2.0,
        exit_zscore: float = 0.0,
        stop_loss_zscore: float = 4.0
    ):
        self.lookback_period = lookback_period
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
        self.stop_loss_zscore = stop_loss_zscore
        
        # Price history
        self.prices: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=lookback_period)
        )
        
        # Pair relationships
        self.pairs: Dict[Tuple[str, str], Dict] = {}
        
        # Active trades
        self.active_trades: Dict[Tuple[str, str], Dict] = {}
        
        # Trade history
        self.trade_history: List[Dict] = []
        
        self._lock = threading.RLock()
        
        logger.info("PairsTradingEngine initialized")
    
    def update_price(self, symbol: str, price: float):
        """Update price"""
        with self._lock:
            self.prices[symbol].append(price)
    
    def calculate_hedge_ratio(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Calculate hedge ratio using OLS"""
        with self._lock:
            prices1 = np.array(list(self.prices.get(symbol1, [])))
            prices2 = np.array(list(self.prices.get(symbol2, [])))
            
            if len(prices1) < 30 or len(prices2) < 30:
                return None
            
            # Align lengths
            min_len = min(len(prices1), len(prices2))
            prices1 = prices1[-min_len:]
            prices2 = prices2[-min_len:]
            
            # OLS regression
            X = np.column_stack([np.ones(len(prices2)), prices2])
            beta = np.linalg.lstsq(X, prices1, rcond=None)[0]
            
            return beta[1]
    
    def calculate_spread(
        self,
        symbol1: str,
        symbol2: str,
        hedge_ratio: float
    ) -> Optional[np.ndarray]:
        """Calculate spread"""
        with self._lock:
            prices1 = np.array(list(self.prices.get(symbol1, [])))
            prices2 = np.array(list(self.prices.get(symbol2, [])))
            
            if len(prices1) < 30 or len(prices2) < 30:
                return None
            
            min_len = min(len(prices1), len(prices2))
            prices1 = prices1[-min_len:]
            prices2 = prices2[-min_len:]
            
            spread = prices1 - hedge_ratio * prices2
            
            return spread
    
    def analyze_pair(self, symbol1: str, symbol2: str) -> Dict[str, Any]:
        """Analyze a pair for trading"""
        hedge_ratio = self.calculate_hedge_ratio(symbol1, symbol2)
        
        if hedge_ratio is None:
            return {'valid': False}
        
        spread = self.calculate_spread(symbol1, symbol2, hedge_ratio)
        
        if spread is None:
            return {'valid': False}
        
        # Calculate z-score
        mean = np.mean(spread)
        std = np.std(spread)
        current_zscore = (spread[-1] - mean) / std if std > 0 else 0
        
        # Check for signal
        signal = None
        if current_zscore > self.entry_zscore:
            signal = 'short_spread'  # Short symbol1, long symbol2
        elif current_zscore < -self.entry_zscore:
            signal = 'long_spread'   # Long symbol1, short symbol2
        elif abs(current_zscore) < self.exit_zscore:
            signal = 'exit'
        
        # Store pair info
        self.pairs[(symbol1, symbol2)] = {
            'hedge_ratio': hedge_ratio,
            'mean': mean,
            'std': std,
            'current_zscore': current_zscore,
            'signal': signal,
            'timestamp': datetime.now()
        }
        
        return {
            'valid': True,
            'hedge_ratio': hedge_ratio,
            'spread_mean': mean,
            'spread_std': std,
            'current_zscore': current_zscore,
            'signal': signal,
            'half_life': self._calculate_half_life(spread)
        }
    
    def _calculate_half_life(self, spread: np.ndarray) -> float:
        """Calculate mean reversion half-life"""
        spread_lag = spread[:-1]
        spread_diff = np.diff(spread)
        
        if len(spread_lag) < 2:
            return float('inf')
        
        # OLS regression
        X = np.column_stack([np.ones(len(spread_lag)), spread_lag])
        beta = np.linalg.lstsq(X, spread_diff, rcond=None)[0]
        
        if beta[1] >= 0:
            return float('inf')
        
        return -np.log(2) / beta[1]
    
    def get_signal(self, symbol1: str, symbol2: str) -> Optional[Dict]:
        """Get trading signal for a pair"""
        pair_info = self.pairs.get((symbol1, symbol2))
        
        if not pair_info:
            return None
        
        signal = pair_info.get('signal')
        
        if signal and signal != 'exit':
            return {
                'pair': (symbol1, symbol2),
                'signal': signal,
                'zscore': pair_info['current_zscore'],
                'hedge_ratio': pair_info['hedge_ratio'],
                'timestamp': pair_info['timestamp']
            }
        
        return None


class MeanReversionScalper:
    """
    Mean reversion scalping strategy
    """
    
    def __init__(
        self,
        lookback: int = 20,
        entry_std: float = 2.0,
        exit_std: float = 0.5,
        max_hold_seconds: float = 60
    ):
        self.lookback = lookback
        self.entry_std = entry_std
        self.exit_std = exit_std
        self.max_hold_seconds = max_hold_seconds
        
        # Price history
        self.prices: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=lookback)
        )
        
        # Active scalps
        self.active_scalps: Dict[str, Dict] = {}
        
        # Statistics
        self.stats = {
            'scalps_entered': 0,
            'scalps_exited': 0,
            'win_rate': 0.0,
            'avg_hold_time': 0.0
        }
        
        self._lock = threading.RLock()
        
        logger.info("MeanReversionScalper initialized")
    
    def update_price(self, symbol: str, price: float) -> Optional[Dict]:
        """Update price and check for signals"""
        with self._lock:
            self.prices[symbol].append(price)
            
            if len(self.prices[symbol]) < self.lookback:
                return None
            
            prices = np.array(list(self.prices[symbol]))
            mean = np.mean(prices)
            std = np.std(prices)
            
            if std == 0:
                return None
            
            zscore = (price - mean) / std
            
            # Check for entry
            if symbol not in self.active_scalps:
                if zscore > self.entry_std:
                    # Price too high - short
                    return self._enter_scalp(symbol, 'short', price, zscore, mean)
                elif zscore < -self.entry_std:
                    # Price too low - long
                    return self._enter_scalp(symbol, 'long', price, zscore, mean)
            else:
                # Check for exit
                scalp = self.active_scalps[symbol]
                hold_time = (datetime.now() - scalp['entry_time']).total_seconds()
                
                if abs(zscore) < self.exit_std or hold_time > self.max_hold_seconds:
                    return self._exit_scalp(symbol, price, zscore)
            
            return None
    
    def _enter_scalp(
        self,
        symbol: str,
        side: str,
        price: float,
        zscore: float,
        target: float
    ) -> Dict:
        """Enter a scalp"""
        scalp = {
            'symbol': symbol,
            'side': side,
            'entry_price': price,
            'entry_zscore': zscore,
            'target_price': target,
            'entry_time': datetime.now()
        }
        
        self.active_scalps[symbol] = scalp
        self.stats['scalps_entered'] += 1
        
        return {
            'action': 'enter',
            **scalp
        }
    
    def _exit_scalp(self, symbol: str, price: float, zscore: float) -> Dict:
        """Exit a scalp"""
        scalp = self.active_scalps.pop(symbol)
        
        # Calculate P&L
        if scalp['side'] == 'long':
            pnl = price - scalp['entry_price']
        else:
            pnl = scalp['entry_price'] - price
        
        hold_time = (datetime.now() - scalp['entry_time']).total_seconds()
        
        self.stats['scalps_exited'] += 1
        
        return {
            'action': 'exit',
            'symbol': symbol,
            'side': scalp['side'],
            'entry_price': scalp['entry_price'],
            'exit_price': price,
            'pnl': pnl,
            'hold_time_seconds': hold_time
        }


class MomentumIgnitionDetector:
    """
    Detects momentum ignition patterns
    """
    
    def __init__(
        self,
        volume_spike_threshold: float = 3.0,
        price_move_threshold: float = 0.5,
        time_window_seconds: float = 5.0
    ):
        self.volume_spike_threshold = volume_spike_threshold
        self.price_move_threshold = price_move_threshold
        self.time_window = time_window_seconds
        
        # Trade history
        self.trades: Dict[str, Deque[Dict]] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        # Detected ignitions
        self.ignitions: List[Dict] = []
        
        # Callbacks
        self.on_ignition: List[Callable] = []
        
        self._lock = threading.RLock()
        
        logger.info("MomentumIgnitionDetector initialized")
    
    def record_trade(
        self,
        symbol: str,
        price: float,
        size: float,
        side: str
    ):
        """Record a trade"""
        with self._lock:
            self.trades[symbol].append({
                'price': price,
                'size': size,
                'side': side,
                'timestamp': datetime.now()
            })
        
        # Check for ignition
        self._check_ignition(symbol)
    
    def _check_ignition(self, symbol: str):
        """Check for momentum ignition"""
        with self._lock:
            trades = list(self.trades.get(symbol, []))
            
            if len(trades) < 10:
                return
            
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.time_window)
            
            # Get recent trades
            recent = [t for t in trades if t['timestamp'] > cutoff]
            
            if len(recent) < 5:
                return
            
            # Calculate metrics
            recent_volume = sum(t['size'] for t in recent)
            older = [t for t in trades if t['timestamp'] <= cutoff]
            
            if not older:
                return
            
            avg_volume = np.mean([t['size'] for t in older])
            
            # Volume spike
            volume_ratio = recent_volume / (avg_volume * len(recent)) if avg_volume > 0 else 0
            
            # Price move
            price_start = recent[0]['price']
            price_end = recent[-1]['price']
            price_move_pct = abs(price_end - price_start) / price_start * 100
            
            # Check thresholds
            if volume_ratio > self.volume_spike_threshold and price_move_pct > self.price_move_threshold:
                ignition = {
                    'symbol': symbol,
                    'timestamp': now,
                    'volume_ratio': volume_ratio,
                    'price_move_pct': price_move_pct,
                    'direction': 'up' if price_end > price_start else 'down',
                    'trade_count': len(recent)
                }
                
                self.ignitions.append(ignition)
                
                # Fire callbacks
                for callback in self.on_ignition:
                    try:
                        callback(ignition)
                    except Exception as e:
                        logger.error(f"Ignition callback error: {e}")
    
    def get_recent_ignitions(self, count: int = 10) -> List[Dict]:
        """Get recent ignitions"""
        return self.ignitions[-count:]


# Export
__all__ = [
    'TickDataHandler',
    'OrderBookImbalanceDetector',
    'LatencyOptimizer',
    'MarketMakingEngine',
    'StatisticalArbitrageEngine',
    'PairsTradingEngine',
    'MeanReversionScalper',
    'MomentumIgnitionDetector',
    'Tick',
    'TickType',
    'OrderBook',
    'OrderBookLevel',
    'ImbalanceSignal',
    'SignalStrength',
    'LatencyMetrics'
]
