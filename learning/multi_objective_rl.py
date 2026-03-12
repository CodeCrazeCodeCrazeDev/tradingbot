"""
Multi-Objective Reinforcement Learning - Phase 1
Optimize multiple objectives simultaneously (profit, risk, stability)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import numpy as np
import logging
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class TradeMetrics:
    """Comprehensive metrics for a single trade."""
    pnl: float
    sharpe_contribution: float
    drawdown_impact: float
    volatility_score: float
    execution_quality: float
    holding_time: float = 0.0
    slippage: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'pnl': self.pnl,
            'sharpe': self.sharpe_contribution,
            'drawdown': self.drawdown_impact,
            'volatility': self.volatility_score,
            'execution': self.execution_quality,
            'holding_time': self.holding_time,
            'slippage': self.slippage
        }


@dataclass
class ObjectiveWeights:
    """Weights for different trading objectives."""
    profit: float = 0.40
    sharpe: float = 0.25
    drawdown: float = 0.20
    stability: float = 0.10
    execution: float = 0.05
    
    def normalize(self):
        """Ensure weights sum to 1.0."""
        total = self.profit + self.sharpe + self.drawdown + self.stability + self.execution
        if total > 0:
            self.profit /= total
            self.sharpe /= total
            self.drawdown /= total
            self.stability /= total
            self.execution /= total
    
    def to_dict(self) -> Dict:
        return {
            'profit': self.profit,
            'sharpe': self.sharpe,
            'drawdown': self.drawdown,
            'stability': self.stability,
            'execution': self.execution
        }


class MultiObjectiveRL:
    """
    Multi-Objective Reinforcement Learning
    Balances multiple trading objectives with adaptive weighting
    """
    
    def __init__(self, history_size: int = 100):
        self.objectives = ObjectiveWeights()
        self.objectives.normalize()
        
        self.performance_history = deque(maxlen=history_size)
        self.objective_history = {
            'profit': deque(maxlen=history_size),
            'sharpe': deque(maxlen=history_size),
            'drawdown': deque(maxlen=history_size),
            'stability': deque(maxlen=history_size),
            'execution': deque(maxlen=history_size)
        }
        
        # Normalization statistics
        self.profit_stats = {'mean': 0.0, 'std': 1.0}
        self.sharpe_stats = {'mean': 0.0, 'std': 1.0}
        
        logger.info("✅ Multi-Objective RL initialized")
        logger.info(f"   Objectives: {self.objectives.to_dict()}")
    
    def compute_reward(self, metrics: TradeMetrics) -> float:
        """
        Compute weighted multi-objective reward.
        
        Args:
            metrics: Trade performance metrics
        
        Returns:
            Combined reward value
        """
        # Normalize each metric
        normalized = {
            'profit': self._normalize_profit(metrics.pnl),
            'sharpe': metrics.sharpe_contribution,
            'drawdown': -abs(metrics.drawdown_impact),  # Negative is bad
            'stability': 1.0 - min(metrics.volatility_score, 1.0),
            'execution': metrics.execution_quality
        }
        
        # Weighted sum
        total_reward = (
            self.objectives.profit * normalized['profit'] +
            self.objectives.sharpe * normalized['sharpe'] +
            self.objectives.drawdown * normalized['drawdown'] +
            self.objectives.stability * normalized['stability'] +
            self.objectives.execution * normalized['execution']
        )
        
        # Record for adaptation
        for key, value in normalized.items():
            self.objective_history[key].append(value)
        
        self.performance_history.append(total_reward)
        
        return total_reward
    
    def _normalize_profit(self, pnl: float) -> float:
        """Normalize profit to [-1, 1] range."""
        if self.profit_stats['std'] == 0:
            return np.tanh(pnl / 1000)  # Default normalization
        
        z_score = (pnl - self.profit_stats['mean']) / self.profit_stats['std']
        return np.tanh(z_score)  # Squash to [-1, 1]
    
    def update_normalization_stats(self):
        """Update normalization statistics from history."""
        if len(self.objective_history['profit']) > 10:
            profits = list(self.objective_history['profit'])
            self.profit_stats['mean'] = np.mean(profits)
            self.profit_stats['std'] = np.std(profits) + 1e-8
    
    def adapt_objectives(self, market_regime: str):
        """
        Adjust objective weights based on market conditions.
        
        Args:
            market_regime: 'high_volatility', 'trending', 'ranging', 'crisis'
        """
        logger.info(f"🎯 Adapting objectives for {market_regime} regime")
        
        if market_regime == 'high_volatility':
            # Focus on risk management
            self.objectives = ObjectiveWeights(
                profit=0.25,
                sharpe=0.30,
                drawdown=0.30,
                stability=0.15,
                execution=0.00
            )
        
        elif market_regime == 'trending':
            # Focus on profit capture
            self.objectives = ObjectiveWeights(
                profit=0.50,
                sharpe=0.20,
                drawdown=0.15,
                stability=0.10,
                execution=0.05
            )
        
        elif market_regime == 'ranging':
            # Focus on stability and execution
            self.objectives = ObjectiveWeights(
                profit=0.30,
                sharpe=0.25,
                drawdown=0.15,
                stability=0.20,
                execution=0.10
            )
        
        elif market_regime == 'crisis':
            # Maximum risk aversion
            self.objectives = ObjectiveWeights(
                profit=0.10,
                sharpe=0.20,
                drawdown=0.50,
                stability=0.20,
                execution=0.00
            )
        
        else:  # balanced
            self.objectives = ObjectiveWeights()
        
        self.objectives.normalize()
        logger.info(f"   New weights: {self.objectives.to_dict()}")
    
    def pareto_optimization(
        self,
        policies: List[Tuple[str, Dict[str, float]]]
    ) -> List[Tuple[str, Dict[str, float]]]:
        """
        Find Pareto-optimal policies (non-dominated solutions).
        
        Args:
            policies: List of (policy_name, objective_scores) tuples
        
        Returns:
            Pareto-optimal policies
        """
        pareto_front = []
        
        for i, (name_i, scores_i) in enumerate(policies):
            is_dominated = False
            
            for j, (name_j, scores_j) in enumerate(policies):
                if i == j:
                    continue
                
                if self._dominates(scores_j, scores_i):
                    is_dominated = True
                    break
            
            if not is_dominated:
                pareto_front.append((name_i, scores_i))
        
        logger.info(f"📊 Pareto front: {len(pareto_front)}/{len(policies)} policies")
        return pareto_front
    
    def _dominates(self, scores_a: Dict[str, float], scores_b: Dict[str, float]) -> bool:
        """
        Check if policy A dominates policy B.
        A dominates B if A is better or equal in all objectives and strictly better in at least one.
        """
        better_in_all = True
        strictly_better_in_one = False
        
        for objective in ['profit', 'sharpe', 'stability', 'execution']:
            if scores_a.get(objective, 0) < scores_b.get(objective, 0):
                better_in_all = False
                break
            if scores_a.get(objective, 0) > scores_b.get(objective, 0):
                strictly_better_in_one = True
        
        # For drawdown, lower (less negative) is better
        if scores_a.get('drawdown', 0) > scores_b.get('drawdown', 0):
            better_in_all = False
        if scores_a.get('drawdown', 0) < scores_b.get('drawdown', 0):
            strictly_better_in_one = True
        
        return better_in_all and strictly_better_in_one
    
    def get_objective_performance(self) -> Dict[str, float]:
        """Get average performance for each objective."""
        performance = {}
        
        for objective, history in self.objective_history.items():
            if len(history) > 0:
                performance[objective] = np.mean(list(history))
            else:
                performance[objective] = 0.0
        
        return performance
    
    def get_overall_performance(self) -> float:
        """Get overall weighted performance."""
        if len(self.performance_history) == 0:
            return 0.0
        return np.mean(list(self.performance_history))
    
    def auto_tune_objectives(self):
        """
        Automatically tune objective weights based on recent performance.
        Increases weight of underperforming objectives.
        """
        if len(self.performance_history) < 20:
            return
        
        performance = self.get_objective_performance()
        
        # Calculate adjustment factors
        adjustments = {}
        for objective, score in performance.items():
            if objective == 'drawdown':
                # For drawdown, closer to 0 is better
                adjustments[objective] = 1.0 + abs(score)
            else:
                # For others, higher is better
                adjustments[objective] = 1.0 / (score + 1.0)
        
        # Update weights
        self.objectives.profit *= adjustments['profit']
        self.objectives.sharpe *= adjustments['sharpe']
        self.objectives.drawdown *= adjustments['drawdown']
        self.objectives.stability *= adjustments['stability']
        self.objectives.execution *= adjustments['execution']
        
        self.objectives.normalize()
        
        logger.info("🔧 Auto-tuned objectives:")
        logger.info(f"   {self.objectives.to_dict()}")
    
    def calculate_scalarization(
        self,
        objectives_vector: np.ndarray,
        method: str = 'weighted_sum'
    ) -> float:
        """
        Scalarize multiple objectives into single value.
        
        Args:
            objectives_vector: [profit, sharpe, drawdown, stability, execution]
            method: 'weighted_sum', 'chebyshev', 'augmented_chebyshev'
        
        Returns:
            Scalar value
        """
        weights = np.array([
            self.objectives.profit,
            self.objectives.sharpe,
            self.objectives.drawdown,
            self.objectives.stability,
            self.objectives.execution
        ])
        
        if method == 'weighted_sum':
            return np.dot(weights, objectives_vector)
        
        elif method == 'chebyshev':
            # Minimize maximum weighted deviation
            return -np.max(weights * objectives_vector)
        
        elif method == 'augmented_chebyshev':
            # Chebyshev + small weighted sum term
            chebyshev = -np.max(weights * objectives_vector)
            weighted_sum = np.dot(weights, objectives_vector)
            return chebyshev + 0.01 * weighted_sum
        
        else:
            return np.dot(weights, objectives_vector)
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics."""
        return {
            'current_weights': self.objectives.to_dict(),
            'objective_performance': self.get_objective_performance(),
            'overall_performance': self.get_overall_performance(),
            'num_trades': len(self.performance_history),
            'profit_stats': self.profit_stats
        }
    
    def save_state(self) -> Dict:
        """Save state for persistence."""
        return {
            'objectives': self.objectives.to_dict(),
            'performance_history': list(self.performance_history),
            'objective_history': {
                k: list(v) for k, v in self.objective_history.items()
            },
            'profit_stats': self.profit_stats
        }
    
    def load_state(self, state: Dict):
        """Load saved state."""
        obj = state['objectives']
        self.objectives = ObjectiveWeights(**obj)
        
        self.performance_history = deque(state['performance_history'], maxlen=100)
        
        for key, values in state['objective_history'].items():
            self.objective_history[key] = deque(values, maxlen=100)
        
        self.profit_stats = state['profit_stats']
        
        logger.info("📂 Multi-Objective RL state loaded")
