"""
Core Trading Engine Upgrades 51-75
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque
import hashlib
import json

# UPGRADE 051: Breakeven Manager
class BreakevenManager:
    def __init__(self, trigger_rr: float = 1.0):
        self.trigger_rr = trigger_rr
        self.positions: Dict[str, Dict] = {}
        
    def set_position(self, pos_id: str, entry: float, stop: float, direction: str):
        risk = abs(entry - stop)
        self.positions[pos_id] = {'entry': entry, 'stop': stop, 'risk': risk, 'direction': direction, 'be_set': False}
        
    def check_breakeven(self, pos_id: str, current: float) -> Optional[float]:
        if pos_id not in self.positions: return None
        p = self.positions[pos_id]
        if p['be_set']: return None
        profit = (current - p['entry']) if p['direction'] == 'long' else (p['entry'] - current)
        if profit >= p['risk'] * self.trigger_rr:
            p['be_set'] = True
            return p['entry']
        return None

# UPGRADE 052: Partial Close Manager
class PartialCloseManager:
    def __init__(self, levels: List[Tuple[float, float]] = None):
        self.levels = levels or [(1.0, 0.33), (2.0, 0.33), (3.0, 0.34)]
        self.positions: Dict[str, Dict] = {}
        
    def set_position(self, pos_id: str, entry: float, stop: float, size: float):
        self.positions[pos_id] = {'entry': entry, 'stop': stop, 'size': size, 'remaining': size, 'closed_levels': []}
        
    def check_partial(self, pos_id: str, current: float, direction: str) -> Optional[Tuple[float, float]]:
        if pos_id not in self.positions: return None
        p = self.positions[pos_id]
        risk = abs(p['entry'] - p['stop'])
        profit = (current - p['entry']) if direction == 'long' else (p['entry'] - current)
        rr = profit / risk if risk > 0 else 0
        for level_rr, portion in self.levels:
            if level_rr not in p['closed_levels'] and rr >= level_rr:
                close_size = p['size'] * portion
                p['remaining'] -= close_size
                p['closed_levels'].append(level_rr)
                return (close_size, level_rr)
        return None

# UPGRADE 053: Trade Journal Logger
class TradeJournalLogger:
    def __init__(self):
        self.entries: List[Dict] = []
        
    def log_entry(self, symbol: str, direction: str, entry: float, stop: float, target: float, reason: str, setup: str):
        self.entries.append({
            'timestamp': datetime.utcnow().isoformat(), 'symbol': symbol, 'direction': direction,
            'entry': entry, 'stop': stop, 'target': target, 'reason': reason, 'setup': setup, 'status': 'open'
        })
        return len(self.entries) - 1
    
    def log_exit(self, idx: int, exit_price: float, pnl: float, notes: str):
        if 0 <= idx < len(self.entries):
            self.entries[idx].update({'exit': exit_price, 'pnl': pnl, 'notes': notes, 'status': 'closed'})

# UPGRADE 054: Setup Pattern Tracker
class SetupPatternTracker:
    def __init__(self):
        self.setups: Dict[str, Dict] = {}
        
    def record(self, setup_name: str, pnl: float):
        if setup_name not in self.setups:
            self.setups[setup_name] = {'trades': 0, 'wins': 0, 'total_pnl': 0, 'pnls': []}
        self.setups[setup_name]['trades'] += 1
        self.setups[setup_name]['total_pnl'] += pnl
        self.setups[setup_name]['pnls'].append(pnl)
        if pnl > 0: self.setups[setup_name]['wins'] += 1
        
    def get_best_setups(self, n: int = 5) -> List[Tuple[str, float]]:
        return sorted([(s, d['total_pnl']) for s, d in self.setups.items()], key=lambda x: -x[1])[:n]

# UPGRADE 055: Market Condition Classifier
class MarketConditionClassifier:
    class Condition(Enum):
        TRENDING_UP = auto(); TRENDING_DOWN = auto(); RANGING = auto()
        VOLATILE = auto(); QUIET = auto(); BREAKOUT = auto()
    
    def classify(self, prices: List[float], volumes: List[float]) -> 'MarketConditionClassifier.Condition':
        if len(prices) < 20: return self.Condition.QUIET
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        vol = np.std(returns)
        trend = (prices[-1] - prices[0]) / prices[0]
        if vol > 0.03: return self.Condition.VOLATILE
        if trend > 0.02: return self.Condition.TRENDING_UP
        if trend < -0.02: return self.Condition.TRENDING_DOWN
        if vol < 0.005: return self.Condition.QUIET
        return self.Condition.RANGING

# UPGRADE 056: Adaptive Strategy Selector
class AdaptiveStrategySelector:
    def __init__(self):
        self.strategies = {'trend': ['trend_follow', 'breakout'], 'range': ['mean_reversion', 'scalp'], 'volatile': ['momentum']}
        
    def select(self, condition: str) -> List[str]:
        return self.strategies.get(condition.lower(), ['default'])

# UPGRADE 057: Signal Aggregator
class SignalAggregator:
    def __init__(self):
        self.signals: Dict[str, List[Dict]] = {}
        
    def add_signal(self, symbol: str, source: str, direction: str, strength: float):
        if symbol not in self.signals: self.signals[symbol] = []
        self.signals[symbol].append({'source': source, 'direction': direction, 'strength': strength, 'time': datetime.utcnow()})
        
    def aggregate(self, symbol: str) -> Dict[str, Any]:
        if symbol not in self.signals: return {'direction': 'neutral', 'confidence': 0}
        recent = [s for s in self.signals[symbol] if (datetime.utcnow() - s['time']).seconds < 300]
        if not recent: return {'direction': 'neutral', 'confidence': 0}
        bull = sum(s['strength'] for s in recent if s['direction'] == 'bullish')
        bear = sum(s['strength'] for s in recent if s['direction'] == 'bearish')
        total = bull + bear
        if bull > bear: return {'direction': 'bullish', 'confidence': bull / total if total else 0}
        if bear > bull: return {'direction': 'bearish', 'confidence': bear / total if total else 0}
        return {'direction': 'neutral', 'confidence': 0}

# UPGRADE 058: Confirmation Engine
class ConfirmationEngine:
    def __init__(self, required: int = 3):
        self.required = required
        
    def check(self, confirmations: List[bool]) -> bool:
        return sum(confirmations) >= self.required

# UPGRADE 059: Entry Filter Chain
class EntryFilterChain:
    def __init__(self):
        self.filters: List[callable] = []
        
    def add_filter(self, filter_func: callable):
        self.filters.append(filter_func)
        
    def check(self, context: Dict) -> Tuple[bool, List[str]]:
        failed = []
        for f in self.filters:
            try:
                if not f(context): failed.append(f.__name__)
            except Exception as e: failed.append(f.__name__)
        return len(failed) == 0, failed

# UPGRADE 060: Exit Filter Chain
class ExitFilterChain:
    def __init__(self):
        self.filters: List[callable] = []
        
    def add_filter(self, filter_func: callable):
        self.filters.append(filter_func)
        
    def should_exit(self, context: Dict) -> Tuple[bool, str]:
        for f in self.filters:
            try:
                if f(context): return True, f.__name__
            except Exception as e: pass
        return False, ''

# UPGRADE 061: Risk Budget Manager
class RiskBudgetManager:
    def __init__(self, daily_limit: float = 0.02, weekly_limit: float = 0.05):
        self.daily_limit = daily_limit
        self.weekly_limit = weekly_limit
        self.daily_used = 0
        self.weekly_used = 0
        self.last_reset = datetime.utcnow()
        
    def can_trade(self, risk: float) -> bool:
        self._check_reset()
        return (self.daily_used + risk <= self.daily_limit) and (self.weekly_used + risk <= self.weekly_limit)
    
    def use_budget(self, risk: float):
        self.daily_used += risk
        self.weekly_used += risk
        
    def _check_reset(self):
        now = datetime.utcnow()
        if now.date() != self.last_reset.date(): self.daily_used = 0
        if now.isocalendar()[1] != self.last_reset.isocalendar()[1]: self.weekly_used = 0
        self.last_reset = now

# UPGRADE 062: Correlation Risk Manager
class CorrelationRiskManager:
    def __init__(self, max_correlated: float = 0.3):
        self.max_correlated = max_correlated
        self.correlations: Dict[Tuple[str, str], float] = {}
        self.positions: Dict[str, float] = {}
        
    def set_correlation(self, sym1: str, sym2: str, corr: float):
        self.correlations[(sym1, sym2)] = corr
        
    def can_add_position(self, symbol: str, size: float) -> bool:
        total_correlated = 0
        for pos_sym, pos_size in self.positions.items():
            corr = self.correlations.get((symbol, pos_sym)) or self.correlations.get((pos_sym, symbol), 0)
            if abs(corr) > 0.7: total_correlated += pos_size
        return total_correlated + size <= self.max_correlated

# UPGRADE 063: Drawdown Recovery Mode
class DrawdownRecoveryMode:
    def __init__(self, trigger: float = 0.1, reduction: float = 0.5):
        self.trigger = trigger
        self.reduction = reduction
        self.in_recovery = False
        
    def check(self, current_dd: float) -> float:
        if current_dd >= self.trigger: self.in_recovery = True
        if current_dd < self.trigger * 0.5: self.in_recovery = False
        return self.reduction if self.in_recovery else 1.0

# UPGRADE 064: Equity Curve Analyzer
class EquityCurveAnalyzer:
    def __init__(self):
        self.equity: deque = deque(maxlen=1000)
        
    def update(self, value: float):
        self.equity.append({'value': value, 'time': datetime.utcnow()})
        
    def analyze(self) -> Dict[str, Any]:
        if len(self.equity) < 10: return {'trend': 'unknown', 'smoothness': 0}
        values = [e['value'] for e in self.equity]
        returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
        trend = 'up' if values[-1] > values[0] else 'down'
        smoothness = 1 - np.std(returns) * 10
        return {'trend': trend, 'smoothness': max(0, smoothness), 'volatility': np.std(returns)}

# UPGRADE 065: Monte Carlo Simulator
class MonteCarloSimulator:
    def simulate(self, returns: List[float], n_sims: int = 1000, n_periods: int = 252) -> Dict[str, float]:
        if len(returns) < 20: return {'median': 0, 'worst_5': 0, 'best_5': 0}
        results = []
        for _ in range(n_sims):
            sim_returns = np.random.choice(returns, n_periods, replace=True)
            final = np.prod(1 + np.array(sim_returns))
            results.append(final - 1)
        results = sorted(results)
        return {'median': results[n_sims // 2], 'worst_5': results[int(n_sims * 0.05)], 'best_5': results[int(n_sims * 0.95)]}

# UPGRADE 066: Walk Forward Optimizer
class WalkForwardOptimizer:
    def __init__(self, in_sample: int = 100, out_sample: int = 20):
        self.in_sample = in_sample
        self.out_sample = out_sample
        
    def get_windows(self, data_len: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        windows = []
        start = 0
        while start + self.in_sample + self.out_sample <= data_len:
            in_start, in_end = start, start + self.in_sample
            out_start, out_end = in_end, in_end + self.out_sample
            windows.append(((in_start, in_end), (out_start, out_end)))
            start += self.out_sample
        return windows

# UPGRADE 067: Parameter Sensitivity Analyzer
class ParameterSensitivityAnalyzer:
    def analyze(self, base_result: float, varied_results: Dict[str, List[Tuple[float, float]]]) -> Dict[str, float]:
        sensitivities = {}
        for param, results in varied_results.items():
            if not results: continue
            changes = [abs(r - base_result) / abs(base_result) if base_result else 0 for _, r in results]
            sensitivities[param] = np.mean(changes) if changes else 0
        return sensitivities

# UPGRADE 068: Regime Change Detector
class RegimeChangeDetector:
    def __init__(self, window: int = 50):
        self.window = window
        self.history: deque = deque(maxlen=window * 2)
        
    def detect(self, value: float) -> bool:
        self.history.append(value)
        if len(self.history) < self.window * 2: return False
        old = list(self.history)[:self.window]
        new = list(self.history)[self.window:]
        old_mean, new_mean = np.mean(old), np.mean(new)
        old_std = np.std(old) or 0.0001
        return abs(new_mean - old_mean) > 2 * old_std

# UPGRADE 069: Anomaly Detector
class AnomalyDetector:
    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
        self.history: deque = deque(maxlen=100)
        
    def check(self, value: float) -> bool:
        self.history.append(value)
        if len(self.history) < 20: return False
        mean, std = np.mean(self.history), np.std(self.history) or 0.0001
        return abs(value - mean) > self.threshold * std

# UPGRADE 070: Flash Crash Detector
class FlashCrashDetector:
    def __init__(self, threshold: float = 0.05, window_secs: int = 60):
        self.threshold = threshold
        self.window = window_secs
        self.prices: deque = deque(maxlen=1000)
        
    def check(self, price: float, timestamp: datetime) -> bool:
        self.prices.append({'price': price, 'time': timestamp})
        recent = [p for p in self.prices if (timestamp - p['time']).seconds <= self.window]
        if len(recent) < 2: return False
        max_p, min_p = max(p['price'] for p in recent), min(p['price'] for p in recent)
        return (max_p - min_p) / max_p > self.threshold

# UPGRADE 071: News Impact Tracker
class NewsImpactTracker:
    def __init__(self):
        self.events: List[Dict] = []
        
    def add_event(self, symbol: str, headline: str, sentiment: float, importance: str):
        self.events.append({'symbol': symbol, 'headline': headline, 'sentiment': sentiment, 
                          'importance': importance, 'time': datetime.utcnow()})
        
    def get_recent_impact(self, symbol: str, mins: int = 30) -> float:
        cutoff = datetime.utcnow() - timedelta(minutes=mins)
        recent = [e for e in self.events if e['symbol'] == symbol and e['time'] > cutoff]
        if not recent: return 0
        weights = {'high': 3, 'medium': 2, 'low': 1}
        return sum(e['sentiment'] * weights.get(e['importance'], 1) for e in recent) / len(recent)

# UPGRADE 072: Economic Calendar Integration
class EconomicCalendarIntegration:
    def __init__(self):
        self.events: List[Dict] = []
        
    def add_event(self, name: str, time: datetime, impact: str, currency: str):
        self.events.append({'name': name, 'time': time, 'impact': impact, 'currency': currency})
        
    def get_upcoming(self, mins: int = 60) -> List[Dict]:
        now = datetime.utcnow()
        return [e for e in self.events if 0 <= (e['time'] - now).total_seconds() <= mins * 60]
    
    def should_avoid_trading(self, currency: str, mins_before: int = 15) -> bool:
        upcoming = self.get_upcoming(mins_before)
        return any(e['currency'] == currency and e['impact'] == 'high' for e in upcoming)

# UPGRADE 073: Sentiment Score Aggregator
class SentimentScoreAggregator:
    def __init__(self):
        self.scores: Dict[str, List[Dict]] = {}
        
    def add_score(self, symbol: str, source: str, score: float, weight: float = 1.0):
        if symbol not in self.scores: self.scores[symbol] = []
        self.scores[symbol].append({'source': source, 'score': score, 'weight': weight, 'time': datetime.utcnow()})
        
    def get_aggregate(self, symbol: str, max_age_mins: int = 60) -> float:
        if symbol not in self.scores: return 0
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_mins)
        recent = [s for s in self.scores[symbol] if s['time'] > cutoff]
        if not recent: return 0
        total_weight = sum(s['weight'] for s in recent)
        return sum(s['score'] * s['weight'] for s in recent) / total_weight if total_weight else 0

# UPGRADE 074: Social Media Sentiment Tracker
class SocialMediaSentimentTracker:
    def __init__(self):
        self.mentions: Dict[str, deque] = {}
        
    def add_mention(self, symbol: str, sentiment: float, platform: str):
        if symbol not in self.mentions: self.mentions[symbol] = deque(maxlen=1000)
        self.mentions[symbol].append({'sentiment': sentiment, 'platform': platform, 'time': datetime.utcnow()})
        
    def get_sentiment(self, symbol: str) -> Dict[str, float]:
        if symbol not in self.mentions: return {'score': 0, 'volume': 0}
        recent = [m for m in self.mentions[symbol] if (datetime.utcnow() - m['time']).seconds < 3600]
        if not recent: return {'score': 0, 'volume': 0}
        return {'score': np.mean([m['sentiment'] for m in recent]), 'volume': len(recent)}

# UPGRADE 075: Order Execution Analyzer
class OrderExecutionAnalyzer:
    def __init__(self):
        self.executions: List[Dict] = []
        
    def record(self, order_id: str, expected: float, actual: float, size: float, latency_ms: float):
        slippage = (actual - expected) / expected * 10000  # bps
        self.executions.append({'order_id': order_id, 'expected': expected, 'actual': actual,
                               'size': size, 'slippage_bps': slippage, 'latency_ms': latency_ms})
        
    def get_stats(self) -> Dict[str, float]:
        if not self.executions: return {'avg_slippage': 0, 'avg_latency': 0}
        return {
            'avg_slippage': np.mean([e['slippage_bps'] for e in self.executions]),
            'avg_latency': np.mean([e['latency_ms'] for e in self.executions]),
            'max_slippage': max(e['slippage_bps'] for e in self.executions)
        }
