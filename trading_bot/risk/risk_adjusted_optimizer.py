"""
Risk-Adjusted Return Optimization System
Institutional-Grade Performance Optimization

This module provides comprehensive risk-adjusted optimization:
- Omega Ratio optimization
- Sortino Ratio optimization
- Calmar Ratio optimization
- Information Ratio optimization
- Risk parity with tail risk
- CVaR-constrained optimization
- Drawdown-constrained optimization
- Multi-objective optimization

Portfolio Manager + Actuary + Risk Manager Perspective
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from scipy.optimize import minimize, differential_evolution
try:
    from scipy import stats
except ImportError:
    scipy = None
import warnings
import numpy
import pandas

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class RiskMetric(Enum):
    """Risk-adjusted performance metrics"""
    SHARPE = "SHARPE"  # (Return - Rf) / Volatility
    SORTINO = "SORTINO"  # (Return - Rf) / Downside Deviation
    CALMAR = "CALMAR"  # Return / Max Drawdown
    OMEGA = "OMEGA"  # Probability weighted gains / losses
    INFORMATION = "INFORMATION"  # Alpha / Tracking Error
    TREYNOR = "TREYNOR"  # (Return - Rf) / Beta
    STERLING = "STERLING"  # Return / Avg Drawdown
    BURKE = "BURKE"  # Return / sqrt(sum of squared drawdowns)


class OptimizationObjective(Enum):
    """Optimization objectives"""
    MAX_SHARPE = "MAX_SHARPE"
    MAX_SORTINO = "MAX_SORTINO"
    MAX_CALMAR = "MAX_CALMAR"
    MAX_OMEGA = "MAX_OMEGA"
    MIN_CVAR = "MIN_CVAR"
    MIN_MAX_DRAWDOWN = "MIN_MAX_DRAWDOWN"
    RISK_PARITY = "RISK_PARITY"
    MULTI_OBJECTIVE = "MULTI_OBJECTIVE"


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    # Return metrics
    total_return: float
    annualized_return: float
    
    # Volatility metrics
    volatility: float
    downside_deviation: float
    upside_deviation: float
    
    # Drawdown metrics
    max_drawdown: float
    avg_drawdown: float
    drawdown_duration: int  # Days
    
    # Tail risk metrics
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    
    # Risk-adjusted metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float
    information_ratio: float
    treynor_ratio: float
    sterling_ratio: float
    burke_ratio: float
    
    # Higher moments
    skewness: float
    kurtosis: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'annualized_return': round(self.annualized_return, 4),
            'volatility': round(self.volatility, 4),
            'max_drawdown': round(self.max_drawdown, 4),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'sortino_ratio': round(self.sortino_ratio, 2),
            'calmar_ratio': round(self.calmar_ratio, 2),
            'omega_ratio': round(self.omega_ratio, 2),
            'var_95': round(self.var_95, 4),
            'cvar_95': round(self.cvar_95, 4),
            'skewness': round(self.skewness, 2),
            'kurtosis': round(self.kurtosis, 2)
        }


@dataclass
class OptimizationResult:
    """Optimization result"""
    objective: OptimizationObjective
    weights: Dict[str, float]
    metrics: RiskMetrics
    
    # Optimization details
    success: bool
    iterations: int
    message: str
    
    # Constraints satisfied
    constraints_satisfied: Dict[str, bool]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'objective': self.objective.value,
            'weights': {k: round(v, 4) for k, v in self.weights.items()},
            'metrics': self.metrics.to_dict(),
            'success': self.success,
            'iterations': self.iterations,
            'message': self.message,
            'constraints_satisfied': self.constraints_satisfied
        }


@dataclass
class OptimizationConstraints:
    """Optimization constraints"""
    min_weight: float = 0.0
    max_weight: float = 1.0
    max_volatility: Optional[float] = None
    max_drawdown: Optional[float] = None
    max_cvar: Optional[float] = None
    min_return: Optional[float] = None
    max_tracking_error: Optional[float] = None
    sector_limits: Optional[Dict[str, Tuple[float, float]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'min_weight': self.min_weight,
            'max_weight': self.max_weight,
            'max_volatility': self.max_volatility,
            'max_drawdown': self.max_drawdown,
            'max_cvar': self.max_cvar,
            'min_return': self.min_return
        }


class RiskAdjustedOptimizer:
    """
    Risk-Adjusted Return Optimization System
    
    Provides institutional-grade portfolio optimization:
    
    1. Risk-Adjusted Metrics
       - Sharpe Ratio: Risk-adjusted return
       - Sortino Ratio: Downside risk-adjusted
       - Calmar Ratio: Drawdown-adjusted
       - Omega Ratio: Probability-weighted
       - Information Ratio: Active return / tracking error
    
    2. Optimization Objectives
       - Maximize Sharpe/Sortino/Calmar/Omega
       - Minimize CVaR/Max Drawdown
       - Risk Parity with tail risk
       - Multi-objective Pareto optimization
    
    3. Constraints
       - Position limits
       - Volatility constraints
       - Drawdown constraints
       - CVaR constraints
       - Sector limits
    
    4. Advanced Features
       - Non-normal return distributions
       - Fat-tail handling
       - Regime-conditional optimization
       - Robust optimization
    
    Key Principles:
    - Optimize for risk-adjusted returns, not raw returns
    - Account for tail risk (CVaR, not just VaR)
    - Consider drawdown constraints
    - Use multiple metrics for robustness
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize optimizer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        self.risk_free_rate = self.config.get('risk_free_rate', 0.04)
        self.threshold_return = self.config.get('threshold_return', 0.0)  # For Omega
        self.max_iterations = self.config.get('max_iterations', 1000)
        
        # Statistics
        self.optimizations_run = 0
        
        logger.info("RiskAdjustedOptimizer initialized")
    
    def calculate_risk_metrics(self,
                              returns: np.ndarray,
                              benchmark_returns: Optional[np.ndarray] = None) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics
        
        Args:
            returns: Array of returns
            benchmark_returns: Optional benchmark returns
            
        Returns:
            RiskMetrics object
        """
        # Basic return metrics
        total_return = np.prod(1 + returns) - 1
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1 if len(returns) > 0 else 0
        
        # Volatility metrics
        volatility = np.std(returns) * np.sqrt(252)
        
        downside_returns = returns[returns < self.threshold_return]
        downside_deviation = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else volatility
        
        upside_returns = returns[returns > self.threshold_return]
        upside_deviation = np.std(upside_returns) * np.sqrt(252) if len(upside_returns) > 0 else volatility
        
        # Drawdown metrics
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        max_drawdown = abs(drawdown.min())
        avg_drawdown = abs(drawdown[drawdown < 0].mean()) if len(drawdown[drawdown < 0]) > 0 else 0
        
        # Drawdown duration
        in_drawdown = drawdown < 0
        if in_drawdown.any():
            drawdown_periods = np.diff(np.where(np.concatenate(([in_drawdown[0]], in_drawdown[:-1] != in_drawdown[1:], [True])))[0])[:2]
            drawdown_duration = int(drawdown_periods.max()) if len(drawdown_periods) > 0 else 0
        else:
            drawdown_duration = 0
        
        # Tail risk metrics
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        cvar_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95
        cvar_99 = returns[returns <= var_99].mean() if len(returns[returns <= var_99]) > 0 else var_99
        
        # Risk-adjusted metrics
        sharpe = (annualized_return - self.risk_free_rate) / volatility if volatility > 0 else 0
        sortino = (annualized_return - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
        calmar = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        # Omega ratio
        gains = returns[returns > self.threshold_return] - self.threshold_return
        losses = self.threshold_return - returns[returns <= self.threshold_return]
        omega = gains.sum() / losses.sum() if losses.sum() > 0 else float('inf')
        
        # Information ratio (vs benchmark)
        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            active_returns = returns - benchmark_returns
            tracking_error = np.std(active_returns) * np.sqrt(252)
            information = np.mean(active_returns) * 252 / tracking_error if tracking_error > 0 else 0
        else:
            information = 0
        
        # Treynor ratio (vs market)
        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            covariance = np.cov(returns, benchmark_returns)[0, 1]
            variance = np.var(benchmark_returns)
            beta = covariance / variance if variance > 0 else 1
            treynor = (annualized_return - self.risk_free_rate) / beta if beta != 0 else 0
        else:
            treynor = 0
        
        # Sterling ratio
        sterling = annualized_return / avg_drawdown if avg_drawdown > 0 else 0
        
        # Burke ratio
        squared_drawdowns = drawdown[drawdown < 0] ** 2
        burke = annualized_return / np.sqrt(squared_drawdowns.sum()) if squared_drawdowns.sum() > 0 else 0
        
        # Higher moments
        skewness = float(stats.skew(returns))
        kurtosis = float(stats.kurtosis(returns))
        
        return RiskMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            downside_deviation=downside_deviation,
            upside_deviation=upside_deviation,
            max_drawdown=max_drawdown,
            avg_drawdown=avg_drawdown,
            drawdown_duration=drawdown_duration,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            omega_ratio=omega,
            information_ratio=information,
            treynor_ratio=treynor,
            sterling_ratio=sterling,
            burke_ratio=burke,
            skewness=skewness,
            kurtosis=kurtosis
        )
    
    def optimize(self,
                returns: pd.DataFrame,
                objective: OptimizationObjective = OptimizationObjective.MAX_SHARPE,
                constraints: Optional[OptimizationConstraints] = None,
                benchmark_returns: Optional[np.ndarray] = None) -> OptimizationResult:
        """
        Optimize portfolio for risk-adjusted returns
        
        Args:
            returns: DataFrame of asset returns
            objective: Optimization objective
            constraints: Optimization constraints
            benchmark_returns: Optional benchmark returns
            
        Returns:
            OptimizationResult with optimal weights
        """
        self.optimizations_run += 1
        
        constraints = constraints or OptimizationConstraints()
        assets = returns.columns.tolist()
        n_assets = len(assets)
        
        # Initial weights
        x0 = np.array([1.0 / n_assets] * n_assets)
        
        # Bounds
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
        
        # Constraint: weights sum to 1
        constraint_list = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        
        # Add additional constraints
        if constraints.max_volatility is not None:
            constraint_list.append({
                'type': 'ineq',
                'fun': lambda x: constraints.max_volatility - self._portfolio_volatility(x, returns)
            })
        
        if constraints.max_cvar is not None:
            constraint_list.append({
                'type': 'ineq',
                'fun': lambda x: -constraints.max_cvar - self._portfolio_cvar(x, returns)
            })
        
        if constraints.min_return is not None:
            constraint_list.append({
                'type': 'ineq',
                'fun': lambda x: self._portfolio_return(x, returns) - constraints.min_return
            })
        
        # Select objective function
        if objective == OptimizationObjective.MAX_SHARPE:
            objective_func = lambda x: -self._sharpe_ratio(x, returns)
        elif objective == OptimizationObjective.MAX_SORTINO:
            objective_func = lambda x: -self._sortino_ratio(x, returns)
        elif objective == OptimizationObjective.MAX_CALMAR:
            objective_func = lambda x: -self._calmar_ratio(x, returns)
        elif objective == OptimizationObjective.MAX_OMEGA:
            objective_func = lambda x: -self._omega_ratio(x, returns)
        elif objective == OptimizationObjective.MIN_CVAR:
            objective_func = lambda x: -self._portfolio_cvar(x, returns)
        elif objective == OptimizationObjective.MIN_MAX_DRAWDOWN:
            objective_func = lambda x: self._max_drawdown(x, returns)
        elif objective == OptimizationObjective.RISK_PARITY:
            objective_func = lambda x: self._risk_parity_objective(x, returns)
        else:
            pass
        try:
            objective_func = lambda x: -self._sharpe_ratio(x, returns)
        
            # Optimize
            result = minimize(
                objective_func,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraint_list,
                options={'maxiter': self.max_iterations}
            )
            
            weights = result.x
            success = result.success
            iterations = result.nit
            message = result.message
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            weights = x0
            success = False
            iterations = 0
            message = str(e)
        
        # Calculate portfolio returns and metrics
        portfolio_returns = np.dot(returns.values, weights)
        metrics = self.calculate_risk_metrics(portfolio_returns, benchmark_returns)
        
        # Check constraints
        constraints_satisfied = self._check_constraints(weights, returns, constraints)
        
        return OptimizationResult(
            objective=objective,
            weights={asset: w for asset, w in zip(assets, weights)},
            metrics=metrics,
            success=success,
            iterations=iterations,
            message=message,
            constraints_satisfied=constraints_satisfied
        )
    
    def multi_objective_optimize(self,
                                returns: pd.DataFrame,
                                objectives: List[OptimizationObjective],
                                weights_objectives: Optional[List[float]] = None,
                                constraints: Optional[OptimizationConstraints] = None) -> OptimizationResult:
        """
        Multi-objective optimization
        
        Args:
            returns: DataFrame of asset returns
            objectives: List of objectives to optimize
            weights_objectives: Weights for each objective
            constraints: Optimization constraints
            
        Returns:
            OptimizationResult with Pareto-optimal weights
        """
        if weights_objectives is None:
            weights_objectives = [1.0 / len(objectives)] * len(objectives)
        
        constraints = constraints or OptimizationConstraints()
        assets = returns.columns.tolist()
        n_assets = len(assets)
        
        # Combined objective function
        def combined_objective(x):
            total = 0
            for obj, weight in zip(objectives, weights_objectives):
                if obj == OptimizationObjective.MAX_SHARPE:
                    total -= weight * self._sharpe_ratio(x, returns)
                elif obj == OptimizationObjective.MAX_SORTINO:
                    total -= weight * self._sortino_ratio(x, returns)
                elif obj == OptimizationObjective.MAX_CALMAR:
                    total -= weight * self._calmar_ratio(x, returns)
                elif obj == OptimizationObjective.MIN_CVAR:
                    total += weight * (-self._portfolio_cvar(x, returns))
                elif obj == OptimizationObjective.MIN_MAX_DRAWDOWN:
                    total += weight * self._max_drawdown(x, returns)
            return total
        
        # Bounds and constraints
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
        constraint_list = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        
        try:
            result = minimize(
                combined_objective,
                np.array([1.0 / n_assets] * n_assets),
                method='SLSQP',
                bounds=bounds,
                constraints=constraint_list,
                options={'maxiter': self.max_iterations}
            )
            
            weights = result.x
            success = result.success
            iterations = result.nit
            message = result.message
            
        except Exception as e:
            weights = np.array([1.0 / n_assets] * n_assets)
            success = False
            iterations = 0
            message = str(e)
        
        portfolio_returns = np.dot(returns.values, weights)
        metrics = self.calculate_risk_metrics(portfolio_returns)
        
        return OptimizationResult(
            objective=OptimizationObjective.MULTI_OBJECTIVE,
            weights={asset: w for asset, w in zip(assets, weights)},
            metrics=metrics,
            success=success,
            iterations=iterations,
            message=message,
            constraints_satisfied=self._check_constraints(weights, returns, constraints)
        )
    
    def efficient_frontier_risk_adjusted(self,
                                        returns: pd.DataFrame,
                                        metric: RiskMetric = RiskMetric.SHARPE,
                                        n_portfolios: int = 50) -> List[OptimizationResult]:
        """
        Generate efficient frontier for risk-adjusted metric
        
        Args:
            returns: DataFrame of asset returns
            metric: Risk metric to optimize
            n_portfolios: Number of portfolios
            
        Returns:
            List of OptimizationResult on frontier
        """
        # Map metric to objective
        metric_to_objective = {
            RiskMetric.SHARPE: OptimizationObjective.MAX_SHARPE,
            RiskMetric.SORTINO: OptimizationObjective.MAX_SORTINO,
            RiskMetric.CALMAR: OptimizationObjective.MAX_CALMAR,
            RiskMetric.OMEGA: OptimizationObjective.MAX_OMEGA
        }
        
        objective = metric_to_objective.get(metric, OptimizationObjective.MAX_SHARPE)
        
        # Generate range of volatility targets
        min_vol = 0.05
        max_vol = 0.40
        vol_targets = np.linspace(min_vol, max_vol, n_portfolios)
        
        frontier = []
        
        for vol_target in vol_targets:
            constraints = OptimizationConstraints(
                min_weight=0.0,
                max_weight=0.5,
                max_volatility=vol_target
            )
            
            result = self.optimize(returns, objective, constraints)
            
            if result.success:
                frontier.append(result)
        
        return frontier
    
    def _sharpe_ratio(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Calculate Sharpe ratio for weights"""
        portfolio_returns = np.dot(returns.values, weights)
        ann_return = np.mean(portfolio_returns) * 252
        volatility = np.std(portfolio_returns) * np.sqrt(252)
        return (ann_return - self.risk_free_rate) / volatility if volatility > 0 else 0
    
    def _sortino_ratio(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Calculate Sortino ratio for weights"""
        portfolio_returns = np.dot(returns.values, weights)
        ann_return = np.mean(portfolio_returns) * 252
        
        downside = portfolio_returns[portfolio_returns < 0]
        downside_std = np.std(downside) * np.sqrt(252) if len(downside) > 0 else np.std(portfolio_returns) * np.sqrt(252)
        
        return (ann_return - self.risk_free_rate) / downside_std if downside_std > 0 else 0
    
    def _calmar_ratio(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Calculate Calmar ratio for weights"""
        portfolio_returns = np.dot(returns.values, weights)
        ann_return = np.mean(portfolio_returns) * 252
        max_dd = self._max_drawdown(weights, returns)
        return ann_return / max_dd if max_dd > 0 else 0
    
    def _omega_ratio(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Calculate Omega ratio for weights"""
        portfolio_returns = np.dot(returns.values, weights)
        
        gains = portfolio_returns[portfolio_returns > self.threshold_return] - self.threshold_return
        losses = self.threshold_return - portfolio_returns[portfolio_returns <= self.threshold_return]
        
        return gains.sum() / losses.sum() if losses.sum() > 0 else float('inf')
    
    def _portfolio_volatility(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Calculate portfolio volatility"""
        portfolio_returns = np.dot(returns.values, weights)
        return np.std(portfolio_returns) * np.sqrt(252)
    
    def _portfolio_return(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Calculate portfolio return"""
        portfolio_returns = np.dot(returns.values, weights)
        return np.mean(portfolio_returns) * 252
    
    def _portfolio_cvar(self, weights: np.ndarray, returns: pd.DataFrame, alpha: float = 0.05) -> float:
        """Calculate portfolio CVaR"""
        portfolio_returns = np.dot(returns.values, weights)
        var = np.percentile(portfolio_returns, alpha * 100)
        cvar = portfolio_returns[portfolio_returns <= var].mean()
        return cvar if not np.isnan(cvar) else var
    
    def _max_drawdown(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Calculate maximum drawdown"""
        portfolio_returns = np.dot(returns.values, weights)
        cumulative = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min())
    
    def _risk_parity_objective(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Risk parity objective function"""
        cov_matrix = returns.cov().values * 252
        
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        marginal_contrib = np.dot(cov_matrix, weights)
        risk_contrib = weights * marginal_contrib / portfolio_vol
        
        target_risk = portfolio_vol / len(weights)
        
        return np.sum((risk_contrib - target_risk) ** 2)
    
    def _check_constraints(self,
                          weights: np.ndarray,
                          returns: pd.DataFrame,
                          constraints: OptimizationConstraints) -> Dict[str, bool]:
        """Check if constraints are satisfied"""
        satisfied = {}
        
        satisfied['weights_sum_to_1'] = abs(np.sum(weights) - 1) < 0.001
        satisfied['min_weight'] = all(w >= constraints.min_weight - 0.001 for w in weights)
        satisfied['max_weight'] = all(w <= constraints.max_weight + 0.001 for w in weights)
        
        if constraints.max_volatility is not None:
            vol = self._portfolio_volatility(weights, returns)
            satisfied['max_volatility'] = vol <= constraints.max_volatility + 0.001
        
        if constraints.max_cvar is not None:
            cvar = self._portfolio_cvar(weights, returns)
            satisfied['max_cvar'] = cvar >= constraints.max_cvar - 0.001
        
        if constraints.min_return is not None:
            ret = self._portfolio_return(weights, returns)
            satisfied['min_return'] = ret >= constraints.min_return - 0.001
        
        return satisfied
    
    def compare_metrics(self, returns: pd.DataFrame) -> Dict[str, OptimizationResult]:
        """
        Compare optimization results across different metrics
        
        Args:
            returns: DataFrame of asset returns
            
        Returns:
            Dictionary of {metric: OptimizationResult}
        """
        results = {}
        
        for objective in [
            OptimizationObjective.MAX_SHARPE,
            OptimizationObjective.MAX_SORTINO,
            OptimizationObjective.MAX_CALMAR,
            OptimizationObjective.MAX_OMEGA,
            OptimizationObjective.MIN_CVAR,
            OptimizationObjective.MIN_MAX_DRAWDOWN,
            OptimizationObjective.RISK_PARITY
        ]:
            try:
                result = self.optimize(returns, objective)
                results[objective.value] = result
            except Exception as e:
                logger.warning(f"Optimization failed for {objective.value}: {e}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        return {
            'optimizations_run': self.optimizations_run,
            'risk_free_rate': self.risk_free_rate,
            'threshold_return': self.threshold_return
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create optimizer
    optimizer = RiskAdjustedOptimizer({
        'risk_free_rate': 0.04,
        'threshold_return': 0.0
    })
    
    # Generate sample returns
    np.random.seed(42)
    n_assets = 5
    n_days = 756  # 3 years
    
    # Simulate correlated returns
    mean_returns = np.array([0.10, 0.12, 0.08, 0.15, 0.07]) / 252
    volatilities = np.array([0.15, 0.20, 0.12, 0.25, 0.10]) / np.sqrt(252)
    
    corr = np.array([
        [1.0, 0.6, 0.3, 0.4, 0.2],
        [0.6, 1.0, 0.4, 0.5, 0.3],
        [0.3, 0.4, 1.0, 0.3, 0.5],
        [0.4, 0.5, 0.3, 1.0, 0.2],
        [0.2, 0.3, 0.5, 0.2, 1.0]
    ])
    
    L = np.linalg.cholesky(corr)
    returns_raw = np.random.randn(n_days, n_assets)
    returns_corr = np.dot(returns_raw, L.T)
    returns_scaled = returns_corr * volatilities + mean_returns
    
    # Add some fat tails
    returns_scaled += np.random.standard_t(5, size=(n_days, n_assets)) * 0.005
    
    returns_df = pd.DataFrame(
        returns_scaled,
        columns=['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'JNJ']
    )
    
    # Calculate risk metrics for equal weight portfolio
    logger.info("\n=== Equal Weight Portfolio Metrics ===")
    equal_returns = returns_df.mean(axis=1).values
    metrics = optimizer.calculate_risk_metrics(equal_returns)
    logger.info(f"Annualized Return: {metrics.annualized_return:.2%}")
    logger.info(f"Volatility: {metrics.volatility:.2%}")
    logger.info(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    logger.info(f"Sortino Ratio: {metrics.sortino_ratio:.2f}")
    logger.info(f"Calmar Ratio: {metrics.calmar_ratio:.2f}")
    logger.info(f"Omega Ratio: {metrics.omega_ratio:.2f}")
    logger.info(f"Max Drawdown: {metrics.max_drawdown:.2%}")
    logger.info(f"CVaR 95%: {metrics.cvar_95:.4f}")
    logger.info(f"Skewness: {metrics.skewness:.2f}")
    logger.info(f"Kurtosis: {metrics.kurtosis:.2f}")
    
    # Compare optimization objectives
    logger.info("\n=== Optimization Comparison ===")
    results = optimizer.compare_metrics(returns_df)
    
    for objective, result in results.items():
        logger.info(f"\n{objective}:")
        logger.info(f"  Success: {result.success}")
        logger.info(f"  Weights: {', '.join([f'{k}: {v:.1%}' for k, v in result.weights.items()])}")
        logger.info(f"  Sharpe: {result.metrics.sharpe_ratio:.2f}")
        logger.info(f"  Sortino: {result.metrics.sortino_ratio:.2f}")
        logger.info(f"  Calmar: {result.metrics.calmar_ratio:.2f}")
        logger.info(f"  Max DD: {result.metrics.max_drawdown:.2%}")
    
    # Multi-objective optimization
    logger.info("\n=== Multi-Objective Optimization ===")
    multi_result = optimizer.multi_objective_optimize(
        returns_df,
        objectives=[
            OptimizationObjective.MAX_SHARPE,
            OptimizationObjective.MIN_MAX_DRAWDOWN,
            OptimizationObjective.MIN_CVAR
        ],
        weights_objectives=[0.4, 0.3, 0.3]
    )
    logger.info(f"Weights: {', '.join([f'{k}: {v:.1%}' for k, v in multi_result.weights.items()])}")
    logger.info(f"Sharpe: {multi_result.metrics.sharpe_ratio:.2f}")
    logger.info(f"Max DD: {multi_result.metrics.max_drawdown:.2%}")
    logger.info(f"CVaR 95%: {multi_result.metrics.cvar_95:.4f}")
    
    # Constrained optimization
    logger.info("\n=== Constrained Optimization ===")
    constraints = OptimizationConstraints(
        min_weight=0.05,
        max_weight=0.40,
        max_volatility=0.15,
        max_drawdown=0.15
    )
    
    constrained_result = optimizer.optimize(
        returns_df,
        OptimizationObjective.MAX_SHARPE,
        constraints
    )
    logger.info(f"Weights: {', '.join([f'{k}: {v:.1%}' for k, v in constrained_result.weights.items()])}")
    logger.info(f"Constraints Satisfied: {constrained_result.constraints_satisfied}")
    logger.info(f"Sharpe: {constrained_result.metrics.sharpe_ratio:.2f}")
    logger.info(f"Volatility: {constrained_result.metrics.volatility:.2%}")
