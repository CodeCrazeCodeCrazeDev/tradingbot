import logging
logger = logging.getLogger(__name__)
"""
Real-Time Liquidity Analysis Module

This module provides real-time streaming capabilities for liquidity analysis,
enabling continuous monitoring of liquidity pools, order blocks, and fair value gaps
with minimal latency and memory overhead.
"""

import asyncio
import threading
import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import weakref
import json

import numpy as np
import pandas as pd
from loguru import logger

from .liquidity import (
    LiquidityAnalyzer, LiquidityPool, OrderBlock, FairValueGap, LiquidityGrab,
    LiquidityType, OrderBlockType, FVGType
)
from .market_structure import TimeFrame
from ..performance.memory_optimization import MemoryOptimizer, RingBuffer, DataStructureType
import numpy
import pandas


class StreamingMode(Enum):
    """Streaming modes for real-time analysis."""
    TICK_BY_TICK = "tick_by_tick"
    CANDLE_CLOSE = "candle_close"
    TIME_INTERVAL = "time_interval"
    VOLUME_THRESHOLD = "volume_threshold"


class AlertType(Enum):
    """Types of liquidity alerts."""
    POOL_FORMED = "pool_formed"
    POOL_GRABBED = "pool_grabbed"
    ORDER_BLOCK_FORMED = "order_block_formed"
    ORDER_BLOCK_MITIGATED = "order_block_mitigated"
    FVG_FORMED = "fvg_formed"
    FVG_FILLED = "fvg_filled"
    PREMIUM_ZONE_ENTERED = "premium_zone_entered"
    DISCOUNT_ZONE_ENTERED = "discount_zone_entered"


@dataclass
class LiquidityAlert:
    """Real-time liquidity alert."""
    alert_type: AlertType
    timestamp: float
    symbol: str
    timeframe: TimeFrame
    price: float
    data: Dict[str, Any]
    strength: float = 1.0
    confidence: float = 1.0


@dataclass
class StreamingConfig:
    """Configuration for real-time streaming."""
    mode: StreamingMode = StreamingMode.CANDLE_CLOSE
    update_interval: float = 1.0  # seconds
    volume_threshold: float = 1000.0
    buffer_size: int = 1000
    enable_alerts: bool = True
    alert_threshold: float = 1.2
    memory_optimization: bool = True
    max_history: int = 10000


class RealTimeLiquidityAnalyzer:
    """
    Real-time liquidity analysis with streaming capabilities.
    
    Provides continuous monitoring of liquidity conditions with minimal latency
    and memory overhead using optimized data structures and algorithms.
    """
    
    def __init__(self, config: StreamingConfig = None):
        """Initialize the real-time liquidity analyzer."""
        self.config = config or StreamingConfig()
        
        # Core analyzer
        self.analyzer = LiquidityAnalyzer(
            multi_timeframe=True,
            default_timeframe=TimeFrame.M15
        )
        
        # Memory optimizer
        self.memory_optimizer = MemoryOptimizer()
        
        # Streaming data buffers
        self.price_buffers: Dict[str, Dict[TimeFrame, RingBuffer]] = defaultdict(
            lambda: defaultdict(lambda: RingBuffer(self.config.buffer_size))
        )
        self.volume_buffers: Dict[str, Dict[TimeFrame, RingBuffer]] = defaultdict(
            lambda: defaultdict(lambda: RingBuffer(self.config.buffer_size))
        )
        
        # Real-time state tracking
        self.active_pools: Dict[str, Dict[TimeFrame, List[LiquidityPool]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.active_order_blocks: Dict[str, Dict[TimeFrame, List[OrderBlock]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.active_fvgs: Dict[str, Dict[TimeFrame, List[FairValueGap]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # Alert system
        self.alert_callbacks: List[Callable[[LiquidityAlert], None]] = []
        self.alert_history: deque = deque(maxlen=1000)
        
        # Performance tracking
        self.update_times: deque = deque(maxlen=100)
        self.processing_stats = {
            'total_updates': 0,
            'avg_update_time': 0.0,
            'alerts_generated': 0,
            'memory_usage': 0
        }
        
        # Threading
        self.running = False
        self.update_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()
        
        # Async support
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        
    def start_streaming(self, symbols: List[str], timeframes: List[TimeFrame]):
        """Start real-time streaming for specified symbols and timeframes."""
        logger.info(f"Starting real-time liquidity streaming for {len(symbols)} symbols, {len(timeframes)} timeframes")
        
        self.symbols = symbols
        self.timeframes = timeframes
        self.running = True
        
        # Initialize buffers for all symbol-timeframe combinations
        for symbol in symbols:
            for tf in timeframes:
                self.price_buffers[symbol][tf] = RingBuffer(self.config.buffer_size, dtype=np.float32)
                self.volume_buffers[symbol][tf] = RingBuffer(self.config.buffer_size, dtype=np.float32)
        
        # Start update thread based on streaming mode
        if self.config.mode == StreamingMode.TIME_INTERVAL:
            self.update_thread = threading.Thread(target=self._time_based_updates, daemon=True)
            self.update_thread.start()
        
        logger.info("Real-time liquidity streaming started")
    
    def stop_streaming(self):
        """Stop real-time streaming."""
        logger.info("Stopping real-time liquidity streaming")
        
        self.running = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5.0)
        
        logger.info("Real-time liquidity streaming stopped")
    
    def update_tick(self, symbol: str, timeframe: TimeFrame, price: float, 
                   volume: float, timestamp: Optional[float] = None):
        """Update with new tick data."""
        if not self.running:
            return
        
        start_time = time.time()
        
        with self.lock:
            # Add to buffers
            ts = int((timestamp or time.time()) * 1000)
            self.price_buffers[symbol][timeframe].append(price, ts)
            self.volume_buffers[symbol][timeframe].append(volume, ts)
            
            # Process based on streaming mode
            if self.config.mode == StreamingMode.TICK_BY_TICK:
                self._process_symbol_timeframe(symbol, timeframe)
            elif self.config.mode == StreamingMode.VOLUME_THRESHOLD:
                total_volume = np.sum(self.volume_buffers[symbol][timeframe].get_latest(10))
                if total_volume >= self.config.volume_threshold:
                    self._process_symbol_timeframe(symbol, timeframe)
        
        # Track performance
        update_time = time.time() - start_time
        self.update_times.append(update_time)
        self.processing_stats['total_updates'] += 1
        self.processing_stats['avg_update_time'] = np.mean(self.update_times)
    
    def update_candle(self, symbol: str, timeframe: TimeFrame, ohlcv: Dict[str, float]):
        """Update with new candle data."""
        if not self.running:
            return
        
        start_time = time.time()
        
        with self.lock:
            # Extract OHLCV data
            open_price = ohlcv.get('open', 0.0)
            high = ohlcv.get('high', 0.0)
            low = ohlcv.get('low', 0.0)
            close = ohlcv.get('close', 0.0)
            volume = ohlcv.get('volume', 0.0)
            timestamp = ohlcv.get('timestamp', time.time())
            
            # Add to buffers (using close price for price buffer)
            ts = int(timestamp * 1000)
            self.price_buffers[symbol][timeframe].append(close, ts)
            self.volume_buffers[symbol][timeframe].append(volume, ts)
            
            # Process on candle close
            if self.config.mode == StreamingMode.CANDLE_CLOSE:
                self._process_symbol_timeframe(symbol, timeframe, ohlcv)
        
        # Track performance
        update_time = time.time() - start_time
        self.update_times.append(update_time)
        self.processing_stats['total_updates'] += 1
        self.processing_stats['avg_update_time'] = np.mean(self.update_times)
    
    def _time_based_updates(self):
        """Time-based update loop."""
        while self.running:
            try:
                start_time = time.time()
                
                with self.lock:
                    for symbol in self.symbols:
                        for timeframe in self.timeframes:
                            self._process_symbol_timeframe(symbol, timeframe)
                
                # Track performance
                update_time = time.time() - start_time
                self.update_times.append(update_time)
                self.processing_stats['total_updates'] += 1
                self.processing_stats['avg_update_time'] = np.mean(self.update_times)
                
                # Sleep for the remainder of the interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.config.update_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in time-based updates: {e}")
                time.sleep(1.0)
    
    def _process_symbol_timeframe(self, symbol: str, timeframe: TimeFrame, 
                                ohlcv: Optional[Dict[str, float]] = None):
        """Process liquidity analysis for a specific symbol and timeframe."""
        try:
            # Get recent data from buffers
            prices = self.price_buffers[symbol][timeframe].get_values()
            volumes = self.volume_buffers[symbol][timeframe].get_values()
            timestamps = self.price_buffers[symbol][timeframe].get_timestamps()
            
            if len(prices) < 10:  # Need minimum data for analysis
                return
            
            # Create DataFrame for analysis
            df = self._create_analysis_dataframe(prices, volumes, timestamps, ohlcv)
            
            if self.config.memory_optimization:
                df, _ = self.memory_optimizer.optimize_dataframe(df, DataStructureType.OHLCV)
            
            # Perform liquidity analysis
            self._analyze_liquidity_pools(symbol, timeframe, df)
            self._analyze_order_blocks(symbol, timeframe, df)
            self._analyze_fair_value_gaps(symbol, timeframe, df)
            
            # Check for premium/discount zones
            self._check_premium_discount_zones(symbol, timeframe, df)
            
            # Clean up old data
            self._cleanup_expired_data(symbol, timeframe)
            
        except Exception as e:
            logger.error(f"Error processing {symbol} {timeframe}: {e}")
    
    def _create_analysis_dataframe(self, prices: np.ndarray, volumes: np.ndarray, 
                                 timestamps: np.ndarray, ohlcv: Optional[Dict[str, float]] = None) -> pd.DataFrame:
        """Create DataFrame for liquidity analysis."""
        if ohlcv:
            # Use provided OHLCV data for the latest candle
            data = {
                'open': np.append(prices[:-1], ohlcv['open']),
                'high': np.append(prices[:-1], ohlcv['high']),
                'low': np.append(prices[:-1], ohlcv['low']),
                'close': prices,
                'volume': volumes
            }
        else:
            # Estimate OHLC from price data (simplified)
            data = {
                'open': np.roll(prices, 1),
                'high': prices,  # Simplified - in real implementation, track high/low
                'low': prices,
                'close': prices,
                'volume': volumes
            }
            data['open'][0] = prices[0]  # Fix first value
        
        # Create timestamps index
        dt_index = pd.to_datetime(timestamps, unit='ms')
        
        return pd.DataFrame(data, index=dt_index)
    
    def _analyze_liquidity_pools(self, symbol: str, timeframe: TimeFrame, df: pd.DataFrame):
        """Analyze liquidity pools and detect changes."""
        try:
            buy_pools, sell_pools = self.analyzer.find_equal_highs_lows(df, timeframe)
            
            # Compare with existing pools to detect new formations
            existing_buy = self.active_pools[symbol][timeframe]
            existing_sell = self.active_pools[symbol][timeframe]
            
            # Detect new buy pools
            for pool in buy_pools:
                if not self._pool_exists(pool, existing_buy):
                    self.active_pools[symbol][timeframe].append(pool)
                    
                    if self.config.enable_alerts and pool.strength >= self.config.alert_threshold:
                        alert = LiquidityAlert(
                            alert_type=AlertType.POOL_FORMED,
                            timestamp=time.time(),
                            symbol=symbol,
                            timeframe=timeframe,
                            price=pool.price,
                            data={'pool': pool, 'type': 'buy'},
                            strength=pool.strength
                        )
                        self._emit_alert(alert)
            
            # Detect new sell pools
            for pool in sell_pools:
                if not self._pool_exists(pool, existing_sell):
                    self.active_pools[symbol][timeframe].append(pool)
                    
                    if self.config.enable_alerts and pool.strength >= self.config.alert_threshold:
                        alert = LiquidityAlert(
                            alert_type=AlertType.POOL_FORMED,
                            timestamp=time.time(),
                            symbol=symbol,
                            timeframe=timeframe,
                            price=pool.price,
                            data={'pool': pool, 'type': 'sell'},
                            strength=pool.strength
                        )
                        self._emit_alert(alert)
            
            # Check for liquidity grabs
            all_pools = buy_pools + sell_pools
            grabs = self.analyzer.detect_grabs(df, all_pools, timeframe)
            
            for grab in grabs:
                if grab.confirmed and self.config.enable_alerts:
                    alert = LiquidityAlert(
                        alert_type=AlertType.POOL_GRABBED,
                        timestamp=time.time(),
                        symbol=symbol,
                        timeframe=timeframe,
                        price=grab.close_price,
                        data={'grab': grab},
                        strength=grab.strength
                    )
                    self._emit_alert(alert)
            
        except Exception as e:
            logger.error(f"Error analyzing liquidity pools for {symbol} {timeframe}: {e}")
    
    def _analyze_order_blocks(self, symbol: str, timeframe: TimeFrame, df: pd.DataFrame):
        """Analyze order blocks and detect changes."""
        try:
            order_blocks = self.analyzer.detect_order_blocks(df, timeframe)
            
            # Compare with existing order blocks
            existing_obs = self.active_order_blocks[symbol][timeframe]
            
            for ob in order_blocks:
                if not self._order_block_exists(ob, existing_obs):
                    self.active_order_blocks[symbol][timeframe].append(ob)
                    
                    if self.config.enable_alerts and ob.strength >= self.config.alert_threshold:
                        alert = LiquidityAlert(
                            alert_type=AlertType.ORDER_BLOCK_FORMED,
                            timestamp=time.time(),
                            symbol=symbol,
                            timeframe=timeframe,
                            price=(ob.high + ob.low) / 2,
                            data={'order_block': ob},
                            strength=ob.strength
                        )
                        self._emit_alert(alert)
            
            # Check for mitigation
            self.analyzer.check_order_block_mitigation(df, existing_obs)
            
            for ob in existing_obs:
                if ob.mitigated and self.config.enable_alerts:
                    alert = LiquidityAlert(
                        alert_type=AlertType.ORDER_BLOCK_MITIGATED,
                        timestamp=time.time(),
                        symbol=symbol,
                        timeframe=timeframe,
                        price=(ob.high + ob.low) / 2,
                        data={'order_block': ob},
                        strength=ob.strength
                    )
                    self._emit_alert(alert)
            
        except Exception as e:
            logger.error(f"Error analyzing order blocks for {symbol} {timeframe}: {e}")
    
    def _analyze_fair_value_gaps(self, symbol: str, timeframe: TimeFrame, df: pd.DataFrame):
        """Analyze fair value gaps and detect changes."""
        try:
            fvgs = self.analyzer.detect_fair_value_gaps(df, timeframe)
            
            # Compare with existing FVGs
            existing_fvgs = self.active_fvgs[symbol][timeframe]
            
            for fvg in fvgs:
                if not self._fvg_exists(fvg, existing_fvgs):
                    self.active_fvgs[symbol][timeframe].append(fvg)
                    
                    if self.config.enable_alerts and fvg.strength >= self.config.alert_threshold:
                        alert = LiquidityAlert(
                            alert_type=AlertType.FVG_FORMED,
                            timestamp=time.time(),
                            symbol=symbol,
                            timeframe=timeframe,
                            price=(fvg.high + fvg.low) / 2,
                            data={'fvg': fvg},
                            strength=fvg.strength
                        )
                        self._emit_alert(alert)
            
            # Check for filling
            self.analyzer.check_fvg_filling(df, existing_fvgs)
            
            for fvg in existing_fvgs:
                if fvg.filled and self.config.enable_alerts:
                    alert = LiquidityAlert(
                        alert_type=AlertType.FVG_FILLED,
                        timestamp=time.time(),
                        symbol=symbol,
                        timeframe=timeframe,
                        price=(fvg.high + fvg.low) / 2,
                        data={'fvg': fvg},
                        strength=fvg.strength
                    )
                    self._emit_alert(alert)
            
        except Exception as e:
            logger.error(f"Error analyzing FVGs for {symbol} {timeframe}: {e}")
    
    def _check_premium_discount_zones(self, symbol: str, timeframe: TimeFrame, df: pd.DataFrame):
        """Check for premium and discount zone entries."""
        try:
            premium_zones, discount_zones = self.analyzer.identify_premium_discount_zones(df, timeframe)
            current_price = df['close'].iloc[-1]
            
            # Check premium zone entries
            for high, low in premium_zones:
                if low <= current_price <= high:
                    if self.config.enable_alerts:
                        alert = LiquidityAlert(
                            alert_type=AlertType.PREMIUM_ZONE_ENTERED,
                            timestamp=time.time(),
                            symbol=symbol,
                            timeframe=timeframe,
                            price=current_price,
                            data={'zone': (high, low)},
                            strength=1.5
                        )
                        self._emit_alert(alert)
            
            # Check discount zone entries
            for high, low in discount_zones:
                if low <= current_price <= high:
                    if self.config.enable_alerts:
                        alert = LiquidityAlert(
                            alert_type=AlertType.DISCOUNT_ZONE_ENTERED,
                            timestamp=time.time(),
                            symbol=symbol,
                            timeframe=timeframe,
                            price=current_price,
                            data={'zone': (high, low)},
                            strength=1.5
                        )
                        self._emit_alert(alert)
            
        except Exception as e:
            logger.error(f"Error checking premium/discount zones for {symbol} {timeframe}: {e}")
    
    def _pool_exists(self, pool: LiquidityPool, existing_pools: List[LiquidityPool]) -> bool:
        """Check if a liquidity pool already exists."""
        tolerance = 0.0001
        for existing in existing_pools:
            if (existing.kind == pool.kind and 
                abs(existing.price - pool.price) < tolerance):
                return True
        return False
    
    def _order_block_exists(self, ob: OrderBlock, existing_obs: List[OrderBlock]) -> bool:
        """Check if an order block already exists."""
        for existing in existing_obs:
            if (existing.start_idx == ob.start_idx and 
                existing.type == ob.type):
                return True
        return False
    
    def _fvg_exists(self, fvg: FairValueGap, existing_fvgs: List[FairValueGap]) -> bool:
        """Check if a fair value gap already exists."""
        for existing in existing_fvgs:
            if (existing.idx == fvg.idx and 
                existing.type == fvg.type):
                return True
        return False
    
    def _cleanup_expired_data(self, symbol: str, timeframe: TimeFrame):
        """Clean up expired liquidity data."""
        current_time = time.time()
        
        # Remove old pools (older than max_history)
        self.active_pools[symbol][timeframe] = [
            pool for pool in self.active_pools[symbol][timeframe]
            if not pool.created_at or 
            (current_time - pool.created_at.timestamp()) < self.config.max_history
        ]
        
        # Remove old order blocks
        self.active_order_blocks[symbol][timeframe] = [
            ob for ob in self.active_order_blocks[symbol][timeframe]
            if not ob.created_at or 
            (current_time - ob.created_at.timestamp()) < self.config.max_history
        ]
        
        # Remove old FVGs
        self.active_fvgs[symbol][timeframe] = [
            fvg for fvg in self.active_fvgs[symbol][timeframe]
            if not fvg.created_at or 
            (current_time - fvg.created_at.timestamp()) < self.config.max_history
        ]
    
    def _emit_alert(self, alert: LiquidityAlert):
        """Emit a liquidity alert to all registered callbacks."""
        try:
            self.alert_history.append(alert)
            self.processing_stats['alerts_generated'] += 1
            
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
            
            logger.info(f"Alert: {alert.alert_type.value} for {alert.symbol} at {alert.price}")
            
        except Exception as e:
            logger.error(f"Error emitting alert: {e}")
    
    def add_alert_callback(self, callback: Callable[[LiquidityAlert], None]):
        """Add an alert callback function."""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[LiquidityAlert], None]):
        """Remove an alert callback function."""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def get_active_liquidity(self, symbol: str, timeframe: TimeFrame) -> Dict[str, List]:
        """Get all active liquidity data for a symbol and timeframe."""
        return {
            'pools': self.active_pools[symbol][timeframe],
            'order_blocks': self.active_order_blocks[symbol][timeframe],
            'fvgs': self.active_fvgs[symbol][timeframe]
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            **self.processing_stats,
            'buffer_usage': {
                symbol: {
                    tf.name: {
                        'price_buffer_size': self.price_buffers[symbol][tf].size,
                        'volume_buffer_size': self.volume_buffers[symbol][tf].size
                    }
                    for tf in self.price_buffers[symbol]
                }
                for symbol in self.price_buffers
            },
            'active_data_count': {
                symbol: {
                    tf.name: {
                        'pools': len(self.active_pools[symbol][tf]),
                        'order_blocks': len(self.active_order_blocks[symbol][tf]),
                        'fvgs': len(self.active_fvgs[symbol][tf])
                    }
                    for tf in self.active_pools[symbol]
                }
                for symbol in self.active_pools
            }
        }
    
    async def async_update_tick(self, symbol: str, timeframe: TimeFrame, 
                              price: float, volume: float, timestamp: Optional[float] = None):
        """Async version of update_tick."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.update_tick, symbol, timeframe, price, volume, timestamp)
    
    async def async_update_candle(self, symbol: str, timeframe: TimeFrame, ohlcv: Dict[str, float]):
        """Async version of update_candle."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.update_candle, symbol, timeframe, ohlcv)


# Utility functions for easy integration
def create_default_streaming_analyzer(symbols: List[str], timeframes: List[TimeFrame]) -> RealTimeLiquidityAnalyzer:
    """Create a default real-time liquidity analyzer with optimized settings."""
    config = StreamingConfig(
        mode=StreamingMode.CANDLE_CLOSE,
        update_interval=1.0,
        buffer_size=1000,
        enable_alerts=True,
        alert_threshold=1.2,
        memory_optimization=True,
        max_history=3600  # 1 hour
    )
    
    analyzer = RealTimeLiquidityAnalyzer(config)
    analyzer.start_streaming(symbols, timeframes)
    
    return analyzer


def create_high_frequency_analyzer(symbols: List[str], timeframes: List[TimeFrame]) -> RealTimeLiquidityAnalyzer:
    """Create a high-frequency real-time analyzer for tick-by-tick analysis."""
    config = StreamingConfig(
        mode=StreamingMode.TICK_BY_TICK,
        update_interval=0.1,
        buffer_size=5000,
        enable_alerts=True,
        alert_threshold=1.0,
        memory_optimization=True,
        max_history=1800  # 30 minutes
    )
    
    analyzer = RealTimeLiquidityAnalyzer(config)
    analyzer.start_streaming(symbols, timeframes)
    
    return analyzer


if __name__ == "__main__":
    # Example usage
    
    def alert_handler(alert: LiquidityAlert):
        logger.info(f"ALERT: {alert.alert_type.value} - {alert.symbol} @ {alert.price:.5f}")
    
    # Create analyzer
    analyzer = create_default_streaming_analyzer(['EURUSD'], [TimeFrame.M15])
    analyzer.add_alert_callback(alert_handler)
    
    # Simulate some market data
    base_price = 1.1000
    for i in range(100):
        price = base_price + np.random.normal(0, 0.0001)
        volume = np.random.uniform(100, 1000)
        
        analyzer.update_tick('EURUSD', TimeFrame.M15, price, volume)
        time.sleep(0.1)
    
    # Get performance stats
    stats = analyzer.get_performance_stats()
    logger.info(f"Performance: {stats}")
    
    # Stop streaming
    analyzer.stop_streaming()
