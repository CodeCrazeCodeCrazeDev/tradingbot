"""
Enhanced Fitness Evaluator with Tail Risk Metrics
Implements comprehensive fitness evaluation including VaR, CVaR, and other tail risk measures.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from scipy import stats
import logging

from .backtesting_engine import BacktestResult

logger = logging.getLogger(__name__)


@dataclass
class EnhancedFitnessScore:
    """Comprehensive fitness score with tail risk metrics"""
    # Traditional metrics
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    
    # Tail risk metrics
    var_95: float  # Value at Risk (95%)
    var_99: float  # Value at Risk (99%)
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    cvar_99: float
    skewness: float
    kurtosis: float
    
    # Advanced metrics
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float
    
    # Regime stability
    regime_stability: float
    worst_regime_sharpe: float
    
    # Complexity penalty
    complexity_penalty: float
    
    # Overall score
    total_fitness: float
    
    # Component breakdown
    metrics: Dict[str, float] = field(default_factory=dict)


class EnhancedFitnessEvaluator:
    """
    Enhanced multi-objective fitness evaluator with tail risk metrics.
    
    Evaluates strategies across multiple dimensions:
    - Risk-adjusted returns (Sharpe, Sortino, Calmar)
    - Tail risk (VaR, CVaR, skewness, kurtosis)
    - Drawdown characteristics
    - Regime stability
    - Complexity penalty
    """
    
    def __init__(self,
                 risk_free_rate: float = 0.02,
                 target_sharpe: float = 1.5,
                 max_acceptable_dd: float = 0.2,
                 complexity_weight: float = 0.1,
                 tail_risk_weight: float = 0.25,
                 return_weight: float = 0.35,
                 stability_weight: float = 0.3):
        """
        Initialize enhanced fitness evaluator.
        
        Args:
            risk_free_rate: Annual risk-free rate
            target_sharpe: Target Sharpe ratio
            max_acceptable_dd: Maximum acceptable drawdown
            complexity_weight: Weight for complexity penalty
            tail_risk_weight: Weight for tail risk metrics
            return_weight: Weight for return metrics
            stability_weight: Weight for stability metrics
        """
        self.risk_free_rate = risk_free_rate
        self.target_sharpe = target_sharpe
        self.max_acceptable_dd = max_acceptable_dd
        
        # Weights for fitness components
        self.weights = {
            'returns': return_weight,
            'tail_risk': tail_risk_weight,
            'stability': stability_weight,
            'complexity': complexity_weight
        }
        
        logger.info("EnhancedFitnessEvaluator initialized")
    
    def evaluate(self,
                backtest_result: BacktestResult,
                complexity: int = 1,
                regime_stability: float = 1.0,
                worst_regime_sharpe: float = 1.0) -> EnhancedFitnessScore:
        """
        Calculate comprehensive fitness score.
        
        Args:
            backtest_result: Results from backtest
            complexity: Strategy complexity measure
            regime_stability: Performance stability across regimes
            worst_regime_sharpe: Sharpe ratio in worst regime
            
        Returns:
            EnhancedFitnessScore with all metrics
        """
        returns = backtest_result.returns.dropna()
        
        if len(returns) == 0:
            return self._empty_score()
        
        # Calculate return metrics
        total_return = backtest_result.total_return
        sharpe = backtest_result.sharpe_ratio
        sortino = self._calculate_sortino(returns)
        calmar = self._calculate_calmar(returns, backtest_result.max_drawdown)
        omega = self._calculate_omega(returns)
        
        # Calculate tail risk metrics
        var_95 = self._calculate_var(returns, 0.95)
        var_99 = self._calculate_var(returns, 0.99)
        cvar_95 = self._calculate_cvar(returns, 0.95)
        cvar_99 = self._calculate_cvar(returns, 0.99)
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        # Complexity penalty (Occam's razor)
        complexity_penalty = self._calculate_complexity_penalty(complexity)
        
        # Component scores (0-1 scale)
        return_score = self._score_returns(total_return, sharpe, sortino, calmar)
        tail_risk_score = self._score_tail_risk(var_95, var_99, cvar_95, skewness, kurtosis)
        stability_score = self._score_stability(
            backtest_result.max_drawdown, regime_stability, worst_regime_sharpe
        )
        
        # Weighted total fitness
        total_fitness = (
            self.weights['returns'] * return_score +
            self.weights['tail_risk'] * tail_risk_score +
            self.weights['stability'] * stability_score -
            self.weights['complexity'] * complexity_penalty
        )
        
        # Ensure non-negative
        total_fitness = max(0.0, total_fitness)
        
        return EnhancedFitnessScore(
            sharpe_ratio=sharpe,
            max_drawdown=backtest_result.max_drawdown,
            total_return=total_return,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            skewness=skewness,
            kurtosis=kurtosis,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            omega_ratio=omega,
            regime_stability=regime_stability,
            worst_regime_sharpe=worst_regime_sharpe,
            complexity_penalty=complexity_penalty,
            total_fitness=total_fitness,
            metrics={
                'return_score': return_score,
                'tail_risk_score': tail_risk_score,
                'stability_score': stability_score,
                'num_trades': backtest_result.num_trades,
                'win_rate': backtest_result.win_rate,
                'profit_factor': backtest_result.profit_factor
            }
        )
    
    def _calculate_sortino(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio (downside risk adjusted)"""
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        # Annualized
        excess_return = returns.mean() * 252 - self.risk_free_rate
        downside_deviation = downside_returns.std() * np.sqrt(252)
        
        return excess_return / downside_deviation
    
    def _calculate_calmar(self, returns: pd.Series, max_drawdown: float) -> float:
        """Calculate Calmar ratio (return / max drawdown)"""
        if max_drawdown == 0:
            return 0.0
        
        annualized_return = returns.mean() * 252
        return annualized_return / abs(max_drawdown)
    
    def _calculate_omega(self, returns: pd.Series, threshold: float = 0.0) -> float:
        """Calculate Omega ratio"""
        excess_returns = returns - threshold
        
        gains = excess_returns[excess_returns > 0].sum()
        losses = abs(excess_returns[excess_returns < 0].sum())
        
        if losses == 0:
            return float('inf') if gains > 0 else 1.0
        
        return gains / losses
    
    def _calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk.
        
        VaR at confidence level (e.g., 95% VaR = 5th percentile)
        """
        return np.percentile(returns, (1 - confidence) * 100)
    
    def _calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (Expected Shortfall).
        
        Average of returns beyond VaR threshold.
        """
        var = self._calculate_var(returns, confidence)
        tail_returns = returns[returns <= var]
        
        if len(tail_returns) == 0:
            return var
        
        return tail_returns.mean()
    
    def _calculate_complexity_penalty(self, complexity: int) -> float:
        """
        Calculate complexity penalty.
        
        Higher complexity = higher penalty (Occam's razor).
        """
        # Soft penalty that increases with complexity
        return np.log(1 + complexity) / 5.0
    
    def _score_returns(self, 
                      total_return: float, 
                      sharpe: float, 
                      sortino: float, 
                      calmar: float) -> float:
        """Score return metrics (0-1 scale)"""
        # Sharpe score (target is 1.5+)
        sharpe_score = min(1.0, sharpe / self.target_sharpe)
        
        # Sortino score
        sortino_score = min(1.0, sortino / self.target_sharpe)
        
        # Calmar score (good is 2+)
        calmar_score = min(1.0, calmar / 2.0)
        
        # Return magnitude score (annualized)
        annual_return = total_return * 252 / 252  # Adjust if needed
        return_score = min(1.0, max(0, annual_return / 0.5))
        
        # Weighted combination
        return (
            0.4 * sharpe_score +
            0.3 * sortino_score +
            0.2 * calmar_score +
            0.1 * return_score
        )
    
    def _score_tail_risk(self,
                        var_95: float,
                        var_99: float,
                        cvar_95: float,
                        skewness: float,
                        kurtosis: float) -> float:
        """Score tail risk metrics (0-1 scale, higher = better)"""
        # VaR score (less negative is better)
        # Typical daily VaR ranges from -0.05 to 0
        var_score = 1.0 - min(1.0, abs(var_95) / 0.05)
        
        # CVaR score
        cvar_score = 1.0 - min(1.0, abs(cvar_95) / 0.07)
        
        # Skewness score (positive skew is better)
        # Normalize: typical range -2 to +2
        skew_score = (skewness + 2) / 4.0
        skew_score = max(0.0, min(1.0, skew_score))
        
        # Kurtosis score (lower kurtosis = thinner tails = better)
        # Excess kurtosis: 0 is normal, >3 is fat-tailed
        kurt_score = 1.0 - min(1.0, max(0, kurtosis) / 3.0)
        
        return (
            0.3 * var_score +
            0.3 * cvar_score +
            0.2 * skew_score +
            0.2 * kurt_score
        )
    
    def _score_stability(self,
                        max_drawdown: float,
                        regime_stability: float,
                        worst_regime_sharpe: float) -> float:
        """Score stability metrics (0-1 scale)"""
        # Drawdown score
        dd_score = 1.0 - min(1.0, abs(max_drawdown) / self.max_acceptable_dd)
        
        # Regime stability score (already 0-1)
        regime_score = regime_stability
        
        # Worst regime Sharpe score
        worst_regime_score = min(1.0, max(0, worst_regime_sharpe) / 1.0)
        
        return (
            0.4 * dd_score +
            0.4 * regime_score +
            0.2 * worst_regime_score
        )
    
    def _empty_score(self) -> EnhancedFitnessScore:
        """Return empty fitness score for invalid backtests"""
        return EnhancedFitnessScore(
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            total_return=0.0,
            var_95=0.0,
            var_99=0.0,
            cvar_95=0.0,
            cvar_99=0.0,
            skewness=0.0,
            kurtosis=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            omega_ratio=1.0,
            regime_stability=0.0,
            worst_regime_sharpe=0.0,
            complexity_penalty=0.0,
            total_fitness=0.0
        )
    
    def get_tail_risk_report(self, backtest_result: BacktestResult) -> Dict[str, Any]:
        """Generate detailed tail risk report"""
        returns = backtest_result.returns.dropna()
        
        if len(returns) == 0:
            return {'error': 'No returns data'}
        
        # Calculate all tail risk metrics
        var_90 = self._calculate_var(returns, 0.90)
        var_95 = self._calculate_var(returns, 0.95)
        var_99 = self._calculate_var(returns, 0.99)
        
        cvar_90 = self._calculate_cvar(returns, 0.90)
        cvar_95 = self._calculate_cvar(returns, 0.95)
        cvar_99 = self._calculate_cvar(returns, 0.99)
        
        # Tail events
        extreme_losses = returns[returns < var_99]
        
        return {
            'var': {
                '90%': var_90,
                '95%': var_95,
                '99%': var_99
            },
            'cvar': {
                '90%': cvar_90,
                '95%': cvar_95,
                '99%': cvar_99
            },
            'distribution': {
                'skewness': returns.skew(),
                'kurtosis': returns.kurtosis(),
                'jarque_bera': stats.jarque_bera(returns)[0],
                'jarque_bera_pvalue': stats.jarque_bera(returns)[1]
            },
            'tail_events': {
                'count_99': len(extreme_losses),
                'max_loss': returns.min(),
                'avg_extreme_loss': extreme_losses.mean() if len(extreme_losses) > 0 else 0
            },
            'risk_ratios': {
                'var_to_cvar_95': var_95 / cvar_95 if cvar_95 != 0 else 0,
                'tail_heavy': returns.kurtosis() > 3
            }
        }
