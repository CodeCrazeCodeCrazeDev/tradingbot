"""
Skill #30: Inverse RL Policy Extractor
======================================

Extracts trading policies from expert behavior using
inverse reinforcement learning.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExpertTrajectory:
    """Expert trading trajectory."""
    states: np.ndarray
    actions: List[int]
    rewards: List[float]
    total_return: float


@dataclass
class LearnedReward:
    """Learned reward function."""
    weights: np.ndarray
    feature_names: List[str]
    explained_variance: float


@dataclass
class InverseRLResult:
    """Inverse RL result."""
    learned_reward: LearnedReward
    extracted_policy: Dict[str, float]
    expert_similarity: float
    recommended_action: int
    trading_signal: str
    confidence: float


class InverseRLPolicyExtractor:
    """Inverse RL for extracting expert trading policies."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.num_features = self.config.get('num_features', 10)
            self.learning_rate = self.config.get('learning_rate', 0.01)
            self.expert_trajectories: List[ExpertTrajectory] = []
            self.reward_weights = np.random.randn(self.num_features) * 0.1
            logger.info("InverseRLPolicyExtractor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_expert_trajectory(
        self,
        prices: np.ndarray,
        actions: List[int],
        returns: List[float]
    ):
        """Add expert trading trajectory."""
        try:
            states = self._extract_states(prices)
            total_return = sum(returns)
        
            self.expert_trajectories.append(ExpertTrajectory(
                states=states,
                actions=actions,
                rewards=returns,
                total_return=total_return
            ))
        except Exception as e:
            logger.error(f"Error in add_expert_trajectory: {e}")
            raise
    
    def learn_reward(self, iterations: int = 100) -> LearnedReward:
        """Learn reward function from expert trajectories."""
        try:
            if not self.expert_trajectories:
                return LearnedReward(
                    weights=self.reward_weights,
                    feature_names=self._get_feature_names(),
                    explained_variance=0
                )
        
            # Maximum entropy IRL (simplified)
            for _ in range(iterations):
                gradient = np.zeros(self.num_features)
            
                for traj in self.expert_trajectories:
                    # Expert feature expectations
                    expert_features = np.mean(traj.states, axis=0)
                
                    # Policy feature expectations (simplified)
                    policy_features = self._compute_policy_features(traj.states)
                
                    # Gradient
                    gradient += expert_features - policy_features
            
                gradient /= len(self.expert_trajectories)
                self.reward_weights += self.learning_rate * gradient
        
            # Calculate explained variance
            explained_var = self._calculate_explained_variance()
        
            return LearnedReward(
                weights=self.reward_weights,
                feature_names=self._get_feature_names(),
                explained_variance=explained_var
            )
        except Exception as e:
            logger.error(f"Error in learn_reward: {e}")
            raise
    
    def extract_policy(self, prices: np.ndarray) -> InverseRLResult:
        """Extract policy for current market state."""
        try:
            if len(prices) < 20:
                return self._create_empty_result()
        
            # Learn reward if not done
            learned_reward = self.learn_reward()
        
            # Get current state
            states = self._extract_states(prices)
            current_state = states[-1] if len(states) > 0 else np.zeros(self.num_features)
        
            # Compute action values
            action_values = self._compute_action_values(current_state)
        
            # Extract policy
            policy = {
                'hold': float(action_values[0]),
                'buy': float(action_values[1]),
                'sell': float(action_values[2])
            }
        
            # Best action
            best_action = int(np.argmax(action_values))
        
            # Expert similarity
            similarity = self._compute_expert_similarity(current_state)
        
            # Confidence
            confidence = self._compute_confidence(action_values, similarity)
        
            signal = self._generate_signal(best_action, confidence, policy)
        
            return InverseRLResult(
                learned_reward=learned_reward,
                extracted_policy=policy,
                expert_similarity=similarity,
                recommended_action=best_action,
                trading_signal=signal,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in extract_policy: {e}")
            raise
    
    def _extract_states(self, prices: np.ndarray) -> np.ndarray:
        """Extract state features from prices."""
        try:
            if len(prices) < 20:
                return np.zeros((1, self.num_features))
        
            states = []
            returns = np.diff(prices) / prices[:-1]
        
            for i in range(20, len(prices)):
                window = returns[i-20:i]
                state = np.array([
                    np.mean(window),
                    np.std(window),
                    np.min(window),
                    np.max(window),
                    window[-1],
                    np.mean(window[-5:]),
                    np.std(window[-5:]),
                    prices[i] / prices[i-20] - 1,
                    prices[i] / prices[i-5] - 1,
                    np.sign(window[-1])
                ])
                states.append(state)
        
            return np.array(states) if states else np.zeros((1, self.num_features))
        except Exception as e:
            logger.error(f"Error in _extract_states: {e}")
            raise
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names."""
        return [
            'mean_return', 'volatility', 'min_return', 'max_return',
            'last_return', 'recent_mean', 'recent_vol',
            'trend_20', 'trend_5', 'direction'
        ]
    
    def _compute_policy_features(self, states: np.ndarray) -> np.ndarray:
        """Compute expected features under current policy."""
        # Simplified: use softmax policy
        try:
            features = np.zeros(self.num_features)
        
            for state in states:
                reward = np.dot(state, self.reward_weights)
                prob = 1 / (1 + np.exp(-reward))
                features += state * prob
        
            return features / len(states) if len(states) > 0 else features
        except Exception as e:
            logger.error(f"Error in _compute_policy_features: {e}")
            raise
    
    def _compute_action_values(self, state: np.ndarray) -> np.ndarray:
        """Compute action values for state."""
        try:
            base_reward = np.dot(state, self.reward_weights)
        
            # Action-specific adjustments
            hold_value = base_reward * 0.1
            buy_value = base_reward if base_reward > 0 else base_reward * 0.5
            sell_value = -base_reward if base_reward < 0 else -base_reward * 0.5
        
            return np.array([hold_value, buy_value, sell_value])
        except Exception as e:
            logger.error(f"Error in _compute_action_values: {e}")
            raise
    
    def _compute_expert_similarity(self, state: np.ndarray) -> float:
        """Compute similarity to expert states."""
        try:
            if not self.expert_trajectories:
                return 0.0
        
            similarities = []
            for traj in self.expert_trajectories:
                for expert_state in traj.states:
                    sim = np.dot(state, expert_state) / (
                        np.linalg.norm(state) * np.linalg.norm(expert_state) + 1e-10
                    )
                    similarities.append(sim)
        
            return float(np.max(similarities)) if similarities else 0.0
        except Exception as e:
            logger.error(f"Error in _compute_expert_similarity: {e}")
            raise
    
    def _compute_confidence(self, action_values: np.ndarray, similarity: float) -> float:
        """Compute confidence in recommendation."""
        # Higher difference between best and second best = higher confidence
        try:
            sorted_values = np.sort(action_values)[::-1]
            value_gap = sorted_values[0] - sorted_values[1] if len(sorted_values) > 1 else 0
        
            confidence = min(0.9, 0.3 + value_gap * 2 + similarity * 0.3)
            return max(0.1, confidence)
        except Exception as e:
            logger.error(f"Error in _compute_confidence: {e}")
            raise
    
    def _calculate_explained_variance(self) -> float:
        """Calculate how well learned reward explains expert behavior."""
        try:
            if not self.expert_trajectories:
                return 0.0
        
            total_var = 0
            explained_var = 0
        
            for traj in self.expert_trajectories:
                actual_rewards = traj.rewards
                predicted_rewards = [np.dot(s, self.reward_weights) for s in traj.states]
            
                if len(actual_rewards) == len(predicted_rewards):
                    total_var += np.var(actual_rewards)
                    residual_var = np.var(np.array(actual_rewards) - np.array(predicted_rewards))
                    explained_var += total_var - residual_var
        
            return explained_var / (total_var + 1e-10) if total_var > 0 else 0
        except Exception as e:
            logger.error(f"Error in _calculate_explained_variance: {e}")
            raise
    
    def _generate_signal(
        self,
        action: int,
        confidence: float,
        policy: Dict[str, float]
    ) -> str:
        """Generate trading signal."""
        try:
            action_names = ['HOLD', 'BUY', 'SELL']
            action_name = action_names[action]
        
            if confidence < 0.4:
                return f"LOW CONFIDENCE ({confidence:.0%}): Expert policy unclear"
        
            return f"{action_name}: Expert policy suggests {action_name.lower()} ({confidence:.0%} confidence)"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> InverseRLResult:
        """Create empty result."""
        return InverseRLResult(
            learned_reward=LearnedReward(np.zeros(self.num_features), [], 0),
            extracted_policy={},
            expert_similarity=0,
            recommended_action=0,
            trading_signal="Insufficient data",
            confidence=0
        )
