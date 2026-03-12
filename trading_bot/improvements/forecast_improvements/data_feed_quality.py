"""
Data Feed Quality - Improvement #2 (CRITICAL)
==============================================

Multi-source validated data for better signals and fewer false trades.

Features:
- Multiple data source validation
- Tick-level data for precise entries
- Volume profile data
- Order book depth (Level 2)
- Data staleness detection with auto-switch
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import statistics
import threading

try:
    import yfinance as yf
except ImportError:
    yf = None

logger = logging.getLogger(__name__)


class DataQuality(Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"  # All sources agree, fresh data
    GOOD = "good"           # Most sources agree, recent data
    ACCEPTABLE = "acceptable"  # Some discrepancy, usable
    POOR = "poor"           # Significant discrepancy
    STALE = "stale"         # Data too old
    UNAVAILABLE = "unavailable"


class DataSourceStatus(Enum):
    """Data source status"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class Tick:
    """Single tick data"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: datetime
    source: str = ""
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2


@dataclass
class OHLCV:
    """OHLCV bar data"""
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    tick_volume: int = 0
    spread: float = 0.0
    source: str = ""


@dataclass
class OrderBookLevel:
    """Single order book level"""
    price: float
    volume: float
    count: int = 1


@dataclass
class OrderBook:
    """Order book (Level 2) data"""
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: datetime
    source: str = ""
    
    @property
    def best_bid(self) -> float:
        return self.bids[0].price if self.bids else 0.0
    
    @property
    def best_ask(self) -> float:
        return self.asks[0].price if self.asks else 0.0
    
    @property
    def spread(self) -> float:
        return self.best_ask - self.best_bid
    
    @property
    def mid_price(self) -> float:
        return (self.best_bid + self.best_ask) / 2
    
    def get_depth(self, levels: int = 5) -> Dict[str, float]:
        """Get bid/ask depth for N levels"""
        bid_depth = sum(l.volume for l in self.bids[:levels])
        ask_depth = sum(l.volume for l in self.asks[:levels])
        return {
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'imbalance': (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else 0
        }


@dataclass
class VolumeProfile:
    """Volume profile data"""
    symbol: str
    timeframe: str
    levels: Dict[float, float]  # price -> volume
    poc: float  # Point of Control (highest volume price)
    value_area_high: float
    value_area_low: float
    timestamp: datetime
    
    def get_volume_at_price(self, price: float, tolerance: float = 0.0001) -> float:
        """Get volume at a specific price level"""
        for level_price, volume in self.levels.items():
            if abs(level_price - price) <= tolerance:
                return volume
        return 0.0
    
    def is_in_value_area(self, price: float) -> bool:
        """Check if price is in value area"""
        return self.value_area_low <= price <= self.value_area_high


class DataSource(ABC):
    """Abstract data source"""
    
    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority
        self.status = DataSourceStatus.UNKNOWN
        self.last_update: Optional[datetime] = None
        self.error_count = 0
        self.latency_ms: float = 0.0
    
    @abstractmethod
    async def get_tick(self, symbol: str) -> Optional[Tick]:
        """Get latest tick"""
        pass
    
    @abstractmethod
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        """Get OHLCV bars"""
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str, depth: int = 10) -> Optional[OrderBook]:
        """Get order book"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if source is healthy"""
        pass


class MT5DataSource(DataSource):
    """MetaTrader 5 data source"""
    
    def __init__(self, priority: int = 1):
        super().__init__("MT5", priority)
        self._mt5 = None
        self._initialized = False
    
    async def _ensure_initialized(self) -> bool:
        if self._initialized:
            return True
        try:
        
            import MetaTrader5 as mt5
            self._mt5 = mt5
            if not self._mt5.initialize():
                logger.warning("MT5 not initialized")
                return False
            self._initialized = True
            self.status = DataSourceStatus.ACTIVE
            return True
        except ImportError:
            logger.warning("MetaTrader5 package not installed")
            return False
    
    async def get_tick(self, symbol: str) -> Optional[Tick]:
        if not await self._ensure_initialized():
            return None
        
        start = time.time()
        try:
            tick = self._mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            
            self.latency_ms = (time.time() - start) * 1000
            self.last_update = datetime.now()
            self.status = DataSourceStatus.ACTIVE
            
            return Tick(
                symbol=symbol,
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume,
                timestamp=datetime.fromtimestamp(tick.time),
                source=self.name
            )
        except Exception as e:
            logger.error(f"MT5 tick error: {e}")
            self.error_count += 1
            return None
    
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        if not await self._ensure_initialized():
            return []
        try:
        
            # Map timeframe string to MT5 constant
            tf_map = {
                'M1': self._mt5.TIMEFRAME_M1,
                'M5': self._mt5.TIMEFRAME_M5,
                'M15': self._mt5.TIMEFRAME_M15,
                'M30': self._mt5.TIMEFRAME_M30,
                'H1': self._mt5.TIMEFRAME_H1,
                'H4': self._mt5.TIMEFRAME_H4,
                'D1': self._mt5.TIMEFRAME_D1,
                'W1': self._mt5.TIMEFRAME_W1,
                'MN1': self._mt5.TIMEFRAME_MN1,
            }
            
            mt5_tf = tf_map.get(timeframe.upper(), self._mt5.TIMEFRAME_H1)
            rates = self._mt5.copy_rates_from_pos(symbol, mt5_tf, 0, limit)
            
            if rates is None:
                return []
            
            self.last_update = datetime.now()
            
            return [
                OHLCV(
                    symbol=symbol,
                    timeframe=timeframe,
                    open=r['open'],
                    high=r['high'],
                    low=r['low'],
                    close=r['close'],
                    volume=r['real_volume'],
                    timestamp=datetime.fromtimestamp(r['time']),
                    tick_volume=r['tick_volume'],
                    spread=r['spread'],
                    source=self.name
                )
                for r in rates
            ]
        except Exception as e:
            logger.error(f"MT5 OHLCV error: {e}")
            self.error_count += 1
            return []
    
    async def get_order_book(self, symbol: str, depth: int = 10) -> Optional[OrderBook]:
        if not await self._ensure_initialized():
            return None
        try:
        
            # MT5 doesn't provide full order book, simulate from tick
            tick = self._mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            
            # Create synthetic order book from bid/ask
            bids = [OrderBookLevel(price=tick.bid - i * 0.0001, volume=100.0) for i in range(depth)]
            asks = [OrderBookLevel(price=tick.ask + i * 0.0001, volume=100.0) for i in range(depth)]
            
            return OrderBook(
                symbol=symbol,
                bids=bids,
                asks=asks,
                timestamp=datetime.now(),
                source=self.name
            )
        except Exception as e:
            logger.error(f"MT5 order book error: {e}")
            return None
    
    async def health_check(self) -> bool:
        if not await self._ensure_initialized():
            self.status = DataSourceStatus.OFFLINE
            return False
        try:
        
            info = self._mt5.terminal_info()
            if info and info.connected:
                self.status = DataSourceStatus.ACTIVE
                return True
            self.status = DataSourceStatus.DEGRADED
            return False
        except Exception:
            self.status = DataSourceStatus.OFFLINE
            return False


class YahooFinanceDataSource(DataSource):
    """Yahoo Finance data source (backup)"""
    
    def __init__(self, priority: int = 2):
        super().__init__("YahooFinance", priority)
    
    async def get_tick(self, symbol: str) -> Optional[Tick]:
            
        try:
            # Convert forex symbol format
            yf_symbol = self._convert_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            
            info = ticker.info
            if not info:
                return None
            
            bid = info.get('bid', 0) or info.get('regularMarketPrice', 0)
            ask = info.get('ask', 0) or info.get('regularMarketPrice', 0)
            
            self.last_update = datetime.now()
            self.status = DataSourceStatus.ACTIVE
            
            return Tick(
                symbol=symbol,
                bid=bid,
                ask=ask,
                last=info.get('regularMarketPrice', bid),
                volume=info.get('volume', 0),
                timestamp=datetime.now(),
                source=self.name
            )
        except ImportError:
            logger.warning("yfinance not installed")
            return None
        except Exception as e:
            logger.error(f"Yahoo Finance tick error: {e}")
            self.error_count += 1
            return None
    
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
            
        try:
            yf_symbol = self._convert_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            
            # Map timeframe to yfinance interval
            interval_map = {
                'M1': '1m', 'M5': '5m', 'M15': '15m', 'M30': '30m',
                'H1': '1h', 'H4': '4h', 'D1': '1d', 'W1': '1wk', 'MN1': '1mo'
            }
            
            interval = interval_map.get(timeframe.upper(), '1h')
            period = '7d' if interval in ['1m', '5m', '15m', '30m'] else '1mo'
            
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return []
            
            self.last_update = datetime.now()
            
            return [
                OHLCV(
                    symbol=symbol,
                    timeframe=timeframe,
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    close=row['Close'],
                    volume=row['Volume'],
                    timestamp=idx.to_pydatetime(),
                    source=self.name
                )
                for idx, row in hist.tail(limit).iterrows()
            ]
        except ImportError:
            return []
        except Exception as e:
            logger.error(f"Yahoo Finance OHLCV error: {e}")
            return []
    
    async def get_order_book(self, symbol: str, depth: int = 10) -> Optional[OrderBook]:
        # Yahoo Finance doesn't provide order book
        return None
    
    async def health_check(self) -> bool:
        try:
            ticker = yf.Ticker("EURUSD=X")
            info = ticker.info
            if info:
                self.status = DataSourceStatus.ACTIVE
                return True
            self.status = DataSourceStatus.DEGRADED
            return False
        except Exception:
            self.status = DataSourceStatus.OFFLINE
            return False
    
    def _convert_symbol(self, symbol: str) -> str:
        """Convert MT5 symbol to Yahoo Finance format"""
        # EURUSD -> EURUSD=X
        if len(symbol) == 6 and symbol.isalpha():
            return f"{symbol}=X"
        return symbol


class MultiSourceValidator:
    """Validates data across multiple sources"""
    
    def __init__(self, sources: List[DataSource], config: Optional[Dict] = None):
        self.sources = sorted(sources, key=lambda s: s.priority)
        self.config = config or {}
        self.max_price_deviation = self.config.get('max_price_deviation', 0.001)  # 0.1%
        self.max_staleness_seconds = self.config.get('max_staleness_seconds', 60)
        self._validation_history: deque = deque(maxlen=1000)
    
    async def get_validated_tick(self, symbol: str) -> Tuple[Optional[Tick], DataQuality]:
        """Get tick data validated across sources"""
        ticks = []
        
        for source in self.sources:
            try:
                tick = await source.get_tick(symbol)
                if tick:
                    ticks.append(tick)
            except Exception as e:
                logger.error(f"Source {source.name} error: {e}")
        
        if not ticks:
            return None, DataQuality.UNAVAILABLE
        
        if len(ticks) == 1:
            quality = self._assess_single_tick_quality(ticks[0])
            return ticks[0], quality
        
        # Validate across sources
        quality, validated_tick = self._validate_ticks(ticks)
        
        self._validation_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'quality': quality,
            'sources': len(ticks)
        })
        
        return validated_tick, quality
    
    def _assess_single_tick_quality(self, tick: Tick) -> DataQuality:
        """Assess quality of single tick"""
        age = (datetime.now() - tick.timestamp).total_seconds()
        
        if age > self.max_staleness_seconds:
            return DataQuality.STALE
        elif age > self.max_staleness_seconds / 2:
            return DataQuality.ACCEPTABLE
        else:
            return DataQuality.GOOD
    
    def _validate_ticks(self, ticks: List[Tick]) -> Tuple[DataQuality, Tick]:
        """Validate multiple ticks and return best one"""
        # Calculate average mid price
        mid_prices = [t.mid for t in ticks]
        avg_mid = statistics.mean(mid_prices)
        
        # Check deviation
        max_deviation = max(abs(m - avg_mid) / avg_mid for m in mid_prices)
        
        # Find freshest tick
        freshest = min(ticks, key=lambda t: (datetime.now() - t.timestamp).total_seconds())
        
        # Determine quality
        if max_deviation < self.max_price_deviation / 2:
            quality = DataQuality.EXCELLENT
        elif max_deviation < self.max_price_deviation:
            quality = DataQuality.GOOD
        elif max_deviation < self.max_price_deviation * 2:
            quality = DataQuality.ACCEPTABLE
        else:
            quality = DataQuality.POOR
        
        # Check staleness
        age = (datetime.now() - freshest.timestamp).total_seconds()
        if age > self.max_staleness_seconds:
            quality = DataQuality.STALE
        
        return quality, freshest
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        if not self._validation_history:
            return {'total': 0}
        
        quality_counts = {}
        for record in self._validation_history:
            q = record['quality'].value
            quality_counts[q] = quality_counts.get(q, 0) + 1
        
        return {
            'total': len(self._validation_history),
            'quality_distribution': quality_counts,
            'avg_sources': statistics.mean(r['sources'] for r in self._validation_history)
        }


class TickDataProcessor:
    """Processes tick-level data for precise entries"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.tick_buffer: Dict[str, deque] = {}
        self.buffer_size = self.config.get('buffer_size', 1000)
        self._lock = threading.Lock()
    
    def add_tick(self, tick: Tick):
        """Add tick to buffer"""
        with self._lock:
            if tick.symbol not in self.tick_buffer:
                self.tick_buffer[tick.symbol] = deque(maxlen=self.buffer_size)
            self.tick_buffer[tick.symbol].append(tick)
    
    def get_ticks(self, symbol: str, count: int = 100) -> List[Tick]:
        """Get recent ticks"""
        with self._lock:
            if symbol not in self.tick_buffer:
                return []
            return list(self.tick_buffer[symbol])[-count:]
    
    def get_tick_statistics(self, symbol: str, window: int = 100) -> Dict[str, Any]:
        """Get tick statistics"""
        ticks = self.get_ticks(symbol, window)
        
        if not ticks:
            return {}
        
        prices = [t.mid for t in ticks]
        spreads = [t.spread for t in ticks]
        volumes = [t.volume for t in ticks]
        
        return {
            'count': len(ticks),
            'avg_price': statistics.mean(prices),
            'price_std': statistics.stdev(prices) if len(prices) > 1 else 0,
            'avg_spread': statistics.mean(spreads),
            'max_spread': max(spreads),
            'min_spread': min(spreads),
            'total_volume': sum(volumes),
            'avg_volume': statistics.mean(volumes),
            'tick_rate': self._calculate_tick_rate(ticks)
        }
    
    def _calculate_tick_rate(self, ticks: List[Tick]) -> float:
        """Calculate ticks per second"""
        if len(ticks) < 2:
            return 0.0
        
        time_span = (ticks[-1].timestamp - ticks[0].timestamp).total_seconds()
        if time_span > 0:
            return len(ticks) / time_span
        return 0.0
    
    def detect_price_spike(self, symbol: str, threshold: float = 0.001) -> bool:
        """Detect sudden price spike"""
        ticks = self.get_ticks(symbol, 10)
        
        if len(ticks) < 2:
            return False
        
        recent_change = abs(ticks[-1].mid - ticks[-2].mid) / ticks[-2].mid
        return recent_change > threshold
    
    def get_vwap(self, symbol: str, window: int = 100) -> float:
        """Calculate Volume Weighted Average Price"""
        ticks = self.get_ticks(symbol, window)
        
        if not ticks:
            return 0.0
        
        total_value = sum(t.mid * t.volume for t in ticks)
        total_volume = sum(t.volume for t in ticks)
        
        if total_volume > 0:
            return total_value / total_volume
        return ticks[-1].mid


class VolumeProfileAnalyzer:
    """Analyzes volume profile for trading decisions"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.num_levels = self.config.get('num_levels', 50)
        self.value_area_percent = self.config.get('value_area_percent', 0.70)
    
    def calculate_volume_profile(self, bars: List[OHLCV]) -> Optional[VolumeProfile]:
        """Calculate volume profile from OHLCV data"""
        if not bars:
            return None
        
        # Find price range
        all_highs = [b.high for b in bars]
        all_lows = [b.low for b in bars]
        price_high = max(all_highs)
        price_low = min(all_lows)
        
        # Create price levels
        level_size = (price_high - price_low) / self.num_levels
        levels: Dict[float, float] = {}
        
        for i in range(self.num_levels):
            level_price = price_low + (i + 0.5) * level_size
            levels[level_price] = 0.0
        
        # Distribute volume to levels
        for bar in bars:
            bar_levels = self._get_bar_levels(bar, price_low, level_size)
            volume_per_level = bar.volume / len(bar_levels) if bar_levels else 0
            
            for level in bar_levels:
                if level in levels:
                    levels[level] += volume_per_level
        
        # Find POC (Point of Control)
        poc = max(levels.keys(), key=lambda k: levels[k])
        
        # Calculate Value Area
        total_volume = sum(levels.values())
        target_volume = total_volume * self.value_area_percent
        
        # Expand from POC until we reach target volume
        sorted_levels = sorted(levels.keys())
        poc_idx = sorted_levels.index(poc)
        
        va_low_idx = poc_idx
        va_high_idx = poc_idx
        current_volume = levels[poc]
        
        while current_volume < target_volume and (va_low_idx > 0 or va_high_idx < len(sorted_levels) - 1):
            low_vol = levels[sorted_levels[va_low_idx - 1]] if va_low_idx > 0 else 0
            high_vol = levels[sorted_levels[va_high_idx + 1]] if va_high_idx < len(sorted_levels) - 1 else 0
            
            if low_vol >= high_vol and va_low_idx > 0:
                va_low_idx -= 1
                current_volume += low_vol
            elif va_high_idx < len(sorted_levels) - 1:
                va_high_idx += 1
                current_volume += high_vol
            else:
                break
        
        return VolumeProfile(
            symbol=bars[0].symbol,
            timeframe=bars[0].timeframe,
            levels=levels,
            poc=poc,
            value_area_high=sorted_levels[va_high_idx],
            value_area_low=sorted_levels[va_low_idx],
            timestamp=datetime.now()
        )
    
    def _get_bar_levels(self, bar: OHLCV, price_low: float, level_size: float) -> List[float]:
        """Get price levels touched by a bar"""
        levels = []
        current = bar.low
        
        while current <= bar.high:
            level_idx = int((current - price_low) / level_size)
            level_price = price_low + (level_idx + 0.5) * level_size
            if level_price not in levels:
                levels.append(level_price)
            current += level_size
        
        return levels
    
    def find_high_volume_nodes(self, profile: VolumeProfile, threshold: float = 0.8) -> List[float]:
        """Find high volume nodes (support/resistance)"""
        if not profile.levels:
            return []
        
        max_volume = max(profile.levels.values())
        threshold_volume = max_volume * threshold
        
        return [price for price, vol in profile.levels.items() if vol >= threshold_volume]
    
    def find_low_volume_nodes(self, profile: VolumeProfile, threshold: float = 0.2) -> List[float]:
        """Find low volume nodes (potential breakout areas)"""
        if not profile.levels:
            return []
        
        max_volume = max(profile.levels.values())
        threshold_volume = max_volume * threshold
        
        return [price for price, vol in profile.levels.items() if vol <= threshold_volume]


class OrderBookDepth:
    """Analyzes order book depth for liquidity"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.history: Dict[str, deque] = {}
        self.history_size = self.config.get('history_size', 100)
    
    def update(self, order_book: OrderBook):
        """Update order book history"""
        if order_book.symbol not in self.history:
            self.history[order_book.symbol] = deque(maxlen=self.history_size)
        self.history[order_book.symbol].append(order_book)
    
    def get_liquidity_score(self, order_book: OrderBook, levels: int = 5) -> float:
        """Calculate liquidity score (0-1)"""
        depth = order_book.get_depth(levels)
        total_depth = depth['bid_depth'] + depth['ask_depth']
        
        # Normalize based on typical depth (configurable)
        typical_depth = self.config.get('typical_depth', 1000.0)
        score = min(total_depth / typical_depth, 1.0)
        
        return score
    
    def get_imbalance(self, order_book: OrderBook, levels: int = 5) -> float:
        """Get order book imbalance (-1 to 1)"""
        depth = order_book.get_depth(levels)
        return depth['imbalance']
    
    def detect_large_orders(self, order_book: OrderBook, threshold: float = 2.0) -> List[Dict]:
        """Detect unusually large orders"""
        large_orders = []
        
        # Calculate average order size
        all_volumes = [l.volume for l in order_book.bids + order_book.asks]
        if not all_volumes:
            return []
        
        avg_volume = statistics.mean(all_volumes)
        threshold_volume = avg_volume * threshold
        
        for level in order_book.bids:
            if level.volume >= threshold_volume:
                large_orders.append({
                    'side': 'bid',
                    'price': level.price,
                    'volume': level.volume,
                    'ratio': level.volume / avg_volume
                })
        
        for level in order_book.asks:
            if level.volume >= threshold_volume:
                large_orders.append({
                    'side': 'ask',
                    'price': level.price,
                    'volume': level.volume,
                    'ratio': level.volume / avg_volume
                })
        
        return large_orders
    
    def get_price_impact(self, order_book: OrderBook, volume: float, side: str) -> float:
        """Estimate price impact for a given volume"""
        levels = order_book.asks if side.lower() == 'buy' else order_book.bids
        
        remaining_volume = volume
        total_cost = 0.0
        
        for level in levels:
            if remaining_volume <= 0:
                break
            
            fill_volume = min(remaining_volume, level.volume)
            total_cost += fill_volume * level.price
            remaining_volume -= fill_volume
        
        if volume > 0:
            avg_price = total_cost / (volume - remaining_volume) if (volume - remaining_volume) > 0 else 0
            mid_price = order_book.mid_price
            
            if mid_price > 0:
                return abs(avg_price - mid_price) / mid_price
        
        return 0.0


class DataStalenessDetector:
    """Detects stale data and triggers source switching"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.max_age_seconds = self.config.get('max_age_seconds', 30)
        self.warning_age_seconds = self.config.get('warning_age_seconds', 15)
        self.last_updates: Dict[str, Dict[str, datetime]] = {}  # symbol -> source -> timestamp
        self._callbacks: List[Callable] = []
    
    def update(self, symbol: str, source: str, timestamp: Optional[datetime] = None):
        """Record data update"""
        if symbol not in self.last_updates:
            self.last_updates[symbol] = {}
        self.last_updates[symbol][source] = timestamp or datetime.now()
    
    def check_staleness(self, symbol: str, source: str) -> Tuple[bool, float]:
        """Check if data is stale, returns (is_stale, age_seconds)"""
        if symbol not in self.last_updates or source not in self.last_updates[symbol]:
            return True, float('inf')
        
        last_update = self.last_updates[symbol][source]
        age = (datetime.now() - last_update).total_seconds()
        
        is_stale = age > self.max_age_seconds
        
        if is_stale:
            asyncio.create_task(self._notify_staleness(symbol, source, age))
        
        return is_stale, age
    
    def get_freshest_source(self, symbol: str) -> Optional[str]:
        """Get the freshest data source for a symbol"""
        if symbol not in self.last_updates:
            return None
        
        sources = self.last_updates[symbol]
        if not sources:
            return None
        
        return min(sources.keys(), key=lambda s: (datetime.now() - sources[s]).total_seconds())
    
    def register_callback(self, callback: Callable):
        """Register staleness callback"""
        self._callbacks.append(callback)
    
    async def _notify_staleness(self, symbol: str, source: str, age: float):
        """Notify staleness callbacks"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(symbol, source, age)
                else:
                    callback(symbol, source, age)
            except Exception as e:
                logger.error(f"Staleness callback error: {e}")


class DataSourceSwitcher:
    """Automatically switches between data sources"""
    
    def __init__(self, sources: List[DataSource], staleness_detector: DataStalenessDetector):
        self.sources = {s.name: s for s in sources}
        self.staleness_detector = staleness_detector
        self.active_sources: Dict[str, str] = {}  # symbol -> source_name
        self.source_priority = sorted(sources, key=lambda s: s.priority)
    
    async def get_best_source(self, symbol: str) -> Optional[DataSource]:
        """Get the best available source for a symbol"""
        # Check current active source
        if symbol in self.active_sources:
            current = self.active_sources[symbol]
            is_stale, _ = self.staleness_detector.check_staleness(symbol, current)
            
            if not is_stale and self.sources[current].status == DataSourceStatus.ACTIVE:
                return self.sources[current]
        
        # Find best available source
        for source in self.source_priority:
            if source.status == DataSourceStatus.ACTIVE:
                is_stale, _ = self.staleness_detector.check_staleness(symbol, source.name)
                if not is_stale:
                    self.active_sources[symbol] = source.name
                    return source
        
        # Fallback to any available source
        for source in self.source_priority:
            if source.status != DataSourceStatus.OFFLINE:
                self.active_sources[symbol] = source.name
                return source
        
        return None
    
    async def switch_source(self, symbol: str, reason: str = ""):
        """Force switch to next available source"""
        current = self.active_sources.get(symbol)
        
        for source in self.source_priority:
            if source.name != current and source.status != DataSourceStatus.OFFLINE:
                old_source = current
                self.active_sources[symbol] = source.name
                logger.info(f"Switched {symbol} from {old_source} to {source.name}: {reason}")
                return
        
        logger.warning(f"No alternative source available for {symbol}")


class DataFeedQuality:
    """
    Master data feed quality manager.
    Combines all data quality functionality.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize data sources
        self.sources: List[DataSource] = []
        self._init_sources()
        
        # Initialize components
        self.validator = MultiSourceValidator(self.sources, self.config)
        self.tick_processor = TickDataProcessor(self.config)
        self.volume_analyzer = VolumeProfileAnalyzer(self.config)
        self.order_book_depth = OrderBookDepth(self.config)
        self.staleness_detector = DataStalenessDetector(self.config)
        self.source_switcher = DataSourceSwitcher(self.sources, self.staleness_detector)
        
        # Register staleness callback
        self.staleness_detector.register_callback(self._on_staleness)
    
    def _init_sources(self):
        """Initialize data sources"""
        # Add MT5 as primary
        self.sources.append(MT5DataSource(priority=1))
        
        # Add Yahoo Finance as backup
        self.sources.append(YahooFinanceDataSource(priority=2))
    
    async def _on_staleness(self, symbol: str, source: str, age: float):
        """Handle staleness detection"""
        logger.warning(f"Stale data detected: {symbol} from {source} (age: {age:.1f}s)")
        await self.source_switcher.switch_source(symbol, f"Stale data ({age:.1f}s)")
    
    async def get_tick(self, symbol: str) -> Tuple[Optional[Tick], DataQuality]:
        """Get validated tick data"""
        tick, quality = await self.validator.get_validated_tick(symbol)
        
        if tick:
            self.tick_processor.add_tick(tick)
            self.staleness_detector.update(symbol, tick.source, tick.timestamp)
        
        return tick, quality
    
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        """Get OHLCV data from best source"""
        source = await self.source_switcher.get_best_source(symbol)
        
        if source:
            bars = await source.get_ohlcv(symbol, timeframe, limit)
            if bars:
                self.staleness_detector.update(symbol, source.name)
                return bars
        
        # Fallback to any source
        for src in self.sources:
            bars = await src.get_ohlcv(symbol, timeframe, limit)
            if bars:
                return bars
        
        return []
    
    async def get_order_book(self, symbol: str, depth: int = 10) -> Optional[OrderBook]:
        """Get order book data"""
        source = await self.source_switcher.get_best_source(symbol)
        
        if source:
            order_book = await source.get_order_book(symbol, depth)
            if order_book:
                self.order_book_depth.update(order_book)
                return order_book
        
        return None
    
    async def get_volume_profile(self, symbol: str, timeframe: str = 'H1', bars: int = 100) -> Optional[VolumeProfile]:
        """Get volume profile"""
        ohlcv = await self.get_ohlcv(symbol, timeframe, bars)
        if ohlcv:
            return self.volume_analyzer.calculate_volume_profile(ohlcv)
        return None
    
    def get_tick_stats(self, symbol: str) -> Dict[str, Any]:
        """Get tick statistics"""
        return self.tick_processor.get_tick_statistics(symbol)
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Get overall data quality report"""
        source_status = {s.name: {
            'status': s.status.value,
            'latency_ms': s.latency_ms,
            'error_count': s.error_count,
            'last_update': s.last_update.isoformat() if s.last_update else None
        } for s in self.sources}
        
        return {
            'sources': source_status,
            'validation_stats': self.validator.get_validation_stats(),
            'active_sources': dict(self.source_switcher.active_sources)
        }
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all data sources"""
        results = {}
        for source in self.sources:
            results[source.name] = await source.health_check()
        return results
