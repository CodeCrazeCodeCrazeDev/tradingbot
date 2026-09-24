"""
Multi-Armed Bandit for Strategy Selection
==========================================

Dynamic strategy selection using Thompson Sampling,
UCB, and contextual bandits for optimal exploration/exploitation.
"""

import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class BanditAlgorithm(Enum):
    """Bandit algorithm types"""
    EPSILON_GREEDY = "epsilon_greedy"
    UCB1 = "ucb1"
    UCB_TUNED = "ucb_tuned"
    THOMPSON_SAMPLING = "thompson_sampling"
    EXP3 = "exp3"
    CONTEXTUAL_LINEAR = "contextual_linear"
    CONTEXTUAL_NEURAL = "contextual_neural"


@dataclass
class ArmStatistics:
    """Statistics for a single arm (strategy)"""
    arm_id: str
    name: str
    pulls: int = 0
    total_reward: float = 0.0
    squared_reward: float = 0.0
    successes: int = 0  # For Beta distribution
    failures: int = 0
    last_reward: float = 0.0
    last_pulled: Optional[datetime] = None
    
    # For contextual bandits
    theta: Optional[np.ndarray] = None  # Linear weights
    A: Optional[np.ndarray] = None  # Design matrix
    b: Optional[np.ndarray] = None  # Reward vector
    
    @property
    def mean_reward(self) -> float:
        return self.total_reward / self.pulls if self.pulls > 0 else 0.0
    
    @property
    def variance(self) -> float:
        if self.pulls < 2:
            return float('inf')
        mean = self.mean_reward
        return (self.squared_reward / self.pulls) - (mean ** 2)
    
    @property
    def std_dev(self) -> float:
        var = self.variance
        return math.sqrt(var) if var > 0 else 0.0


@dataclass
class BanditConfig:
    """Configuration for bandit algorithms"""
    epsilon: float = 0.1  # For epsilon-greedy
    c: float = 2.0  # Exploration parameter for UCB
    gamma: float = 0.1  # For EXP3
    alpha: float = 1.0  # Prior for Thompson Sampling
    beta: float = 1.0  # Prior for Thompson Sampling
    context_dim: int = 10  # For contextual bandits
    lambda_reg: float = 1.0  # Regularization for LinUCB
    decay_rate: float = 0.999  # Reward decay for non-stationary


class MultiArmedBandit:
    """
    Multi-Armed Bandit for Strategy Selection
    
    Implements multiple bandit algorithms for optimal
    strategy selection with exploration/exploitation balance.
    """
    
    def __init__(
        self,
        algorithm: BanditAlgorithm = BanditAlgorithm.THOMPSON_SAMPLING,
        config: Optional[BanditConfig] = None
    ):
        self.algorithm = algorithm
        self.config = config or BanditConfig()
        
        self.arms: Dict[str, ArmStatistics] = {}
        self.total_pulls = 0
        self.history: List[Dict[str, Any]] = []
        
        # For EXP3
        self.exp3_weights: Dict[str, float] = {}
        
        logger.info(f"MultiArmedBandit initialized with {algorithm.value}")
    
    def add_arm(self, arm_id: str, name: str):
        """Add a new arm (strategy)"""
        
        if arm_id in self.arms:
            logger.warning(f"Arm {arm_id} already exists")
            return
        
        arm = ArmStatistics(arm_id=arm_id, name=name)
        
        # Initialize for contextual bandits
        if self.algorithm in [BanditAlgorithm.CONTEXTUAL_LINEAR, BanditAlgorithm.CONTEXTUAL_NEURAL]:
            d = self.config.context_dim
            arm.A = np.eye(d) * self.config.lambda_reg
            arm.b = np.zeros(d)
            arm.theta = np.zeros(d)
        
        self.arms[arm_id] = arm
        self.exp3_weights[arm_id] = 1.0
        
        logger.info(f"Added arm: {name} ({arm_id})")
    
    def remove_arm(self, arm_id: str):
        """Remove an arm"""
        
        if arm_id in self.arms:
            del self.arms[arm_id]
            if arm_id in self.exp3_weights:
                del self.exp3_weights[arm_id]
            logger.info(f"Removed arm: {arm_id}")
    
    def _epsilon_greedy_select(self) -> str:
        """Epsilon-greedy selection"""
        
        if random.random() < self.config.epsilon:
            # Explore
            return random.choice(list(self.arms.keys()))
        else:
            # Exploit
            return max(self.arms.keys(), key=lambda k: self.arms[k].mean_reward)
    
    def _ucb1_select(self) -> str:
        """UCB1 selection"""
        
        # Pull each arm at least once
        for arm_id, arm in self.arms.items():
            if arm.pulls == 0:
                return arm_id
        
        def ucb_value(arm: ArmStatistics) -> float:
            exploration = self.config.c * math.sqrt(
                math.log(self.total_pulls) / arm.pulls
            )
            return arm.mean_reward + exploration
        
        return max(self.arms.keys(), key=lambda k: ucb_value(self.arms[k]))
    
    def _ucb_tuned_select(self) -> str:
        """UCB-Tuned selection (variance-aware)"""
        
        for arm_id, arm in self.arms.items():
            if arm.pulls == 0:
                return arm_id
        
        def ucb_tuned_value(arm: ArmStatistics) -> float:
            log_t = math.log(self.total_pulls)
            variance_term = arm.variance + math.sqrt(2 * log_t / arm.pulls)
            exploration = math.sqrt(
                (log_t / arm.pulls) * min(0.25, variance_term)
            )
            return arm.mean_reward + exploration
        
        return max(self.arms.keys(), key=lambda k: ucb_tuned_value(self.arms[k]))
    
    def _thompson_sampling_select(self) -> str:
        """Thompson Sampling selection (Beta-Bernoulli)"""
        
        samples = {}
        
        for arm_id, arm in self.arms.items():
            # Sample from Beta distribution
            alpha = self.config.alpha + arm.successes
            beta = self.config.beta + arm.failures
            samples[arm_id] = np.random.beta(alpha, beta)
        
        return max(samples.keys(), key=lambda k: samples[k])
    
    def _thompson_sampling_gaussian_select(self) -> str:
        """Thompson Sampling with Gaussian rewards"""
        
        samples = {}
        
        for arm_id, arm in self.arms.items():
            if arm.pulls == 0:
                samples[arm_id] = float('inf')
            else:
                # Sample from posterior (Normal-Gamma)
                mean = arm.mean_reward
                std = arm.std_dev / math.sqrt(arm.pulls) if arm.pulls > 0 else 1.0
                samples[arm_id] = np.random.normal(mean, std)
        
        return max(samples.keys(), key=lambda k: samples[k])
    
    def _exp3_select(self) -> str:
        """EXP3 selection (adversarial setting)"""
        
        # Compute probabilities
        total_weight = sum(self.exp3_weights.values())
        K = len(self.arms)
        
        probs = {}
        for arm_id in self.arms:
            probs[arm_id] = (
                (1 - self.config.gamma) * (self.exp3_weights[arm_id] / total_weight) +
                self.config.gamma / K
            )
        
        # Sample according to probabilities
        r = random.random()
        cumsum = 0.0
        for arm_id, prob in probs.items():
            cumsum += prob
            if r <= cumsum:
                return arm_id
        
        return list(self.arms.keys())[-1]
    
    def _contextual_linear_select(self, context: np.ndarray) -> str:
        """LinUCB selection"""
        
        ucb_values = {}
        
        for arm_id, arm in self.arms.items():
            if arm.A is None:
                continue
            
            # Compute theta
            A_inv = np.linalg.inv(arm.A)
            theta = A_inv @ arm.b
            
            # Compute UCB
            mean = theta @ context
            std = math.sqrt(context @ A_inv @ context)
            ucb_values[arm_id] = mean + self.config.c * std
        
        return max(ucb_values.keys(), key=lambda k: ucb_values[k])
    
    def select_arm(self, context: Optional[np.ndarray] = None) -> str:
        """
        Select an arm based on the configured algorithm
        
        Args:
            context: Optional context vector for contextual bandits
        
        Returns:
            Selected arm ID
        """
        
        if not self.arms:
            raise ValueError("No arms available")
        
        if self.algorithm == BanditAlgorithm.EPSILON_GREEDY:
            return self._epsilon_greedy_select()
        
        elif self.algorithm == BanditAlgorithm.UCB1:
            return self._ucb1_select()
        
        elif self.algorithm == BanditAlgorithm.UCB_TUNED:
            return self._ucb_tuned_select()
        
        elif self.algorithm == BanditAlgorithm.THOMPSON_SAMPLING:
            return self._thompson_sampling_gaussian_select()
        
        elif self.algorithm == BanditAlgorithm.EXP3:
            return self._exp3_select()
        
        elif self.algorithm == BanditAlgorithm.CONTEXTUAL_LINEAR:
            if context is None:
                raise ValueError("Context required for contextual bandit")
            return self._contextual_linear_select(context)
        
        else:
            return random.choice(list(self.arms.keys()))
    
    def update(
        self,
        arm_id: str,
        reward: float,
        context: Optional[np.ndarray] = None,
        success: bool = True
    ):
        """
        Update arm statistics after observing reward
        
        Args:
            arm_id: ID of the pulled arm
            reward: Observed reward
            context: Context vector (for contextual bandits)
            success: Whether the pull was successful (for Beta distribution)
        """
        
        if arm_id not in self.arms:
            logger.warning(f"Unknown arm: {arm_id}")
            return
        
        arm = self.arms[arm_id]
        
        # Update basic statistics
        arm.pulls += 1
        arm.total_reward += reward
        arm.squared_reward += reward ** 2
        arm.last_reward = reward
        arm.last_pulled = datetime.utcnow()
        
        if success:
            arm.successes += 1
        else:
            arm.failures += 1
        
        self.total_pulls += 1
        
        # Update EXP3 weights
        if self.algorithm == BanditAlgorithm.EXP3:
            K = len(self.arms)
            total_weight = sum(self.exp3_weights.values())
            prob = (
                (1 - self.config.gamma) * (self.exp3_weights[arm_id] / total_weight) +
                self.config.gamma / K
            )
            estimated_reward = reward / prob
            self.exp3_weights[arm_id] *= math.exp(
                self.config.gamma * estimated_reward / K
            )
        
        # Update contextual bandit
        if self.algorithm == BanditAlgorithm.CONTEXTUAL_LINEAR and context is not None:
            arm.A += np.outer(context, context)
            arm.b += reward * context
            arm.theta = np.linalg.inv(arm.A) @ arm.b
        
        # Record history
        self.history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'arm_id': arm_id,
            'reward': reward,
            'total_pulls': self.total_pulls
        })
    
    def decay_rewards(self):
        """Apply decay to rewards for non-stationary environments"""
        
        for arm in self.arms.values():
            arm.total_reward *= self.config.decay_rate
            arm.squared_reward *= self.config.decay_rate
            arm.successes = int(arm.successes * self.config.decay_rate)
            arm.failures = int(arm.failures * self.config.decay_rate)
    
    def get_arm_rankings(self) -> List[Tuple[str, float]]:
        """Get arms ranked by estimated value"""
        
        rankings = []
        
        for arm_id, arm in self.arms.items():
            if self.algorithm == BanditAlgorithm.THOMPSON_SAMPLING:
                # Use posterior mean
                alpha = self.config.alpha + arm.successes
                beta = self.config.beta + arm.failures
                value = alpha / (alpha + beta)
            else:
                value = arm.mean_reward
            
            rankings.append((arm_id, value))
        
        return sorted(rankings, key=lambda x: x[1], reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get bandit statistics"""
        
        return {
            'algorithm': self.algorithm.value,
            'total_pulls': self.total_pulls,
            'num_arms': len(self.arms),
            'arms': {
                arm_id: {
                    'name': arm.name,
                    'pulls': arm.pulls,
                    'mean_reward': arm.mean_reward,
                    'std_dev': arm.std_dev,
                    'successes': arm.successes,
                    'failures': arm.failures
                }
                for arm_id, arm in self.arms.items()
            },
            'rankings': self.get_arm_rankings()
        }


class ContextualBandit(MultiArmedBandit):
    """
    Contextual Bandit with Neural Network
    
    Uses a neural network to learn context-reward relationships
    for more complex decision making.
    """
    
    def __init__(
        self,
        context_dim: int = 10,
        hidden_dims: List[int] = [64, 32],
        learning_rate: float = 0.01,
        exploration_bonus: float = 0.1
    ):
        super().__init__(
            algorithm=BanditAlgorithm.CONTEXTUAL_NEURAL,
            config=BanditConfig(context_dim=context_dim)
        )
        
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.exploration_bonus = exploration_bonus
        
        # Neural network weights (simplified)
        self.networks: Dict[str, Dict[str, np.ndarray]] = {}
        
        logger.info("ContextualBandit initialized")
    
    def _init_network(self, arm_id: str):
        """Initialize neural network for an arm"""
        
        dims = [self.config.context_dim] + self.hidden_dims + [1]
        
        weights = {}
        for i in range(len(dims) - 1):
            weights[f'W{i}'] = np.random.randn(dims[i], dims[i+1]) * 0.1
            weights[f'b{i}'] = np.zeros(dims[i+1])
        
        self.networks[arm_id] = weights
    
    def _forward(self, arm_id: str, context: np.ndarray) -> float:
        """Forward pass through network"""
        
        if arm_id not in self.networks:
            self._init_network(arm_id)
        
        weights = self.networks[arm_id]
        x = context
        
        for i in range(len(self.hidden_dims) + 1):
            x = x @ weights[f'W{i}'] + weights[f'b{i}']
            if i < len(self.hidden_dims):
                x = np.maximum(0, x)  # ReLU
        
        return float(x[0]) if x.shape else float(x)
    
    def _backward(self, arm_id: str, context: np.ndarray, target: float):
        """Backward pass (simplified gradient descent)"""
        
        if arm_id not in self.networks:
            return
        
        weights = self.networks[arm_id]
        prediction = self._forward(arm_id, context)
        error = target - prediction
        
        # Simple gradient update (approximate)
        for key in weights:
            if key.startswith('W'):
                weights[key] += self.learning_rate * error * 0.01 * np.random.randn(*weights[key].shape)
    
    def select_arm(self, context: np.ndarray) -> str:
        """Select arm using neural network predictions"""
        
        if not self.arms:
            raise ValueError("No arms available")
        
        values = {}
        
        for arm_id in self.arms:
            predicted_reward = self._forward(arm_id, context)
            
            # Add exploration bonus
            arm = self.arms[arm_id]
            exploration = self.exploration_bonus / math.sqrt(arm.pulls + 1)
            
            values[arm_id] = predicted_reward + exploration
        
        return max(values.keys(), key=lambda k: values[k])
    
    def update(
        self,
        arm_id: str,
        reward: float,
        context: np.ndarray,
        success: bool = True
    ):
        """Update with neural network training"""
        
        super().update(arm_id, reward, context, success)
        
        # Train network
        self._backward(arm_id, context, reward)


class NonStationaryBandit(MultiArmedBandit):
    """
    Non-Stationary Bandit with Change Detection
    
    Handles environments where reward distributions change over time.
    """
    
    def __init__(
        self,
        algorithm: BanditAlgorithm = BanditAlgorithm.UCB1,
        window_size: int = 100,
        change_threshold: float = 2.0
    ):
        super().__init__(algorithm=algorithm)
        
        self.window_size = window_size
        self.change_threshold = change_threshold
        
        # Sliding window for each arm
        self.windows: Dict[str, List[float]] = {}
        
        logger.info("NonStationaryBandit initialized")
    
    def add_arm(self, arm_id: str, name: str):
        super().add_arm(arm_id, name)
        self.windows[arm_id] = []
    
    def update(
        self,
        arm_id: str,
        reward: float,
        context: Optional[np.ndarray] = None,
        success: bool = True
    ):
        """Update with change detection"""
        
        super().update(arm_id, reward, context, success)
        
        # Update sliding window
        if arm_id not in self.windows:
            self.windows[arm_id] = []
        
        self.windows[arm_id].append(reward)
        
        if len(self.windows[arm_id]) > self.window_size:
            self.windows[arm_id].pop(0)
        
        # Check for change
        if self._detect_change(arm_id):
            logger.info(f"Change detected for arm {arm_id}, resetting statistics")
            self._reset_arm(arm_id)
    
    def _detect_change(self, arm_id: str) -> bool:
        """Detect distribution change using CUSUM"""
        
        window = self.windows[arm_id]
        if len(window) < self.window_size // 2:
            return False
        
        mid = len(window) // 2
        first_half = np.mean(window[:mid])
        second_half = np.mean(window[mid:])
        
        std = np.std(window) + 1e-6
        z_score = abs(second_half - first_half) / std
        
        return z_score > self.change_threshold
    
    def _reset_arm(self, arm_id: str):
        """Reset arm statistics after change detection"""
        
        arm = self.arms[arm_id]
        
        # Keep recent statistics only
        recent_rewards = self.windows[arm_id][-self.window_size // 2:]
        
        arm.pulls = len(recent_rewards)
        arm.total_reward = sum(recent_rewards)
        arm.squared_reward = sum(r ** 2 for r in recent_rewards)
        arm.successes = sum(1 for r in recent_rewards if r > 0)
        arm.failures = arm.pulls - arm.successes


class StrategyBandit:
    """
    High-level Strategy Selection using Bandits
    
    Integrates with trading strategies for optimal selection.
    """
    
    def __init__(
        self,
        algorithm: BanditAlgorithm = BanditAlgorithm.THOMPSON_SAMPLING,
        use_context: bool = True,
        context_features: List[str] = None
    ):
        self.use_context = use_context
        self.context_features = context_features or [
            'volatility', 'trend_strength', 'volume_ratio',
            'spread', 'momentum', 'rsi', 'macd_signal',
            'hour_of_day', 'day_of_week', 'market_regime'
        ]
        
        if use_context:
            self.bandit = ContextualBandit(
                context_dim=len(self.context_features)
            )
        else:
            self.bandit = MultiArmedBandit(algorithm=algorithm)
        
        self.strategy_map: Dict[str, str] = {}  # arm_id -> strategy_name
        
        logger.info("StrategyBandit initialized")
    
    def register_strategy(self, strategy_id: str, strategy_name: str):
        """Register a trading strategy"""
        
        self.bandit.add_arm(strategy_id, strategy_name)
        self.strategy_map[strategy_id] = strategy_name
    
    def extract_context(self, market_data: Dict[str, Any]) -> np.ndarray:
        """Extract context features from market data"""
        
        context = []
        
        for feature in self.context_features:
            value = market_data.get(feature, 0.0)
            context.append(float(value))
        
        return np.array(context)
    
    def select_strategy(self, market_data: Optional[Dict[str, Any]] = None) -> str:
        """Select best strategy for current market conditions"""
        
        if self.use_context and market_data:
            context = self.extract_context(market_data)
            arm_id = self.bandit.select_arm(context)
        else:
            arm_id = self.bandit.select_arm()
        
        return self.strategy_map.get(arm_id, arm_id)
    
    def record_outcome(
        self,
        strategy_id: str,
        profit: float,
        market_data: Optional[Dict[str, Any]] = None
    ):
        """Record strategy outcome"""
        
        # Normalize profit to [0, 1] range for better bandit performance
        normalized_reward = 1.0 / (1.0 + math.exp(-profit))  # Sigmoid
        
        context = None
        if self.use_context and market_data:
            context = self.extract_context(market_data)
        
        self.bandit.update(
            strategy_id,
            normalized_reward,
            context=context,
            success=profit > 0
        )
    
    def get_strategy_rankings(self) -> List[Tuple[str, float]]:
        """Get strategies ranked by performance"""
        
        rankings = self.bandit.get_arm_rankings()
        return [(self.strategy_map.get(arm_id, arm_id), value) for arm_id, value in rankings]
    
    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive report"""
        
        stats = self.bandit.get_statistics()
        stats['strategy_rankings'] = self.get_strategy_rankings()
        return stats


# Convenience functions
def create_strategy_bandit(
    strategies: List[Tuple[str, str]],
    algorithm: str = "thompson_sampling",
    use_context: bool = True
) -> StrategyBandit:
    """Create and initialize a strategy bandit"""
    
    algo_map = {
        'epsilon_greedy': BanditAlgorithm.EPSILON_GREEDY,
        'ucb1': BanditAlgorithm.UCB1,
        'ucb_tuned': BanditAlgorithm.UCB_TUNED,
        'thompson_sampling': BanditAlgorithm.THOMPSON_SAMPLING,
        'exp3': BanditAlgorithm.EXP3
    }
    
    bandit = StrategyBandit(
        algorithm=algo_map.get(algorithm, BanditAlgorithm.THOMPSON_SAMPLING),
        use_context=use_context
    )
    
    for strategy_id, strategy_name in strategies:
        bandit.register_strategy(strategy_id, strategy_name)
    
    return bandit
