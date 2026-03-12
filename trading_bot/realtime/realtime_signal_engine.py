"""
Real-Time Signal Engine
=======================

Event-driven signal generation that reacts to real-time data streams.
No polling - signals are generated immediately when conditions are met.

Features:
1. Event-driven signal generation
2. Multi-timeframe real-time analysis
3. Real-time indicator calculation
4. Signal confidence scoring
5. Signal TTL and decay
6. Duplicate signal prevention
7. Signal broadcasting

Author: AlphaAlgo Trading System
Version: 3.0.0
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import hashlib
import numpy as np

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of trading signals"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    TREND_FOLLOWING = "trend_following"
    ORDERFLOW = "orderflow"
    MICROSTRUCTURE = "microstructure"
    SENTIMENT = "sentiment"
    COMPOSITE = "composite"


class SignalDirection(Enum):
    """Signal direction"""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"


class SignalStrength(Enum):
    """Signal strength classification"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class RealTimeSignal:
    """Real-time trading signal"""
    signal_id: str
    symbol: str
    direction: SignalDirection
    signal_type: SignalType
    confidence: float
    strength: SignalStrength
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    ttl_seconds: int = 60
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl_seconds)
    
    @property
    def age_seconds(self) -> float:
        return (datetime.now() - self.timestamp).total_seconds()
    
    @property
    def decay_factor(self) -> float:
        """Signal confidence decay over time"""
        age = self.age_seconds
        if age >= self.ttl_seconds:
            return 0.0
        return 1.0 - (age / self.ttl_seconds)
    
    @property
    def effective_confidence(self) -> float:
        """Confidence adjusted for decay"""
        return self.confidence * self.decay_factor
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'direction': self.direction.value,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'effective_confidence': self.effective_confidence,
            'strength': self.strength.value,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'timestamp': self.timestamp.isoformat(),
            'ttl_seconds': self.ttl_seconds,
            'age_seconds': self.age_seconds,
            'is_expired': self.is_expired,
            'metadata': self.metadata
        }


class RealTimeIndicators:
    """
    Real-time indicator calculations.
    Updates incrementally with each new tick.
    """
    
    def __init__(self, symbol: str, max_periods: int = 500):
        self.symbol = symbol
        self.max_periods = max_periods
        
        # Price buffers
        self._prices: deque = deque(maxlen=max_periods)
        self._highs: deque = deque(maxlen=max_periods)
        self._lows: deque = deque(maxlen=max_periods)
        self._volumes: deque = deque(maxlen=max_periods)
        self._timestamps: deque = deque(maxlen=max_periods)
        
        # Cached calculations
        self._ema_cache: Dict[int, float] = {}
        self._sma_cache: Dict[int, float] = {}
        self._rsi_cache: Dict[int, float] = {}
        self._atr_cache: Dict[int, float] = {}
        
        # Last update
        self._last_update: Optional[datetime] = None
    
    def update(self, price: float, high: float = None, low: float = None, 
               volume: float = 0, timestamp: datetime = None):
        """Update with new price data"""
        high = high or price
        low = low or price
        timestamp = timestamp or datetime.now()
        
        self._prices.append(price)
        self._highs.append(high)
        self._lows.append(low)
        self._volumes.append(volume)
        self._timestamps.append(timestamp)
        
        # Invalidate caches
        self._ema_cache.clear()
        self._sma_cache.clear()
        self._rsi_cache.clear()
        self._atr_cache.clear()
        
        self._last_update = timestamp
    
    @property
    def prices(self) -> np.ndarray:
        return np.array(self._prices)
    
    @property
    def current_price(self) -> Optional[float]:
        return self._prices[-1] if self._prices else None
    
    def sma(self, period: int) -> Optional[float]:
        """Simple Moving Average"""
        if period in self._sma_cache:
            return self._sma_cache[period]
        
        if len(self._prices) < period:
            return None
        
        prices = list(self._prices)[-period:]
        result = sum(prices) / period
        self._sma_cache[period] = result
        return result
    
    def ema(self, period: int) -> Optional[float]:
        """Exponential Moving Average"""
        if period in self._ema_cache:
            return self._ema_cache[period]
        
        if len(self._prices) < period:
            return None
        
        prices = list(self._prices)
        multiplier = 2 / (period + 1)
        
        # Start with SMA
        ema = sum(prices[:period]) / period
        
        # Calculate EMA
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        self._ema_cache[period] = ema
        return ema
    
    def rsi(self, period: int = 14) -> Optional[float]:
        """Relative Strength Index"""
        if period in self._rsi_cache:
            return self._rsi_cache[period]
        
        if len(self._prices) < period + 1:
            return None
        
        prices = list(self._prices)
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            result = 100.0
        else:
            rs = avg_gain / avg_loss
            result = 100 - (100 / (1 + rs))
        
        self._rsi_cache[period] = result
        return result
    
    def atr(self, period: int = 14) -> Optional[float]:
        """Average True Range"""
        if period in self._atr_cache:
            return self._atr_cache[period]
        
        if len(self._prices) < period + 1:
            return None
        
        highs = list(self._highs)
        lows = list(self._lows)
        closes = list(self._prices)
        
        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)
        
        result = sum(true_ranges[-period:]) / period
        self._atr_cache[period] = result
        return result
    
    def bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> Optional[tuple]:
        """Bollinger Bands (middle, upper, lower)"""
        if len(self._prices) < period:
            return None
        
        prices = list(self._prices)[-period:]
        middle = sum(prices) / period
        std = np.std(prices)
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return (middle, upper, lower)
    
    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[tuple]:
        """MACD (macd_line, signal_line, histogram)"""
        fast_ema = self.ema(fast)
        slow_ema = self.ema(slow)
        
        if fast_ema is None or slow_ema is None:
            return None
        
        macd_line = fast_ema - slow_ema
        
        # For signal line, we'd need historical MACD values
        # Simplified: use current MACD as approximation
        signal_line = macd_line * 0.9  # Approximation
        histogram = macd_line - signal_line
        
        return (macd_line, signal_line, histogram)
    
    def momentum(self, period: int = 10) -> Optional[float]:
        """Price momentum"""
        if len(self._prices) < period:
            return None
        
        prices = list(self._prices)
        return (prices[-1] - prices[-period]) / prices[-period]
    
    def volatility(self, period: int = 20) -> Optional[float]:
        """Price volatility (standard deviation of returns)"""
        if len(self._prices) < period + 1:
            return None
        
        prices = list(self._prices)[-period-1:]
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        return np.std(returns)
    
    def trend_strength(self, period: int = 20) -> Optional[float]:
        """Trend strength (-1 to 1)"""
        if len(self._prices) < period:
            return None
        
        prices = list(self._prices)[-period:]
        
        # Linear regression slope
        x = np.arange(period)
        y = np.array(prices)
        
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalize by price
        normalized_slope = slope / prices[-1] * period
        
        return max(min(normalized_slope * 10, 1.0), -1.0)


class SignalGenerator:
    """
    Base class for signal generators.
    """
    
    def __init__(self, name: str, signal_type: SignalType):
        self.name = name
        self.signal_type = signal_type
        self.enabled = True
        self._signal_count = 0
    
    async def generate(self, symbol: str, indicators: RealTimeIndicators,
                       tick_data: Any = None, orderbook: Any = None) -> Optional[RealTimeSignal]:
        """Generate signal - override in subclass"""
    
    def _create_signal_id(self, symbol: str) -> str:
        """Create unique signal ID"""
        self._signal_count += 1
        return f"{self.name}-{symbol}-{self._signal_count}-{int(time.time()*1000)}"


class MomentumSignalGenerator(SignalGenerator):
    """Momentum-based signal generator"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("momentum", SignalType.MOMENTUM)
        config = config or {}
        self.momentum_period = config.get('period', 10)
        self.threshold = config.get('threshold', 0.005)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
    
    async def generate(self, symbol: str, indicators: RealTimeIndicators,
                       tick_data: Any = None, orderbook: Any = None) -> Optional[RealTimeSignal]:
        momentum = indicators.momentum(self.momentum_period)
        rsi = indicators.rsi(14)
        price = indicators.current_price
        atr = indicators.atr(14)
        
        if momentum is None or rsi is None or price is None or atr is None:
            return None
        
        direction = None
        confidence = 0.0
        
        # Strong momentum with RSI confirmation
        if momentum > self.threshold and rsi < self.rsi_overbought:
            direction = SignalDirection.BUY
            confidence = min(abs(momentum) * 50 + (self.rsi_overbought - rsi) / 100, 1.0)
        elif momentum < -self.threshold and rsi > self.rsi_oversold:
            direction = SignalDirection.SELL
            confidence = min(abs(momentum) * 50 + (rsi - self.rsi_oversold) / 100, 1.0)
        
        if direction is None or confidence < 0.5:
            return None
        
        # Calculate stops
        stop_distance = atr * 2
        take_profit_distance = atr * 3
        
        if direction == SignalDirection.BUY:
            stop_loss = price - stop_distance
            take_profit = price + take_profit_distance
        else:
            stop_loss = price + stop_distance
            take_profit = price - take_profit_distance
        
        strength = self._classify_strength(confidence)
        
        return RealTimeSignal(
            signal_id=self._create_signal_id(symbol),
            symbol=symbol,
            direction=direction,
            signal_type=self.signal_type,
            confidence=confidence,
            strength=strength,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now(),
            ttl_seconds=60,
            metadata={
                'momentum': momentum,
                'rsi': rsi,
                'atr': atr
            }
        )
    
    def _classify_strength(self, confidence: float) -> SignalStrength:
        if confidence >= 0.9:
            return SignalStrength.VERY_STRONG
        elif confidence >= 0.75:
            return SignalStrength.STRONG
        elif confidence >= 0.6:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK


class MeanReversionSignalGenerator(SignalGenerator):
    """Mean reversion signal generator"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("mean_reversion", SignalType.MEAN_REVERSION)
        config = config or {}
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2.0)
        self.rsi_period = config.get('rsi_period', 14)
    
    async def generate(self, symbol: str, indicators: RealTimeIndicators,
                       tick_data: Any = None, orderbook: Any = None) -> Optional[RealTimeSignal]:
        bb = indicators.bollinger_bands(self.bb_period, self.bb_std)
        rsi = indicators.rsi(self.rsi_period)
        price = indicators.current_price
        atr = indicators.atr(14)
        
        if bb is None or rsi is None or price is None or atr is None:
            return None
        
        middle, upper, lower = bb
        direction = None
        confidence = 0.0
        
        # Price at lower band with oversold RSI
        if price <= lower and rsi < 30:
            direction = SignalDirection.BUY
            band_distance = (lower - price) / (upper - lower)
            confidence = min(0.5 + band_distance + (30 - rsi) / 100, 1.0)
        # Price at upper band with overbought RSI
        elif price >= upper and rsi > 70:
            direction = SignalDirection.SELL
            band_distance = (price - upper) / (upper - lower)
            confidence = min(0.5 + band_distance + (rsi - 70) / 100, 1.0)
        
        if direction is None or confidence < 0.5:
            return None
        
        # Target the middle band
        if direction == SignalDirection.BUY:
            stop_loss = price - atr * 1.5
            take_profit = middle
        else:
            stop_loss = price + atr * 1.5
            take_profit = middle
        
        strength = SignalStrength.STRONG if confidence >= 0.75 else SignalStrength.MODERATE
        
        return RealTimeSignal(
            signal_id=self._create_signal_id(symbol),
            symbol=symbol,
            direction=direction,
            signal_type=self.signal_type,
            confidence=confidence,
            strength=strength,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now(),
            ttl_seconds=45,
            metadata={
                'bb_middle': middle,
                'bb_upper': upper,
                'bb_lower': lower,
                'rsi': rsi
            }
        )


class BreakoutSignalGenerator(SignalGenerator):
    """Breakout signal generator"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("breakout", SignalType.BREAKOUT)
        config = config or {}
        self.lookback = config.get('lookback', 20)
        self.volume_threshold = config.get('volume_threshold', 1.5)
    
    async def generate(self, symbol: str, indicators: RealTimeIndicators,
                       tick_data: Any = None, orderbook: Any = None) -> Optional[RealTimeSignal]:
        if len(indicators._prices) < self.lookback:
            return None
        
        price = indicators.current_price
        atr = indicators.atr(14)
        
        if price is None or atr is None:
            return None
        
        # Get recent highs and lows
        recent_highs = list(indicators._highs)[-self.lookback:-1]
        recent_lows = list(indicators._lows)[-self.lookback:-1]
        
        if not recent_highs or not recent_lows:
            return None
        
        resistance = max(recent_highs)
        support = min(recent_lows)
        
        direction = None
        confidence = 0.0
        
        # Breakout above resistance
        if price > resistance:
            direction = SignalDirection.BUY
            breakout_strength = (price - resistance) / atr
            confidence = min(0.6 + breakout_strength * 0.2, 1.0)
        # Breakdown below support
        elif price < support:
            direction = SignalDirection.SELL
            breakdown_strength = (support - price) / atr
            confidence = min(0.6 + breakdown_strength * 0.2, 1.0)
        
        if direction is None or confidence < 0.6:
            return None
        
        # Breakout targets
        range_size = resistance - support
        
        if direction == SignalDirection.BUY:
            stop_loss = resistance - atr * 0.5  # Just below breakout level
            take_profit = price + range_size  # Measured move
        else:
            stop_loss = support + atr * 0.5
            take_profit = price - range_size
        
        return RealTimeSignal(
            signal_id=self._create_signal_id(symbol),
            symbol=symbol,
            direction=direction,
            signal_type=self.signal_type,
            confidence=confidence,
            strength=SignalStrength.STRONG,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now(),
            ttl_seconds=30,
            metadata={
                'resistance': resistance,
                'support': support,
                'range_size': range_size
            }
        )


class OrderFlowSignalGenerator(SignalGenerator):
    """Order flow based signal generator"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("orderflow", SignalType.ORDERFLOW)
        config = config or {}
        self.imbalance_threshold = config.get('imbalance_threshold', 0.3)
    
    async def generate(self, symbol: str, indicators: RealTimeIndicators,
                       tick_data: Any = None, orderbook: Any = None) -> Optional[RealTimeSignal]:
        if orderbook is None:
            return None
        
        price = indicators.current_price
        atr = indicators.atr(14)
        
        if price is None or atr is None:
            return None
        
        # Calculate order book imbalance
        bid_volume = sum(level.quantity for level in orderbook.bids[:10])
        ask_volume = sum(level.quantity for level in orderbook.asks[:10])
        
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return None
        
        imbalance = (bid_volume - ask_volume) / total_volume
        
        direction = None
        confidence = 0.0
        
        if imbalance > self.imbalance_threshold:
            direction = SignalDirection.BUY
            confidence = min(0.5 + abs(imbalance), 1.0)
        elif imbalance < -self.imbalance_threshold:
            direction = SignalDirection.SELL
            confidence = min(0.5 + abs(imbalance), 1.0)
        
        if direction is None or confidence < 0.6:
            return None
        
        if direction == SignalDirection.BUY:
            stop_loss = price - atr * 1.5
            take_profit = price + atr * 2
        else:
            stop_loss = price + atr * 1.5
            take_profit = price - atr * 2
        
        return RealTimeSignal(
            signal_id=self._create_signal_id(symbol),
            symbol=symbol,
            direction=direction,
            signal_type=self.signal_type,
            confidence=confidence,
            strength=SignalStrength.MODERATE,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now(),
            ttl_seconds=20,
            metadata={
                'imbalance': imbalance,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume
            }
        )


class RealTimeSignalEngine:
    """
    Real-time signal generation engine.
    
    Features:
    - Event-driven signal generation
    - Multiple signal generators
    - Signal aggregation and filtering
    - Duplicate prevention
    - Signal broadcasting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Indicators per symbol
        self._indicators: Dict[str, RealTimeIndicators] = {}
        
        # Signal generators
        self._generators: List[SignalGenerator] = []
        self._init_generators()
        
        # Active signals
        self._active_signals: Dict[str, RealTimeSignal] = {}
        self._signal_history: deque = deque(maxlen=1000)
        
        # Subscribers
        self._subscribers: List[Callable] = []
        
        # Duplicate prevention
        self._recent_signal_hashes: Set[str] = set()
        self._hash_expiry: Dict[str, datetime] = {}
        
        # Metrics
        self._metrics = {
            'signals_generated': 0,
            'signals_filtered': 0,
            'signals_expired': 0
        }
        
        self._running = False
        
        logger.info("RealTimeSignalEngine initialized")
    
    def _init_generators(self):
        """Initialize signal generators"""
        gen_config = self.config.get('generators', {})
        
        self._generators = [
            MomentumSignalGenerator(gen_config.get('momentum', {})),
            MeanReversionSignalGenerator(gen_config.get('mean_reversion', {})),
            BreakoutSignalGenerator(gen_config.get('breakout', {})),
            OrderFlowSignalGenerator(gen_config.get('orderflow', {})),
        ]
        
        logger.info(f"Initialized {len(self._generators)} signal generators")
    
    async def on_tick(self, symbol: str, tick_data: Any):
        """Handle new tick data - generate signals"""
        # Update indicators
        if symbol not in self._indicators:
            self._indicators[symbol] = RealTimeIndicators(symbol)
        
        indicators = self._indicators[symbol]
        indicators.update(
            price=tick_data.last,
            high=tick_data.ask,
            low=tick_data.bid,
            volume=tick_data.volume,
            timestamp=tick_data.timestamp
        )
        
        # Generate signals from all generators
        await self._generate_signals(symbol, indicators, tick_data)
    
    async def on_orderbook(self, symbol: str, orderbook: Any):
        """Handle order book update"""
        if symbol not in self._indicators:
            return
        
        indicators = self._indicators[symbol]
        
        # Generate order flow signals
        for generator in self._generators:
            if generator.signal_type == SignalType.ORDERFLOW:
                signal = await generator.generate(symbol, indicators, orderbook=orderbook)
                if signal:
                    await self._process_signal(signal)
    
    async def _generate_signals(self, symbol: str, indicators: RealTimeIndicators,
                                tick_data: Any = None, orderbook: Any = None):
        """Generate signals from all generators"""
        for generator in self._generators:
            if not generator.enabled:
                continue
            try:
            
                signal = await generator.generate(symbol, indicators, tick_data, orderbook)
                if signal:
                    await self._process_signal(signal)
            except Exception as e:
                logger.error(f"Signal generation error in {generator.name}: {e}")
    
    async def _process_signal(self, signal: RealTimeSignal):
        """Process and validate a new signal"""
        # Check for duplicates
        signal_hash = self._compute_signal_hash(signal)
        if signal_hash in self._recent_signal_hashes:
            self._metrics['signals_filtered'] += 1
            return
        
        # Add to duplicate prevention
        self._recent_signal_hashes.add(signal_hash)
        self._hash_expiry[signal_hash] = datetime.now() + timedelta(seconds=signal.ttl_seconds)
        
        # Store signal
        self._active_signals[signal.signal_id] = signal
        self._signal_history.append(signal)
        self._metrics['signals_generated'] += 1
        
        logger.info(f"Signal generated: {signal.symbol} {signal.direction.value} "
                   f"confidence={signal.confidence:.2f} type={signal.signal_type.value}")
        
        # Notify subscribers
        await self._notify_subscribers(signal)
    
    def _compute_signal_hash(self, signal: RealTimeSignal) -> str:
        """Compute hash for duplicate detection"""
        key = f"{signal.symbol}:{signal.direction.value}:{signal.signal_type.value}"
        return hashlib.md5(key.encode()).hexdigest()
    
    async def _notify_subscribers(self, signal: RealTimeSignal):
        """Notify all subscribers of new signal"""
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(signal)
                else:
                    callback(signal)
            except Exception as e:
                logger.error(f"Signal subscriber error: {e}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to signals"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from signals"""
        self._subscribers = [cb for cb in self._subscribers if cb != callback]
    
    def get_active_signals(self, symbol: str = None) -> List[RealTimeSignal]:
        """Get active (non-expired) signals"""
        signals = []
        expired = []
        
        for signal_id, signal in self._active_signals.items():
            if signal.is_expired:
                expired.append(signal_id)
            elif symbol is None or signal.symbol == symbol:
                signals.append(signal)
        
        # Clean up expired
        for signal_id in expired:
            del self._active_signals[signal_id]
            self._metrics['signals_expired'] += 1
        
        return signals
    
    def get_best_signal(self, symbol: str) -> Optional[RealTimeSignal]:
        """Get best signal for a symbol by effective confidence"""
        signals = self.get_active_signals(symbol)
        if not signals:
            return None
        
        return max(signals, key=lambda s: s.effective_confidence)
    
    async def _cleanup_loop(self):
        """Cleanup expired signals and hashes"""
        while self._running:
            try:
                now = datetime.now()
                
                # Clean expired hashes
                expired_hashes = [
                    h for h, exp in self._hash_expiry.items()
                    if now > exp
                ]
                for h in expired_hashes:
                    self._recent_signal_hashes.discard(h)
                    del self._hash_expiry[h]
                
                # Clean expired signals
                self.get_active_signals()  # This cleans up expired
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(10)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics"""
        return {
            **self._metrics,
            'active_signals': len(self._active_signals),
            'symbols_tracked': len(self._indicators),
            'generators_active': len([g for g in self._generators if g.enabled])
        }
    
    async def start(self):
        """Start the signal engine"""
        self._running = True
        asyncio.create_task(self._cleanup_loop())
        logger.info("RealTimeSignalEngine started")
    
    async def stop(self):
        """Stop the signal engine"""
        self._running = False
        logger.info("RealTimeSignalEngine stopped")
