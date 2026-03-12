"""
Risk Management Upgrades 151-200
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque

# UPGRADE 151: Risk Limit Enforcer
class RiskLimitEnforcer:
    def __init__(self):
        self.limits = {'max_position': 0.1, 'max_loss': 0.02, 'max_leverage': 5}
        
    def check(self, action: Dict, state: Dict) -> Tuple[bool, str]:
        if action.get('size', 0) / state.get('equity', 1) > self.limits['max_position']:
            return False, "Position size exceeds limit"
        if state.get('daily_loss', 0) > self.limits['max_loss']:
            return False, "Daily loss limit reached"
        return True, "OK"

# UPGRADE 152: Pre-Trade Risk Check
class PreTradeRiskCheck:
    def __init__(self):
        self.checks = []
        
    def add_check(self, check_func):
        self.checks.append(check_func)
        
    def run(self, order: Dict, state: Dict) -> Tuple[bool, List[str]]:
        failures = []
        for check in self.checks:
            try:
                if not check(order, state): failures.append(check.__name__)
            except Exception as e: failures.append(f"{check.__name__}: {e}")
        return len(failures) == 0, failures

# UPGRADE 153: Post-Trade Risk Check
class PostTradeRiskCheck:
    def check(self, portfolio: Dict, limits: Dict) -> List[str]:
        violations = []
        if portfolio.get('leverage', 0) > limits.get('max_leverage', 5):
            violations.append('Leverage exceeded')
        if portfolio.get('concentration', 0) > limits.get('max_concentration', 0.3):
            violations.append('Concentration exceeded')
        return violations

# UPGRADE 154: Real-Time Risk Monitor
class RealTimeRiskMonitor:
    def __init__(self):
        self.metrics: Dict[str, deque] = {}
        self.alerts: List[Dict] = []
        
    def update(self, metric: str, value: float, threshold: float):
        if metric not in self.metrics: self.metrics[metric] = deque(maxlen=100)
        self.metrics[metric].append({'value': value, 'time': datetime.utcnow()})
        if value > threshold:
            self.alerts.append({'metric': metric, 'value': value, 'threshold': threshold, 'time': datetime.utcnow()})

# UPGRADE 155: Risk Event Logger
class RiskEventLogger:
    def __init__(self):
        self.events: List[Dict] = []
        
    def log(self, event_type: str, severity: str, details: Dict):
        self.events.append({
            'type': event_type, 'severity': severity, 'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def get_recent(self, hours: int = 24) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [e for e in self.events if datetime.fromisoformat(e['timestamp']) > cutoff]

# UPGRADE 156: Risk Report Generator
class RiskReportGenerator:
    def generate(self, metrics: Dict, positions: Dict, history: List) -> Dict:
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {'total_risk': metrics.get('var', 0), 'positions': len(positions)},
            'metrics': metrics,
            'top_risks': sorted(positions.items(), key=lambda x: abs(x[1]), reverse=True)[:5],
            'recommendations': self._get_recommendations(metrics)
        }
    
    def _get_recommendations(self, metrics: Dict) -> List[str]:
        recs = []
        if metrics.get('leverage', 0) > 3: recs.append('Reduce leverage')
        if metrics.get('concentration', 0) > 0.2: recs.append('Diversify positions')
        return recs

# UPGRADE 157: Counterparty Risk Manager
class CounterpartyRiskManager:
    def __init__(self):
        self.exposures: Dict[str, float] = {}
        self.limits: Dict[str, float] = {}
        
    def set_limit(self, counterparty: str, limit: float):
        self.limits[counterparty] = limit
        
    def add_exposure(self, counterparty: str, amount: float) -> bool:
        current = self.exposures.get(counterparty, 0)
        limit = self.limits.get(counterparty, float('inf'))
        if current + amount > limit: return False
        self.exposures[counterparty] = current + amount
        return True

# UPGRADE 158: Settlement Risk Monitor
class SettlementRiskMonitor:
    def __init__(self):
        self.pending: Dict[str, Dict] = {}
        
    def add_pending(self, trade_id: str, amount: float, settlement_date: datetime):
        self.pending[trade_id] = {'amount': amount, 'date': settlement_date}
        
    def get_exposure(self, days: int = 3) -> float:
        cutoff = datetime.utcnow() + timedelta(days=days)
        return sum(t['amount'] for t in self.pending.values() if t['date'] <= cutoff)

# UPGRADE 159: Operational Risk Tracker
class OperationalRiskTracker:
    def __init__(self):
        self.incidents: List[Dict] = []
        
    def log_incident(self, category: str, description: str, impact: float):
        self.incidents.append({
            'category': category, 'description': description, 'impact': impact,
            'timestamp': datetime.utcnow()
        })
        
    def get_stats(self) -> Dict[str, Any]:
        if not self.incidents: return {'count': 0, 'total_impact': 0}
        return {
            'count': len(self.incidents),
            'total_impact': sum(i['impact'] for i in self.incidents),
            'by_category': self._group_by_category()
        }
    
    def _group_by_category(self) -> Dict[str, int]:
        cats = {}
        for i in self.incidents:
            cats[i['category']] = cats.get(i['category'], 0) + 1
        return cats

# UPGRADE 160: Model Risk Validator
class ModelRiskValidator:
    def validate(self, predictions: List[float], actuals: List[float]) -> Dict[str, float]:
        if len(predictions) < 10: return {'mse': 0, 'mae': 0, 'accuracy': 0}
        min_len = min(len(predictions), len(actuals))
        preds, acts = np.array(predictions[-min_len:]), np.array(actuals[-min_len:])
        return {
            'mse': np.mean((preds - acts) ** 2),
            'mae': np.mean(np.abs(preds - acts)),
            'correlation': np.corrcoef(preds, acts)[0, 1] if len(preds) > 1 else 0
        }

# UPGRADE 161: Liquidity Coverage Ratio
class LiquidityCoverageRatio:
    def calculate(self, liquid_assets: float, net_outflows_30d: float) -> float:
        return liquid_assets / net_outflows_30d if net_outflows_30d > 0 else float('inf')

# UPGRADE 162: Net Stable Funding Ratio
class NetStableFundingRatio:
    def calculate(self, stable_funding: float, required_funding: float) -> float:
        return stable_funding / required_funding if required_funding > 0 else float('inf')

# UPGRADE 163: Risk Capacity Calculator
class RiskCapacityCalculator:
    def calculate(self, equity: float, max_dd_tolerance: float, current_dd: float) -> float:
        remaining_capacity = max_dd_tolerance - current_dd
        return equity * remaining_capacity if remaining_capacity > 0 else 0

# UPGRADE 164: Risk Appetite Framework
class RiskAppetiteFramework:
    def __init__(self):
        self.appetite = {'conservative': 0.01, 'moderate': 0.02, 'aggressive': 0.03}
        self.current = 'moderate'
        
    def set_appetite(self, level: str):
        if level in self.appetite: self.current = level
        
    def get_risk_per_trade(self) -> float:
        return self.appetite[self.current]

# UPGRADE 165: Risk Tolerance Adjuster
class RiskToleranceAdjuster:
    def adjust(self, base_risk: float, win_streak: int, loss_streak: int, dd: float) -> float:
        multiplier = 1.0
        if win_streak >= 3: multiplier *= 1.1
        if loss_streak >= 2: multiplier *= 0.8
        if dd > 0.05: multiplier *= 0.7
        if dd > 0.1: multiplier *= 0.5
        return base_risk * multiplier

# UPGRADE 166: Adaptive Stop Loss
class AdaptiveStopLoss:
    def calculate(self, atr: float, volatility_regime: str, direction: str) -> float:
        multipliers = {'LOW': 2.0, 'NORMAL': 1.5, 'HIGH': 1.0, 'EXTREME': 0.75}
        return atr * multipliers.get(volatility_regime, 1.5)

# UPGRADE 167: Trailing Stop Manager
class TrailingStopManager:
    def __init__(self):
        self.stops: Dict[str, Dict] = {}
        
    def set_stop(self, pos_id: str, initial_stop: float, trail_distance: float, direction: str):
        self.stops[pos_id] = {'stop': initial_stop, 'trail': trail_distance, 'direction': direction, 'best': initial_stop}
        
    def update(self, pos_id: str, current_price: float) -> Optional[float]:
        if pos_id not in self.stops: return None
        s = self.stops[pos_id]
        if s['direction'] == 'long':
            if current_price > s['best']: s['best'] = current_price
            new_stop = s['best'] - s['trail']
            if new_stop > s['stop']: s['stop'] = new_stop
        else:
            if current_price < s['best']: s['best'] = current_price
            new_stop = s['best'] + s['trail']
            if new_stop < s['stop']: s['stop'] = new_stop
        return s['stop']

# UPGRADE 168: Chandelier Exit
class ChandelierExit:
    def calculate(self, highest_high: float, atr: float, multiplier: float = 3.0) -> float:
        return highest_high - (atr * multiplier)

# UPGRADE 169: Parabolic SAR Stop
class ParabolicSARStop:
    def __init__(self, af_start: float = 0.02, af_max: float = 0.2):
        self.af_start = af_start
        self.af_max = af_max
        
    def calculate(self, prices: List[float], direction: str) -> float:
        if len(prices) < 3: return prices[-1]
        af = self.af_start
        if direction == 'long':
            sar = min(prices[-3:])
            ep = max(prices)
        else:
            sar = max(prices[-3:])
            ep = min(prices)
        sar = sar + af * (ep - sar)
        return sar

# UPGRADE 170: Volatility Stop
class VolatilityStop:
    def calculate(self, price: float, atr: float, multiplier: float = 2.0, direction: str = 'long') -> float:
        if direction == 'long': return price - (atr * multiplier)
        return price + (atr * multiplier)

# UPGRADE 171: Time-Based Stop
class TimeBasedStop:
    def __init__(self, max_duration_mins: int = 60):
        self.max_duration = max_duration_mins
        self.entries: Dict[str, datetime] = {}
        
    def set_entry(self, pos_id: str):
        self.entries[pos_id] = datetime.utcnow()
        
    def should_exit(self, pos_id: str) -> bool:
        if pos_id not in self.entries: return False
        elapsed = (datetime.utcnow() - self.entries[pos_id]).total_seconds() / 60
        return elapsed >= self.max_duration

# UPGRADE 172: Profit Protection Stop
class ProfitProtectionStop:
    def __init__(self, trigger_profit: float = 0.02, lock_percent: float = 0.5):
        self.trigger = trigger_profit
        self.lock = lock_percent
        
    def calculate(self, entry: float, current: float, direction: str) -> Optional[float]:
        if direction == 'long':
            profit_pct = (current - entry) / entry
            if profit_pct >= self.trigger:
                return entry + (current - entry) * self.lock
        else:
            profit_pct = (entry - current) / entry
            if profit_pct >= self.trigger:
                return entry - (entry - current) * self.lock
        return None

# UPGRADE 173: Multi-Level Take Profit
class MultiLevelTakeProfit:
    def __init__(self, levels: List[Tuple[float, float]] = None):
        self.levels = levels or [(1.0, 0.33), (2.0, 0.33), (3.0, 0.34)]
        
    def get_targets(self, entry: float, stop: float, direction: str) -> List[Dict]:
        risk = abs(entry - stop)
        targets = []
        for rr, portion in self.levels:
            if direction == 'long': price = entry + risk * rr
            else: price = entry - risk * rr
            targets.append({'price': price, 'portion': portion, 'rr': rr})
        return targets

# UPGRADE 174: Dynamic Take Profit
class DynamicTakeProfit:
    def calculate(self, entry: float, atr: float, momentum: float, direction: str) -> float:
        base_target = atr * 2
        momentum_adj = 1 + abs(momentum) * 0.5
        target_distance = base_target * momentum_adj
        if direction == 'long': return entry + target_distance
        return entry - target_distance

# UPGRADE 175: Risk-Adjusted Position Sizer
class RiskAdjustedPositionSizer:
    def calculate(self, equity: float, risk_pct: float, entry: float, stop: float, win_rate: float) -> float:
        risk_amount = equity * risk_pct
        stop_distance = abs(entry - stop)
        if stop_distance == 0: return 0
        base_size = risk_amount / stop_distance
        confidence = min(1.5, max(0.5, win_rate * 2))
        return base_size * confidence

# UPGRADE 176: Volatility-Adjusted Position Sizer
class VolatilityAdjustedPositionSizer:
    def calculate(self, equity: float, risk_pct: float, atr: float, target_vol: float = 0.15) -> float:
        if atr == 0: return 0
        vol_scalar = target_vol / (atr * np.sqrt(252))
        return equity * risk_pct * min(2.0, max(0.25, vol_scalar))

# UPGRADE 177: Kelly Position Sizer
class KellyPositionSizer:
    def calculate(self, equity: float, win_rate: float, avg_win: float, avg_loss: float, fraction: float = 0.25) -> float:
        if avg_loss == 0: return 0
        win_loss_ratio = avg_win / abs(avg_loss)
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        kelly = max(0, min(0.25, kelly * fraction))
        return equity * kelly

# UPGRADE 178: Fixed Fractional Position Sizer
class FixedFractionalPositionSizer:
    def calculate(self, equity: float, fraction: float, entry: float, stop: float) -> float:
        risk_amount = equity * fraction
        stop_distance = abs(entry - stop)
        return risk_amount / stop_distance if stop_distance > 0 else 0

# UPGRADE 179: Optimal F Position Sizer
class OptimalFPositionSizer:
    def calculate(self, equity: float, largest_loss: float, optimal_f: float = 0.25) -> float:
        if largest_loss == 0: return equity * optimal_f
        return equity * optimal_f / abs(largest_loss)

# UPGRADE 180: Anti-Martingale Sizer
class AntiMartingaleSizer:
    def __init__(self, base_size: float = 0.01, increment: float = 0.005):
        self.base = base_size
        self.increment = increment
        self.consecutive_wins = 0
        
    def update(self, is_win: bool):
        if is_win: self.consecutive_wins += 1
        else: self.consecutive_wins = 0
        
    def get_size(self, equity: float) -> float:
        return equity * (self.base + self.increment * self.consecutive_wins)

# UPGRADE 181: Equity Curve Position Sizer
class EquityCurvePositionSizer:
    def __init__(self, lookback: int = 20):
        self.lookback = lookback
        self.equity_history: deque = deque(maxlen=lookback * 2)
        
    def update(self, equity: float):
        self.equity_history.append(equity)
        
    def get_multiplier(self) -> float:
        if len(self.equity_history) < self.lookback * 2: return 1.0
        recent = list(self.equity_history)[-self.lookback:]
        older = list(self.equity_history)[-self.lookback*2:-self.lookback]
        if np.mean(recent) > np.mean(older): return 1.2
        return 0.8

# UPGRADE 182: Correlation-Based Position Sizer
class CorrelationBasedPositionSizer:
    def calculate(self, base_size: float, correlation: float, existing_exposure: float) -> float:
        if abs(correlation) > 0.7:
            return base_size * (1 - abs(correlation)) * 0.5
        return base_size

# UPGRADE 183: Regime-Based Position Sizer
class RegimeBasedPositionSizer:
    def __init__(self):
        self.multipliers = {'TRENDING': 1.2, 'RANGING': 0.8, 'VOLATILE': 0.5, 'QUIET': 1.0}
        
    def calculate(self, base_size: float, regime: str) -> float:
        return base_size * self.multipliers.get(regime, 1.0)

# UPGRADE 184: Time-Decay Risk Adjuster
class TimeDecayRiskAdjuster:
    def adjust(self, base_risk: float, hours_in_trade: float, max_hours: float = 24) -> float:
        decay = max(0.5, 1 - (hours_in_trade / max_hours) * 0.5)
        return base_risk * decay

# UPGRADE 185: News-Based Risk Adjuster
class NewsBasedRiskAdjuster:
    def adjust(self, base_risk: float, news_impact: str, time_to_news_mins: int) -> float:
        if news_impact == 'high' and time_to_news_mins < 30:
            return base_risk * 0.25
        if news_impact == 'medium' and time_to_news_mins < 15:
            return base_risk * 0.5
        return base_risk

# UPGRADE 186: Session-Based Risk Adjuster
class SessionBasedRiskAdjuster:
    def __init__(self):
        self.multipliers = {'ASIAN': 0.8, 'LONDON': 1.0, 'NEW_YORK': 1.0, 'OVERLAP': 1.2}
        
    def adjust(self, base_risk: float, session: str) -> float:
        return base_risk * self.multipliers.get(session, 1.0)

# UPGRADE 187: Spread-Based Risk Adjuster
class SpreadBasedRiskAdjuster:
    def adjust(self, base_risk: float, current_spread: float, avg_spread: float) -> float:
        if avg_spread == 0: return base_risk
        spread_ratio = current_spread / avg_spread
        if spread_ratio > 2: return base_risk * 0.5
        if spread_ratio > 1.5: return base_risk * 0.75
        return base_risk

# UPGRADE 188: Liquidity-Based Risk Adjuster
class LiquidityBasedRiskAdjuster:
    def adjust(self, base_risk: float, current_volume: float, avg_volume: float) -> float:
        if avg_volume == 0: return base_risk
        liquidity_ratio = current_volume / avg_volume
        if liquidity_ratio < 0.5: return base_risk * 0.5
        if liquidity_ratio < 0.75: return base_risk * 0.75
        return base_risk

# UPGRADE 189: Momentum-Based Risk Adjuster
class MomentumBasedRiskAdjuster:
    def adjust(self, base_risk: float, momentum: float, direction: str) -> float:
        if (momentum > 0 and direction == 'long') or (momentum < 0 and direction == 'short'):
            return base_risk * 1.1
        return base_risk * 0.9

# UPGRADE 190: Trend Strength Risk Adjuster
class TrendStrengthRiskAdjuster:
    def adjust(self, base_risk: float, adx: float, direction_aligned: bool) -> float:
        if adx > 25 and direction_aligned: return base_risk * 1.2
        if adx < 20: return base_risk * 0.8
        return base_risk

# UPGRADE 191: Multi-Factor Risk Scorer
class MultiFactorRiskScorer:
    def score(self, factors: Dict[str, float], weights: Dict[str, float] = None) -> float:
        if weights is None:
            weights = {k: 1.0 / len(factors) for k in factors}
        total_weight = sum(weights.get(k, 0) for k in factors)
        if total_weight == 0: return 0
        return sum(factors[k] * weights.get(k, 0) for k in factors) / total_weight

# UPGRADE 192: Risk Decomposition Engine
class RiskDecompositionEngine:
    def decompose(self, total_risk: float, components: Dict[str, float]) -> Dict[str, float]:
        total_component = sum(components.values())
        if total_component == 0: return {}
        return {k: v / total_component * total_risk for k, v in components.items()}

# UPGRADE 193: Risk Aggregation Engine
class RiskAggregationEngine:
    def aggregate(self, risks: Dict[str, float], correlations: Dict[Tuple[str, str], float] = None) -> float:
        if not risks: return 0
        if correlations is None:
            return sum(risks.values())
        total = 0
        symbols = list(risks.keys())
        for i, s1 in enumerate(symbols):
            for j, s2 in enumerate(symbols):
                corr = correlations.get((s1, s2), 1 if s1 == s2 else 0)
                total += risks[s1] * risks[s2] * corr
        return np.sqrt(total)

# UPGRADE 194: Marginal Risk Calculator
class MarginalRiskCalculator:
    def calculate(self, current_var: float, new_position_var: float, correlation: float) -> float:
        combined = np.sqrt(current_var**2 + new_position_var**2 + 2*correlation*current_var*new_position_var)
        return combined - current_var

# UPGRADE 195: Incremental Risk Calculator
class IncrementalRiskCalculator:
    def calculate(self, portfolio_risk: float, position_risk: float, position_weight: float) -> float:
        return position_risk * position_weight / portfolio_risk if portfolio_risk > 0 else 0

# UPGRADE 196: Component Risk Calculator
class ComponentRiskCalculator:
    def calculate(self, position_risks: Dict[str, float], weights: Dict[str, float], correlations: Dict) -> Dict[str, float]:
        total_risk = sum(position_risks.values())
        if total_risk == 0: return {}
        return {s: r * weights.get(s, 0) / total_risk for s, r in position_risks.items()}

# UPGRADE 197: Risk Budget Optimizer
class RiskBudgetOptimizer:
    def optimize(self, target_risk: float, position_vols: Dict[str, float], max_weight: float = 0.2) -> Dict[str, float]:
        if not position_vols: return {}
        inv_vols = {s: 1/v for s, v in position_vols.items() if v > 0}
        total = sum(inv_vols.values())
        weights = {s: min(max_weight, iv / total) for s, iv in inv_vols.items()}
        return weights

# UPGRADE 198: Risk Parity Optimizer
class RiskParityOptimizer:
    def optimize(self, volatilities: Dict[str, float], target_vol: float = 0.1) -> Dict[str, float]:
        if not volatilities: return {}
        inv_vols = {s: 1/v for s, v in volatilities.items() if v > 0}
        total = sum(inv_vols.values())
        return {s: iv / total for s, iv in inv_vols.items()}

# UPGRADE 199: Mean-Variance Optimizer
class MeanVarianceOptimizer:
    def optimize(self, returns: Dict[str, float], volatilities: Dict[str, float], risk_aversion: float = 1.0) -> Dict[str, float]:
        if not returns: return {}
        scores = {}
        for s in returns:
            if s in volatilities and volatilities[s] > 0:
                scores[s] = returns[s] - risk_aversion * volatilities[s]**2
        total = sum(max(0, s) for s in scores.values())
        if total == 0: return {s: 1/len(scores) for s in scores}
        return {s: max(0, sc) / total for s, sc in scores.items()}

# UPGRADE 200: Black-Litterman Optimizer
class BlackLittermanOptimizer:
    def optimize(self, market_weights: Dict[str, float], views: Dict[str, float], confidence: float = 0.5) -> Dict[str, float]:
        if not market_weights: return {}
        adjusted = {}
        for s, w in market_weights.items():
            view = views.get(s, 0)
            adjusted[s] = w * (1 - confidence) + view * confidence
        total = sum(max(0, v) for v in adjusted.values())
        if total == 0: return market_weights
        return {s: max(0, v) / total for s, v in adjusted.items()}
