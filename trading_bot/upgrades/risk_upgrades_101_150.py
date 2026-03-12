"""
Risk Management Upgrades 101-150
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque

# UPGRADE 101: Value at Risk Calculator
import logging

logger = logging.getLogger(__name__)

class VaRCalculator:
    def historical_var(self, returns: List[float], confidence: float = 0.95) -> float:
        try:
            if len(returns) < 20: return 0
            sorted_returns = sorted(returns)
            idx = int(len(sorted_returns) * (1 - confidence))
            return abs(sorted_returns[idx])
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in historical_var: {e}")
            raise
    
    def parametric_var(self, returns: List[float], confidence: float = 0.95) -> float:
        try:
            if len(returns) < 20: return 0
            mean, std = np.mean(returns), np.std(returns)
            z_score = {0.95: 1.645, 0.99: 2.326}.get(confidence, 1.645)
            return abs(mean - z_score * std)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in parametric_var: {e}")
            raise

# UPGRADE 102: Conditional VaR (CVaR) Calculator
class CVaRCalculator:
    def calculate(self, returns: List[float], confidence: float = 0.95) -> float:
        try:
            if len(returns) < 20: return 0
            sorted_returns = sorted(returns)
            cutoff_idx = int(len(sorted_returns) * (1 - confidence))
            tail_returns = sorted_returns[:cutoff_idx + 1]
            return abs(np.mean(tail_returns)) if tail_returns else 0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 103: Stress Test Engine
class StressTestEngine:
    def __init__(self):
        try:
            self.scenarios = {
                'market_crash': -0.20, 'flash_crash': -0.10, 'black_swan': -0.35,
                'moderate_decline': -0.05, 'volatility_spike': -0.08
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def run_test(self, portfolio_value: float, positions: Dict[str, float]) -> Dict[str, float]:
        try:
            results = {}
            for scenario, shock in self.scenarios.items():
                loss = portfolio_value * abs(shock)
                results[scenario] = {'loss': loss, 'remaining': portfolio_value - loss}
            return results
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in run_test: {e}")
            raise

# UPGRADE 104: Correlation Stress Tester
class CorrelationStressTester:
    def stress_test(self, positions: Dict[str, float], correlations: Dict, stress_corr: float = 0.9) -> float:
        try:
            total_exposure = sum(abs(v) for v in positions.values())
            stressed_exposure = total_exposure * stress_corr
            return stressed_exposure
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in stress_test: {e}")
            raise

# UPGRADE 105: Liquidity Risk Manager
class LiquidityRiskManager:
    def __init__(self, max_position_pct: float = 0.1):
        try:
            self.max_pct = max_position_pct
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def check_liquidity(self, order_size: float, avg_volume: float) -> Dict[str, Any]:
        try:
            pct_of_volume = order_size / avg_volume if avg_volume > 0 else 1
            is_safe = pct_of_volume <= self.max_pct
            return {'safe': is_safe, 'pct_of_volume': pct_of_volume, 'recommended_size': avg_volume * self.max_pct}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in check_liquidity: {e}")
            raise

# UPGRADE 106: Concentration Risk Monitor
class ConcentrationRiskMonitor:
    def __init__(self, max_single: float = 0.2, max_sector: float = 0.4):
        try:
            self.max_single = max_single
            self.max_sector = max_sector
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def check(self, positions: Dict[str, float], sectors: Dict[str, str], total_equity: float) -> List[str]:
        try:
            violations = []
            for sym, size in positions.items():
                if abs(size) / total_equity > self.max_single:
                    violations.append(f"{sym}: {abs(size)/total_equity:.1%} > {self.max_single:.1%}")
            sector_exposure = {}
            for sym, size in positions.items():
                sector = sectors.get(sym, 'unknown')
                sector_exposure[sector] = sector_exposure.get(sector, 0) + abs(size)
            for sector, exp in sector_exposure.items():
                if exp / total_equity > self.max_sector:
                    violations.append(f"Sector {sector}: {exp/total_equity:.1%} > {self.max_sector:.1%}")
            return violations
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in check: {e}")
            raise

# UPGRADE 107: Tail Risk Monitor
class TailRiskMonitor:
    def __init__(self, threshold: float = 3.0):
        try:
            self.threshold = threshold
            self.returns: deque = deque(maxlen=252)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, ret: float) -> bool:
        try:
            self.returns.append(ret)
            if len(self.returns) < 20: return False
            std = np.std(self.returns)
            return abs(ret) > self.threshold * std
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise

# UPGRADE 108: Drawdown Ladder
class DrawdownLadder:
    def __init__(self):
        try:
            self.levels = [(0.05, 0.75), (0.10, 0.50), (0.15, 0.25), (0.20, 0)]
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def get_risk_multiplier(self, current_dd: float) -> float:
        try:
            for dd_level, multiplier in self.levels:
                if current_dd >= dd_level: return multiplier
            return 1.0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in get_risk_multiplier: {e}")
            raise

# UPGRADE 109: Daily Loss Limit
class DailyLossLimit:
    def __init__(self, limit_pct: float = 0.02):
        try:
            self.limit = limit_pct
            self.daily_pnl = 0
            self.last_reset = datetime.utcnow().date()
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, pnl: float) -> bool:
        try:
            if datetime.utcnow().date() != self.last_reset:
                self.daily_pnl = 0
                self.last_reset = datetime.utcnow().date()
            self.daily_pnl += pnl
            return self.daily_pnl <= -self.limit
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise
    
    def can_trade(self, equity: float) -> bool:
        return abs(self.daily_pnl) < equity * self.limit

# UPGRADE 110: Weekly Loss Limit
class WeeklyLossLimit:
    def __init__(self, limit_pct: float = 0.05):
        try:
            self.limit = limit_pct
            self.weekly_pnl = 0
            self.last_reset = datetime.utcnow().isocalendar()[1]
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, pnl: float, equity: float) -> bool:
        try:
            current_week = datetime.utcnow().isocalendar()[1]
            if current_week != self.last_reset:
                self.weekly_pnl = 0
                self.last_reset = current_week
            self.weekly_pnl += pnl
            return self.weekly_pnl <= -equity * self.limit
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise

# UPGRADE 111: Monthly Loss Limit
class MonthlyLossLimit:
    def __init__(self, limit_pct: float = 0.10):
        try:
            self.limit = limit_pct
            self.monthly_pnl = 0
            self.last_reset = datetime.utcnow().month
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, pnl: float, equity: float) -> bool:
        try:
            if datetime.utcnow().month != self.last_reset:
                self.monthly_pnl = 0
                self.last_reset = datetime.utcnow().month
            self.monthly_pnl += pnl
            return self.monthly_pnl <= -equity * self.limit
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise

# UPGRADE 112: Consecutive Loss Limiter
class ConsecutiveLossLimiter:
    def __init__(self, max_consecutive: int = 5):
        try:
            self.max = max_consecutive
            self.current = 0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, is_loss: bool) -> bool:
        try:
            if is_loss: self.current += 1
            else: self.current = 0
            return self.current >= self.max
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise
    
    def reset(self):
        try:
            self.current = 0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in reset: {e}")
            raise

# UPGRADE 113: Position Limit Manager
class PositionLimitManager:
    def __init__(self, max_positions: int = 10, max_per_symbol: float = 0.1):
        try:
            self.max_positions = max_positions
            self.max_per_symbol = max_per_symbol
            self.positions: Dict[str, float] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def can_open(self, symbol: str, size: float, equity: float) -> Tuple[bool, str]:
        try:
            if len(self.positions) >= self.max_positions and symbol not in self.positions:
                return False, "Max positions reached"
            if size / equity > self.max_per_symbol:
                return False, "Position too large"
            return True, "OK"
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in can_open: {e}")
            raise

# UPGRADE 114: Leverage Monitor
class LeverageMonitor:
    def __init__(self, max_leverage: float = 5.0):
        try:
            self.max_leverage = max_leverage
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate(self, total_exposure: float, equity: float) -> float:
        return total_exposure / equity if equity > 0 else 0
    
    def is_safe(self, total_exposure: float, equity: float) -> bool:
        return self.calculate(total_exposure, equity) <= self.max_leverage

# UPGRADE 115: Margin Call Detector
class MarginCallDetector:
    def __init__(self, warning_level: float = 150, call_level: float = 100):
        try:
            self.warning = warning_level
            self.call = call_level
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def check(self, margin_level: float) -> str:
        try:
            if margin_level <= self.call: return 'MARGIN_CALL'
            if margin_level <= self.warning: return 'WARNING'
            return 'OK'
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in check: {e}")
            raise

# UPGRADE 116: Risk Parity Calculator
class RiskParityCalculator:
    def calculate_weights(self, volatilities: Dict[str, float], target_risk: float = 0.1) -> Dict[str, float]:
        try:
            if not volatilities: return {}
            inv_vols = {s: 1/v for s, v in volatilities.items() if v > 0}
            total_inv = sum(inv_vols.values())
            return {s: iv / total_inv for s, iv in inv_vols.items()}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_weights: {e}")
            raise

# UPGRADE 117: Beta Calculator
class BetaCalculator:
    def calculate(self, asset_returns: List[float], market_returns: List[float]) -> float:
        try:
            if len(asset_returns) < 20 or len(market_returns) < 20: return 1.0
            min_len = min(len(asset_returns), len(market_returns))
            cov = np.cov(asset_returns[-min_len:], market_returns[-min_len:])[0, 1]
            var = np.var(market_returns[-min_len:])
            return cov / var if var > 0 else 1.0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 118: Portfolio Beta Manager
class PortfolioBetaManager:
    def __init__(self, target_beta: float = 1.0, tolerance: float = 0.2):
        try:
            self.target = target_beta
            self.tolerance = tolerance
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate_portfolio_beta(self, positions: Dict[str, float], betas: Dict[str, float], total: float) -> float:
        try:
            if total == 0: return 0
            return sum(size * betas.get(sym, 1.0) for sym, size in positions.items()) / total
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_portfolio_beta: {e}")
            raise
    
    def needs_rebalance(self, portfolio_beta: float) -> bool:
        return abs(portfolio_beta - self.target) > self.tolerance

# UPGRADE 119: Volatility Targeting
class VolatilityTargeting:
    def __init__(self, target_vol: float = 0.15):
        try:
            self.target = target_vol
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate_scalar(self, current_vol: float) -> float:
        try:
            if current_vol <= 0: return 1.0
            return min(2.0, max(0.25, self.target / current_vol))
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_scalar: {e}")
            raise

# UPGRADE 120: Dynamic Risk Budgeting
class DynamicRiskBudgeting:
    def __init__(self, base_budget: float = 0.02):
        try:
            self.base = base_budget
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def get_budget(self, win_rate: float, recent_pnl: float, volatility: float) -> float:
        try:
            confidence = min(1.5, max(0.5, win_rate * 2))
            momentum = 1.2 if recent_pnl > 0 else 0.8
            vol_adj = 1.0 / (1 + volatility * 5)
            return self.base * confidence * momentum * vol_adj
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in get_budget: {e}")
            raise

# UPGRADE 121: Risk-Adjusted Return Calculator
class RiskAdjustedReturnCalculator:
    def calculate(self, returns: List[float], risk_free: float = 0.02) -> Dict[str, float]:
        try:
            if len(returns) < 20: return {'sharpe': 0, 'sortino': 0, 'calmar': 0}
            ret_arr = np.array(returns)
            excess = ret_arr - risk_free / 252
            sharpe = np.mean(excess) / (np.std(excess) or 0.0001) * np.sqrt(252)
            downside = ret_arr[ret_arr < 0]
            sortino = np.mean(excess) / (np.std(downside) or 0.0001) * np.sqrt(252) if len(downside) > 0 else 0
            cumulative = np.cumprod(1 + ret_arr)
            max_dd = np.max(np.maximum.accumulate(cumulative) - cumulative) / np.max(cumulative)
            calmar = (np.mean(ret_arr) * 252) / max_dd if max_dd > 0 else 0
            return {'sharpe': sharpe, 'sortino': sortino, 'calmar': calmar}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 122: Correlation Matrix Manager
class CorrelationMatrixManager:
    def __init__(self, window: int = 60):
        try:
            self.window = window
            self.returns: Dict[str, deque] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def update(self, symbol: str, ret: float):
        try:
            if symbol not in self.returns: self.returns[symbol] = deque(maxlen=self.window)
            self.returns[symbol].append(ret)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in update: {e}")
            raise
        
    def get_matrix(self) -> Dict[Tuple[str, str], float]:
        try:
            matrix = {}
            symbols = list(self.returns.keys())
            for i, s1 in enumerate(symbols):
                for s2 in symbols[i+1:]:
                    if len(self.returns[s1]) >= 20 and len(self.returns[s2]) >= 20:
                        r1, r2 = list(self.returns[s1]), list(self.returns[s2])
                        min_len = min(len(r1), len(r2))
                        matrix[(s1, s2)] = np.corrcoef(r1[-min_len:], r2[-min_len:])[0, 1]
            return matrix
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in get_matrix: {e}")
            raise

# UPGRADE 123: Hedge Ratio Calculator
class HedgeRatioCalculator:
    def calculate(self, asset_returns: List[float], hedge_returns: List[float]) -> float:
        try:
            if len(asset_returns) < 20: return 0
            min_len = min(len(asset_returns), len(hedge_returns))
            cov = np.cov(asset_returns[-min_len:], hedge_returns[-min_len:])[0, 1]
            var = np.var(hedge_returns[-min_len:])
            return -cov / var if var > 0 else 0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 124: Delta Hedger
class DeltaHedger:
    def calculate_hedge(self, position_delta: float, hedge_delta: float) -> float:
        try:
            if hedge_delta == 0: return 0
            return -position_delta / hedge_delta
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_hedge: {e}")
            raise

# UPGRADE 125: Greeks Calculator
class GreeksCalculator:
    def calculate_delta(self, option_change: float, underlying_change: float) -> float:
        return option_change / underlying_change if underlying_change != 0 else 0
    
    def calculate_gamma(self, delta_change: float, underlying_change: float) -> float:
        return delta_change / underlying_change if underlying_change != 0 else 0
    
    def calculate_theta(self, option_change: float, time_change: float) -> float:
        return option_change / time_change if time_change != 0 else 0

# UPGRADE 126: Portfolio Greeks Aggregator
class PortfolioGreeksAggregator:
    def aggregate(self, positions: List[Dict]) -> Dict[str, float]:
        return {
            'delta': sum(p.get('delta', 0) * p.get('size', 0) for p in positions),
            'gamma': sum(p.get('gamma', 0) * p.get('size', 0) for p in positions),
            'theta': sum(p.get('theta', 0) * p.get('size', 0) for p in positions),
            'vega': sum(p.get('vega', 0) * p.get('size', 0) for p in positions)
        }

# UPGRADE 127: Scenario Analyzer
class ScenarioAnalyzer:
    def analyze(self, positions: Dict[str, float], scenarios: List[Dict[str, float]]) -> List[Dict]:
        try:
            results = []
            for scenario in scenarios:
                pnl = sum(size * scenario.get(sym, 0) for sym, size in positions.items())
                results.append({'scenario': scenario, 'pnl': pnl})
            return results
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise

# UPGRADE 128: Risk Attribution
class RiskAttribution:
    def attribute(self, portfolio_var: float, position_vars: Dict[str, float]) -> Dict[str, float]:
        try:
            total = sum(position_vars.values())
            if total == 0: return {}
            return {sym: var / total * portfolio_var for sym, var in position_vars.items()}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in attribute: {e}")
            raise

# UPGRADE 129: Factor Risk Decomposer
class FactorRiskDecomposer:
    def decompose(self, returns: List[float], factor_returns: Dict[str, List[float]]) -> Dict[str, float]:
        try:
            if len(returns) < 20: return {}
            exposures = {}
            for factor, f_returns in factor_returns.items():
                if len(f_returns) >= 20:
                    min_len = min(len(returns), len(f_returns))
                    cov = np.cov(returns[-min_len:], f_returns[-min_len:])[0, 1]
                    var = np.var(f_returns[-min_len:])
                    exposures[factor] = cov / var if var > 0 else 0
            return exposures
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in decompose: {e}")
            raise

# UPGRADE 130: Tracking Error Calculator
class TrackingErrorCalculator:
    def calculate(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        try:
            if len(portfolio_returns) < 20: return 0
            min_len = min(len(portfolio_returns), len(benchmark_returns))
            diff = np.array(portfolio_returns[-min_len:]) - np.array(benchmark_returns[-min_len:])
            return np.std(diff) * np.sqrt(252)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 131: Information Ratio Calculator
class InformationRatioCalculator:
    def calculate(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
        try:
            if len(portfolio_returns) < 20: return 0
            min_len = min(len(portfolio_returns), len(benchmark_returns))
            diff = np.array(portfolio_returns[-min_len:]) - np.array(benchmark_returns[-min_len:])
            return np.mean(diff) / (np.std(diff) or 0.0001) * np.sqrt(252)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 132: Treynor Ratio Calculator
class TreynorRatioCalculator:
    def calculate(self, portfolio_return: float, risk_free: float, beta: float) -> float:
        return (portfolio_return - risk_free) / beta if beta != 0 else 0

# UPGRADE 133: Jensen's Alpha Calculator
class JensensAlphaCalculator:
    def calculate(self, portfolio_return: float, risk_free: float, beta: float, market_return: float) -> float:
        try:
            expected = risk_free + beta * (market_return - risk_free)
            return portfolio_return - expected
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 134: Omega Ratio Calculator
class OmegaRatioCalculator:
    def calculate(self, returns: List[float], threshold: float = 0) -> float:
        try:
            if not returns: return 0
            gains = sum(r - threshold for r in returns if r > threshold)
            losses = sum(threshold - r for r in returns if r < threshold)
            return gains / losses if losses > 0 else float('inf')
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 135: Ulcer Index Calculator
class UlcerIndexCalculator:
    def calculate(self, prices: List[float]) -> float:
        try:
            if len(prices) < 2: return 0
            peak = prices[0]
            drawdowns = []
            for p in prices:
                if p > peak: peak = p
                dd = (peak - p) / peak * 100
                drawdowns.append(dd ** 2)
            return np.sqrt(np.mean(drawdowns))
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 136: Pain Index Calculator
class PainIndexCalculator:
    def calculate(self, prices: List[float]) -> float:
        try:
            if len(prices) < 2: return 0
            peak = prices[0]
            drawdowns = []
            for p in prices:
                if p > peak: peak = p
                drawdowns.append((peak - p) / peak)
            return np.mean(drawdowns)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 137: Gain-to-Pain Ratio
class GainToPainRatio:
    def calculate(self, returns: List[float]) -> float:
        try:
            if not returns: return 0
            total_return = sum(returns)
            pain = sum(abs(r) for r in returns if r < 0)
            return total_return / pain if pain > 0 else float('inf')
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 138: Risk-Adjusted Momentum
class RiskAdjustedMomentum:
    def calculate(self, returns: List[float], lookback: int = 20) -> float:
        try:
            if len(returns) < lookback: return 0
            recent = returns[-lookback:]
            return np.mean(recent) / (np.std(recent) or 0.0001)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 139: Downside Deviation Calculator
class DownsideDeviationCalculator:
    def calculate(self, returns: List[float], mar: float = 0) -> float:
        try:
            if not returns: return 0
            downside = [r for r in returns if r < mar]
            if not downside: return 0
            return np.sqrt(np.mean([(r - mar) ** 2 for r in downside]))
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 140: Upside Potential Ratio
class UpsidePotentialRatio:
    def calculate(self, returns: List[float], mar: float = 0) -> float:
        try:
            upside = [r - mar for r in returns if r > mar]
            downside_dev = np.sqrt(np.mean([(r - mar) ** 2 for r in returns if r < mar])) if any(r < mar for r in returns) else 0.0001
            return np.mean(upside) / downside_dev if upside else 0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 141: Capture Ratio Calculator
class CaptureRatioCalculator:
    def calculate(self, portfolio_returns: List[float], benchmark_returns: List[float]) -> Dict[str, float]:
        try:
            if len(portfolio_returns) < 20: return {'up': 0, 'down': 0}
            min_len = min(len(portfolio_returns), len(benchmark_returns))
            p_ret, b_ret = portfolio_returns[-min_len:], benchmark_returns[-min_len:]
            up_p = [p_ret[i] for i in range(min_len) if b_ret[i] > 0]
            up_b = [b_ret[i] for i in range(min_len) if b_ret[i] > 0]
            down_p = [p_ret[i] for i in range(min_len) if b_ret[i] < 0]
            down_b = [b_ret[i] for i in range(min_len) if b_ret[i] < 0]
            up_capture = np.mean(up_p) / np.mean(up_b) if up_b and np.mean(up_b) != 0 else 0
            down_capture = np.mean(down_p) / np.mean(down_b) if down_b and np.mean(down_b) != 0 else 0
            return {'up': up_capture, 'down': down_capture}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 142: Maximum Adverse Excursion
class MaximumAdverseExcursion:
    def calculate(self, trade_prices: List[float], entry: float, direction: str) -> float:
        try:
            if not trade_prices: return 0
            if direction == 'long':
                return max(0, entry - min(trade_prices))
            return max(0, max(trade_prices) - entry)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 143: Maximum Favorable Excursion
class MaximumFavorableExcursion:
    def calculate(self, trade_prices: List[float], entry: float, direction: str) -> float:
        try:
            if not trade_prices: return 0
            if direction == 'long':
                return max(0, max(trade_prices) - entry)
            return max(0, entry - min(trade_prices))
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 144: Trade Efficiency Ratio
class TradeEfficiencyRatio:
    def calculate(self, mfe: float, mae: float, actual_pnl: float) -> float:
        try:
            if mfe == 0: return 0
            return actual_pnl / mfe
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 145: Risk-Reward Realization
class RiskRewardRealization:
    def calculate(self, planned_rr: float, actual_rr: float) -> float:
        try:
            if planned_rr == 0: return 0
            return actual_rr / planned_rr
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 146: Exposure Manager
class ExposureManager:
    def __init__(self, max_gross: float = 2.0, max_net: float = 1.0):
        try:
            self.max_gross = max_gross
            self.max_net = max_net
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate(self, long_exposure: float, short_exposure: float, equity: float) -> Dict[str, float]:
        try:
            gross = (long_exposure + short_exposure) / equity if equity > 0 else 0
            net = (long_exposure - short_exposure) / equity if equity > 0 else 0
            return {'gross': gross, 'net': net, 'gross_ok': gross <= self.max_gross, 'net_ok': abs(net) <= self.max_net}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 147: Currency Exposure Manager
class CurrencyExposureManager:
    def __init__(self, max_per_currency: float = 0.3):
        try:
            self.max = max_per_currency
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate(self, positions: Dict[str, float], currencies: Dict[str, str], equity: float) -> Dict[str, float]:
        try:
            exposure = {}
            for sym, size in positions.items():
                ccy = currencies.get(sym, 'USD')
                exposure[ccy] = exposure.get(ccy, 0) + abs(size)
            return {ccy: exp / equity for ccy, exp in exposure.items()}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 148: Sector Exposure Manager
class SectorExposureManager:
    def __init__(self, max_per_sector: float = 0.25):
        try:
            self.max = max_per_sector
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate(self, positions: Dict[str, float], sectors: Dict[str, str], equity: float) -> Dict[str, float]:
        try:
            exposure = {}
            for sym, size in positions.items():
                sector = sectors.get(sym, 'Other')
                exposure[sector] = exposure.get(sector, 0) + abs(size)
            return {s: exp / equity for s, exp in exposure.items()}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 149: Geographic Exposure Manager
class GeographicExposureManager:
    def __init__(self, max_per_region: float = 0.4):
        try:
            self.max = max_per_region
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate(self, positions: Dict[str, float], regions: Dict[str, str], equity: float) -> Dict[str, float]:
        try:
            exposure = {}
            for sym, size in positions.items():
                region = regions.get(sym, 'Global')
                exposure[region] = exposure.get(region, 0) + abs(size)
            return {r: exp / equity for r, exp in exposure.items()}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate: {e}")
            raise

# UPGRADE 150: Risk Dashboard Generator
class RiskDashboardGenerator:
    def generate(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'summary': {
                'var_95': metrics.get('var', 0),
                'current_dd': metrics.get('drawdown', 0),
                'sharpe': metrics.get('sharpe', 0),
                'leverage': metrics.get('leverage', 0)
            },
            'alerts': self._generate_alerts(metrics),
            'status': 'OK' if not self._generate_alerts(metrics) else 'WARNING'
        }
    
    def _generate_alerts(self, metrics: Dict) -> List[str]:
        try:
            alerts = []
            if metrics.get('drawdown', 0) > 0.1: alerts.append('Drawdown > 10%')
            if metrics.get('leverage', 0) > 3: alerts.append('High leverage')
            if metrics.get('var', 0) > 0.05: alerts.append('High VaR')
            return alerts
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in _generate_alerts: {e}")
            raise
