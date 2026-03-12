"""
Signal Processing Upgrades 501-550
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque

# UPGRADE 501: Signal Generator Base
class SignalGeneratorBase:
    def __init__(self, name: str):
        self.name = name
        self.signals: List[Dict] = []
        
    def generate(self, data: Dict) -> Optional[Dict]:
        pass
    
    def record_signal(self, signal: Dict):
        signal['generator'] = self.name
        signal['timestamp'] = datetime.utcnow().isoformat()
        self.signals.append(signal)

# UPGRADE 502: Moving Average Crossover Signal
class MovingAverageCrossoverSignal(SignalGeneratorBase):
    def __init__(self, fast: int = 10, slow: int = 20):
        super().__init__('ma_crossover')
        self.fast = fast
        self.slow = slow
        
    def generate(self, prices: List[float]) -> Optional[Dict]:
        if len(prices) < self.slow: return None
        fast_ma = np.mean(prices[-self.fast:])
        slow_ma = np.mean(prices[-self.slow:])
        prev_fast = np.mean(prices[-self.fast-1:-1])
        prev_slow = np.mean(prices[-self.slow-1:-1])
        if prev_fast <= prev_slow and fast_ma > slow_ma:
            return {'direction': 'long', 'strength': (fast_ma - slow_ma) / slow_ma}
        if prev_fast >= prev_slow and fast_ma < slow_ma:
            return {'direction': 'short', 'strength': (slow_ma - fast_ma) / slow_ma}
        return None

# UPGRADE 503: RSI Signal Generator
class RSISignalGenerator(SignalGeneratorBase):
    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        super().__init__('rsi')
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    def calculate_rsi(self, prices: List[float]) -> float:
        if len(prices) < self.period + 1: return 50
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-self.period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-self.period:]]
        avg_gain = np.mean(gains) or 0.0001
        avg_loss = np.mean(losses) or 0.0001
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def generate(self, prices: List[float]) -> Optional[Dict]:
        rsi = self.calculate_rsi(prices)
        if rsi < self.oversold:
            return {'direction': 'long', 'strength': (self.oversold - rsi) / self.oversold, 'rsi': rsi}
        if rsi > self.overbought:
            return {'direction': 'short', 'strength': (rsi - self.overbought) / (100 - self.overbought), 'rsi': rsi}
        return None

# UPGRADE 504: MACD Signal Generator
class MACDSignalGenerator(SignalGeneratorBase):
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__('macd')
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
        
    def _ema(self, data: List[float], period: int) -> List[float]:
        if len(data) < period: return data
        multiplier = 2 / (period + 1)
        ema = [np.mean(data[:period])]
        for price in data[period:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])
        return ema
    
    def generate(self, prices: List[float]) -> Optional[Dict]:
        if len(prices) < self.slow + self.signal_period: return None
        fast_ema = self._ema(prices, self.fast)
        slow_ema = self._ema(prices, self.slow)
        min_len = min(len(fast_ema), len(slow_ema))
        macd_line = [fast_ema[i] - slow_ema[i] for i in range(min_len)]
        signal_line = self._ema(macd_line, self.signal_period)
        if len(signal_line) < 2: return None
        if macd_line[-2] <= signal_line[-2] and macd_line[-1] > signal_line[-1]:
            return {'direction': 'long', 'strength': abs(macd_line[-1] - signal_line[-1])}
        if macd_line[-2] >= signal_line[-2] and macd_line[-1] < signal_line[-1]:
            return {'direction': 'short', 'strength': abs(macd_line[-1] - signal_line[-1])}
        return None

# UPGRADE 505: Bollinger Band Signal
class BollingerBandSignal(SignalGeneratorBase):
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__('bollinger')
        self.period = period
        self.std_dev = std_dev
        
    def generate(self, prices: List[float]) -> Optional[Dict]:
        if len(prices) < self.period: return None
        sma = np.mean(prices[-self.period:])
        std = np.std(prices[-self.period:])
        upper = sma + self.std_dev * std
        lower = sma - self.std_dev * std
        current = prices[-1]
        if current < lower:
            return {'direction': 'long', 'strength': (lower - current) / std if std > 0 else 0}
        if current > upper:
            return {'direction': 'short', 'strength': (current - upper) / std if std > 0 else 0}
        return None

# UPGRADE 506: Stochastic Signal Generator
class StochasticSignalGenerator(SignalGeneratorBase):
    def __init__(self, k_period: int = 14, d_period: int = 3, overbought: float = 80, oversold: float = 20):
        super().__init__('stochastic')
        self.k_period = k_period
        self.d_period = d_period
        self.overbought = overbought
        self.oversold = oversold
        
    def generate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict]:
        if len(closes) < self.k_period + self.d_period: return None
        k_values = []
        for i in range(self.k_period, len(closes) + 1):
            highest = max(highs[i-self.k_period:i])
            lowest = min(lows[i-self.k_period:i])
            k = ((closes[i-1] - lowest) / (highest - lowest) * 100) if highest != lowest else 50
            k_values.append(k)
        d = np.mean(k_values[-self.d_period:])
        k = k_values[-1]
        if k < self.oversold and k > d:
            return {'direction': 'long', 'strength': (self.oversold - k) / self.oversold, 'k': k, 'd': d}
        if k > self.overbought and k < d:
            return {'direction': 'short', 'strength': (k - self.overbought) / (100 - self.overbought), 'k': k, 'd': d}
        return None

# UPGRADE 507: ADX Trend Signal
class ADXTrendSignal(SignalGeneratorBase):
    def __init__(self, period: int = 14, threshold: float = 25):
        super().__init__('adx')
        self.period = period
        self.threshold = threshold
        
    def generate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict]:
        if len(closes) < self.period + 1: return None
        plus_dm, minus_dm, tr = [], [], []
        for i in range(1, len(closes)):
            high_diff = highs[i] - highs[i-1]
            low_diff = lows[i-1] - lows[i]
            plus_dm.append(high_diff if high_diff > low_diff and high_diff > 0 else 0)
            minus_dm.append(low_diff if low_diff > high_diff and low_diff > 0 else 0)
            tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])))
        atr = np.mean(tr[-self.period:])
        plus_di = np.mean(plus_dm[-self.period:]) / atr * 100 if atr > 0 else 0
        minus_di = np.mean(minus_dm[-self.period:]) / atr * 100 if atr > 0 else 0
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if plus_di + minus_di > 0 else 0
        if dx > self.threshold:
            direction = 'long' if plus_di > minus_di else 'short'
            return {'direction': direction, 'strength': dx / 100, 'adx': dx}
        return None

# UPGRADE 508: Volume Breakout Signal
class VolumeBreakoutSignal(SignalGeneratorBase):
    def __init__(self, volume_mult: float = 2.0, price_threshold: float = 0.02):
        super().__init__('volume_breakout')
        self.volume_mult = volume_mult
        self.price_threshold = price_threshold
        
    def generate(self, prices: List[float], volumes: List[float]) -> Optional[Dict]:
        if len(prices) < 20 or len(volumes) < 20: return None
        avg_volume = np.mean(volumes[-20:-1])
        current_volume = volumes[-1]
        price_change = (prices[-1] - prices[-2]) / prices[-2]
        if current_volume > avg_volume * self.volume_mult and abs(price_change) > self.price_threshold:
            direction = 'long' if price_change > 0 else 'short'
            return {'direction': direction, 'strength': current_volume / avg_volume / 10, 'volume_ratio': current_volume / avg_volume}
        return None

# UPGRADE 509: Support Resistance Signal
class SupportResistanceSignal(SignalGeneratorBase):
    def __init__(self, lookback: int = 50, tolerance: float = 0.002):
        super().__init__('support_resistance')
        self.lookback = lookback
        self.tolerance = tolerance
        
    def find_levels(self, prices: List[float]) -> Tuple[List[float], List[float]]:
        supports, resistances = [], []
        for i in range(2, len(prices) - 2):
            if prices[i] < prices[i-1] and prices[i] < prices[i-2] and prices[i] < prices[i+1] and prices[i] < prices[i+2]:
                supports.append(prices[i])
            if prices[i] > prices[i-1] and prices[i] > prices[i-2] and prices[i] > prices[i+1] and prices[i] > prices[i+2]:
                resistances.append(prices[i])
        return supports, resistances
    
    def generate(self, prices: List[float]) -> Optional[Dict]:
        if len(prices) < self.lookback: return None
        supports, resistances = self.find_levels(prices[-self.lookback:])
        current = prices[-1]
        for support in supports:
            if abs(current - support) / support < self.tolerance:
                return {'direction': 'long', 'strength': 0.7, 'level': support, 'type': 'support'}
        for resistance in resistances:
            if abs(current - resistance) / resistance < self.tolerance:
                return {'direction': 'short', 'strength': 0.7, 'level': resistance, 'type': 'resistance'}
        return None

# UPGRADE 510: Trend Line Break Signal
class TrendLineBreakSignal(SignalGeneratorBase):
    def __init__(self, min_touches: int = 3):
        super().__init__('trendline_break')
        self.min_touches = min_touches
        
    def generate(self, prices: List[float]) -> Optional[Dict]:
        if len(prices) < 20: return None
        highs_idx = [i for i in range(1, len(prices)-1) if prices[i] > prices[i-1] and prices[i] > prices[i+1]]
        lows_idx = [i for i in range(1, len(prices)-1) if prices[i] < prices[i-1] and prices[i] < prices[i+1]]
        if len(highs_idx) >= 2:
            slope = (prices[highs_idx[-1]] - prices[highs_idx[-2]]) / (highs_idx[-1] - highs_idx[-2])
            projected = prices[highs_idx[-1]] + slope * (len(prices) - 1 - highs_idx[-1])
            if prices[-1] > projected:
                return {'direction': 'long', 'strength': (prices[-1] - projected) / projected, 'type': 'resistance_break'}
        if len(lows_idx) >= 2:
            slope = (prices[lows_idx[-1]] - prices[lows_idx[-2]]) / (lows_idx[-1] - lows_idx[-2])
            projected = prices[lows_idx[-1]] + slope * (len(prices) - 1 - lows_idx[-1])
            if prices[-1] < projected:
                return {'direction': 'short', 'strength': (projected - prices[-1]) / projected, 'type': 'support_break'}
        return None

# UPGRADE 511: Candlestick Pattern Signal
class CandlestickPatternSignal(SignalGeneratorBase):
    def __init__(self):
        super().__init__('candlestick')
        
    def generate(self, candles: List[Dict]) -> Optional[Dict]:
        if len(candles) < 3: return None
        c = candles[-1]
        body = c['close'] - c['open']
        range_ = c['high'] - c['low']
        if range_ == 0: return None
        if abs(body) < range_ * 0.1 and c['high'] - max(c['open'], c['close']) > range_ * 0.6:
            return {'direction': 'short', 'strength': 0.6, 'pattern': 'shooting_star'}
        if abs(body) < range_ * 0.1 and min(c['open'], c['close']) - c['low'] > range_ * 0.6:
            return {'direction': 'long', 'strength': 0.6, 'pattern': 'hammer'}
        if len(candles) >= 2:
            prev = candles[-2]
            if prev['close'] < prev['open'] and c['close'] > c['open']:
                if c['open'] < prev['close'] and c['close'] > prev['open']:
                    return {'direction': 'long', 'strength': 0.7, 'pattern': 'bullish_engulfing'}
            if prev['close'] > prev['open'] and c['close'] < c['open']:
                if c['open'] > prev['close'] and c['close'] < prev['open']:
                    return {'direction': 'short', 'strength': 0.7, 'pattern': 'bearish_engulfing'}
        return None

# UPGRADE 512: Divergence Signal
class DivergenceSignal(SignalGeneratorBase):
    def __init__(self, lookback: int = 14):
        super().__init__('divergence')
        self.lookback = lookback
        
    def generate(self, prices: List[float], indicator: List[float]) -> Optional[Dict]:
        if len(prices) < self.lookback or len(indicator) < self.lookback: return None
        price_highs = [i for i in range(1, self.lookback-1) if prices[-self.lookback+i] > prices[-self.lookback+i-1] and prices[-self.lookback+i] > prices[-self.lookback+i+1]]
        price_lows = [i for i in range(1, self.lookback-1) if prices[-self.lookback+i] < prices[-self.lookback+i-1] and prices[-self.lookback+i] < prices[-self.lookback+i+1]]
        if len(price_highs) >= 2:
            if prices[-self.lookback+price_highs[-1]] > prices[-self.lookback+price_highs[-2]]:
                if indicator[-self.lookback+price_highs[-1]] < indicator[-self.lookback+price_highs[-2]]:
                    return {'direction': 'short', 'strength': 0.8, 'type': 'bearish_divergence'}
        if len(price_lows) >= 2:
            if prices[-self.lookback+price_lows[-1]] < prices[-self.lookback+price_lows[-2]]:
                if indicator[-self.lookback+price_lows[-1]] > indicator[-self.lookback+price_lows[-2]]:
                    return {'direction': 'long', 'strength': 0.8, 'type': 'bullish_divergence'}
        return None

# UPGRADE 513: Momentum Signal
class MomentumSignal(SignalGeneratorBase):
    def __init__(self, period: int = 10, threshold: float = 0.02):
        super().__init__('momentum')
        self.period = period
        self.threshold = threshold
        
    def generate(self, prices: List[float]) -> Optional[Dict]:
        if len(prices) < self.period: return None
        momentum = (prices[-1] - prices[-self.period]) / prices[-self.period]
        if momentum > self.threshold:
            return {'direction': 'long', 'strength': min(1, momentum / self.threshold / 2), 'momentum': momentum}
        if momentum < -self.threshold:
            return {'direction': 'short', 'strength': min(1, abs(momentum) / self.threshold / 2), 'momentum': momentum}
        return None

# UPGRADE 514: Mean Reversion Signal
class MeanReversionSignal(SignalGeneratorBase):
    def __init__(self, period: int = 20, std_threshold: float = 2.0):
        super().__init__('mean_reversion')
        self.period = period
        self.std_threshold = std_threshold
        
    def generate(self, prices: List[float]) -> Optional[Dict]:
        if len(prices) < self.period: return None
        mean = np.mean(prices[-self.period:])
        std = np.std(prices[-self.period:])
        if std == 0: return None
        z_score = (prices[-1] - mean) / std
        if z_score < -self.std_threshold:
            return {'direction': 'long', 'strength': min(1, abs(z_score) / 4), 'z_score': z_score}
        if z_score > self.std_threshold:
            return {'direction': 'short', 'strength': min(1, abs(z_score) / 4), 'z_score': z_score}
        return None

# UPGRADE 515: Breakout Signal
class BreakoutSignal(SignalGeneratorBase):
    def __init__(self, period: int = 20, confirmation_bars: int = 2):
        super().__init__('breakout')
        self.period = period
        self.confirmation = confirmation_bars
        
    def generate(self, prices: List[float]) -> Optional[Dict]:
        if len(prices) < self.period + self.confirmation: return None
        high = max(prices[-self.period-self.confirmation:-self.confirmation])
        low = min(prices[-self.period-self.confirmation:-self.confirmation])
        confirmed_above = all(p > high for p in prices[-self.confirmation:])
        confirmed_below = all(p < low for p in prices[-self.confirmation:])
        if confirmed_above:
            return {'direction': 'long', 'strength': (prices[-1] - high) / high, 'breakout_level': high}
        if confirmed_below:
            return {'direction': 'short', 'strength': (low - prices[-1]) / low, 'breakout_level': low}
        return None

# UPGRADE 516: Channel Breakout Signal
class ChannelBreakoutSignal(SignalGeneratorBase):
    def __init__(self, period: int = 20):
        super().__init__('channel_breakout')
        self.period = period
        
    def generate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict]:
        if len(closes) < self.period: return None
        upper = max(highs[-self.period:])
        lower = min(lows[-self.period:])
        current = closes[-1]
        if current > upper:
            return {'direction': 'long', 'strength': (current - upper) / upper, 'channel': {'upper': upper, 'lower': lower}}
        if current < lower:
            return {'direction': 'short', 'strength': (lower - current) / lower, 'channel': {'upper': upper, 'lower': lower}}
        return None

# UPGRADE 517: Volatility Breakout Signal
class VolatilityBreakoutSignal(SignalGeneratorBase):
    def __init__(self, atr_period: int = 14, multiplier: float = 1.5):
        super().__init__('volatility_breakout')
        self.atr_period = atr_period
        self.multiplier = multiplier
        
    def generate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict]:
        if len(closes) < self.atr_period + 1: return None
        tr = [max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])) for i in range(1, len(closes))]
        atr = np.mean(tr[-self.atr_period:])
        prev_close = closes[-2]
        current = closes[-1]
        if current > prev_close + atr * self.multiplier:
            return {'direction': 'long', 'strength': (current - prev_close) / atr / self.multiplier, 'atr': atr}
        if current < prev_close - atr * self.multiplier:
            return {'direction': 'short', 'strength': (prev_close - current) / atr / self.multiplier, 'atr': atr}
        return None

# UPGRADE 518: Price Action Signal
class PriceActionSignal(SignalGeneratorBase):
    def __init__(self):
        super().__init__('price_action')
        
    def generate(self, candles: List[Dict]) -> Optional[Dict]:
        if len(candles) < 5: return None
        higher_highs = all(candles[i]['high'] > candles[i-1]['high'] for i in range(-3, 0))
        higher_lows = all(candles[i]['low'] > candles[i-1]['low'] for i in range(-3, 0))
        lower_highs = all(candles[i]['high'] < candles[i-1]['high'] for i in range(-3, 0))
        lower_lows = all(candles[i]['low'] < candles[i-1]['low'] for i in range(-3, 0))
        if higher_highs and higher_lows:
            return {'direction': 'long', 'strength': 0.7, 'pattern': 'uptrend'}
        if lower_highs and lower_lows:
            return {'direction': 'short', 'strength': 0.7, 'pattern': 'downtrend'}
        return None

# UPGRADE 519: Order Flow Signal
class OrderFlowSignal(SignalGeneratorBase):
    def __init__(self, imbalance_threshold: float = 0.6):
        super().__init__('order_flow')
        self.threshold = imbalance_threshold
        
    def generate(self, trades: List[Dict]) -> Optional[Dict]:
        if len(trades) < 100: return None
        buy_volume = sum(t['volume'] for t in trades if t.get('side') == 'buy')
        sell_volume = sum(t['volume'] for t in trades if t.get('side') == 'sell')
        total = buy_volume + sell_volume
        if total == 0: return None
        imbalance = (buy_volume - sell_volume) / total
        if imbalance > self.threshold:
            return {'direction': 'long', 'strength': imbalance, 'buy_volume': buy_volume, 'sell_volume': sell_volume}
        if imbalance < -self.threshold:
            return {'direction': 'short', 'strength': abs(imbalance), 'buy_volume': buy_volume, 'sell_volume': sell_volume}
        return None

# UPGRADE 520: Sentiment Signal
class SentimentSignal(SignalGeneratorBase):
    def __init__(self, threshold: float = 0.3):
        super().__init__('sentiment')
        self.threshold = threshold
        
    def generate(self, sentiment_scores: List[float]) -> Optional[Dict]:
        if len(sentiment_scores) < 5: return None
        avg_sentiment = np.mean(sentiment_scores[-5:])
        if avg_sentiment > self.threshold:
            return {'direction': 'long', 'strength': avg_sentiment, 'sentiment': avg_sentiment}
        if avg_sentiment < -self.threshold:
            return {'direction': 'short', 'strength': abs(avg_sentiment), 'sentiment': avg_sentiment}
        return None

# UPGRADE 521: Correlation Signal
class CorrelationSignal(SignalGeneratorBase):
    def __init__(self, correlation_threshold: float = 0.8):
        super().__init__('correlation')
        self.threshold = correlation_threshold
        
    def generate(self, asset_returns: List[float], leader_returns: List[float]) -> Optional[Dict]:
        if len(asset_returns) < 20 or len(leader_returns) < 20: return None
        corr = np.corrcoef(asset_returns[-20:], leader_returns[-20:])[0, 1]
        if abs(corr) > self.threshold:
            leader_direction = 'long' if leader_returns[-1] > 0 else 'short'
            if corr > 0:
                return {'direction': leader_direction, 'strength': abs(corr), 'correlation': corr}
            else:
                direction = 'short' if leader_direction == 'long' else 'long'
                return {'direction': direction, 'strength': abs(corr), 'correlation': corr}
        return None

# UPGRADE 522: Regime Signal
class RegimeSignal(SignalGeneratorBase):
    def __init__(self):
        super().__init__('regime')
        
    def generate(self, prices: List[float], volumes: List[float]) -> Optional[Dict]:
        if len(prices) < 50: return None
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = np.std(returns[-20:])
        trend = (prices[-1] - prices[-20]) / prices[-20]
        if volatility < 0.01 and abs(trend) < 0.02:
            return {'direction': 'neutral', 'strength': 0, 'regime': 'ranging'}
        if trend > 0.05:
            return {'direction': 'long', 'strength': min(1, trend * 10), 'regime': 'trending_up'}
        if trend < -0.05:
            return {'direction': 'short', 'strength': min(1, abs(trend) * 10), 'regime': 'trending_down'}
        return None

# UPGRADE 523: Multi-Timeframe Signal
class MultiTimeframeSignal(SignalGeneratorBase):
    def __init__(self):
        super().__init__('multi_timeframe')
        self.timeframe_signals: Dict[str, Dict] = {}
        
    def add_signal(self, timeframe: str, signal: Dict):
        self.timeframe_signals[timeframe] = signal
        
    def generate(self) -> Optional[Dict]:
        if len(self.timeframe_signals) < 2: return None
        long_count = sum(1 for s in self.timeframe_signals.values() if s.get('direction') == 'long')
        short_count = sum(1 for s in self.timeframe_signals.values() if s.get('direction') == 'short')
        total = len(self.timeframe_signals)
        if long_count > total * 0.6:
            return {'direction': 'long', 'strength': long_count / total, 'confluence': self.timeframe_signals}
        if short_count > total * 0.6:
            return {'direction': 'short', 'strength': short_count / total, 'confluence': self.timeframe_signals}
        return None

# UPGRADE 524: Signal Combiner
class SignalCombiner:
    def __init__(self):
        self.weights: Dict[str, float] = {}
        
    def set_weight(self, signal_name: str, weight: float):
        self.weights[signal_name] = weight
        
    def combine(self, signals: List[Dict]) -> Dict:
        if not signals: return {'direction': 'neutral', 'strength': 0}
        long_score, short_score = 0, 0
        total_weight = 0
        for signal in signals:
            name = signal.get('generator', 'unknown')
            weight = self.weights.get(name, 1.0)
            strength = signal.get('strength', 0.5)
            if signal.get('direction') == 'long':
                long_score += weight * strength
            elif signal.get('direction') == 'short':
                short_score += weight * strength
            total_weight += weight
        if total_weight == 0: return {'direction': 'neutral', 'strength': 0}
        if long_score > short_score:
            return {'direction': 'long', 'strength': long_score / total_weight}
        if short_score > long_score:
            return {'direction': 'short', 'strength': short_score / total_weight}
        return {'direction': 'neutral', 'strength': 0}

# UPGRADE 525: Signal Filter
class SignalFilter:
    def __init__(self):
        self.filters: List[Callable] = []
        
    def add_filter(self, filter_func: Callable):
        self.filters.append(filter_func)
        
    def filter(self, signal: Dict, context: Dict) -> bool:
        for f in self.filters:
            if not f(signal, context): return False
        return True

# UPGRADE 526: Signal Validator
class SignalValidator:
    def __init__(self):
        self.required_fields = ['direction', 'strength']
        
    def validate(self, signal: Dict) -> Tuple[bool, List[str]]:
        errors = []
        for field in self.required_fields:
            if field not in signal: errors.append(f"Missing {field}")
        if signal.get('direction') not in ['long', 'short', 'neutral']:
            errors.append("Invalid direction")
        if not 0 <= signal.get('strength', -1) <= 1:
            errors.append("Strength must be between 0 and 1")
        return len(errors) == 0, errors

# UPGRADE 527: Signal Scorer
class SignalScorer:
    def __init__(self):
        self.history: List[Dict] = []
        
    def record(self, signal: Dict, outcome: float):
        self.history.append({'signal': signal, 'outcome': outcome})
        
    def get_score(self, signal_type: str) -> float:
        relevant = [h for h in self.history if h['signal'].get('generator') == signal_type]
        if not relevant: return 0.5
        wins = sum(1 for h in relevant if h['outcome'] > 0)
        return wins / len(relevant)

# UPGRADE 528: Signal Confidence Calculator
class SignalConfidenceCalculator:
    def calculate(self, signal: Dict, historical_accuracy: float, market_conditions: Dict) -> float:
        base_confidence = signal.get('strength', 0.5)
        accuracy_adj = historical_accuracy * 0.3
        volatility = market_conditions.get('volatility', 0.02)
        vol_adj = max(0, 0.2 - volatility * 5)
        return min(1, base_confidence * 0.5 + accuracy_adj + vol_adj)

# UPGRADE 529: Signal Priority Manager
class SignalPriorityManager:
    def __init__(self):
        self.priorities: Dict[str, int] = {}
        
    def set_priority(self, signal_type: str, priority: int):
        self.priorities[signal_type] = priority
        
    def sort_signals(self, signals: List[Dict]) -> List[Dict]:
        return sorted(signals, key=lambda s: self.priorities.get(s.get('generator', ''), 0), reverse=True)

# UPGRADE 530: Signal Cooldown Manager
class SignalCooldownManager:
    def __init__(self):
        self.last_signal: Dict[str, datetime] = {}
        self.cooldowns: Dict[str, int] = {}
        
    def set_cooldown(self, signal_type: str, seconds: int):
        self.cooldowns[signal_type] = seconds
        
    def can_signal(self, signal_type: str) -> bool:
        if signal_type not in self.last_signal: return True
        cooldown = self.cooldowns.get(signal_type, 0)
        elapsed = (datetime.utcnow() - self.last_signal[signal_type]).total_seconds()
        return elapsed >= cooldown
    
    def record_signal(self, signal_type: str):
        self.last_signal[signal_type] = datetime.utcnow()

# UPGRADE 531: Signal Rate Limiter
class SignalRateLimiter:
    def __init__(self, max_signals_per_hour: int = 10):
        self.max_rate = max_signals_per_hour
        self.signals: deque = deque()
        
    def can_signal(self) -> bool:
        now = datetime.utcnow()
        while self.signals and (now - self.signals[0]).total_seconds() > 3600:
            self.signals.popleft()
        return len(self.signals) < self.max_rate
    
    def record_signal(self):
        self.signals.append(datetime.utcnow())

# UPGRADE 532: Signal Aggregator
class SignalAggregator:
    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self.signals: deque = deque()
        
    def add(self, signal: Dict):
        self.signals.append({'signal': signal, 'time': datetime.utcnow()})
        self._cleanup()
        
    def _cleanup(self):
        cutoff = datetime.utcnow() - timedelta(seconds=self.window)
        while self.signals and self.signals[0]['time'] < cutoff:
            self.signals.popleft()
            
    def get_aggregate(self) -> Dict:
        if not self.signals: return {'direction': 'neutral', 'count': 0}
        long_count = sum(1 for s in self.signals if s['signal'].get('direction') == 'long')
        short_count = sum(1 for s in self.signals if s['signal'].get('direction') == 'short')
        total = len(self.signals)
        if long_count > short_count:
            return {'direction': 'long', 'strength': long_count / total, 'count': total}
        if short_count > long_count:
            return {'direction': 'short', 'strength': short_count / total, 'count': total}
        return {'direction': 'neutral', 'count': total}

# UPGRADE 533: Signal Decay Manager
class SignalDecayManager:
    def __init__(self, half_life_seconds: int = 300):
        self.half_life = half_life_seconds
        
    def apply_decay(self, signal: Dict, age_seconds: float) -> Dict:
        decay_factor = 0.5 ** (age_seconds / self.half_life)
        decayed = signal.copy()
        decayed['strength'] = signal.get('strength', 0.5) * decay_factor
        decayed['decayed'] = True
        return decayed

# UPGRADE 534: Signal Conflict Resolver
class SignalConflictResolver:
    def resolve(self, signals: List[Dict]) -> Dict:
        if not signals: return {'direction': 'neutral', 'strength': 0}
        long_signals = [s for s in signals if s.get('direction') == 'long']
        short_signals = [s for s in signals if s.get('direction') == 'short']
        if not long_signals and not short_signals:
            return {'direction': 'neutral', 'strength': 0}
        long_strength = sum(s.get('strength', 0) for s in long_signals)
        short_strength = sum(s.get('strength', 0) for s in short_signals)
        if long_strength > short_strength * 1.5:
            return {'direction': 'long', 'strength': long_strength / (long_strength + short_strength)}
        if short_strength > long_strength * 1.5:
            return {'direction': 'short', 'strength': short_strength / (long_strength + short_strength)}
        return {'direction': 'neutral', 'strength': 0, 'conflict': True}

# UPGRADE 535: Signal Confirmation Engine
class SignalConfirmationEngine:
    def __init__(self, required_confirmations: int = 2):
        self.required = required_confirmations
        
    def confirm(self, primary_signal: Dict, confirming_signals: List[Dict]) -> bool:
        if not primary_signal: return False
        direction = primary_signal.get('direction')
        confirmations = sum(1 for s in confirming_signals if s.get('direction') == direction)
        return confirmations >= self.required

# UPGRADE 536: Signal Quality Assessor
class SignalQualityAssessor:
    def assess(self, signal: Dict, market_context: Dict) -> Dict:
        quality_score = 0
        factors = []
        if signal.get('strength', 0) > 0.7:
            quality_score += 30
            factors.append('high_strength')
        if market_context.get('trend_aligned', False):
            quality_score += 25
            factors.append('trend_aligned')
        if market_context.get('volume_confirmed', False):
            quality_score += 20
            factors.append('volume_confirmed')
        if market_context.get('low_volatility', False):
            quality_score += 15
            factors.append('low_volatility')
        if signal.get('multi_timeframe', False):
            quality_score += 10
            factors.append('multi_timeframe')
        return {'score': quality_score, 'grade': self._grade(quality_score), 'factors': factors}
    
    def _grade(self, score: int) -> str:
        if score >= 80: return 'A'
        if score >= 60: return 'B'
        if score >= 40: return 'C'
        return 'D'

# UPGRADE 537: Signal Entry Optimizer
class SignalEntryOptimizer:
    def optimize(self, signal: Dict, current_price: float, atr: float) -> Dict:
        direction = signal.get('direction')
        if direction == 'long':
            entry = current_price - atr * 0.2
            stop = entry - atr * 1.5
            target = entry + atr * 3
        elif direction == 'short':
            entry = current_price + atr * 0.2
            stop = entry + atr * 1.5
            target = entry - atr * 3
        else:
            return signal
        return {**signal, 'entry': entry, 'stop': stop, 'target': target, 'risk_reward': 2.0}

# UPGRADE 538: Signal Exit Optimizer
class SignalExitOptimizer:
    def __init__(self):
        self.exit_rules: List[Callable] = []
        
    def add_rule(self, rule: Callable):
        self.exit_rules.append(rule)
        
    def should_exit(self, position: Dict, market_data: Dict) -> Tuple[bool, str]:
        for rule in self.exit_rules:
            should_exit, reason = rule(position, market_data)
            if should_exit: return True, reason
        return False, ''

# UPGRADE 539: Signal Performance Tracker
class SignalPerformanceTracker:
    def __init__(self):
        self.performance: Dict[str, Dict] = {}
        
    def record_trade(self, signal_type: str, pnl: float, holding_time: float):
        if signal_type not in self.performance:
            self.performance[signal_type] = {'trades': 0, 'wins': 0, 'total_pnl': 0, 'total_time': 0}
        self.performance[signal_type]['trades'] += 1
        if pnl > 0: self.performance[signal_type]['wins'] += 1
        self.performance[signal_type]['total_pnl'] += pnl
        self.performance[signal_type]['total_time'] += holding_time
        
    def get_stats(self, signal_type: str) -> Dict:
        if signal_type not in self.performance: return {}
        p = self.performance[signal_type]
        return {
            'win_rate': p['wins'] / p['trades'] if p['trades'] > 0 else 0,
            'avg_pnl': p['total_pnl'] / p['trades'] if p['trades'] > 0 else 0,
            'avg_holding_time': p['total_time'] / p['trades'] if p['trades'] > 0 else 0
        }

# UPGRADE 540: Signal Attribution Analyzer
class SignalAttributionAnalyzer:
    def __init__(self):
        self.attributions: Dict[str, List[float]] = {}
        
    def record(self, signal_type: str, contribution: float):
        if signal_type not in self.attributions: self.attributions[signal_type] = []
        self.attributions[signal_type].append(contribution)
        
    def get_attribution(self) -> Dict[str, float]:
        total = sum(sum(v) for v in self.attributions.values())
        if total == 0: return {}
        return {k: sum(v) / total for k, v in self.attributions.items()}

# UPGRADE 541: Signal Backtester
class SignalBacktester:
    def backtest(self, signals: List[Dict], prices: List[float]) -> Dict:
        if len(signals) != len(prices) - 1: return {}
        pnl = 0
        trades = 0
        wins = 0
        for i, signal in enumerate(signals):
            if signal.get('direction') == 'long':
                trade_pnl = prices[i+1] - prices[i]
            elif signal.get('direction') == 'short':
                trade_pnl = prices[i] - prices[i+1]
            else:
                continue
            pnl += trade_pnl
            trades += 1
            if trade_pnl > 0: wins += 1
        return {'total_pnl': pnl, 'trades': trades, 'win_rate': wins / trades if trades > 0 else 0}

# UPGRADE 542: Signal Optimizer
class SignalOptimizer:
    def __init__(self):
        self.param_history: List[Dict] = []
        
    def record_result(self, params: Dict, performance: float):
        self.param_history.append({'params': params, 'performance': performance})
        
    def get_best_params(self) -> Dict:
        if not self.param_history: return {}
        return max(self.param_history, key=lambda x: x['performance'])['params']

# UPGRADE 543: Signal Ensemble
class SignalEnsemble:
    def __init__(self):
        self.generators: List[SignalGeneratorBase] = []
        self.weights: List[float] = []
        
    def add_generator(self, generator: SignalGeneratorBase, weight: float = 1.0):
        self.generators.append(generator)
        self.weights.append(weight)
        
    def generate(self, data: Dict) -> Dict:
        signals = []
        for gen in self.generators:
            try:
                signal = gen.generate(data)
                if signal: signals.append(signal)
            except Exception as e: pass
        combiner = SignalCombiner()
        for gen, weight in zip(self.generators, self.weights):
            combiner.set_weight(gen.name, weight)
        return combiner.combine(signals)

# UPGRADE 544: Signal Noise Filter
class SignalNoiseFilter:
    def __init__(self, min_strength: float = 0.3, min_duration: int = 2):
        self.min_strength = min_strength
        self.min_duration = min_duration
        self.signal_history: deque = deque(maxlen=10)
        
    def filter(self, signal: Dict) -> Optional[Dict]:
        if signal.get('strength', 0) < self.min_strength: return None
        self.signal_history.append(signal)
        if len(self.signal_history) < self.min_duration: return None
        recent = list(self.signal_history)[-self.min_duration:]
        if all(s.get('direction') == signal.get('direction') for s in recent):
            return signal
        return None

# UPGRADE 545: Signal Regime Adapter
class SignalRegimeAdapter:
    def __init__(self):
        self.regime_weights: Dict[str, Dict[str, float]] = {
            'trending': {'momentum': 1.5, 'mean_reversion': 0.5},
            'ranging': {'momentum': 0.5, 'mean_reversion': 1.5},
            'volatile': {'momentum': 0.7, 'mean_reversion': 0.7}
        }
        
    def adapt(self, signal: Dict, regime: str) -> Dict:
        signal_type = signal.get('generator', 'unknown')
        weight = self.regime_weights.get(regime, {}).get(signal_type, 1.0)
        adapted = signal.copy()
        adapted['strength'] = signal.get('strength', 0.5) * weight
        adapted['regime_adapted'] = True
        return adapted

# UPGRADE 546: Signal Time Filter
class SignalTimeFilter:
    def __init__(self):
        self.allowed_hours: List[int] = list(range(8, 17))
        self.blocked_days: List[int] = [5, 6]
        
    def is_allowed(self, timestamp: datetime = None) -> bool:
        if timestamp is None: timestamp = datetime.utcnow()
        if timestamp.weekday() in self.blocked_days: return False
        if timestamp.hour not in self.allowed_hours: return False
        return True

# UPGRADE 547: Signal News Filter
class SignalNewsFilter:
    def __init__(self):
        self.high_impact_events: List[Dict] = []
        
    def add_event(self, event_time: datetime, duration_mins: int = 30):
        self.high_impact_events.append({'time': event_time, 'duration': duration_mins})
        
    def is_safe(self, timestamp: datetime = None) -> bool:
        if timestamp is None: timestamp = datetime.utcnow()
        for event in self.high_impact_events:
            event_start = event['time'] - timedelta(minutes=event['duration'])
            event_end = event['time'] + timedelta(minutes=event['duration'])
            if event_start <= timestamp <= event_end: return False
        return True

# UPGRADE 548: Signal Correlation Filter
class SignalCorrelationFilter:
    def __init__(self, max_correlation: float = 0.7):
        self.max_corr = max_correlation
        self.active_signals: List[Dict] = []
        
    def can_add(self, new_signal: Dict, correlations: Dict[Tuple[str, str], float]) -> bool:
        new_symbol = new_signal.get('symbol')
        for active in self.active_signals:
            active_symbol = active.get('symbol')
            corr = correlations.get((new_symbol, active_symbol)) or correlations.get((active_symbol, new_symbol), 0)
            if abs(corr) > self.max_corr: return False
        return True
    
    def add_signal(self, signal: Dict):
        self.active_signals.append(signal)

# UPGRADE 549: Signal Risk Adjuster
class SignalRiskAdjuster:
    def adjust(self, signal: Dict, risk_metrics: Dict) -> Dict:
        adjusted = signal.copy()
        base_strength = signal.get('strength', 0.5)
        if risk_metrics.get('drawdown', 0) > 0.1:
            base_strength *= 0.5
        if risk_metrics.get('daily_loss', 0) > 0.02:
            base_strength *= 0.3
        if risk_metrics.get('consecutive_losses', 0) > 3:
            base_strength *= 0.5
        adjusted['strength'] = base_strength
        adjusted['risk_adjusted'] = True
        return adjusted

# UPGRADE 550: Signal Dashboard
class SignalDashboard:
    def __init__(self):
        self.active_signals: List[Dict] = []
        self.signal_history: deque = deque(maxlen=1000)
        self.stats: Dict[str, Any] = {}
        
    def add_signal(self, signal: Dict):
        self.active_signals.append(signal)
        self.signal_history.append({'signal': signal, 'time': datetime.utcnow()})
        self._update_stats()
        
    def _update_stats(self):
        total = len(self.signal_history)
        long_count = sum(1 for s in self.signal_history if s['signal'].get('direction') == 'long')
        short_count = sum(1 for s in self.signal_history if s['signal'].get('direction') == 'short')
        self.stats = {
            'total_signals': total,
            'long_ratio': long_count / total if total > 0 else 0,
            'short_ratio': short_count / total if total > 0 else 0,
            'active_count': len(self.active_signals)
        }
        
    def get_dashboard(self) -> Dict:
        return {
            'stats': self.stats,
            'active_signals': self.active_signals[-10:],
            'timestamp': datetime.utcnow().isoformat()
        }
