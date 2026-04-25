"""
Multi-Objective Fitness Evaluator.

Evaluates strategy genomes across multiple objectives:
- Sharpe ratio (risk-adjusted returns)
- Maximum drawdown (tail risk)
- Regime stability (performance across market conditions)
- Tail risk metrics (VaR, CVaR)
- Complexity penalty (Occam's razor)
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from scipy import stats

from .backtesting_engine import BacktestResult


@dataclass
class FitnessScore:
    """Multi-objective fitness scores"""
    sharpe_ratio: float
    max_drawdown: float
    regime_stability: float
    tail_risk: float
    complexity_penalty: float
    
    total_fitness: float
    
    metrics: Dict[str, float]
    
    def __repr__(self):
        return (f"FitnessScore(sharpe={self.sharpe_ratio:.3f}, "
                f"drawdown={self.max_drawdown:.3f}, "
                f"regime_stability={self.regime_stability:.3f}, "
                f"total={self.total_fitness:.3f})")


class MultiObjectiveFitness:
    """
    Multi-objective fitness evaluator for trading strategies.
    
    Combines multiple performance metrics into a single fitness score
    while maintaining Pareto optimality awareness.
    """
    
    def __init__(
        self,
        sharpe_weight: float = 0.35,
        drawdown_weight: float = 0.25,
        regime_weight: float = 0.20,
        tail_risk_weight: float = 0.15,
        complexity_weight: float = 0.05,
        min_trades: int = 20
    ):
        """
        Initialize fitness evaluator.
        
        Args:
            sharpe_weight: Weight for Sharpe ratio
            drawdown_weight: Weight for max drawdown
            regime_weight: Weight for regime stability
            tail_risk_weight: Weight for tail risk
            complexity_weight: Weight for complexity penalty
            min_trades: Minimum trades required for valid strategy
        """
        self.sharpe_weight = sharpe_weight
        self.drawdown_weight = drawdown_weight
        self.regime_weight = regime_weight
        self.tail_risk_weight = tail_risk_weight
        self.complexity_weight = complexity_weight
        self.min_trades = min_trades
        
        total_weight = sum([
            sharpe_weight, drawdown_weight, regime_weight,
            tail_risk_weight, complexity_weight
        ])
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def evaluate(
        self,
        backtest_result: BacktestResult,
        genome_complexity: int,
        market_data: pd.DataFrame
    ) -> FitnessScore:
        """
        Evaluate complete fitness of a strategy.
        
        Args:
            backtest_result: Results from backtesting
            genome_complexity: Complexity of the strategy genome
            market_data: Market data for regime analysis
        
        Returns:
            FitnessScore with all components
        """
        if backtest_result.num_trades < self.min_trades:
            return self._create_invalid_fitness()
        
        sharpe_score = self._evaluate_sharpe(backtest_result)
        
        drawdown_score = self._evaluate_drawdown(backtest_result)
        
        regime_score = self._evaluate_regime_stability(
            backtest_result, market_data
        )
        
        tail_risk_score = self._evaluate_tail_risk(backtest_result)
        
        complexity_score = self._evaluate_complexity(genome_complexity)
        
        total_fitness = (
            self.sharpe_weight * sharpe_score +
            self.drawdown_weight * drawdown_score +
            self.regime_weight * regime_score +
            self.tail_risk_weight * tail_risk_score +
            self.complexity_weight * complexity_score
        )
        
        return FitnessScore(
            sharpe_ratio=sharpe_score,
            max_drawdown=drawdown_score,
            regime_stability=regime_score,
            tail_risk=tail_risk_score,
            complexity_penalty=complexity_score,
            total_fitness=total_fitness,
            metrics=backtest_result.metrics
        )
    
    def _create_invalid_fitness(self) -> FitnessScore:
        """Create fitness score for invalid strategies"""
        return FitnessScore(
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            regime_stability=0.0,
            tail_risk=0.0,
            complexity_penalty=0.0,
            total_fitness=0.0,
            metrics={}
        )
    
    def _evaluate_sharpe(self, result: BacktestResult) -> float:
        """
        Evaluate Sharpe ratio component.
        
        Normalized to [0, 1] range using sigmoid transformation.
        """
        sharpe = result.sharpe_ratio
        
        normalized = self._sigmoid(sharpe, center=1.0, scale=1.0)
        
        return normalized
    
    def _evaluate_drawdown(self, result: BacktestResult) -> float:
        """
        Evaluate maximum drawdown component.
        
        Lower drawdown is better, so we invert the score.
        """
        max_dd = abs(result.max_drawdown)
        
        if max_dd > 0.5:
            return 0.0
        
        score = 1.0 - (max_dd / 0.5)
        
        return max(0.0, score)
    
    def _evaluate_regime_stability(
        self,
        result: BacktestResult,
        market_data: pd.DataFrame
    ) -> float:
        """
        Evaluate stability across different market regimes.
        
        Measures consistency of performance in different market conditions:
        - Bull markets (high returns)
        - Bear markets (negative returns)
        - High volatility
        - Low volatility
        """
        returns = result.returns.dropna()
        
        if len(returns) < 60:
            return 0.5
        
        market_returns = market_data['returns'].loc[returns.index]
        
        bull_mask = market_returns > market_returns.quantile(0.6)
        bear_mask = market_returns < market_returns.quantile(0.4)
        
        market_vol = market_returns.rolling(20).std()
        high_vol_mask = market_vol > market_vol.quantile(0.6)
        low_vol_mask = market_vol < market_vol.quantile(0.4)
        
        regime_sharpes = []
        
        for mask in [bull_mask, bear_mask, high_vol_mask, low_vol_mask]:
            regime_returns = returns[mask]
            if len(regime_returns) > 20:
                regime_sharpe = (
                    regime_returns.mean() / regime_returns.std() * np.sqrt(252)
                    if regime_returns.std() > 0 else 0
                )
                regime_sharpes.append(regime_sharpe)
        
        if not regime_sharpes:
            return 0.5
        
        stability = 1.0 - (np.std(regime_sharpes) / (abs(np.mean(regime_sharpes)) + 1.0))
        
        positive_regimes = sum(1 for s in regime_sharpes if s > 0)
        consistency_bonus = positive_regimes / len(regime_sharpes)
        
        final_score = 0.7 * max(0, stability) + 0.3 * consistency_bonus
        
        return np.clip(final_score, 0.0, 1.0)
    
    def _evaluate_tail_risk(self, result: BacktestResult) -> float:
        """
        Evaluate tail risk metrics.
        
        Uses VaR (Value at Risk) and CVaR (Conditional VaR) at 95% confidence.
        """
        returns = result.returns.dropna()
        
        if len(returns) < 30:
            return 0.5
        
        var_95 = np.percentile(returns, 5)
        
        cvar_95 = returns[returns <= var_95].mean()
        
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        var_score = self._sigmoid(-var_95, center=0.02, scale=0.01)
        
        cvar_score = self._sigmoid(-cvar_95, center=0.03, scale=0.015)
        
        skew_score = self._sigmoid(skewness, center=0.0, scale=1.0)
        
        kurt_penalty = max(0, 1.0 - abs(kurtosis) / 10.0)
        
        tail_score = (
            0.4 * var_score +
            0.4 * cvar_score +
            0.1 * skew_score +
            0.1 * kurt_penalty
        )
        
        return np.clip(tail_score, 0.0, 1.0)
    
    def _evaluate_complexity(self, complexity: int) -> float:
        """
        Evaluate complexity penalty (Occam's razor).
        
        Simpler strategies are preferred, all else being equal.
        """
        target_complexity = 10
        
        if complexity <= target_complexity:
            return 1.0
        
        penalty = np.exp(-(complexity - target_complexity) / 20.0)
        
        return max(0.3, penalty)
    
    def _sigmoid(self, x: float, center: float = 0.0, scale: float = 1.0) -> float:
        """Sigmoid transformation for normalization"""
        return 1.0 / (1.0 + np.exp(-(x - center) / scale))
    
    def pareto_dominates(self, score1: FitnessScore, score2: FitnessScore) -> bool:
        """
        Check if score1 Pareto-dominates score2.
        
        Score1 dominates if it's better in at least one objective
        and not worse in any objective.
        """
        objectives1 = [
            score1.sharpe_ratio,
            score1.max_drawdown,
            score1.regime_stability,
            score1.tail_risk
        ]
        
        objectives2 = [
            score2.sharpe_ratio,
            score2.max_drawdown,
            score2.regime_stability,
            score2.tail_risk
        ]
        
        better_in_one = False
        worse_in_any = False
        
        for obj1, obj2 in zip(objectives1, objectives2):
            if obj1 > obj2:
                better_in_one = True
            elif obj1 < obj2:
                worse_in_any = True
        
        return better_in_one and not worse_in_any
    
    def get_pareto_frontier(
        self,
        fitness_scores: List[Tuple[str, FitnessScore]]
    ) -> List[str]:
        """
        Get Pareto frontier from a set of fitness scores.
        
        Returns IDs of non-dominated solutions.
        """
        pareto_ids = []
        
        for i, (id1, score1) in enumerate(fitness_scores):
            is_dominated = False
            
            for j, (id2, score2) in enumerate(fitness_scores):
                if i != j and self.pareto_dominates(score2, score1):
                    is_dominated = True
                    break
            
            if not is_dominated:
                pareto_ids.append(id1)
        
        return pareto_ids
    
    def calculate_diversity_bonus(
        self,
        current_score: FitnessScore,
        population_scores: List[FitnessScore]
    ) -> float:
        """
        Calculate diversity bonus for maintaining population diversity.
        
        Rewards strategies that are different from existing population.
        """
        if not population_scores:
            return 0.0
        
        current_vector = np.array([
            current_score.sharpe_ratio,
            current_score.max_drawdown,
            current_score.regime_stability,
            current_score.tail_risk
        ])
        
        distances = []
        for score in population_scores:
            score_vector = np.array([
                score.sharpe_ratio,
                score.max_drawdown,
                score.regime_stability,
                score.tail_risk
            ])
            
            distance = np.linalg.norm(current_vector - score_vector)
            distances.append(distance)
        
        avg_distance = np.mean(distances)
        
        diversity_bonus = min(0.1, avg_distance / 2.0)
        
        return diversity_bonus
