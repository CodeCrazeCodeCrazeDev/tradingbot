"""
Layer 5: Advanced RL Hub
Hierarchical, Distributional, and Meta Reinforcement Learning.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import logging
import numpy

logger = logging.getLogger(__name__)


@dataclass
class RLState:
    """State representation for RL agents."""
    features: np.ndarray
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RLAction:
    """Action from RL agent."""
    action_type: str  # 'buy', 'sell', 'hold'
    size: float = 1.0
    confidence: float = 0.5


class DistributionalRL:
    """
    Distributional RL - Models full return distribution.
    Uses quantile regression for risk-aware decisions.
    """
    
    def __init__(self, num_quantiles: int = 51, config: Optional[Dict[str, Any]] = None):
        self.num_quantiles = num_quantiles
        self.config = config or {}
        self.quantiles = np.linspace(0.01, 0.99, num_quantiles)
        self.q_values: Dict[str, np.ndarray] = {}
        logger.info("DistributionalRL initialized with %d quantiles", num_quantiles)
    
    def get_action(self, state: RLState, risk_level: float = 0.5) -> RLAction:
        """Get action based on distributional Q-values."""
        # Simplified action selection based on risk level
        state_key = self._state_to_key(state)
        
        if state_key not in self.q_values:
            # Initialize with neutral distribution
            self.q_values[state_key] = np.zeros((3, self.num_quantiles))  # buy, sell, hold
        
        q_dist = self.q_values[state_key]
        
        # Risk-sensitive action selection
        # Lower risk_level = more conservative (use lower quantiles)
        quantile_idx = int(risk_level * (self.num_quantiles - 1))
        
        action_values = q_dist[:, quantile_idx]
        best_action_idx = np.argmax(action_values)
        
        actions = ['buy', 'sell', 'hold']
        return RLAction(
            action_type=actions[best_action_idx],
            confidence=float(np.max(action_values)) if np.max(action_values) > 0 else 0.5
        )
    
    def update(self, state: RLState, action: RLAction, reward: float, next_state: RLState):
        """Update distributional Q-values."""
        state_key = self._state_to_key(state)
        action_idx = ['buy', 'sell', 'hold'].index(action.action_type)
        
        if state_key not in self.q_values:
            self.q_values[state_key] = np.zeros((3, self.num_quantiles))
        
        # Simple update (in production, use proper distributional Bellman update)
        learning_rate = self.config.get('learning_rate', 0.01)
        self.q_values[state_key][action_idx] += learning_rate * (reward - self.q_values[state_key][action_idx])
    
    def _state_to_key(self, state: RLState) -> str:
        """Convert state to hashable key."""
        return str(tuple(np.round(state.features, 2)))
    
    def get_risk_metrics(self, state: RLState) -> Dict[str, float]:
        """Get risk metrics from distribution."""
        state_key = self._state_to_key(state)
        
        if state_key not in self.q_values:
            return {'var_5': 0.0, 'cvar_5': 0.0, 'expected': 0.0}
        
        q_dist = self.q_values[state_key]
        best_action = np.argmax(np.mean(q_dist, axis=1))
        
        return {
            'var_5': float(np.percentile(q_dist[best_action], 5)),
            'cvar_5': float(np.mean(q_dist[best_action][q_dist[best_action] <= np.percentile(q_dist[best_action], 5)])) if len(q_dist[best_action]) > 0 else 0.0,
            'expected': float(np.mean(q_dist[best_action]))
        }


class MetaRL:
    """
    Meta RL - Fast adaptation to new market conditions.
    Implements MAML-style meta-learning.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.meta_parameters: Dict[str, float] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.adaptation_steps = config.get('adaptation_steps', 5) if config else 5
        logger.info("MetaRL initialized")
    
    def adapt(self, task_data: List[Tuple[RLState, RLAction, float]]) -> Dict[str, float]:
        """Adapt to new task using few-shot learning."""
        if not task_data:
            return self.meta_parameters.copy()
        
        # Simple adaptation: adjust parameters based on task performance
        adapted_params = self.meta_parameters.copy()
        
        total_reward = sum(r for _, _, r in task_data)
        avg_reward = total_reward / len(task_data)
        
        # Adjust risk tolerance based on recent performance
        adapted_params['risk_tolerance'] = adapted_params.get('risk_tolerance', 0.5)
        if avg_reward > 0:
            adapted_params['risk_tolerance'] = min(adapted_params['risk_tolerance'] * 1.1, 0.9)
        else:
            adapted_params['risk_tolerance'] = max(adapted_params['risk_tolerance'] * 0.9, 0.1)
        
        return adapted_params
    
    def get_action(self, state: RLState, adapted_params: Optional[Dict[str, float]] = None) -> RLAction:
        """Get action using adapted parameters."""
        params = adapted_params or self.meta_parameters
        risk_tolerance = params.get('risk_tolerance', 0.5)
        
        # Simple policy based on state features
        if len(state.features) > 0:
            signal = np.mean(state.features)
            if signal > 0.1:
                return RLAction('buy', confidence=min(abs(signal), 1.0))
            elif signal < -0.1:
                return RLAction('sell', confidence=min(abs(signal), 1.0))
        
        return RLAction('hold', confidence=0.5)
    
    def update_meta(self, task_results: List[Dict[str, Any]]):
        """Update meta-parameters from task results."""
        if not task_results:
            return
        
        # Aggregate learning across tasks
        avg_performance = np.mean([t.get('performance', 0) for t in task_results])
        
        # Update meta-parameters
        self.meta_parameters['risk_tolerance'] = self.meta_parameters.get('risk_tolerance', 0.5)
        if avg_performance > 0:
            self.meta_parameters['risk_tolerance'] = min(self.meta_parameters['risk_tolerance'] + 0.01, 0.9)
        else:
            self.meta_parameters['risk_tolerance'] = max(self.meta_parameters['risk_tolerance'] - 0.01, 0.1)


class HierarchicalRL:
    """
    Hierarchical RL - Multi-level decision making.
    High-level: regime/strategy selection
    Low-level: specific trading actions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.high_level_policy: Dict[str, float] = {}  # Strategy weights
        self.low_level_policies: Dict[str, Dict[str, float]] = {}  # Action policies per strategy
        self.current_strategy: str = 'balanced'
        logger.info("HierarchicalRL initialized")
    
    def select_strategy(self, state: RLState) -> str:
        """High-level: Select trading strategy."""
        # Simple strategy selection based on state
        if len(state.features) > 0:
            volatility = state.features[0] if len(state.features) > 0 else 0.5
            trend = state.features[1] if len(state.features) > 1 else 0.0
            
            if volatility > 0.7:
                self.current_strategy = 'defensive'
            elif abs(trend) > 0.5:
                self.current_strategy = 'trend_following'
            elif volatility < 0.3:
                self.current_strategy = 'mean_reversion'
            else:
                self.current_strategy = 'balanced'
        
        return self.current_strategy
    
    def get_action(self, state: RLState) -> RLAction:
        """Get action using hierarchical policy."""
        strategy = self.select_strategy(state)
        
        # Low-level action based on strategy
        if strategy == 'defensive':
            return RLAction('hold', size=0.5, confidence=0.7)
        elif strategy == 'trend_following':
            trend = state.features[1] if len(state.features) > 1 else 0.0
            if trend > 0:
                return RLAction('buy', size=1.0, confidence=min(abs(trend), 1.0))
            else:
                return RLAction('sell', size=1.0, confidence=min(abs(trend), 1.0))
        elif strategy == 'mean_reversion':
            price_deviation = state.features[2] if len(state.features) > 2 else 0.0
            if price_deviation > 0.5:
                return RLAction('sell', size=0.8, confidence=0.6)
            elif price_deviation < -0.5:
                return RLAction('buy', size=0.8, confidence=0.6)
        
        return RLAction('hold', confidence=0.5)
    
    def update(self, state: RLState, action: RLAction, reward: float):
        """Update hierarchical policies."""
        strategy = self.current_strategy
        
        # Update strategy weights
        if strategy not in self.high_level_policy:
            self.high_level_policy[strategy] = 0.0
        
        learning_rate = self.config.get('learning_rate', 0.01)
        self.high_level_policy[strategy] += learning_rate * reward


class AdvancedRLHub:
    """
    Advanced RL Hub - Layer 5 of Cognitive Architecture.
    Coordinates multiple RL approaches.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.distributional = DistributionalRL(config=config)
        self.meta = MetaRL(config=config)
        self.hierarchical = HierarchicalRL(config=config)
        logger.info("AdvancedRLHub initialized")
    
    def get_action(self, state: RLState, mode: str = 'ensemble') -> RLAction:
        """Get action from RL hub."""
        if mode == 'distributional':
            return self.distributional.get_action(state)
        elif mode == 'meta':
            return self.meta.get_action(state)
        elif mode == 'hierarchical':
            return self.hierarchical.get_action(state)
        else:
            # Ensemble: combine all approaches
            actions = [
                self.distributional.get_action(state),
                self.meta.get_action(state),
                self.hierarchical.get_action(state)
            ]
            
            # Vote on action
            action_votes = {'buy': 0, 'sell': 0, 'hold': 0}
            total_confidence = 0.0
            
            for action in actions:
                action_votes[action.action_type] += action.confidence
                total_confidence += action.confidence
            
            best_action = max(action_votes, key=action_votes.get)
            avg_confidence = action_votes[best_action] / len(actions)
            
            return RLAction(best_action, confidence=avg_confidence)
    
    def update(self, state: RLState, action: RLAction, reward: float, next_state: RLState):
        """Update all RL components."""
        self.distributional.update(state, action, reward, next_state)
        self.hierarchical.update(state, action, reward)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of RL hub."""
        return {
            'distributional_quantiles': self.distributional.num_quantiles,
            'meta_params': self.meta.meta_parameters,
            'current_strategy': self.hierarchical.current_strategy
        }
