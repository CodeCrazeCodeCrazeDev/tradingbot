"""
Policy and Value Networks - DeepMind AlphaGo/AlphaZero Pattern

Implements the dual-network architecture from AlphaGo:
- Policy Network: Predicts probability distribution over actions (what to do)
- Value Network: Estimates expected outcome from current state (how good)

This is the core of DeepMind's approach to game-playing AI:
1. Policy network suggests promising moves (reduces search space)
2. Value network evaluates positions (replaces rollouts)
3. Combined with MCTS for powerful decision-making

Reference: "Mastering the game of Go with deep neural networks and tree search" (Silver et al., 2016)
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import numpy as np
import uuid

logger = logging.getLogger(__name__)


@dataclass
class PolicyOutput:
    """Output from the policy network"""
    actions: List[Dict[str, Any]]  # Possible actions
    probabilities: Dict[str, float]  # Action -> probability
    top_action: Dict[str, Any]  # Most likely action
    entropy: float  # Uncertainty in the distribution
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValueOutput:
    """Output from the value network"""
    value: float  # Expected value (-1 to 1 or 0 to 1)
    confidence: float  # Confidence in the estimate
    uncertainty: float  # Epistemic uncertainty
    features_used: List[str]  # Which features contributed most
    timestamp: datetime = field(default_factory=datetime.now)


class PolicyNetwork:
    """
    Policy Network - DeepMind AlphaGo Pattern
    
    The policy network takes a state and outputs a probability distribution
    over possible actions. This is used to:
    1. Guide MCTS search (focus on promising moves)
    2. Provide action suggestions
    3. Learn from successful trajectories
    
    Architecture (conceptual):
    ┌─────────────────────────────────────────────────────────────┐
    │                    POLICY NETWORK                            │
    │                                                              │
    │  Input: State features (market, portfolio, risk)            │
    │         ↓                                                    │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │  Feature Extraction (CNN/Transformer)                │    │
    │  │  - Market patterns                                   │    │
    │  │  - Portfolio state                                   │    │
    │  │  - Historical context                                │    │
    │  └─────────────────────────────────────────────────────┘    │
    │         ↓                                                    │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │  Policy Head (Softmax over actions)                  │    │
    │  │  - Trade actions (buy/sell/hold)                     │    │
    │  │  - Position sizing                                   │    │
    │  │  - Risk adjustments                                  │    │
    │  └─────────────────────────────────────────────────────┘    │
    │         ↓                                                    │
    │  Output: P(action | state) for all actions                  │
    └─────────────────────────────────────────────────────────────┘
    
    In production, this would be a neural network (PyTorch/TensorFlow).
    Here we implement a rule-based version that can be replaced.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        self.config = config or {}
        
        # Action space definition
        self.action_types = [
            'buy', 'sell', 'hold',
            'increase_position', 'decrease_position',
            'set_stop_loss', 'set_take_profit',
            'hedge', 'rebalance',
            'research', 'wait'
        ]
        
        # Learning parameters
        self.learning_rate = self.config.get('learning_rate', 0.001)
        self.temperature = self.config.get('temperature', 1.0)  # For softmax
        
        # Experience replay
        self.experience_buffer: List[Dict] = []
        self.max_buffer_size = self.config.get('max_buffer_size', 10000)
        
        # Policy weights (simplified - would be neural network weights)
        self.action_weights: Dict[str, float] = {
            action: 1.0 / len(self.action_types) 
            for action in self.action_types
        }
        
        # Feature importance
        self.feature_weights: Dict[str, float] = {
            'trend': 0.2,
            'volatility': 0.15,
            'momentum': 0.15,
            'risk': 0.2,
            'opportunity': 0.15,
            'portfolio_state': 0.15
        }
        
        logger.info("Policy Network initialized")
    
    async def initialize(self):
        """Initialize the policy network"""
        # In production: load pre-trained weights
        logger.info("Policy Network ready")
    
    async def predict(self, context) -> PolicyOutput:
        """
        Predict action probabilities given current state.
        
        This is the forward pass of the policy network.
        
        Args:
            context: SystemContext with current state
            
        Returns:
            PolicyOutput with action probabilities
        """
        # Extract features from context
        features = self._extract_features(context)
        
        # Compute action scores (simplified - would be neural network forward pass)
        action_scores = self._compute_action_scores(features)
        
        # Apply softmax to get probabilities
        probabilities = self._softmax(action_scores)
        
        # Generate action details
        actions = self._generate_actions(probabilities, features)
        
        # Find top action
        top_action_type = max(probabilities, key=probabilities.get)
        top_action = next(
            (a for a in actions if a.get('type') == top_action_type),
            actions[0] if actions else {'type': 'hold'}
        )
        
        # Calculate entropy (uncertainty)
        entropy = self._calculate_entropy(probabilities)
        
        return PolicyOutput(
            actions=actions,
            probabilities=probabilities,
            top_action=top_action,
            entropy=entropy
        )
    
    def _extract_features(self, context) -> Dict[str, float]:
        """Extract features from context for policy network"""
        features = {}
        
        # Market features
        market_state = getattr(context, 'market_state', {})
        if isinstance(market_state, dict):
            features['price'] = market_state.get('price', 0)
            features['volatility'] = market_state.get('volatility', 0)
            features['trend'] = self._encode_trend(market_state.get('trend', 'neutral'))
            features['momentum'] = market_state.get('momentum', 0)
        
        # Portfolio features
        portfolio_state = getattr(context, 'portfolio_state', {})
        if isinstance(portfolio_state, dict):
            features['equity'] = portfolio_state.get('equity', 0)
            features['exposure'] = portfolio_state.get('exposure', 0)
            features['pnl'] = portfolio_state.get('pnl', 0)
            features['drawdown'] = portfolio_state.get('drawdown', 0)
        
        # Risk features
        risk_metrics = getattr(context, 'risk_metrics', {})
        if isinstance(risk_metrics, dict):
            features['var'] = risk_metrics.get('var', 0)
            features['sharpe'] = risk_metrics.get('sharpe', 0)
            features['risk_score'] = risk_metrics.get('risk_score', 0.5)
        
        # Normalize features
        features = self._normalize_features(features)
        
        return features
    
    def _encode_trend(self, trend: str) -> float:
        """Encode trend as numeric value"""
        trend_map = {
            'strong_bullish': 1.0,
            'bullish': 0.5,
            'neutral': 0.0,
            'bearish': -0.5,
            'strong_bearish': -1.0
        }
        return trend_map.get(trend, 0.0)
    
    def _normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Normalize features to [-1, 1] range"""
        normalized = {}
        for key, value in features.items():
            if isinstance(value, (int, float)):
                # Simple normalization (would use running statistics in production)
                normalized[key] = np.tanh(value)
            else:
                normalized[key] = 0.0
        return normalized
    
    def _compute_action_scores(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Compute scores for each action based on features.
        
        This is a simplified version - in production would be neural network.
        """
        scores = {}
        
        trend = features.get('trend', 0)
        volatility = features.get('volatility', 0)
        exposure = features.get('exposure', 0)
        risk_score = features.get('risk_score', 0.5)
        pnl = features.get('pnl', 0)
        
        # Buy score: higher when bullish, low exposure, low risk
        scores['buy'] = (
            0.3 * max(trend, 0) +
            0.2 * (1 - abs(exposure)) +
            0.2 * (1 - risk_score) +
            0.1 * self.action_weights['buy']
        )
        
        # Sell score: higher when bearish or high exposure
        scores['sell'] = (
            0.3 * max(-trend, 0) +
            0.2 * abs(exposure) +
            0.2 * risk_score +
            0.1 * self.action_weights['sell']
        )
        
        # Hold score: higher when uncertain or neutral
        scores['hold'] = (
            0.3 * (1 - abs(trend)) +
            0.2 * (1 - volatility) +
            0.2 * (1 - risk_score) +
            0.1 * self.action_weights['hold']
        )
        
        # Increase position: when profitable and bullish
        scores['increase_position'] = (
            0.3 * max(trend, 0) +
            0.2 * max(pnl, 0) +
            0.2 * (1 - risk_score) +
            0.1 * self.action_weights['increase_position']
        )
        
        # Decrease position: when losing or high risk
        scores['decrease_position'] = (
            0.3 * max(-pnl, 0) +
            0.2 * risk_score +
            0.2 * volatility +
            0.1 * self.action_weights['decrease_position']
        )
        
        # Stop loss: when volatile or risky
        scores['set_stop_loss'] = (
            0.3 * volatility +
            0.2 * risk_score +
            0.2 * abs(exposure) +
            0.1 * self.action_weights['set_stop_loss']
        )
        
        # Take profit: when profitable
        scores['set_take_profit'] = (
            0.4 * max(pnl, 0) +
            0.2 * max(trend, 0) +
            0.1 * self.action_weights['set_take_profit']
        )
        
        # Hedge: when high exposure and volatile
        scores['hedge'] = (
            0.3 * abs(exposure) +
            0.3 * volatility +
            0.1 * self.action_weights['hedge']
        )
        
        # Rebalance: when portfolio drifted
        scores['rebalance'] = (
            0.3 * abs(exposure - 0.5) +
            0.2 * (1 - volatility) +
            0.1 * self.action_weights['rebalance']
        )
        
        # Research: when uncertain
        scores['research'] = (
            0.3 * (1 - abs(trend)) +
            0.2 * volatility +
            0.1 * self.action_weights['research']
        )
        
        # Wait: when no clear signal
        scores['wait'] = (
            0.3 * (1 - abs(trend)) +
            0.2 * (1 - volatility) +
            0.1 * self.action_weights['wait']
        )
        
        return scores
    
    def _softmax(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Apply softmax to convert scores to probabilities"""
        # Apply temperature
        scaled_scores = {
            k: v / self.temperature 
            for k, v in scores.items()
        }
        
        # Compute softmax
        max_score = max(scaled_scores.values())
        exp_scores = {
            k: np.exp(v - max_score)  # Subtract max for numerical stability
            for k, v in scaled_scores.items()
        }
        
        total = sum(exp_scores.values())
        probabilities = {
            k: v / total 
            for k, v in exp_scores.items()
        }
        
        return probabilities
    
    def _generate_actions(
        self, 
        probabilities: Dict[str, float],
        features: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate detailed action specifications"""
        actions = []
        
        for action_type, prob in probabilities.items():
            if prob < 0.01:  # Skip very low probability actions
                continue
            
            action = {
                'type': action_type,
                'probability': prob,
                'parameters': self._generate_action_parameters(action_type, features)
            }
            actions.append(action)
        
        # Sort by probability
        actions.sort(key=lambda x: x['probability'], reverse=True)
        
        return actions
    
    def _generate_action_parameters(
        self, 
        action_type: str,
        features: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate parameters for an action"""
        params = {}
        
        if action_type in ['buy', 'sell']:
            # Position sizing based on risk
            risk_score = features.get('risk_score', 0.5)
            params['size'] = 0.02 * (1 - risk_score)  # 0-2% based on risk
            params['order_type'] = 'limit'
            
        elif action_type in ['increase_position', 'decrease_position']:
            params['adjustment'] = 0.5  # 50% adjustment
            
        elif action_type == 'set_stop_loss':
            volatility = features.get('volatility', 0.01)
            params['stop_distance'] = volatility * 2  # 2x volatility
            
        elif action_type == 'set_take_profit':
            params['target_profit'] = 0.02  # 2% target
            
        elif action_type == 'hedge':
            exposure = features.get('exposure', 0)
            params['hedge_ratio'] = abs(exposure) * 0.5  # Hedge 50% of exposure
            
        elif action_type == 'rebalance':
            params['target_allocation'] = {'cash': 0.3, 'positions': 0.7}
        
        return params
    
    def _calculate_entropy(self, probabilities: Dict[str, float]) -> float:
        """Calculate entropy of the probability distribution"""
        entropy = 0.0
        for prob in probabilities.values():
            if prob > 0:
                entropy -= prob * np.log(prob + 1e-10)
        return entropy
    
    async def reinforce(self, action: Dict[str, Any], reward: float):
        """
        Reinforce the policy based on reward.
        
        This implements policy gradient update (simplified).
        In production: would use PPO, A2C, or similar.
        """
        action_type = action.get('type', 'hold')
        
        if action_type in self.action_weights:
            # Simple weight update (would be gradient descent in production)
            self.action_weights[action_type] += self.learning_rate * reward
            
            # Normalize weights
            total = sum(self.action_weights.values())
            self.action_weights = {
                k: v / total 
                for k, v in self.action_weights.items()
            }
        
        # Store experience
        self.experience_buffer.append({
            'action': action,
            'reward': reward,
            'timestamp': datetime.now()
        })
        
        # Trim buffer
        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer = self.experience_buffer[-self.max_buffer_size:]
        
        logger.debug(f"Reinforced action {action_type} with reward {reward}")
    
    async def train(self, batch_size: int = 32):
        """
        Train the policy network on experience buffer.
        
        In production: would do proper neural network training.
        """
        if len(self.experience_buffer) < batch_size:
            return
        
        # Sample batch
        indices = np.random.choice(
            len(self.experience_buffer), 
            size=batch_size, 
            replace=False
        )
        
        batch = [self.experience_buffer[i] for i in indices]
        
        # Update weights based on batch
        for experience in batch:
            action_type = experience['action'].get('type', 'hold')
            reward = experience['reward']
            
            if action_type in self.action_weights:
                self.action_weights[action_type] += self.learning_rate * reward * 0.1
        
        # Normalize
        total = sum(self.action_weights.values())
        self.action_weights = {
            k: max(v / total, 0.01)  # Minimum probability
            for k, v in self.action_weights.items()
        }
        
        logger.info(f"Trained policy network on batch of {batch_size}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get policy network status"""
        return {
            'action_weights': self.action_weights,
            'experience_buffer_size': len(self.experience_buffer),
            'temperature': self.temperature,
            'learning_rate': self.learning_rate
        }


class ValueNetwork:
    """
    Value Network - DeepMind AlphaGo Pattern
    
    The value network takes a state and outputs an estimate of the
    expected outcome (value). This is used to:
    1. Evaluate positions without full rollouts
    2. Guide search towards promising states
    3. Learn from game outcomes
    
    Architecture (conceptual):
    ┌─────────────────────────────────────────────────────────────┐
    │                    VALUE NETWORK                             │
    │                                                              │
    │  Input: State features (same as policy network)             │
    │         ↓                                                    │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │  Feature Extraction (shared with policy)             │    │
    │  └─────────────────────────────────────────────────────┘    │
    │         ↓                                                    │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │  Value Head (single output)                          │    │
    │  │  - Expected return                                   │    │
    │  │  - Confidence estimate                               │    │
    │  └─────────────────────────────────────────────────────┘    │
    │         ↓                                                    │
    │  Output: V(s) ∈ [-1, 1] (expected outcome)                  │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        self.config = config or {}
        
        # Learning parameters
        self.learning_rate = self.config.get('learning_rate', 0.001)
        
        # Value estimation weights (simplified)
        self.feature_weights: Dict[str, float] = {
            'trend': 0.2,
            'momentum': 0.15,
            'pnl': 0.25,
            'sharpe': 0.15,
            'risk_adjusted_return': 0.15,
            'drawdown': -0.1  # Negative weight for drawdown
        }
        
        # Experience for learning
        self.value_history: List[Dict] = []
        self.max_history = self.config.get('max_history', 10000)
        
        # Running statistics for normalization
        self.value_mean = 0.0
        self.value_std = 1.0
        self.update_count = 0
        
        logger.info("Value Network initialized")
    
    async def initialize(self):
        """Initialize the value network"""
        logger.info("Value Network ready")
    
    async def evaluate(self, context) -> float:
        """
        Evaluate a state and return expected value.
        
        This is the forward pass of the value network.
        
        Args:
            context: SystemContext or simulated state
            
        Returns:
            Expected value in range [0, 1]
        """
        # Extract features
        features = self._extract_features(context)
        
        # Compute value (simplified - would be neural network)
        raw_value = self._compute_value(features)
        
        # Normalize to [0, 1]
        value = self._normalize_value(raw_value)
        
        return value
    
    async def evaluate_with_uncertainty(self, context) -> ValueOutput:
        """
        Evaluate with uncertainty estimation.
        
        Returns full ValueOutput including confidence.
        """
        features = self._extract_features(context)
        raw_value = self._compute_value(features)
        value = self._normalize_value(raw_value)
        
        # Estimate uncertainty (simplified)
        uncertainty = self._estimate_uncertainty(features)
        confidence = 1.0 - uncertainty
        
        # Identify important features
        important_features = self._get_important_features(features)
        
        return ValueOutput(
            value=value,
            confidence=confidence,
            uncertainty=uncertainty,
            features_used=important_features
        )
    
    def _extract_features(self, context) -> Dict[str, float]:
        """Extract features for value estimation"""
        features = {}
        
        # Handle both SystemContext and dict
        if hasattr(context, 'market_state'):
            market_state = context.market_state
            portfolio_state = context.portfolio_state
            risk_metrics = context.risk_metrics
        elif isinstance(context, dict):
            market_state = context.get('market_state', {})
            portfolio_state = context.get('portfolio_state', {})
            risk_metrics = context.get('risk_metrics', {})
        else:
            market_state = {}
            portfolio_state = {}
            risk_metrics = {}
        
        # Market features
        if isinstance(market_state, dict):
            features['trend'] = self._encode_trend(market_state.get('trend', 'neutral'))
            features['momentum'] = market_state.get('momentum', 0)
            features['volatility'] = market_state.get('volatility', 0)
        
        # Portfolio features
        if isinstance(portfolio_state, dict):
            features['pnl'] = portfolio_state.get('pnl', 0)
            features['drawdown'] = portfolio_state.get('drawdown', 0)
            features['exposure'] = portfolio_state.get('exposure', 0)
        
        # Risk features
        if isinstance(risk_metrics, dict):
            features['sharpe'] = risk_metrics.get('sharpe', 0)
            features['var'] = risk_metrics.get('var', 0)
            
            # Compute risk-adjusted return
            pnl = features.get('pnl', 0)
            var = features.get('var', 0.01)
            features['risk_adjusted_return'] = pnl / (var + 0.001)
        
        return features
    
    def _encode_trend(self, trend: str) -> float:
        """Encode trend as numeric"""
        trend_map = {
            'strong_bullish': 1.0,
            'bullish': 0.5,
            'neutral': 0.0,
            'bearish': -0.5,
            'strong_bearish': -1.0
        }
        return trend_map.get(trend, 0.0)
    
    def _compute_value(self, features: Dict[str, float]) -> float:
        """
        Compute raw value from features.
        
        Simplified linear combination - would be neural network.
        """
        value = 0.0
        
        for feature_name, weight in self.feature_weights.items():
            feature_value = features.get(feature_name, 0)
            value += weight * feature_value
        
        return value
    
    def _normalize_value(self, raw_value: float) -> float:
        """Normalize value to [0, 1] range"""
        # Use tanh for smooth normalization
        normalized = (np.tanh(raw_value) + 1) / 2
        return float(np.clip(normalized, 0, 1))
    
    def _estimate_uncertainty(self, features: Dict[str, float]) -> float:
        """
        Estimate epistemic uncertainty.
        
        Higher uncertainty when:
        - Features are extreme
        - Limited experience with similar states
        """
        uncertainty = 0.2  # Base uncertainty
        
        # Higher uncertainty for extreme values
        for value in features.values():
            if isinstance(value, (int, float)):
                if abs(value) > 2:
                    uncertainty += 0.1
        
        # Higher uncertainty with less experience
        if self.update_count < 100:
            uncertainty += 0.2
        elif self.update_count < 1000:
            uncertainty += 0.1
        
        return min(uncertainty, 0.9)
    
    def _get_important_features(self, features: Dict[str, float]) -> List[str]:
        """Get most important features for this evaluation"""
        # Sort by absolute contribution
        contributions = [
            (name, abs(features.get(name, 0) * self.feature_weights.get(name, 0)))
            for name in self.feature_weights
        ]
        contributions.sort(key=lambda x: x[1], reverse=True)
        
        return [name for name, _ in contributions[:3]]
    
    async def update(self, context, actual_value: float):
        """
        Update value network with actual outcome.
        
        This is the learning step - adjusts weights based on
        prediction error.
        """
        # Get prediction
        features = self._extract_features(context)
        predicted_value = self._compute_value(features)
        
        # Compute error
        error = actual_value - predicted_value
        
        # Update weights (simplified gradient descent)
        for feature_name in self.feature_weights:
            feature_value = features.get(feature_name, 0)
            if isinstance(feature_value, (int, float)):
                gradient = error * feature_value
                self.feature_weights[feature_name] += self.learning_rate * gradient
        
        # Update running statistics
        self.update_count += 1
        alpha = 0.01  # Exponential moving average factor
        self.value_mean = (1 - alpha) * self.value_mean + alpha * actual_value
        self.value_std = (1 - alpha) * self.value_std + alpha * abs(actual_value - self.value_mean)
        
        # Store in history
        self.value_history.append({
            'predicted': predicted_value,
            'actual': actual_value,
            'error': error,
            'timestamp': datetime.now()
        })
        
        # Trim history
        if len(self.value_history) > self.max_history:
            self.value_history = self.value_history[-self.max_history:]
        
        logger.debug(f"Updated value network: error={error:.4f}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get value network status"""
        recent_errors = [
            h['error'] for h in self.value_history[-100:]
        ] if self.value_history else [0]
        
        return {
            'feature_weights': self.feature_weights,
            'update_count': self.update_count,
            'mean_recent_error': np.mean(recent_errors),
            'value_mean': self.value_mean,
            'value_std': self.value_std
        }


class DualNetwork:
    """
    Combined Policy-Value Network - AlphaZero Pattern
    
    In AlphaZero, policy and value networks share a common trunk
    (feature extraction) and have separate heads. This improves
    efficiency and allows shared learning.
    
    ┌─────────────────────────────────────────────────────────────┐
    │                    DUAL NETWORK                              │
    │                                                              │
    │  Input: State                                                │
    │         ↓                                                    │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │           Shared Feature Extraction                  │    │
    │  │  (Would be ResNet/Transformer in production)         │    │
    │  └─────────────────────────────────────────────────────┘    │
    │         ↓                                                    │
    │    ┌────┴────┐                                              │
    │    ↓         ↓                                              │
    │  ┌─────┐  ┌─────┐                                           │
    │  │Policy│  │Value│                                           │
    │  │Head  │  │Head │                                           │
    │  └──┬──┘  └──┬──┘                                           │
    │     ↓        ↓                                               │
    │  P(a|s)    V(s)                                             │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        self.config = config or {}
        self.config = config or {}
        self.policy_network = PolicyNetwork(config)
        self.value_network = ValueNetwork(config)
        
        logger.info("Dual Network (Policy + Value) initialized")
    
    async def initialize(self):
        """Initialize both networks"""
        await self.policy_network.initialize()
        await self.value_network.initialize()
        logger.info("Dual Network ready")
    
    async def predict(self, context) -> Tuple[PolicyOutput, ValueOutput]:
        """
        Get both policy and value predictions.
        
        Returns:
            Tuple of (PolicyOutput, ValueOutput)
        """
        # In production, would share feature extraction
        policy_output = await self.policy_network.predict(context)
        value_output = await self.value_network.evaluate_with_uncertainty(context)
        
        return policy_output, value_output
    
    async def update(self, context, action: Dict, reward: float):
        """Update both networks"""
        await self.policy_network.reinforce(action, reward)
        await self.value_network.update(context, reward)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of both networks"""
        return {
            'policy': self.policy_network.get_status(),
            'value': self.value_network.get_status()
        }
