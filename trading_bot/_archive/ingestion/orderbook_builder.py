"""
AlphaAlgo Synthetic Order Book Builder
======================================
Builds and maintains order book state from L2 data.
Provides synthetic order book when only L1 data is available.
"""

from __future__ import annotations

import logging
import time
import math
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Deque, Any
from collections import deque
from enum import Enum, auto
import threading

from .schema import (
    MarketEvent, MarketEventType, L2BookSnapshot, L2PriceLevel,
    QuoteEvent, TradeEvent, TradeSide
)

logger = logging.getLogger(__name__)


class OrderBookMode(Enum):
    """Order book construction mode"""
    REAL_L2 = auto()        # Real L2 data available
    SYNTHETIC_L1 = auto()   # Synthetic from L1 quotes
    SYNTHETIC_TRADES = auto()  # Synthetic from trades only
    HYBRID = auto()         # Mix of real and synthetic


@dataclass
class PriceLevel:
    """Single price level in order book"""
    price: float
    size: float
    order_count: int = 0
    last_update_ts: int = 0
    
    def to_l2_level(self) -> L2PriceLevel:
        return L2PriceLevel(
            price=self.price,
            size=self.size,
            order_count=self.order_count
        )


@dataclass
class OrderBookConfig:
    """Configuration for order book builder"""
    # Depth settings
    max_depth: int = 50                    # Maximum levels to maintain
    synthetic_depth: int = 20              # Depth for synthetic books
    
    # Synthetic book parameters
    tick_size: float = 0.01                # Minimum price increment
    base_spread_bps: float = 10.0          # Base spread in basis points
    depth_decay_factor: float = 0.85       # Size decay per level
    
    # Imbalance model
    imbalance_window: int = 100            # Trades to consider for imbalance
    imbalance_weight: float = 0.3          # How much imbalance affects synthetic book
    
    # Liquidity persistence
    liquidity_half_life_ms: int = 5000     # Half-life for liquidity decay
    min_liquidity_ratio: float = 0.1       # Minimum liquidity as ratio of peak
    
    # Update frequency
    snapshot_interval_ms: int = 100        # Snapshot generation interval
    stale_threshold_ms: int = 5000         # Mark book as stale after this
    
    # Memory
    ring_buffer_size: int = 10000          # Size of trade/quote ring buffer


@dataclass
class OrderBookState:
    """Current state of an order book"""
    symbol: str
    exchange: str
    mode: OrderBookMode
    
    # Price levels
    bids: Dict[float, PriceLevel] = field(default_factory=dict)
    asks: Dict[float, PriceLevel] = field(default_factory=dict)
    
    # Best prices
    best_bid: float = 0.0
    best_ask: float = 0.0
    mid_price: float = 0.0
    spread: float = 0.0
    spread_bps: float = 0.0
    
    # Imbalance
    imbalance: float = 0.0  # -1 to 1, positive = more bids
    
    # Timestamps
    last_update_ts: int = 0
    last_trade_ts: int = 0
    last_quote_ts: int = 0
    
    # Sequence
    sequence: int = 0
    
    # Quality
    is_stale: bool = False
    is_crossed: bool = False
    
    def to_snapshot(self) -> L2BookSnapshot:
        """Convert to L2BookSnapshot"""
        # Sort bids descending, asks ascending
        sorted_bids = sorted(self.bids.values(), key=lambda x: -x.price)
        sorted_asks = sorted(self.asks.values(), key=lambda x: x.price)
        
        return L2BookSnapshot(
            bids=[level.to_l2_level() for level in sorted_bids],
            asks=[level.to_l2_level() for level in sorted_asks],
            depth=max(len(sorted_bids), len(sorted_asks)),
            is_snapshot=True
        )
    
    def get_depth_at_price(self, price: float, side: str) -> float:
        """Get total size at or better than price"""
        if side == 'bid':
            return sum(
                level.size for level in self.bids.values()
                if level.price >= price
            )
        else:
            return sum(
                level.size for level in self.asks.values()
                if level.price <= price
            )
    
    def get_vwap(self, size: float, side: str) -> Optional[float]:
        """Calculate VWAP for given size"""
        if side == 'bid':
            levels = sorted(self.asks.values(), key=lambda x: x.price)
        else:
            levels = sorted(self.bids.values(), key=lambda x: -x.price)
        
        remaining = size
        total_value = 0.0
        total_size = 0.0
        
        for level in levels:
            fill_size = min(remaining, level.size)
            total_value += fill_size * level.price
            total_size += fill_size
            remaining -= fill_size
            
            if remaining <= 0:
                break
        
        if total_size > 0:
            return total_value / total_size
        return None


class TradeImbalanceModel:
    """
    Calculates order flow imbalance from recent trades.
    Used to adjust synthetic order book.
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._trades: Deque[Tuple[float, float, TradeSide]] = deque(maxlen=window_size)
        self._buy_volume: float = 0.0
        self._sell_volume: float = 0.0
    
    def add_trade(self, price: float, size: float, side: TradeSide):
        """Add a trade to the model"""
        # Remove oldest trade's contribution if at capacity
        if len(self._trades) >= self.window_size:
            old_price, old_size, old_side = self._trades[0]
            if old_side == TradeSide.BUY:
                self._buy_volume -= old_size
            elif old_side == TradeSide.SELL:
                self._sell_volume -= old_size
        
        # Add new trade
        self._trades.append((price, size, side))
        if side == TradeSide.BUY:
            self._buy_volume += size
        elif side == TradeSide.SELL:
            self._sell_volume += size
    
    def get_imbalance(self) -> float:
        """
        Calculate imbalance: (buy_vol - sell_vol) / (buy_vol + sell_vol)
        Returns value in [-1, 1]
        """
        total = self._buy_volume + self._sell_volume
        if total == 0:
            return 0.0
        return (self._buy_volume - self._sell_volume) / total
    
    def get_volume_ratio(self) -> float:
        """Get buy/sell volume ratio"""
        if self._sell_volume == 0:
            return float('inf') if self._buy_volume > 0 else 1.0
        return self._buy_volume / self._sell_volume
    
    def clear(self):
        """Clear all trades"""
        self._trades.clear()
        self._buy_volume = 0.0
        self._sell_volume = 0.0


class LiquidityPersistenceModel:
    """
    Models liquidity persistence over time.
    Liquidity decays exponentially from last observed value.
    """
    
    def __init__(self, half_life_ms: int = 5000, min_ratio: float = 0.1):
        self.half_life_ms = half_life_ms
        self.min_ratio = min_ratio
        self._decay_constant = math.log(2) / half_life_ms
    
    def decay_size(self, original_size: float, elapsed_ms: float) -> float:
        """Calculate decayed size"""
        if elapsed_ms <= 0:
            return original_size
        
        decay_factor = math.exp(-self._decay_constant * elapsed_ms)
        decay_factor = max(decay_factor, self.min_ratio)
        
        return original_size * decay_factor


class SyntheticOrderBook:
    """
    Builds synthetic order book from L1 quotes and trades.
    Used when real L2 data is not available.
    """
    
    def __init__(self, config: OrderBookConfig):
        self.config = config
        
        # State per symbol
        self._states: Dict[str, OrderBookState] = {}
        self._locks: Dict[str, threading.RLock] = {}
        
        # Models
        self._imbalance_models: Dict[str, TradeImbalanceModel] = {}
        self._liquidity_model = LiquidityPersistenceModel(
            half_life_ms=config.liquidity_half_life_ms,
            min_ratio=config.min_liquidity_ratio
        )
        
        # Ring buffers for recent data
        self._recent_quotes: Dict[str, Deque[QuoteEvent]] = {}
        self._recent_trades: Dict[str, Deque[TradeEvent]] = {}
        
        logger.info("SyntheticOrderBook initialized")
    
    def _get_key(self, exchange: str, symbol: str) -> str:
        return f"{exchange}:{symbol}"
    
    def _get_lock(self, key: str) -> threading.RLock:
        if key not in self._locks:
            self._locks[key] = threading.RLock()
        return self._locks[key]
    
    def _get_state(self, exchange: str, symbol: str) -> OrderBookState:
        """Get or create order book state"""
        key = self._get_key(exchange, symbol)
        
        if key not in self._states:
            self._states[key] = OrderBookState(
                symbol=symbol,
                exchange=exchange,
                mode=OrderBookMode.SYNTHETIC_L1
            )
            self._imbalance_models[key] = TradeImbalanceModel(
                window_size=self.config.imbalance_window
            )
            self._recent_quotes[key] = deque(maxlen=self.config.ring_buffer_size)
            self._recent_trades[key] = deque(maxlen=self.config.ring_buffer_size)
        
        return self._states[key]
    
    def process_event(self, event: MarketEvent) -> Optional[OrderBookState]:
        """
        Process a market event and update order book.
        Returns updated state if significant change.
        """
        key = self._get_key(event.exchange, event.symbol)
        
        with self._get_lock(key):
            state = self._get_state(event.exchange, event.symbol)
            
            if event.event_type == MarketEventType.QUOTE:
                return self._process_quote(state, event)
            elif event.event_type == MarketEventType.TRADE:
                return self._process_trade(state, event)
            elif event.event_type in (MarketEventType.L2_SNAPSHOT, MarketEventType.L2_DELTA):
                return self._process_l2(state, event)
        
        return None
    
    def _process_quote(self, state: OrderBookState, event: MarketEvent) -> OrderBookState:
        """Process quote event"""
        quote = event.quote
        if not quote:
            return state
        
        key = self._get_key(event.exchange, event.symbol)
        self._recent_quotes[key].append(quote)
        
        # Update best bid/ask
        state.best_bid = quote.bid_price
        state.best_ask = quote.ask_price
        
        if state.best_bid > 0 and state.best_ask > 0:
            state.mid_price = (state.best_bid + state.best_ask) / 2
            state.spread = state.best_ask - state.best_bid
            state.spread_bps = (state.spread / state.mid_price) * 10000
            state.is_crossed = state.best_bid >= state.best_ask
        
        state.last_quote_ts = event.exchange_ts
        state.last_update_ts = event.process_ts
        state.sequence += 1
        
        # Rebuild synthetic book
        self._rebuild_synthetic_book(state, quote)
        
        return state
    
    def _process_trade(self, state: OrderBookState, event: MarketEvent) -> OrderBookState:
        """Process trade event"""
        trade = event.trade
        if not trade:
            return state
        
        key = self._get_key(event.exchange, event.symbol)
        self._recent_trades[key].append(trade)
        
        # Update imbalance model
        self._imbalance_models[key].add_trade(
            trade.price, trade.size, trade.side
        )
        state.imbalance = self._imbalance_models[key].get_imbalance()
        
        # Update mid price from trade
        if state.mid_price == 0:
            state.mid_price = trade.price
        
        state.last_trade_ts = event.exchange_ts
        state.last_update_ts = event.process_ts
        state.sequence += 1
        
        # Adjust synthetic book based on trade
        self._adjust_for_trade(state, trade)
        
        return state
    
    def _process_l2(self, state: OrderBookState, event: MarketEvent) -> OrderBookState:
        """Process L2 event (real order book data)"""
        l2_book = event.l2_book
        if not l2_book:
            return state
        
        state.mode = OrderBookMode.REAL_L2
        
        if l2_book.is_snapshot:
            # Full snapshot - replace book
            state.bids.clear()
            state.asks.clear()
            
            for level in l2_book.bids:
                state.bids[level.price] = PriceLevel(
                    price=level.price,
                    size=level.size,
                    order_count=level.order_count,
                    last_update_ts=event.exchange_ts
                )
            
            for level in l2_book.asks:
                state.asks[level.price] = PriceLevel(
                    price=level.price,
                    size=level.size,
                    order_count=level.order_count,
                    last_update_ts=event.exchange_ts
                )
        else:
            # Delta update
            for level in l2_book.bids:
                if level.size == 0:
                    state.bids.pop(level.price, None)
                else:
                    state.bids[level.price] = PriceLevel(
                        price=level.price,
                        size=level.size,
                        order_count=level.order_count,
                        last_update_ts=event.exchange_ts
                    )
            
            for level in l2_book.asks:
                if level.size == 0:
                    state.asks.pop(level.price, None)
                else:
                    state.asks[level.price] = PriceLevel(
                        price=level.price,
                        size=level.size,
                        order_count=level.order_count,
                        last_update_ts=event.exchange_ts
                    )
        
        # Update best prices
        if state.bids:
            state.best_bid = max(state.bids.keys())
        if state.asks:
            state.best_ask = min(state.asks.keys())
        
        if state.best_bid > 0 and state.best_ask > 0:
            state.mid_price = (state.best_bid + state.best_ask) / 2
            state.spread = state.best_ask - state.best_bid
            state.spread_bps = (state.spread / state.mid_price) * 10000
            state.is_crossed = state.best_bid >= state.best_ask
        
        # Calculate imbalance from book
        total_bid = sum(l.size for l in state.bids.values())
        total_ask = sum(l.size for l in state.asks.values())
        if total_bid + total_ask > 0:
            state.imbalance = (total_bid - total_ask) / (total_bid + total_ask)
        
        state.last_update_ts = event.process_ts
        state.sequence += 1
        
        # Trim to max depth
        self._trim_depth(state)
        
        return state
    
    def _rebuild_synthetic_book(self, state: OrderBookState, quote: QuoteEvent):
        """Rebuild synthetic order book from L1 quote"""
        if state.mode == OrderBookMode.REAL_L2:
            return  # Don't override real L2 data
        
        state.mode = OrderBookMode.SYNTHETIC_L1
        state.bids.clear()
        state.asks.clear()
        
        if quote.bid_price <= 0 or quote.ask_price <= 0:
            return
        
        # Get imbalance adjustment
        key = self._get_key(state.exchange, state.symbol)
        imbalance = self._imbalance_models[key].get_imbalance()
        
        # Calculate tick size
        tick_size = self.config.tick_size
        if state.mid_price > 100:
            tick_size = 0.1
        elif state.mid_price > 1000:
            tick_size = 1.0
        
        # Build bid side
        bid_size = quote.bid_size
        for i in range(self.config.synthetic_depth):
            price = quote.bid_price - (i * tick_size)
            if price <= 0:
                break
            
            # Decay size with depth
            level_size = bid_size * (self.config.depth_decay_factor ** i)
            
            # Adjust for imbalance (more bids if positive imbalance)
            imbalance_adj = 1.0 + (imbalance * self.config.imbalance_weight)
            level_size *= imbalance_adj
            
            state.bids[price] = PriceLevel(
                price=price,
                size=level_size,
                order_count=max(1, int(level_size / (bid_size / 10))),
                last_update_ts=time.time_ns()
            )
        
        # Build ask side
        ask_size = quote.ask_size
        for i in range(self.config.synthetic_depth):
            price = quote.ask_price + (i * tick_size)
            
            # Decay size with depth
            level_size = ask_size * (self.config.depth_decay_factor ** i)
            
            # Adjust for imbalance (more asks if negative imbalance)
            imbalance_adj = 1.0 - (imbalance * self.config.imbalance_weight)
            level_size *= imbalance_adj
            
            state.asks[price] = PriceLevel(
                price=price,
                size=level_size,
                order_count=max(1, int(level_size / (ask_size / 10))),
                last_update_ts=time.time_ns()
            )
    
    def _adjust_for_trade(self, state: OrderBookState, trade: TradeEvent):
        """Adjust synthetic book based on trade"""
        if state.mode == OrderBookMode.REAL_L2:
            return  # Real L2 will have its own updates
        
        # Remove liquidity at trade price
        if trade.side == TradeSide.BUY:
            # Trade hit the ask
            if trade.price in state.asks:
                level = state.asks[trade.price]
                level.size = max(0, level.size - trade.size)
                if level.size <= 0:
                    del state.asks[trade.price]
        elif trade.side == TradeSide.SELL:
            # Trade hit the bid
            if trade.price in state.bids:
                level = state.bids[trade.price]
                level.size = max(0, level.size - trade.size)
                if level.size <= 0:
                    del state.bids[trade.price]
    
    def _trim_depth(self, state: OrderBookState):
        """Trim order book to max depth"""
        if len(state.bids) > self.config.max_depth:
            sorted_bids = sorted(state.bids.keys(), reverse=True)
            for price in sorted_bids[self.config.max_depth:]:
                del state.bids[price]
        
        if len(state.asks) > self.config.max_depth:
            sorted_asks = sorted(state.asks.keys())
            for price in sorted_asks[self.config.max_depth:]:
                del state.asks[price]
    
    def get_state(self, exchange: str, symbol: str) -> Optional[OrderBookState]:
        """Get current order book state"""
        key = self._get_key(exchange, symbol)
        return self._states.get(key)
    
    def get_snapshot(self, exchange: str, symbol: str) -> Optional[L2BookSnapshot]:
        """Get L2 snapshot for symbol"""
        state = self.get_state(exchange, symbol)
        if state:
            return state.to_snapshot()
        return None
    
    def get_all_symbols(self) -> List[Tuple[str, str]]:
        """Get all tracked symbols"""
        return [
            (state.exchange, state.symbol)
            for state in self._states.values()
        ]
    
    def check_staleness(self, threshold_ms: Optional[int] = None) -> Dict[str, bool]:
        """Check which books are stale"""
        threshold = threshold_ms or self.config.stale_threshold_ms
        current_ts = time.time_ns()
        
        results = {}
        for key, state in self._states.items():
            elapsed_ms = (current_ts - state.last_update_ts) / 1e6
            state.is_stale = elapsed_ms > threshold
            results[key] = state.is_stale
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get order book statistics"""
        stats = {
            'total_symbols': len(self._states),
            'symbols': {}
        }
        
        for key, state in self._states.items():
            stats['symbols'][key] = {
                'mode': state.mode.name,
                'bid_levels': len(state.bids),
                'ask_levels': len(state.asks),
                'best_bid': state.best_bid,
                'best_ask': state.best_ask,
                'spread_bps': state.spread_bps,
                'imbalance': state.imbalance,
                'is_stale': state.is_stale,
                'is_crossed': state.is_crossed,
                'sequence': state.sequence,
            }
        
        return stats


class OrderBookManager:
    """
    High-level manager for order books across all symbols.
    Handles snapshots, subscriptions, and state management.
    """
    
    def __init__(self, config: Optional[OrderBookConfig] = None):
        self.config = config or OrderBookConfig()
        self.synthetic_book = SyntheticOrderBook(self.config)
        
        # Snapshot generation
        self._snapshot_callbacks: List[callable] = []
        self._snapshot_task: Optional[asyncio.Task] = None
        
        logger.info("OrderBookManager initialized")
    
    async def start(self):
        """Start snapshot generation"""
        self._snapshot_task = asyncio.create_task(self._snapshot_loop())
    
    async def stop(self):
        """Stop snapshot generation"""
        if self._snapshot_task:
            self._snapshot_task.cancel()
    
    async def _snapshot_loop(self):
        """Periodic snapshot generation"""
        while True:
            await asyncio.sleep(self.config.snapshot_interval_ms / 1000)
            
            # Check staleness
            self.synthetic_book.check_staleness()
            
            # Generate snapshots for subscribers
            for exchange, symbol in self.synthetic_book.get_all_symbols():
                snapshot = self.synthetic_book.get_snapshot(exchange, symbol)
                if snapshot:
                    for callback in self._snapshot_callbacks:
                        try:
                            callback(exchange, symbol, snapshot)
                        except Exception as e:
                            logger.error(f"Snapshot callback error: {e}")
    
    def process_event(self, event: MarketEvent) -> Optional[OrderBookState]:
        """Process market event"""
        return self.synthetic_book.process_event(event)
    
    def subscribe_snapshots(self, callback: callable):
        """Subscribe to snapshot updates"""
        self._snapshot_callbacks.append(callback)
    
    def get_state(self, exchange: str, symbol: str) -> Optional[OrderBookState]:
        """Get order book state"""
        return self.synthetic_book.get_state(exchange, symbol)
    
    def get_snapshot(self, exchange: str, symbol: str) -> Optional[L2BookSnapshot]:
        """Get L2 snapshot"""
        return self.synthetic_book.get_snapshot(exchange, symbol)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return self.synthetic_book.get_stats()
