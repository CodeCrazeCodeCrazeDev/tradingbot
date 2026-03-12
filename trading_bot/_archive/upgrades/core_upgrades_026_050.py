"""
Core Trading Engine Upgrades 26-50
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque

# UPGRADE 026: Liquidity Sweep Detector
class LiquiditySweepDetector:
    def detect(self, candles: List[Dict], swing_highs: List[float], swing_lows: List[float]) -> List[Dict]:
        sweeps = []
        if len(candles) < 3: return sweeps
        c = candles[-1]
        for sh in swing_highs[-5:]:
            if c['high'] > sh and c['close'] < sh: sweeps.append({'type': 'high_sweep', 'level': sh})
        for sl in swing_lows[-5:]:
            if c['low'] < sl and c['close'] > sl: sweeps.append({'type': 'low_sweep', 'level': sl})
        return sweeps

# UPGRADE 027: Divergence Detector
class DivergenceDetector:
    def detect(self, prices: List[float], indicator: List[float]) -> Optional[str]:
        if len(prices) < 20 or len(indicator) < 20: return None
        price_trend = prices[-1] > prices[-10]
        ind_trend = indicator[-1] > indicator[-10]
        if price_trend and not ind_trend: return 'bearish_divergence'
        if not price_trend and ind_trend: return 'bullish_divergence'
        return None

# UPGRADE 028: Multi-Timeframe Analyzer
class MultiTimeframeAnalyzer:
    def __init__(self):
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', 'D']
        self.signals: Dict[str, Dict] = {}
        
    def update(self, symbol: str, tf: str, direction: str, strength: float):
        if symbol not in self.signals: self.signals[symbol] = {}
        self.signals[symbol][tf] = {'direction': direction, 'strength': strength}
        
    def get_confluence(self, symbol: str) -> Dict[str, Any]:
        if symbol not in self.signals: return {'score': 0, 'direction': 'neutral'}
        sigs = self.signals[symbol]
        bullish = sum(1 for s in sigs.values() if s['direction'] == 'bullish')
        bearish = sum(1 for s in sigs.values() if s['direction'] == 'bearish')
        total = len(sigs)
        if bullish > bearish: return {'score': bullish / total, 'direction': 'bullish'}
        if bearish > bullish: return {'score': bearish / total, 'direction': 'bearish'}
        return {'score': 0, 'direction': 'neutral'}

# UPGRADE 029: Entry Timing Optimizer
class EntryTimingOptimizer:
    def __init__(self):
        self.entry_scores: Dict[str, List] = {}
        
    def score_entry(self, symbol: str, price: float, vwap: float, bb: Dict, rsi: float) -> float:
        score = 50
        if price < vwap: score += 10
        if price < bb.get('lower', price): score += 15
        if rsi < 30: score += 15
        elif rsi > 70: score -= 15
        if price > bb.get('middle', price) and price < bb.get('upper', price): score += 5
        return min(100, max(0, score))

# UPGRADE 030: Exit Timing Optimizer
class ExitTimingOptimizer:
    def score_exit(self, pnl_percent: float, rsi: float, bb_percent: float, time_in_trade: int) -> float:
        score = 0
        if pnl_percent > 2: score += 30
        if rsi > 70: score += 20
        if bb_percent > 0.9: score += 20
        if time_in_trade > 60: score += 10
        if pnl_percent < -1: score += 40
        return min(100, score)

# UPGRADE 031: Trade Quality Scorer
class TradeQualityScorer:
    def score(self, entry_score: float, confluence: float, risk_reward: float, volatility_regime: str) -> str:
        total = entry_score * 0.3 + confluence * 100 * 0.3 + min(risk_reward * 20, 40)
        if volatility_regime == 'EXTREME': total *= 0.5
        if total >= 80: return 'A+'
        if total >= 70: return 'A'
        if total >= 60: return 'B'
        if total >= 50: return 'C'
        return 'D'

# UPGRADE 032: Slippage Estimator
class SlippageEstimator:
    def __init__(self):
        self.history: Dict[str, deque] = {}
        
    def estimate(self, symbol: str, order_size: float, liquidity: float, spread: float) -> float:
        base_slip = spread * 0.5
        size_impact = (order_size / liquidity) * 0.1 if liquidity > 0 else 0.01
        return base_slip + size_impact
    
    def record(self, symbol: str, expected: float, actual: float):
        if symbol not in self.history: self.history[symbol] = deque(maxlen=100)
        self.history[symbol].append(actual - expected)
        
    def get_average(self, symbol: str) -> float:
        return np.mean(self.history[symbol]) if symbol in self.history else 0

# UPGRADE 033: Commission Tracker
class CommissionTracker:
    def __init__(self, default_rate: float = 0.001):
        self.rate = default_rate
        self.total_paid: Dict[str, float] = {}
        
    def calculate(self, symbol: str, volume: float, price: float) -> float:
        commission = volume * price * self.rate
        self.total_paid[symbol] = self.total_paid.get(symbol, 0) + commission
        return commission
    
    def get_total(self, symbol: str = None) -> float:
        if symbol: return self.total_paid.get(symbol, 0)
        return sum(self.total_paid.values())

# UPGRADE 034: Profit Factor Calculator
class ProfitFactorCalculator:
    def __init__(self):
        self.wins: List[float] = []
        self.losses: List[float] = []
        
    def add_trade(self, pnl: float):
        if pnl > 0: self.wins.append(pnl)
        else: self.losses.append(abs(pnl))
        
    def calculate(self) -> float:
        total_wins = sum(self.wins)
        total_losses = sum(self.losses) or 0.0001
        return total_wins / total_losses

# UPGRADE 035: Sharpe Ratio Calculator
class SharpeRatioCalculator:
    def __init__(self, risk_free_rate: float = 0.02):
        self.rf = risk_free_rate
        self.returns: deque = deque(maxlen=252)
        
    def add_return(self, ret: float):
        self.returns.append(ret)
        
    def calculate(self) -> float:
        if len(self.returns) < 20: return 0
        returns = np.array(self.returns)
        excess = returns - self.rf / 252
        return np.mean(excess) / (np.std(excess) or 0.0001) * np.sqrt(252)

# UPGRADE 036: Sortino Ratio Calculator
class SortinoRatioCalculator:
    def __init__(self, risk_free_rate: float = 0.02):
        self.rf = risk_free_rate
        self.returns: deque = deque(maxlen=252)
        
    def add_return(self, ret: float):
        self.returns.append(ret)
        
    def calculate(self) -> float:
        if len(self.returns) < 20: return 0
        returns = np.array(self.returns)
        excess = returns - self.rf / 252
        downside = returns[returns < 0]
        downside_std = np.std(downside) if len(downside) > 0 else 0.0001
        return np.mean(excess) / downside_std * np.sqrt(252)

# UPGRADE 037: Maximum Drawdown Tracker
class MaxDrawdownTracker:
    def __init__(self):
        self.peak = 0
        self.max_dd = 0
        self.current_dd = 0
        
    def update(self, equity: float) -> float:
        if equity > self.peak: self.peak = equity
        self.current_dd = (self.peak - equity) / self.peak if self.peak > 0 else 0
        self.max_dd = max(self.max_dd, self.current_dd)
        return self.current_dd

# UPGRADE 038: Win Rate Tracker
class WinRateTracker:
    def __init__(self):
        self.wins = 0
        self.losses = 0
        
    def add_trade(self, is_win: bool):
        if is_win: self.wins += 1
        else: self.losses += 1
        
    def get_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0

# UPGRADE 039: Average Trade Calculator
class AverageTradeCalculator:
    def __init__(self):
        self.trades: List[float] = []
        
    def add_trade(self, pnl: float):
        self.trades.append(pnl)
        
    def get_average(self) -> float:
        return np.mean(self.trades) if self.trades else 0
    
    def get_average_win(self) -> float:
        wins = [t for t in self.trades if t > 0]
        return np.mean(wins) if wins else 0
    
    def get_average_loss(self) -> float:
        losses = [t for t in self.trades if t < 0]
        return np.mean(losses) if losses else 0

# UPGRADE 040: Expectancy Calculator
class ExpectancyCalculator:
    def calculate(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        return (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))

# UPGRADE 041: Kelly Criterion Calculator
class KellyCriterionCalculator:
    def calculate(self, win_rate: float, win_loss_ratio: float) -> float:
        if win_loss_ratio <= 0: return 0
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        return max(0, min(0.25, kelly))  # Cap at 25%

# UPGRADE 042: Risk of Ruin Calculator
class RiskOfRuinCalculator:
    def calculate(self, win_rate: float, risk_per_trade: float, ruin_level: float = 0.5) -> float:
        if win_rate >= 1 or win_rate <= 0: return 0
        q = 1 - win_rate
        if win_rate == 0.5: return ruin_level
        return ((q / win_rate) ** (1 / risk_per_trade)) if win_rate > 0.5 else 1.0

# UPGRADE 043: Trade Duration Analyzer
class TradeDurationAnalyzer:
    def __init__(self):
        self.durations: Dict[str, List[int]] = {'win': [], 'loss': []}
        
    def add_trade(self, duration_mins: int, is_win: bool):
        key = 'win' if is_win else 'loss'
        self.durations[key].append(duration_mins)
        
    def get_stats(self) -> Dict[str, float]:
        return {
            'avg_win_duration': np.mean(self.durations['win']) if self.durations['win'] else 0,
            'avg_loss_duration': np.mean(self.durations['loss']) if self.durations['loss'] else 0,
            'avg_duration': np.mean(self.durations['win'] + self.durations['loss']) if any(self.durations.values()) else 0
        }

# UPGRADE 044: Time-of-Day Performance Analyzer
class TimeOfDayAnalyzer:
    def __init__(self):
        self.hourly_pnl: Dict[int, List[float]] = {h: [] for h in range(24)}
        
    def add_trade(self, hour: int, pnl: float):
        self.hourly_pnl[hour].append(pnl)
        
    def get_best_hours(self, n: int = 3) -> List[int]:
        avgs = {h: np.mean(pnls) for h, pnls in self.hourly_pnl.items() if pnls}
        return sorted(avgs.keys(), key=lambda h: avgs[h], reverse=True)[:n]

# UPGRADE 045: Day-of-Week Performance Analyzer
class DayOfWeekAnalyzer:
    def __init__(self):
        self.daily_pnl: Dict[int, List[float]] = {d: [] for d in range(7)}
        
    def add_trade(self, day: int, pnl: float):
        self.daily_pnl[day].append(pnl)
        
    def get_best_days(self) -> List[int]:
        avgs = {d: np.mean(pnls) for d, pnls in self.daily_pnl.items() if pnls}
        return sorted(avgs.keys(), key=lambda d: avgs[d], reverse=True)

# UPGRADE 046: Consecutive Wins/Losses Tracker
class ConsecutiveTracker:
    def __init__(self):
        self.current_streak = 0
        self.max_win_streak = 0
        self.max_loss_streak = 0
        self.is_winning = True
        
    def add_trade(self, is_win: bool):
        if is_win == self.is_winning:
            self.current_streak += 1
        else:
            self.current_streak = 1
            self.is_winning = is_win
        if is_win: self.max_win_streak = max(self.max_win_streak, self.current_streak)
        else: self.max_loss_streak = max(self.max_loss_streak, self.current_streak)

# UPGRADE 047: Recovery Factor Calculator
class RecoveryFactorCalculator:
    def calculate(self, net_profit: float, max_drawdown: float) -> float:
        if max_drawdown <= 0: return float('inf') if net_profit > 0 else 0
        return net_profit / max_drawdown

# UPGRADE 048: Calmar Ratio Calculator
class CalmarRatioCalculator:
    def calculate(self, annual_return: float, max_drawdown: float) -> float:
        if max_drawdown <= 0: return float('inf') if annual_return > 0 else 0
        return annual_return / max_drawdown

# UPGRADE 049: Trade Frequency Analyzer
class TradeFrequencyAnalyzer:
    def __init__(self):
        self.trades: List[datetime] = []
        
    def add_trade(self, timestamp: datetime):
        self.trades.append(timestamp)
        
    def get_frequency(self) -> Dict[str, float]:
        if len(self.trades) < 2: return {'daily': 0, 'weekly': 0, 'monthly': 0}
        days = (self.trades[-1] - self.trades[0]).days or 1
        total = len(self.trades)
        return {'daily': total / days, 'weekly': total / (days / 7), 'monthly': total / (days / 30)}

# UPGRADE 050: Position Heat Map
class PositionHeatMap:
    def __init__(self):
        self.positions: Dict[str, Dict] = {}
        
    def update(self, symbol: str, size: float, pnl: float, risk: float):
        self.positions[symbol] = {'size': size, 'pnl': pnl, 'risk': risk, 'heat': abs(risk) * abs(size)}
        
    def get_hottest(self, n: int = 5) -> List[Tuple[str, float]]:
        return sorted([(s, p['heat']) for s, p in self.positions.items()], key=lambda x: -x[1])[:n]
    
    def get_total_heat(self) -> float:
        return sum(p['heat'] for p in self.positions.values())
