"""
from typing import List, Optional, Set, Tuple
Institutional Portfolio Construction
====================================
Advanced portfolio construction with:
- Factor-based portfolio construction
- Risk budgeting and parity
- Transaction cost optimization
- Rebalancing algorithms
- Constraint management
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    from scipy.optimize import minimize, LinearConstraint
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class FactorType(Enum):
    """Risk factor types"""
    MARKET = "market"
    SIZE = "size"
    VALUE = "value"
    MOMENTUM = "momentum"
    QUALITY = "quality"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    GROWTH = "growth"
    DIVIDEND = "dividend"
    BETA = "beta"
    CURRENCY = "currency"
    INTEREST_RATE = "interest_rate"
    CREDIT = "credit"
    COMMODITY = "commodity"
    SECTOR = "sector"


class RebalanceMethod(Enum):
    """Rebalancing methods"""
    CALENDAR = "calendar"  # Fixed schedule
    THRESHOLD = "threshold"  # Drift-based
    OPTIMAL = "optimal"  # Cost-optimized
    HYBRID = "hybrid"  # Combination


@dataclass
class FactorExposure:
    """Factor exposure for a position or portfolio"""
    factor: FactorType
    exposure: float  # Beta to factor
    contribution: float  # Contribution to portfolio risk
    target: float  # Target exposure
    limit: float  # Maximum allowed
    
    @property
    def deviation(self) -> float:
        return self.exposure - self.target
    
    @property
    def within_limit(self) -> bool:
        return abs(self.exposure) <= self.limit


@dataclass
class RiskBudget:
    """Risk budget allocation"""
    strategy_id: str
    risk_budget_pct: float  # % of total risk budget
    current_risk_contribution: float
    marginal_risk: float
    risk_adjusted_return: float
    
    @property
    def utilization(self) -> float:
        if self.risk_budget_pct == 0:
            return 0
        return self.current_risk_contribution / self.risk_budget_pct


@dataclass
class TradingCost:
    """Trading cost model"""
    symbol: str
    spread_cost: float  # Bid-ask spread
    market_impact: float  # Price impact
    commission: float  # Broker commission
    slippage: float  # Execution slippage
    
    @property
    def total_cost(self) -> float:
        return self.spread_cost + self.market_impact + self.commission + self.slippage
    
    @classmethod
    def estimate(
        cls,
        symbol: str,
        trade_size: float,
        avg_volume: float,
        spread: float,
        volatility: float
    ) -> 'TradingCost':
        """Estimate trading costs"""
        # Spread cost
        spread_cost = spread / 2
        
        # Market impact (square root model)
        participation_rate = trade_size / avg_volume if avg_volume > 0 else 0.1
        market_impact = volatility * np.sqrt(participation_rate) if NUMPY_AVAILABLE else volatility * (participation_rate ** 0.5)
        
        # Commission (assume 1bp)
        commission = 0.0001
        
        # Slippage (assume 2bp)
        slippage = 0.0002
        
        return cls(
            symbol=symbol,
            spread_cost=spread_cost,
            market_impact=market_impact,
            commission=commission,
            slippage=slippage
        )


class FactorModel:
    """
    Multi-Factor Risk Model
    Decomposes portfolio risk into factor exposures
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Factor definitions
        self.factors = list(FactorType)
        
        # Factor covariance matrix (would be estimated from data)
        self.factor_covariance: Optional[np.ndarray] = None
        
        # Asset factor loadings
        self.factor_loadings: Dict[str, Dict[FactorType, float]] = {}
        
        # Specific risk (idiosyncratic)
        self.specific_risk: Dict[str, float] = {}
        
        logger.info("Factor Model initialized")
    
    def set_factor_loadings(
        self,
        symbol: str,
        loadings: Dict[FactorType, float]
    ):
        """Set factor loadings for an asset"""
        self.factor_loadings[symbol] = loadings
    
    def estimate_factor_covariance(
        self,
        factor_returns: pd.DataFrame
    ) -> np.ndarray:
        """Estimate factor covariance matrix"""
        if not NUMPY_AVAILABLE:
            return None
        
        self.factor_covariance = factor_returns.cov().values * 252  # Annualize
        return self.factor_covariance
    
    def calculate_portfolio_risk(
        self,
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate portfolio risk decomposition"""
        if not NUMPY_AVAILABLE:
            return {'total_risk': 0, 'factor_risk': 0, 'specific_risk': 0}
        
        symbols = list(weights.keys())
        w = np.array([weights[s] for s in symbols])
        
        # Get factor loadings matrix
        n_factors = len(self.factors)
        B = np.zeros((len(symbols), n_factors))
        
        for i, symbol in enumerate(symbols):
            if symbol in self.factor_loadings:
                for j, factor in enumerate(self.factors):
                    B[i, j] = self.factor_loadings[symbol].get(factor, 0)
        
        # Factor covariance (use identity if not set)
        if self.factor_covariance is None:
            F = np.eye(n_factors) * 0.04  # 20% vol per factor
        else:
            F = self.factor_covariance
        
        # Specific risk diagonal
        D = np.diag([self.specific_risk.get(s, 0.3) ** 2 for s in symbols])
        
        # Portfolio variance = w' * (B * F * B' + D) * w
        factor_cov = B @ F @ B.T
        total_cov = factor_cov + D
        
        portfolio_variance = w @ total_cov @ w
        factor_variance = w @ factor_cov @ w
        specific_variance = w @ D @ w
        
        return {
            'total_risk': np.sqrt(portfolio_variance),
            'factor_risk': np.sqrt(factor_variance),
            'specific_risk': np.sqrt(specific_variance),
            'factor_contribution': factor_variance / portfolio_variance if portfolio_variance > 0 else 0,
            'specific_contribution': specific_variance / portfolio_variance if portfolio_variance > 0 else 0
        }
    
    def get_factor_exposures(
        self,
        weights: Dict[str, float]
    ) -> Dict[FactorType, float]:
        """Calculate portfolio factor exposures"""
        exposures = {f: 0.0 for f in self.factors}
        
        for symbol, weight in weights.items():
            if symbol in self.factor_loadings:
                for factor, loading in self.factor_loadings[symbol].items():
                    exposures[factor] += weight * loading
        
        return exposures
    
    def calculate_marginal_risk(
        self,
        weights: Dict[str, float],
        symbol: str
    ) -> float:
        """Calculate marginal contribution to risk"""
        if not NUMPY_AVAILABLE:
            return 0.0
        
        # Small perturbation
        delta = 0.01
        
        # Current risk
        current_risk = self.calculate_portfolio_risk(weights)['total_risk']
        
        # Perturbed weights
        perturbed = weights.copy()
        perturbed[symbol] = perturbed.get(symbol, 0) + delta
        
        # Normalize
        total = sum(perturbed.values())
        perturbed = {k: v / total for k, v in perturbed.items()}
        
        # New risk
        new_risk = self.calculate_portfolio_risk(perturbed)['total_risk']
        
        return (new_risk - current_risk) / delta


class RebalanceEngine:
    """
    Portfolio Rebalancing Engine
    Handles rebalancing with cost optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Rebalancing parameters
        self.method = RebalanceMethod(config.get('method', 'threshold'))
        self.threshold = config.get('threshold', 0.05)  # 5% drift
        self.min_trade_size = config.get('min_trade_size', 1000)
        self.max_turnover = config.get('max_turnover', 0.25)  # 25% per rebalance
        
        # Cost parameters
        self.cost_aversion = config.get('cost_aversion', 1.0)
        
        # History
        self.rebalance_history: List[Dict[str, Any]] = []
        
        logger.info(f"Rebalance Engine initialized: {self.method.value}")
    
    def check_rebalance_needed(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> Tuple[bool, Dict[str, float]]:
        """Check if rebalancing is needed"""
        drifts = {}
        max_drift = 0
        
        all_symbols = set(current_weights.keys()) | set(target_weights.keys())
        
        for symbol in all_symbols:
            current = current_weights.get(symbol, 0)
            target = target_weights.get(symbol, 0)
            drift = current - target
            drifts[symbol] = drift
            max_drift = max(max_drift, abs(drift))
        
        needs_rebalance = max_drift > self.threshold
        
        return needs_rebalance, drifts
    
    def calculate_trades(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float,
        prices: Dict[str, float],
        costs: Optional[Dict[str, TradingCost]] = None
    ) -> List[Dict[str, Any]]:
        """Calculate optimal rebalancing trades"""
        trades = []
        
        all_symbols = set(current_weights.keys()) | set(target_weights.keys())
        
        for symbol in all_symbols:
            current = current_weights.get(symbol, 0)
            target = target_weights.get(symbol, 0)
            
            weight_change = target - current
            value_change = weight_change * portfolio_value
            
            # Skip small trades
            if abs(value_change) < self.min_trade_size:
                continue
            
            price = prices.get(symbol, 1)
            quantity = value_change / price if price > 0 else 0
            
            # Estimate cost
            cost = costs.get(symbol, TradingCost(symbol, 0.001, 0.001, 0.0001, 0.0002)) if costs else None
            estimated_cost = cost.total_cost * abs(value_change) if cost else 0
            
            trades.append({
                'symbol': symbol,
                'side': 'buy' if weight_change > 0 else 'sell',
                'quantity': abs(quantity),
                'value': abs(value_change),
                'weight_change': weight_change,
                'estimated_cost': estimated_cost,
                'price': price
            })
        
        # Sort by value (largest first)
        trades.sort(key=lambda x: x['value'], reverse=True)
        
        # Apply turnover constraint
        total_turnover = sum(t['value'] for t in trades) / portfolio_value
        if total_turnover > self.max_turnover:
            # Scale down trades
            scale = self.max_turnover / total_turnover
            for trade in trades:
                trade['quantity'] *= scale
                trade['value'] *= scale
                trade['weight_change'] *= scale
        
        return trades
    
    def optimize_execution(
        self,
        trades: List[Dict[str, Any]],
        urgency: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Optimize trade execution schedule"""
        optimized = []
        
        for trade in trades:
            # Determine execution algorithm based on size and urgency
            if trade['value'] > 1_000_000:  # Large trade
                algo = 'VWAP' if urgency < 0.7 else 'IS'
                duration = '4h' if urgency < 0.5 else '1h'
            elif trade['value'] > 100_000:  # Medium trade
                algo = 'TWAP' if urgency < 0.7 else 'Aggressive'
                duration = '1h' if urgency < 0.5 else '15m'
            else:  # Small trade
                algo = 'Market'
                duration = 'immediate'
            
            optimized.append({
                **trade,
                'algorithm': algo,
                'duration': duration,
                'urgency': urgency
            })
        
        return optimized
    
    def record_rebalance(
        self,
        trades: List[Dict[str, Any]],
        reason: str
    ):
        """Record rebalancing event"""
        self.rebalance_history.append({
            'timestamp': datetime.now(),
            'reason': reason,
            'num_trades': len(trades),
            'total_value': sum(t['value'] for t in trades),
            'total_cost': sum(t.get('estimated_cost', 0) for t in trades),
            'trades': trades
        })


class InstitutionalPortfolioConstructor:
    """
    Institutional-Grade Portfolio Constructor
    Combines factor model, risk budgeting, and rebalancing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Components
        self.factor_model = FactorModel(config.get('factor_model', {}))
        self.rebalance_engine = RebalanceEngine(config.get('rebalance', {}))
        
        # Portfolio constraints
        self.constraints = {
            'max_position': config.get('max_position', 0.10),  # 10%
            'min_position': config.get('min_position', 0.001),  # 0.1%
            'max_sector': config.get('max_sector', 0.25),  # 25%
            'max_factor_exposure': config.get('max_factor_exposure', 0.5),
            'min_holdings': config.get('min_holdings', 20),
            'max_holdings': config.get('max_holdings', 100),
            'max_turnover': config.get('max_turnover', 0.25)
        }
        
        # Risk targets
        self.risk_targets = {
            'target_volatility': config.get('target_volatility', 0.10),  # 10%
            'max_drawdown': config.get('max_drawdown', 0.15),  # 15%
            'tracking_error': config.get('tracking_error', 0.05)  # 5%
        }
        
        # Current portfolio
        self.current_weights: Dict[str, float] = {}
        self.target_weights: Dict[str, float] = {}
        
        # Risk budgets
        self.risk_budgets: Dict[str, RiskBudget] = {}
        
        logger.info("Institutional Portfolio Constructor initialized")
    
    def construct_portfolio(
        self,
        signals: Dict[str, float],
        expected_returns: Dict[str, float],
        covariance: Optional[np.ndarray] = None,
        method: str = 'risk_parity'
    ) -> Dict[str, float]:
        """Construct optimal portfolio"""
        if not NUMPY_AVAILABLE:
            # Simple equal weight fallback
            n = len(signals)
            return {s: 1/n for s in signals}
        
        symbols = list(signals.keys())
        n = len(symbols)
        
        if method == 'risk_parity':
            weights = self._risk_parity_weights(symbols, covariance)
        elif method == 'mean_variance':
            weights = self._mean_variance_weights(symbols, expected_returns, covariance)
        elif method == 'signal_weighted':
            weights = self._signal_weighted(signals)
        elif method == 'equal_weight':
            weights = {s: 1/n for s in symbols}
        else:
            weights = {s: 1/n for s in symbols}
        
        # Apply constraints
        weights = self._apply_constraints(weights)
        
        self.target_weights = weights
        return weights
    
    def _risk_parity_weights(
        self,
        symbols: List[str],
        covariance: Optional[np.ndarray]
    ) -> Dict[str, float]:
        """Calculate risk parity weights"""
        n = len(symbols)
        
        if covariance is None:
            # Use equal weights if no covariance
            return {s: 1/n for s in symbols}
        
        # Risk parity: equal risk contribution
        def risk_budget_objective(w):
            w = np.array(w)
            port_vol = np.sqrt(w @ covariance @ w)
            marginal_risk = covariance @ w / port_vol
            risk_contrib = w * marginal_risk
            target_risk = port_vol / n
            return np.sum((risk_contrib - target_risk) ** 2)
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Sum to 1
        ]
        bounds = [(0.001, self.constraints['max_position']) for _ in range(n)]
        
        # Initial guess
        x0 = np.ones(n) / n
        
        # Optimize
        result = minimize(
            risk_budget_objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            return {symbols[i]: result.x[i] for i in range(n)}
        else:
            return {s: 1/n for s in symbols}
    
    def _mean_variance_weights(
        self,
        symbols: List[str],
        expected_returns: Dict[str, float],
        covariance: Optional[np.ndarray]
    ) -> Dict[str, float]:
        """Calculate mean-variance optimal weights"""
        n = len(symbols)
        
        if covariance is None:
            return {s: 1/n for s in symbols}
        
        mu = np.array([expected_returns.get(s, 0) for s in symbols])
        
        # Maximize Sharpe ratio
        def neg_sharpe(w):
            w = np.array(w)
            ret = w @ mu
            vol = np.sqrt(w @ covariance @ w)
            return -ret / vol if vol > 0 else 0
        
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
        ]
        bounds = [(0, self.constraints['max_position']) for _ in range(n)]
        
        x0 = np.ones(n) / n
        
        result = minimize(
            neg_sharpe,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            return {symbols[i]: max(0, result.x[i]) for i in range(n)}
        else:
            return {s: 1/n for s in symbols}
    
    def _signal_weighted(
        self,
        signals: Dict[str, float]
    ) -> Dict[str, float]:
        """Weight by signal strength"""
        # Normalize positive signals
        positive_signals = {s: max(0, v) for s, v in signals.items()}
        total = sum(positive_signals.values())
        
        if total == 0:
            n = len(signals)
            return {s: 1/n for s in signals}
        
        return {s: v / total for s, v in positive_signals.items()}
    
    def _apply_constraints(
        self,
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Apply portfolio constraints"""
        constrained = {}
        
        for symbol, weight in weights.items():
            # Position limits
            weight = max(self.constraints['min_position'], weight)
            weight = min(self.constraints['max_position'], weight)
            constrained[symbol] = weight
        
        # Renormalize
        total = sum(constrained.values())
        if total > 0:
            constrained = {s: w / total for s, w in constrained.items()}
        
        # Holdings count
        if len(constrained) > self.constraints['max_holdings']:
            # Keep top N by weight
            sorted_weights = sorted(constrained.items(), key=lambda x: x[1], reverse=True)
            constrained = dict(sorted_weights[:self.constraints['max_holdings']])
            # Renormalize
            total = sum(constrained.values())
            constrained = {s: w / total for s, w in constrained.items()}
        
        return constrained
    
    def set_risk_budget(
        self,
        strategy_id: str,
        budget_pct: float
    ):
        """Set risk budget for a strategy"""
        self.risk_budgets[strategy_id] = RiskBudget(
            strategy_id=strategy_id,
            risk_budget_pct=budget_pct,
            current_risk_contribution=0,
            marginal_risk=0,
            risk_adjusted_return=0
        )
    
    def check_risk_budgets(
        self,
        strategy_risks: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """Check risk budget utilization"""
        results = {}
        
        total_risk = sum(strategy_risks.values())
        
        for strategy_id, budget in self.risk_budgets.items():
            current_risk = strategy_risks.get(strategy_id, 0)
            contribution = current_risk / total_risk if total_risk > 0 else 0
            
            budget.current_risk_contribution = contribution
            
            results[strategy_id] = {
                'budget': budget.risk_budget_pct,
                'current': contribution,
                'utilization': budget.utilization,
                'over_budget': contribution > budget.risk_budget_pct * 1.1  # 10% buffer
            }
        
        return results
    
    def generate_rebalance_trades(
        self,
        portfolio_value: float,
        prices: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate rebalancing trades"""
        needs_rebalance, drifts = self.rebalance_engine.check_rebalance_needed(
            self.current_weights,
            self.target_weights
        )
        
        if not needs_rebalance:
            return []
        
        trades = self.rebalance_engine.calculate_trades(
            self.current_weights,
            self.target_weights,
            portfolio_value,
            prices
        )
        
        # Optimize execution
        optimized_trades = self.rebalance_engine.optimize_execution(trades)
        
        return optimized_trades
    
    def update_weights(
        self,
        new_weights: Dict[str, float]
    ):
        """Update current weights after execution"""
        self.current_weights = new_weights.copy()
    
    def get_portfolio_analytics(self) -> Dict[str, Any]:
        """Get portfolio analytics"""
        risk_decomp = self.factor_model.calculate_portfolio_risk(self.current_weights)
        factor_exposures = self.factor_model.get_factor_exposures(self.current_weights)
        
        return {
            'num_holdings': len(self.current_weights),
            'concentration': max(self.current_weights.values()) if self.current_weights else 0,
            'herfindahl': sum(w**2 for w in self.current_weights.values()),
            'effective_n': 1 / sum(w**2 for w in self.current_weights.values()) if self.current_weights else 0,
            'risk_decomposition': risk_decomp,
            'factor_exposures': {f.value: e for f, e in factor_exposures.items()},
            'target_weights': self.target_weights,
            'current_weights': self.current_weights
        }
