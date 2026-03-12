"""
Quantum Portfolio Optimization
==============================

Advanced portfolio optimization using quantum-inspired algorithms.
Implements QAOA-style optimization for portfolio allocation.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import pandas as pd
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class OptimizationObjective(Enum):
    """Portfolio optimization objectives"""
    MAX_SHARPE = "max_sharpe"
    MIN_VARIANCE = "min_variance"
    MAX_RETURN = "max_return"
    RISK_PARITY = "risk_parity"
    MIN_CVAR = "min_cvar"
    MAX_DIVERSIFICATION = "max_diversification"


@dataclass
class PortfolioAllocation:
    """Portfolio allocation result"""
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    diversification_ratio: float
    max_drawdown_estimate: float
    optimization_method: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'weights': self.weights,
            'expected_return': self.expected_return,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'diversification_ratio': self.diversification_ratio,
            'max_drawdown_estimate': self.max_drawdown_estimate,
            'optimization_method': self.optimization_method,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class RiskMetrics:
    """Portfolio risk metrics"""
    volatility: float
    var_95: float
    cvar_95: float
    max_drawdown: float
    beta: float
    correlation_avg: float


class QuantumPortfolio:
    """
    Quantum-Inspired Portfolio Optimization
    
    Uses quantum-inspired algorithms (simulated annealing, QAOA-style)
    for portfolio optimization with multiple objectives.
    
    Features:
    - Multiple optimization objectives
    - Constraint handling (min/max weights, sector limits)
    - Risk parity allocation
    - CVaR optimization
    - Diversification maximization
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize QuantumPortfolio optimizer.
        
        Args:
            config: Configuration dictionary with:
                - risk_free_rate: Risk-free rate (default: 0.02)
                - min_weight: Minimum asset weight (default: 0.0)
                - max_weight: Maximum asset weight (default: 1.0)
                - target_volatility: Target portfolio volatility
                - num_iterations: Optimization iterations (default: 1000)
        """
        self.config = config or {}
        self.risk_free_rate = self.config.get('risk_free_rate', 0.02)
        self.min_weight = self.config.get('min_weight', 0.0)
        self.max_weight = self.config.get('max_weight', 1.0)
        self.target_volatility = self.config.get('target_volatility', None)
        self.num_iterations = self.config.get('num_iterations', 1000)
        
        self.initialized = True
        self._returns_cache: Dict[str, pd.Series] = {}
        self._cov_matrix: Optional[pd.DataFrame] = None
        
        logger.info("QuantumPortfolio optimizer initialized")
        
    def optimize(
        self,
        returns: pd.DataFrame,
        objective: OptimizationObjective = OptimizationObjective.MAX_SHARPE,
        constraints: Optional[Dict] = None
    ) -> PortfolioAllocation:
        """
        Optimize portfolio allocation.
        
        Args:
            returns: DataFrame of asset returns (columns = assets)
            objective: Optimization objective
            constraints: Additional constraints
            
        Returns:
            PortfolioAllocation with optimal weights
        """
        assets = returns.columns.tolist()
        n_assets = len(assets)
        
        # Calculate statistics
        mean_returns = returns.mean() * 252  # Annualized
        cov_matrix = returns.cov() * 252  # Annualized
        self._cov_matrix = cov_matrix
        
        # Initial weights (equal weight)
        init_weights = np.array([1.0 / n_assets] * n_assets)
        
        # Bounds
        bounds = tuple((self.min_weight, self.max_weight) for _ in range(n_assets))
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}  # Weights sum to 1
        ]
        
        # Add custom constraints
        if constraints:
            if 'sector_limits' in constraints:
                for sector, (assets_in_sector, limit) in constraints['sector_limits'].items():
                    indices = [assets.index(a) for a in assets_in_sector if a in assets]
                    constraints_list.append({
                        'type': 'ineq',
                        'fun': lambda w, idx=indices, lim=limit: lim - np.sum(w[idx])
                    })
        
        # Select objective function
        if objective == OptimizationObjective.MAX_SHARPE:
            result = self._optimize_sharpe(mean_returns, cov_matrix, init_weights, bounds, constraints_list)
        elif objective == OptimizationObjective.MIN_VARIANCE:
            result = self._optimize_min_variance(cov_matrix, init_weights, bounds, constraints_list)
        elif objective == OptimizationObjective.MAX_RETURN:
            result = self._optimize_max_return(mean_returns, init_weights, bounds, constraints_list)
        elif objective == OptimizationObjective.RISK_PARITY:
            result = self._optimize_risk_parity(cov_matrix, init_weights, bounds)
        elif objective == OptimizationObjective.MIN_CVAR:
            result = self._optimize_min_cvar(returns, init_weights, bounds, constraints_list)
        elif objective == OptimizationObjective.MAX_DIVERSIFICATION:
            result = self._optimize_diversification(cov_matrix, init_weights, bounds, constraints_list)
        else:
            result = self._optimize_sharpe(mean_returns, cov_matrix, init_weights, bounds, constraints_list)
        
        # Calculate portfolio metrics
        weights = result.x
        port_return = np.dot(weights, mean_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
        
        # Diversification ratio
        asset_vols = np.sqrt(np.diag(cov_matrix))
        weighted_vols = np.dot(weights, asset_vols)
        div_ratio = weighted_vols / port_vol if port_vol > 0 else 1
        
        # Max drawdown estimate (using volatility)
        max_dd_estimate = port_vol * 2.5  # Rough estimate
        
        return PortfolioAllocation(
            weights=dict(zip(assets, weights.tolist())),
            expected_return=float(port_return),
            volatility=float(port_vol),
            sharpe_ratio=float(sharpe),
            diversification_ratio=float(div_ratio),
            max_drawdown_estimate=float(max_dd_estimate),
            optimization_method=objective.value
        )
    
    def _optimize_sharpe(self, mean_returns, cov_matrix, init_weights, bounds, constraints):
        """Maximize Sharpe ratio"""
        def neg_sharpe(weights):
            port_return = np.dot(weights, mean_returns)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -(port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
        
        return minimize(neg_sharpe, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)
    
    def _optimize_min_variance(self, cov_matrix, init_weights, bounds, constraints):
        """Minimize portfolio variance"""
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))
        
        return minimize(portfolio_variance, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)
    
    def _optimize_max_return(self, mean_returns, init_weights, bounds, constraints):
        """Maximize expected return"""
        def neg_return(weights):
            return -np.dot(weights, mean_returns)
        
        return minimize(neg_return, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)
    
    def _optimize_risk_parity(self, cov_matrix, init_weights, bounds):
        """Risk parity allocation (equal risk contribution)"""
        n = len(init_weights)
        target_risk = 1.0 / n
        
        def risk_parity_objective(weights):
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            marginal_contrib = np.dot(cov_matrix, weights)
            risk_contrib = weights * marginal_contrib / port_vol
            risk_contrib_pct = risk_contrib / port_vol
            return np.sum((risk_contrib_pct - target_risk) ** 2)
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
        return minimize(risk_parity_objective, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)
    
    def _optimize_min_cvar(self, returns, init_weights, bounds, constraints, alpha=0.05):
        """Minimize Conditional Value at Risk (CVaR)"""
        def cvar_objective(weights):
            port_returns = returns.dot(weights)
            var = np.percentile(port_returns, alpha * 100)
            cvar = port_returns[port_returns <= var].mean()
            return -cvar  # Minimize negative CVaR
        
        return minimize(cvar_objective, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)
    
    def _optimize_diversification(self, cov_matrix, init_weights, bounds, constraints):
        """Maximize diversification ratio"""
        asset_vols = np.sqrt(np.diag(cov_matrix))
        
        def neg_diversification(weights):
            weighted_vols = np.dot(weights, asset_vols)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -weighted_vols / port_vol if port_vol > 0 else 0
        
        return minimize(neg_diversification, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)
    
    def quantum_annealing_optimize(
        self,
        returns: pd.DataFrame,
        objective: OptimizationObjective = OptimizationObjective.MAX_SHARPE,
        temperature: float = 1.0,
        cooling_rate: float = 0.995
    ) -> PortfolioAllocation:
        """
        Quantum-inspired simulated annealing optimization.
        
        Args:
            returns: DataFrame of asset returns
            objective: Optimization objective
            temperature: Initial temperature
            cooling_rate: Temperature cooling rate
            
        Returns:
            PortfolioAllocation
        """
        assets = returns.columns.tolist()
        n_assets = len(assets)
        
        mean_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252
        
        # Initialize random weights
        weights = np.random.dirichlet(np.ones(n_assets))
        best_weights = weights.copy()
        
        def evaluate(w):
            port_return = np.dot(w, mean_returns)
            port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
            if objective == OptimizationObjective.MAX_SHARPE:
                return (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
            elif objective == OptimizationObjective.MIN_VARIANCE:
                return -port_vol
            elif objective == OptimizationObjective.MAX_RETURN:
                return port_return
            return (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
        
        best_score = evaluate(weights)
        current_score = best_score
        
        for _ in range(self.num_iterations):
            # Generate neighbor (quantum tunneling simulation)
            perturbation = np.random.randn(n_assets) * temperature * 0.1
            new_weights = weights + perturbation
            new_weights = np.clip(new_weights, self.min_weight, self.max_weight)
            new_weights = new_weights / np.sum(new_weights)  # Normalize
            
            new_score = evaluate(new_weights)
            
            # Accept or reject
            delta = new_score - current_score
            if delta > 0 or np.random.random() < np.exp(delta / temperature):
                weights = new_weights
                current_score = new_score
                
                if current_score > best_score:
                    best_score = current_score
                    best_weights = weights.copy()
            
            # Cool down
            temperature *= cooling_rate
        
        # Calculate final metrics
        port_return = np.dot(best_weights, mean_returns)
        port_vol = np.sqrt(np.dot(best_weights.T, np.dot(cov_matrix, best_weights)))
        sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
        
        asset_vols = np.sqrt(np.diag(cov_matrix))
        div_ratio = np.dot(best_weights, asset_vols) / port_vol if port_vol > 0 else 1
        
        return PortfolioAllocation(
            weights=dict(zip(assets, best_weights.tolist())),
            expected_return=float(port_return),
            volatility=float(port_vol),
            sharpe_ratio=float(sharpe),
            diversification_ratio=float(div_ratio),
            max_drawdown_estimate=float(port_vol * 2.5),
            optimization_method=f"quantum_annealing_{objective.value}"
        )
    
    def efficient_frontier(
        self,
        returns: pd.DataFrame,
        n_points: int = 50
    ) -> List[PortfolioAllocation]:
        """
        Generate efficient frontier portfolios.
        
        Args:
            returns: DataFrame of asset returns
            n_points: Number of points on frontier
            
        Returns:
            List of PortfolioAllocation on efficient frontier
        """
        mean_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252
        
        # Get min and max return portfolios
        min_var = self.optimize(returns, OptimizationObjective.MIN_VARIANCE)
        max_ret = self.optimize(returns, OptimizationObjective.MAX_RETURN)
        
        target_returns = np.linspace(min_var.expected_return, max_ret.expected_return, n_points)
        
        frontier = []
        assets = returns.columns.tolist()
        n_assets = len(assets)
        
        for target in target_returns:
            init_weights = np.array([1.0 / n_assets] * n_assets)
            bounds = tuple((self.min_weight, self.max_weight) for _ in range(n_assets))
            
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
                {'type': 'eq', 'fun': lambda w, t=target: np.dot(w, mean_returns) - t}
            ]
            
            def portfolio_variance(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))

            try:
                result = minimize(portfolio_variance, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)

                if result.success:
                    weights = result.x
                    port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                    sharpe = (target - self.risk_free_rate) / port_vol if port_vol > 0 else 0

                    asset_vols = np.sqrt(np.diag(cov_matrix))
                    div_ratio = np.dot(weights, asset_vols) / port_vol if port_vol > 0 else 1

                    frontier.append(PortfolioAllocation(
                        weights=dict(zip(assets, weights.tolist())),
                        expected_return=float(target),
                        volatility=float(port_vol),
                        sharpe_ratio=float(sharpe),
                        diversification_ratio=float(div_ratio),
                        max_drawdown_estimate=float(port_vol * 2.5),
                        optimization_method="efficient_frontier"
                    ))
            except Exception:
                continue

        return frontier
    
    def get_status(self) -> Dict:
        """Get optimizer status"""
        return {
            'initialized': self.initialized,
            'risk_free_rate': self.risk_free_rate,
            'min_weight': self.min_weight,
            'max_weight': self.max_weight,
            'num_iterations': self.num_iterations,
            'timestamp': datetime.now().isoformat()
        }


def create_quantum_portfolio(config: Optional[Dict] = None) -> QuantumPortfolio:
    """Factory function to create QuantumPortfolio instance"""
    return QuantumPortfolio(config)


if __name__ == "__main__":
    # Demo
    np.random.seed(42)
    
    # Generate sample returns
    n_days = 252
    assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
    returns = pd.DataFrame(
        np.random.randn(n_days, len(assets)) * 0.02 + 0.0005,
        columns=assets
    )
    
    optimizer = create_quantum_portfolio()
    
    print("=== Quantum Portfolio Optimization Demo ===\n")
    
    # Max Sharpe
    print("1. Maximum Sharpe Ratio:")
    result = optimizer.optimize(returns, OptimizationObjective.MAX_SHARPE)
    print(f"   Expected Return: {result.expected_return:.2%}")
    print(f"   Volatility: {result.volatility:.2%}")
    print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"   Weights: {', '.join(f'{k}: {v:.1%}' for k, v in result.weights.items())}")
    
    # Risk Parity
    print("\n2. Risk Parity:")
    result = optimizer.optimize(returns, OptimizationObjective.RISK_PARITY)
    print(f"   Expected Return: {result.expected_return:.2%}")
    print(f"   Volatility: {result.volatility:.2%}")
    print(f"   Weights: {', '.join(f'{k}: {v:.1%}' for k, v in result.weights.items())}")
    
    # Quantum Annealing
    print("\n3. Quantum Annealing:")
    result = optimizer.quantum_annealing_optimize(returns)
    print(f"   Expected Return: {result.expected_return:.2%}")
    print(f"   Volatility: {result.volatility:.2%}")
    print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
    
    # Efficient Frontier
    print("\n4. Efficient Frontier (5 points):")
    frontier = optimizer.efficient_frontier(returns, n_points=5)
    for i, p in enumerate(frontier):
        print(f"   Point {i+1}: Return={p.expected_return:.2%}, Vol={p.volatility:.2%}, Sharpe={p.sharpe_ratio:.2f}")
