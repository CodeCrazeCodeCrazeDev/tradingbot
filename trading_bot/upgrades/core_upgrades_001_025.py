"""
Core Trading Engine Upgrades 1-25
"""
import asyncio
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque
import hashlib
import json
import threading
import time

# UPGRADE 001: Adaptive Tick Processing
import logging

logger = logging.getLogger(__name__)

class AdaptiveTickProcessor:
    def __init__(self, base_interval_ms: float = 100):
        try:
            self.base_interval = base_interval_ms
            self.current_interval = base_interval_ms
            self.tick_buffer = deque(maxlen=1000)
            self.activity_score = 0.5
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def process_tick(self, tick: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.tick_buffer.append(tick)
            if len(self.tick_buffer) >= 10:
                recent = list(self.tick_buffer)[-100:]
                changes = [abs(recent[i].get('price', 0) - recent[i-1].get('price', 0)) for i in range(1, len(recent))]
                if changes:
                    self.activity_score = min(1.0, np.std(changes) * 100)
            if self.activity_score > 0.8:
                self.current_interval = self.base_interval * 0.5
            elif self.activity_score < 0.2:
                self.current_interval = self.base_interval * 2.0
            return {'tick': tick, 'interval_ms': self.current_interval, 'activity_score': self.activity_score}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in process_tick: {e}")
            raise

# UPGRADE 002: Multi-Symbol Correlation Tracker
class MultiSymbolCorrelationTracker:
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self.price_history: Dict[str, deque] = {}
            self.correlation_matrix: Dict[Tuple[str, str], float] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, symbol: str, price: float):
        try:
            if symbol not in self.price_history:
                self.price_history[symbol] = deque(maxlen=self.window_size)
            self.price_history[symbol].append(price)
            symbols = list(self.price_history.keys())
            for i, sym1 in enumerate(symbols):
                for sym2 in symbols[i+1:]:
                    if len(self.price_history[sym1]) >= 20 and len(self.price_history[sym2]) >= 20:
                        arr1, arr2 = np.array(list(self.price_history[sym1])), np.array(list(self.price_history[sym2]))
                        min_len = min(len(arr1), len(arr2))
                        self.correlation_matrix[(sym1, sym2)] = np.corrcoef(arr1[-min_len:], arr2[-min_len:])[0, 1]
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise
                    
    def get_correlation(self, sym1: str, sym2: str) -> Optional[float]:
        return self.correlation_matrix.get((sym1, sym2)) or self.correlation_matrix.get((sym2, sym1))

# UPGRADE 003: Smart Order Book Aggregator
class SmartOrderBookAggregator:
    def __init__(self, num_levels: int = 10, compression_factor: float = 0.001):
        try:
            self.num_levels, self.compression_factor = num_levels, compression_factor
            self.bids, self.asks = [], []
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]):
        try:
            self.bids = self._compress(sorted(bids, key=lambda x: -x[0]))
            self.asks = self._compress(sorted(asks, key=lambda x: x[0]))
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise
        
    def _compress(self, levels):
        try:
            if not levels: return []
            compressed, curr_p, curr_v = [], levels[0][0], 0
            for p, v in levels:
                if abs(p - curr_p) <= curr_p * self.compression_factor:
                    curr_v += v
                else:
                    compressed.append((curr_p, curr_v))
                    curr_p, curr_v = p, v
                if len(compressed) >= self.num_levels: break
            if curr_v > 0 and len(compressed) < self.num_levels:
                compressed.append((curr_p, curr_v))
            return compressed[:self.num_levels]
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _compress: {e}")
            raise
    
    def get_spread(self): return self.asks[0][0] - self.bids[0][0] if self.bids and self.asks else None
    def get_mid_price(self): return (self.asks[0][0] + self.bids[0][0]) / 2 if self.bids and self.asks else None

# UPGRADE 004: Dynamic Position Sizer
class DynamicPositionSizer:
    def __init__(self, base_risk_percent: float = 0.02, max_position_percent: float = 0.1):
        try:
            self.base_risk, self.max_position = base_risk_percent, max_position_percent
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate_size(self, equity: float, entry: float, stop: float, volatility: float = 0.02, confidence: float = 0.5, correlation: float = 0.0) -> float:
        try:
            vol_factor = 1.0 / (1.0 + volatility * 10)
            conf_factor = 0.5 + confidence * 0.5
            corr_factor = 1.0 - min(0.5, correlation)
            risk_amount = equity * self.base_risk * vol_factor * conf_factor * corr_factor
            price_risk = abs(entry - stop)
            if price_risk == 0: return 0
            return min(risk_amount / price_risk, (equity * self.max_position) / entry)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_size: {e}")
            raise

# UPGRADE 005: Intelligent Stop Loss Manager
class IntelligentStopLossManager:
    def __init__(self, atr_multiplier: float = 2.0):
        try:
            self.atr_multiplier = atr_multiplier
            self.stops: Dict[str, Dict] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def set_stop(self, pos_id: str, entry: float, direction: str, atr: float, sr: float = None) -> float:
        try:
            atr_stop = entry - atr * self.atr_multiplier if direction == 'long' else entry + atr * self.atr_multiplier
            if sr:
                buffer = atr * 0.5
                sr_stop = sr - buffer if direction == 'long' else sr + buffer
                stop = max(atr_stop, sr_stop) if direction == 'long' else min(atr_stop, sr_stop)
            else:
                stop = atr_stop
            self.stops[pos_id] = {'entry': entry, 'stop': stop, 'direction': direction, 'atr': atr}
            return stop
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in set_stop: {e}")
            raise
    
    def update_trailing(self, pos_id: str, price: float, trail_mult: float = 1.5) -> Optional[float]:
        try:
            if pos_id not in self.stops: return None
            s = self.stops[pos_id]
            new_stop = price - s['atr'] * trail_mult if s['direction'] == 'long' else price + s['atr'] * trail_mult
            if (s['direction'] == 'long' and new_stop > s['stop']) or (s['direction'] == 'short' and new_stop < s['stop']):
                s['stop'] = new_stop
            return s['stop']
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update_trailing: {e}")
            raise

# UPGRADE 006: Take Profit Optimizer
class TakeProfitOptimizer:
    def calculate_targets(self, entry: float, stop: float, direction: str, atr: float) -> Dict[str, List[float]]:
        try:
            risk = abs(entry - stop)
            sign = 1 if direction == 'long' else -1
            return {
                'fixed_rr': [entry + sign * risk * r for r in [1.0, 2.0, 3.0]],
                'fibonacci': [entry + sign * risk * f for f in [1.0, 1.618, 2.618]],
                'atr_based': [entry + sign * atr * m for m in [1.5, 3.0, 5.0]]
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_targets: {e}")
            raise

# UPGRADE 007: Market Session Detector
class MarketSessionDetector:
    SESSIONS = {'sydney': (22, 7, 0.7), 'tokyo': (0, 9, 0.8), 'london': (8, 17, 1.2), 'new_york': (13, 22, 1.3)}
    
    def get_active_sessions(self, utc_hour: int = None) -> List[str]:
        try:
            if utc_hour is None: utc_hour = datetime.utcnow().hour
            active = []
            for name, (start, end, _) in self.SESSIONS.items():
                if start <= end:
                    if start <= utc_hour < end: active.append(name)
                else:
                    if utc_hour >= start or utc_hour < end: active.append(name)
            return active
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in get_active_sessions: {e}")
            raise
    
    def get_volatility_factor(self, utc_hour: int = None) -> float:
        try:
            active = self.get_active_sessions(utc_hour)
            if not active: return 0.5
            base = max(self.SESSIONS[s][2] for s in active)
            return base * 1.5 if len(active) > 1 else base
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in get_volatility_factor: {e}")
            raise

# UPGRADE 008: Spread Monitor
class SpreadMonitor:
    def __init__(self, window: int = 1000):
        try:
            self.spreads: Dict[str, deque] = {}
            self.window = window
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, symbol: str, bid: float, ask: float) -> float:
        try:
            spread_pct = ((ask - bid) / ((bid + ask) / 2)) * 100
            if symbol not in self.spreads: self.spreads[symbol] = deque(maxlen=self.window)
            self.spreads[symbol].append(spread_pct)
            return spread_pct
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise
    
    def get_average(self, symbol: str) -> Optional[float]:
        return np.mean(self.spreads[symbol]) if symbol in self.spreads else None
    
    def is_anomaly(self, symbol: str, current: float) -> bool:
        try:
            if symbol not in self.spreads or len(self.spreads[symbol]) < 100: return False
            data = list(self.spreads[symbol])
            return current > np.mean(data) + 3 * np.std(data)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in is_anomaly: {e}")
            raise

# UPGRADE 009: Liquidity Analyzer
class LiquidityAnalyzer:
    def analyze(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]) -> Dict[str, Any]:
        try:
            bid_liq = sum(v for _, v in bids[:10])
            ask_liq = sum(v for _, v in asks[:10])
            total = bid_liq + ask_liq
            return {'bid_liquidity': bid_liq, 'ask_liquidity': ask_liq, 'imbalance': (bid_liq - ask_liq) / total if total else 0}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise

# UPGRADE 010: Volume Profile Builder
class VolumeProfileBuilder:
    def __init__(self, bins: int = 50):
        try:
            self.bins = bins
            self.profiles: Dict[str, Dict] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, symbol: str, price: float, volume: float):
        try:
            if symbol not in self.profiles: self.profiles[symbol] = {'data': {}, 'total': 0, 'poc': None}
            bin_idx = int(price * 100)
            if bin_idx not in self.profiles[symbol]['data']: self.profiles[symbol]['data'][bin_idx] = {'price': price, 'volume': 0}
            self.profiles[symbol]['data'][bin_idx]['volume'] += volume
            self.profiles[symbol]['total'] += volume
            sorted_bins = sorted(self.profiles[symbol]['data'].items(), key=lambda x: x[1]['volume'], reverse=True)
            if sorted_bins: self.profiles[symbol]['poc'] = sorted_bins[0][1]['price']
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise

# UPGRADE 011: Price Action Pattern Detector
class PriceActionPatternDetector:
    def analyze(self, o: float, h: float, l: float, c: float) -> List[str]:
        try:
            patterns = []
            body, total = abs(c - o), h - l
            if total == 0: return patterns
            if body / total < 0.1: patterns.append('doji')
            lower_wick = min(o, c) - l
            if lower_wick > body * 2 and c > o: patterns.append('hammer')
            upper_wick = h - max(o, c)
            if upper_wick > body * 2.5 or lower_wick > body * 2.5: patterns.append('pin_bar')
            return patterns
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise

# UPGRADE 012: Trend Strength Calculator
class TrendStrengthCalculator:
    def __init__(self):
        try:
            self.history: Dict[str, deque] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, symbol: str, close: float):
        try:
            if symbol not in self.history: self.history[symbol] = deque(maxlen=100)
            self.history[symbol].append(close)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise
        
    def calculate(self, symbol: str) -> Dict[str, Any]:
        try:
            if symbol not in self.history or len(self.history[symbol]) < 20:
                return {'strength': 0, 'direction': 'neutral'}
            closes = list(self.history[symbol])
            sma_fast, sma_slow = np.mean(closes[-10:]), np.mean(closes[-20:])
            direction = 'bullish' if sma_fast > sma_slow * 1.001 else 'bearish' if sma_fast < sma_slow * 0.999 else 'neutral'
            change = (closes[-1] - closes[0]) / closes[0] if closes[0] else 0
            return {'strength': min(100, abs(change) * 1000), 'direction': direction}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 013: Support/Resistance Finder
class SupportResistanceFinder:
    def __init__(self, sensitivity: float = 0.02):
        try:
            self.sensitivity = sensitivity
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def find_levels(self, highs: List[float], lows: List[float], current: float) -> Dict[str, List[float]]:
        try:
            if len(highs) < 20: return {'support': [], 'resistance': []}
            pivot_highs = [highs[i] for i in range(2, len(highs)-2) if highs[i] == max(highs[i-2:i+3])]
            pivot_lows = [lows[i] for i in range(2, len(lows)-2) if lows[i] == min(lows[i-2:i+3])]
            resistance = sorted([r for r in set(pivot_highs) if r > current])[:5]
            support = sorted([s for s in set(pivot_lows) if s < current], reverse=True)[:5]
            return {'support': support, 'resistance': resistance}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in find_levels: {e}")
            raise

# UPGRADE 014: Momentum Oscillator
class MomentumOscillator:
    def calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        try:
            if len(closes) < period + 1: return 50
            changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [c if c > 0 else 0 for c in changes[-period:]]
            losses = [-c if c < 0 else 0 for c in changes[-period:]]
            avg_gain, avg_loss = np.mean(gains), np.mean(losses) or 0.0001
            return 100 - (100 / (1 + avg_gain / avg_loss))
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_rsi: {e}")
            raise

# UPGRADE 015: Volatility Regime Detector
class VolatilityRegimeDetector:
    class Regime(Enum):
        VERY_LOW = auto(); LOW = auto(); NORMAL = auto(); HIGH = auto(); EXTREME = auto()
    
    def __init__(self):
        try:
            self.history: Dict[str, deque] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def detect(self, symbol: str, returns: List[float]) -> 'VolatilityRegimeDetector.Regime':
        try:
            if len(returns) < 20: return self.Regime.NORMAL
            vol = np.std(returns[-20:]) * np.sqrt(252)
            if symbol not in self.history: self.history[symbol] = deque(maxlen=100)
            self.history[symbol].append(vol)
            if len(self.history[symbol]) < 50: return self.Regime.NORMAL
            pct = sum(1 for v in self.history[symbol] if v < vol) / len(self.history[symbol]) * 100
            if pct < 10: return self.Regime.VERY_LOW
            if pct < 30: return self.Regime.LOW
            if pct < 70: return self.Regime.NORMAL
            if pct < 90: return self.Regime.HIGH
            return self.Regime.EXTREME
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise

# UPGRADE 016: Order Flow Imbalance Tracker
class OrderFlowImbalanceTracker:
    def __init__(self):
        try:
            self.flow: Dict[str, deque] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, symbol: str, volume: float, is_buy: bool) -> float:
        try:
            if symbol not in self.flow: self.flow[symbol] = deque(maxlen=100)
            self.flow[symbol].append(volume if is_buy else -volume)
            data = list(self.flow[symbol])
            buy_vol = sum(v for v in data if v > 0)
            sell_vol = abs(sum(v for v in data if v < 0))
            total = buy_vol + sell_vol
            return (buy_vol - sell_vol) / total if total else 0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise

# UPGRADE 017: Trade Classifier
class TradeClassifier:
    def __init__(self):
        try:
            self.last_prices: Dict[str, float] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def classify(self, symbol: str, price: float) -> str:
        try:
            if symbol not in self.last_prices:
                self.last_prices[symbol] = price
                return 'unknown'
            side = 'buy' if price > self.last_prices[symbol] else 'sell' if price < self.last_prices[symbol] else 'unknown'
            self.last_prices[symbol] = price
            return side
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in classify: {e}")
            raise

# UPGRADE 018: VWAP Calculator
class VWAPCalculator:
    def __init__(self):
        try:
            self.data: Dict[str, Dict] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, symbol: str, h: float, l: float, c: float, v: float) -> float:
        try:
            if symbol not in self.data: self.data[symbol] = {'tp_vol': 0, 'vol': 0}
            tp = (h + l + c) / 3
            self.data[symbol]['tp_vol'] += tp * v
            self.data[symbol]['vol'] += v
            return self.data[symbol]['tp_vol'] / self.data[symbol]['vol'] if self.data[symbol]['vol'] else 0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise

# UPGRADE 019: ATR Calculator
class ATRCalculator:
    def __init__(self, period: int = 14):
        try:
            self.period = period
            self.tr_history: Dict[str, deque] = {}
            self.atr: Dict[str, float] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, symbol: str, h: float, l: float, c: float, prev_c: float = None) -> float:
        try:
            tr = max(h - l, abs(h - prev_c) if prev_c else 0, abs(l - prev_c) if prev_c else 0)
            if symbol not in self.tr_history: self.tr_history[symbol] = deque(maxlen=self.period * 2)
            self.tr_history[symbol].append(tr)
            if len(self.tr_history[symbol]) >= self.period:
                if symbol not in self.atr: self.atr[symbol] = np.mean(list(self.tr_history[symbol])[:self.period])
                else: self.atr[symbol] = (self.atr[symbol] * (self.period - 1) + tr) / self.period
            return self.atr.get(symbol, tr)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise

# UPGRADE 020: Bollinger Bands Calculator
class BollingerBandsCalculator:
    def __init__(self, period: int = 20, std: float = 2.0):
        try:
            self.period, self.std = period, std
            self.history: Dict[str, deque] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, symbol: str, close: float) -> Dict[str, float]:
        try:
            if symbol not in self.history: self.history[symbol] = deque(maxlen=self.period)
            self.history[symbol].append(close)
            if len(self.history[symbol]) < self.period: return {'middle': close, 'upper': close, 'lower': close}
            prices = list(self.history[symbol])
            mid, s = np.mean(prices), np.std(prices)
            return {'middle': mid, 'upper': mid + self.std * s, 'lower': mid - self.std * s}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise

# UPGRADE 021: Fibonacci Calculator
class FibonacciCalculator:
    LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    
    def calculate(self, high: float, low: float, is_uptrend: bool) -> Dict[str, float]:
        try:
            diff = high - low
            return {f'fib_{l}': (high - diff * l if is_uptrend else low + diff * l) for l in self.LEVELS}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 022: Pivot Point Calculator
class PivotPointCalculator:
    def calculate(self, h: float, l: float, c: float) -> Dict[str, float]:
        try:
            p = (h + l + c) / 3
            return {'pivot': p, 'r1': 2*p - l, 's1': 2*p - h, 'r2': p + (h-l), 's2': p - (h-l)}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 023: Market Structure Analyzer
class MarketStructureAnalyzer:
    def analyze(self, highs: List[float], lows: List[float]) -> Dict[str, Any]:
        try:
            if len(highs) < 10: return {'trend': 'unknown'}
            hh = highs[-1] > highs[-5]
            hl = lows[-1] > lows[-5]
            if hh and hl: return {'trend': 'bullish', 'structure': ['HH', 'HL']}
            if not hh and not hl: return {'trend': 'bearish', 'structure': ['LH', 'LL']}
            return {'trend': 'ranging'}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise

# UPGRADE 024: Order Block Detector
class OrderBlockDetector:
    def detect(self, candles: List[Dict]) -> List[Dict]:
        try:
            if len(candles) < 5: return []
            blocks = []
            for i in range(2, len(candles) - 2):
                c, nc = candles[i], candles[i + 1]
                if c['close'] < c['open'] and (nc['close'] - c['close']) / c['close'] > 0.005:
                    blocks.append({'type': 'bullish', 'high': c['high'], 'low': c['low']})
                if c['close'] > c['open'] and (c['close'] - nc['close']) / c['close'] > 0.005:
                    blocks.append({'type': 'bearish', 'high': c['high'], 'low': c['low']})
            return blocks
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise

# UPGRADE 025: Fair Value Gap Detector
class FairValueGapDetector:
    def detect(self, candles: List[Dict]) -> List[Dict]:
        try:
            if len(candles) < 3: return []
            gaps = []
            for i in range(1, len(candles) - 1):
                prev, nxt = candles[i - 1], candles[i + 1]
                if nxt['low'] > prev['high']: gaps.append({'type': 'bullish', 'top': nxt['low'], 'bottom': prev['high']})
                if nxt['high'] < prev['low']: gaps.append({'type': 'bearish', 'top': prev['low'], 'bottom': nxt['high']})
            return gaps
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise
