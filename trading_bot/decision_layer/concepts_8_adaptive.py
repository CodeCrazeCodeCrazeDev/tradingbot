"""
Adaptive Learning Decisions (Concepts 71-80)
ML-powered and learning-based approaches.
"""

import math
import random
import statistics
from collections import deque
from typing import Dict, List, Tuple

from .core_types import (
    DecisionConcept, DecisionContext, DecisionResult,
    DecisionCategory, DecisionAction, DecisionUrgency
)

import logging
logger = logging.getLogger(__name__)



class OnlineLearningDecision(DecisionConcept):
    """Concept 71: Online Learning - Learn from each trade"""
    
    def __init__(self):
        try:
            super().__init__(71, "Online Learning", DecisionCategory.ADAPTIVE)
            self.weights = {'trend': 0.33, 'momentum': 0.33, 'sentiment': 0.33}
            self.learning_rate = 0.1
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Weighted signal
        try:
            signal = (self.weights['trend'] * context.trend +
                     self.weights['momentum'] * context.momentum +
                     self.weights['sentiment'] * context.sentiment)
        
            # Update weights based on recent performance
            if context.win_rate > 0.5:
                # Reinforce current weights
                pass
            else:
                # Adjust toward better performing features
                if abs(context.trend) > abs(context.momentum):
                    self.weights['trend'] += self.learning_rate * 0.1
                    self.weights['momentum'] -= self.learning_rate * 0.05
                else:
                    self.weights['momentum'] += self.learning_rate * 0.1
                    self.weights['trend'] -= self.learning_rate * 0.05
        
            # Normalize weights
            total = sum(self.weights.values())
            self.weights = {k: v / total for k, v in self.weights.items()}
        
            return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
                f"Weights: {self.weights}", {'signal': signal, 'weights': dict(self.weights)})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class ReinforcementDecision(DecisionConcept):
    """Concept 72: Reinforcement Learning - Q-learning inspired"""
    
    def __init__(self):
        try:
            super().__init__(72, "Reinforcement Learning", DecisionCategory.ADAPTIVE)
            self.q_table: Dict[Tuple, Dict[str, float]] = {}
            self.alpha = 0.1
            self.gamma = 0.9
            self.epsilon = 0.1
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Discretize state
        try:
            state = (
                round(context.trend, 1),
                round(context.momentum, 1),
                'high' if context.volatility > 0.3 else 'low'
            )
        
            # Initialize Q-values if new state
            if state not in self.q_table:
                self.q_table[state] = {'buy': 0.0, 'sell': 0.0, 'hold': 0.0}
        
            # Epsilon-greedy action selection
            if random.random() < self.epsilon:
                action_str = random.choice(['buy', 'sell', 'hold'])
            else:
                action_str = max(self.q_table[state], key=self.q_table[state].get)
        
            # Map to action
            action = DecisionAction.BUY if action_str == 'buy' else (DecisionAction.SELL if action_str == 'sell' else DecisionAction.HOLD)
        
            # Simulated reward update (in real system, would use actual P&L)
            reward = context.trend * (1 if action_str == 'buy' else (-1 if action_str == 'sell' else 0))
            self.q_table[state][action_str] += self.alpha * (reward - self.q_table[state][action_str])
        
            return self._create_result(action, max(self.q_table[state].values()) + 0.5, DecisionUrgency.NORMAL,
                f"Q[{action_str}]={self.q_table[state][action_str]:.3f}", {'state': str(state), 'q_values': self.q_table[state]})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class BanditDecision(DecisionConcept):
    """Concept 73: Multi-Armed Bandit - Explore vs exploit"""
    
    def __init__(self):
        try:
            super().__init__(73, "Multi-Armed Bandit", DecisionCategory.ADAPTIVE)
            self.arms = {'trend': {'pulls': 1, 'reward': 0.5}, 'momentum': {'pulls': 1, 'reward': 0.5}, 'contrarian': {'pulls': 1, 'reward': 0.5}}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # UCB1 selection
        try:
            total_pulls = sum(a['pulls'] for a in self.arms.values())
        
            ucb_scores = {}
            for arm, data in self.arms.items():
                avg_reward = data['reward'] / data['pulls']
                exploration = math.sqrt(2 * math.log(total_pulls) / data['pulls'])
                ucb_scores[arm] = avg_reward + exploration
        
            selected_arm = max(ucb_scores, key=ucb_scores.get)
        
            # Generate signal based on selected arm
            if selected_arm == 'trend':
                signal = context.trend
            elif selected_arm == 'momentum':
                signal = context.momentum
            else:  # contrarian
                signal = -context.trend * 0.5
        
            # Update arm (simulated reward)
            reward = 0.5 + signal * context.trend  # Reward if signal aligned with outcome
            self.arms[selected_arm]['pulls'] += 1
            self.arms[selected_arm]['reward'] += reward
        
            return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
                f"Selected: {selected_arm}", {'selected': selected_arm, 'ucb_scores': ucb_scores})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class EnsembleLearningDecision(DecisionConcept):
    """Concept 74: Ensemble Learning - Combine multiple models"""
    
    def __init__(self):
        try:
            super().__init__(74, "Ensemble Learning", DecisionCategory.ADAPTIVE)
            self.model_weights = {'trend_follower': 0.25, 'mean_reverter': 0.25, 'momentum': 0.25, 'sentiment': 0.25}
            self.model_accuracy: Dict[str, deque] = {k: deque(maxlen=20) for k in self.model_weights}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Individual model predictions
        try:
            predictions = {
                'trend_follower': context.trend,
                'mean_reverter': -context.trend * 0.5 if abs(context.trend) > 0.3 else 0,
                'momentum': context.momentum,
                'sentiment': context.sentiment
            }
        
            # Weighted ensemble
            ensemble_signal = sum(self.model_weights[m] * predictions[m] for m in predictions)
        
            # Update weights based on accuracy
            for model, pred in predictions.items():
                correct = (pred > 0 and context.trend > 0) or (pred < 0 and context.trend < 0)
                self.model_accuracy[model].append(1 if correct else 0)
            
                if len(self.model_accuracy[model]) >= 5:
                    acc = sum(self.model_accuracy[model]) / len(self.model_accuracy[model])
                    self.model_weights[model] = 0.1 + acc * 0.4
        
            # Normalize weights
            total = sum(self.model_weights.values())
            self.model_weights = {k: v / total for k, v in self.model_weights.items()}
        
            return self._create_result(self._signal_to_action(ensemble_signal), abs(ensemble_signal), DecisionUrgency.NORMAL,
                f"Ensemble: {ensemble_signal:.3f}", {'predictions': predictions, 'weights': self.model_weights})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class TransferLearningDecision(DecisionConcept):
    """Concept 75: Transfer Learning - Apply knowledge across markets"""
    
    def __init__(self):
        try:
            super().__init__(75, "Transfer Learning", DecisionCategory.ADAPTIVE)
            self.market_patterns: Dict[str, Dict] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Store pattern for this market
        try:
            pattern = {'trend': context.trend, 'vol': context.volatility, 'regime': context.regime}
            self.market_patterns[context.symbol] = pattern
        
            # Find similar markets
            similar_markets = []
            for symbol, p in self.market_patterns.items():
                if symbol != context.symbol:
                    similarity = 1 - (abs(p['trend'] - context.trend) + abs(p['vol'] - context.volatility)) / 2
                    if similarity > 0.7:
                        similar_markets.append((symbol, similarity, p))
        
            if similar_markets:
                # Transfer knowledge from similar markets
                avg_trend = sum(m[2]['trend'] * m[1] for m in similar_markets) / sum(m[1] for m in similar_markets)
                signal = context.trend * 0.6 + avg_trend * 0.4
                reason = f"Transfer from {len(similar_markets)} markets"
            else:
                signal = context.trend
                reason = "No similar markets"
        
            return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL, reason,
                {'similar_count': len(similar_markets), 'signal': signal})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class MetaLearningDecision(DecisionConcept):
    """Concept 76: Meta-Learning - Learn how to learn"""
    
    def __init__(self):
        try:
            super().__init__(76, "Meta-Learning", DecisionCategory.ADAPTIVE)
            self.strategy_performance: Dict[str, deque] = {'aggressive': deque(maxlen=20), 'conservative': deque(maxlen=20), 'adaptive': deque(maxlen=20)}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Three meta-strategies
        try:
            aggressive_signal = context.trend * 1.5 + context.momentum
            conservative_signal = context.trend * 0.5
            adaptive_signal = context.trend if context.volatility < 0.3 else context.trend * 0.3
        
            # Select best performing strategy
            avg_perf = {}
            for strat, perf in self.strategy_performance.items():
                avg_perf[strat] = sum(perf) / len(perf) if perf else 0.5
        
            best_strategy = max(avg_perf, key=avg_perf.get)
        
            if best_strategy == 'aggressive':
                signal = aggressive_signal
            elif best_strategy == 'conservative':
                signal = conservative_signal
            else:
                signal = adaptive_signal
        
            # Update performance (simulated)
            reward = 0.5 + signal * context.trend
            self.strategy_performance[best_strategy].append(reward)
        
            return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
                f"Meta: {best_strategy}", {'best_strategy': best_strategy, 'avg_perf': avg_perf})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class FeatureSelectionDecision(DecisionConcept):
    """Concept 77: Dynamic Feature Selection - Use most predictive features"""
    
    def __init__(self):
        try:
            super().__init__(77, "Feature Selection", DecisionCategory.ADAPTIVE)
            self.feature_importance = {'trend': 1.0, 'momentum': 1.0, 'sentiment': 1.0, 'volatility': 1.0}
            self.feature_history: Dict[str, deque] = {k: deque(maxlen=30) for k in self.feature_importance}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        try:
            features = {'trend': context.trend, 'momentum': context.momentum, 'sentiment': context.sentiment, 'volatility': -context.volatility}
        
            # Track feature values
            for f, v in features.items():
                self.feature_history[f].append(v)
        
            # Calculate feature importance (correlation with trend)
            if len(self.feature_history['trend']) >= 10:
                for f in features:
                    if f != 'trend':
                        corr = self._correlation(list(self.feature_history[f]), list(self.feature_history['trend']))
                        self.feature_importance[f] = abs(corr) + 0.1
        
            # Weighted signal using top features
            total_imp = sum(self.feature_importance.values())
            signal = sum(features[f] * self.feature_importance[f] / total_imp for f in features)
        
            return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
                f"Top feature: {max(self.feature_importance, key=self.feature_importance.get)}",
                {'importance': self.feature_importance, 'signal': signal})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise
    
    def _correlation(self, x: List[float], y: List[float]) -> float:
        try:
            if len(x) < 2: return 0
            mx, my = sum(x) / len(x), sum(y) / len(y)
            num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
            den = math.sqrt(sum((xi - mx) ** 2 for xi in x) * sum((yi - my) ** 2 for yi in y))
            return num / den if den > 0 else 0
        except Exception as e:
            logger.error(f"Error in _correlation: {e}")
            raise


class RegimeAdaptiveDecision(DecisionConcept):
    """Concept 78: Regime-Adaptive - Different strategy per regime"""
    
    def __init__(self):
        try:
            super().__init__(78, "Regime Adaptive", DecisionCategory.ADAPTIVE)
            self.regime_strategies = {
                'trending': lambda c: c.trend * 1.2,
                'ranging': lambda c: -c.trend * 0.5,
                'volatile': lambda c: c.trend * 0.3,
                'quiet': lambda c: c.trend * 0.8
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Detect regime
        try:
            if abs(context.trend) > 0.3:
                regime = 'trending'
            elif context.volatility > 0.4:
                regime = 'volatile'
            elif context.volatility < 0.2:
                regime = 'quiet'
            else:
                regime = 'ranging'
        
            # Apply regime-specific strategy
            signal = self.regime_strategies[regime](context)
        
            return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
                f"Regime: {regime}", {'regime': regime, 'signal': signal})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class MemoryNetworkDecision(DecisionConcept):
    """Concept 79: Memory Network - Remember important patterns"""
    
    def __init__(self):
        try:
            super().__init__(79, "Memory Network", DecisionCategory.ADAPTIVE)
            self.memory: List[Dict] = []
            self.memory_size = 50
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Create memory entry
        try:
            entry = {
                'trend': context.trend,
                'momentum': context.momentum,
                'vol': context.volatility,
                'outcome': None  # Would be filled later
            }
        
            # Query memory for similar situations
            similar = []
            for mem in self.memory:
                similarity = 1 - (abs(mem['trend'] - context.trend) + abs(mem['momentum'] - context.momentum)) / 2
                if similarity > 0.8 and mem['outcome'] is not None:
                    similar.append(mem)
        
            if similar:
                # Use memory to inform decision
                avg_outcome = sum(m['outcome'] for m in similar) / len(similar)
                signal = context.trend * 0.5 + avg_outcome * 0.5
                reason = f"Memory: {len(similar)} similar"
            else:
                signal = context.trend
                reason = "No memory match"
        
            # Store in memory
            entry['outcome'] = context.trend  # Simplified
            self.memory.append(entry)
            if len(self.memory) > self.memory_size:
                self.memory.pop(0)
        
            return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL, reason,
                {'memory_size': len(self.memory), 'similar_count': len(similar)})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


class ContinualLearningDecision(DecisionConcept):
    """Concept 80: Continual Learning - Never stop learning"""
    
    def __init__(self):
        try:
            super().__init__(80, "Continual Learning", DecisionCategory.ADAPTIVE)
            self.model_version = 1
            self.performance_window: deque = deque(maxlen=50)
            self.base_weights = {'trend': 0.4, 'momentum': 0.3, 'sentiment': 0.3}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Current model prediction
        try:
            signal = sum(self.base_weights[k] * getattr(context, k) for k in self.base_weights)
        
            # Track performance
            self.performance_window.append(signal * context.trend)  # Simplified P&L
        
            # Check if model needs update
            if len(self.performance_window) >= 20:
                recent_perf = sum(list(self.performance_window)[-10:]) / 10
                older_perf = sum(list(self.performance_window)[:10]) / 10
            
                if recent_perf < older_perf * 0.8:  # Performance degraded
                    # Update model
                    self.model_version += 1
                    # Shift weights toward recent best performer
                    best = max(['trend', 'momentum', 'sentiment'], key=lambda k: abs(getattr(context, k)))
                    self.base_weights[best] += 0.1
                    total = sum(self.base_weights.values())
                    self.base_weights = {k: v / total for k, v in self.base_weights.items()}
        
            return self._create_result(self._signal_to_action(signal), abs(signal), DecisionUrgency.NORMAL,
                f"Model v{self.model_version}", {'version': self.model_version, 'weights': self.base_weights})
        except Exception as e:
            logger.error(f"Error in decide: {e}")
            raise


ADAPTIVE_CONCEPTS = [
    OnlineLearningDecision,
    ReinforcementDecision,
    BanditDecision,
    EnsembleLearningDecision,
    TransferLearningDecision,
    MetaLearningDecision,
    FeatureSelectionDecision,
    RegimeAdaptiveDecision,
    MemoryNetworkDecision,
    ContinualLearningDecision,
]
