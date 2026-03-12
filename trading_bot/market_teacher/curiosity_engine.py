"""
Curiosity-Driven Exploration Engine
=====================================
Intrinsic motivation for market discovery beyond pure profit optimization.

Features:
- Curiosity bonus for novel discoveries
- Counterfactual learning (what if we had done X?)
- Novelty detection
- Regret minimization
"""

import logging
import random
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import hashlib
import numpy

logger = logging.getLogger(__name__)


class NoveltyType(Enum):
    """Types of novelty detected"""
    NEW_MARKET_STATE = "new_market_state"
    SURPRISING_OUTCOME = "surprising_outcome"
    UNEXPLORED_REGION = "unexplored_region"
    CONTRARIAN_SUCCESS = "contrarian_success"
    ANOMALY = "anomaly"


@dataclass
class CuriosityReward:
    """Reward for curious exploration"""
    reward_id: str
    novelty_type: NoveltyType
    base_reward: float
    curiosity_bonus: float
    total_reward: float
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'reward_id': self.reward_id,
            'novelty_type': self.novelty_type.value,
            'base_reward': self.base_reward,
            'curiosity_bonus': self.curiosity_bonus,
            'total_reward': self.total_reward,
            'description': self.description,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class VirtualTrade:
    """A trade we DIDN'T make but could have"""
    signal_id: str
    entry_price: float
    direction: str
    reason_skipped: str
    timestamp: datetime
    hypothetical_exit_price: Optional[float] = None
    hypothetical_pnl: Optional[float] = None
    evaluated: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'signal_id': self.signal_id,
            'entry_price': self.entry_price,
            'direction': self.direction,
            'reason_skipped': self.reason_skipped,
            'timestamp': self.timestamp.isoformat(),
            'hypothetical_exit_price': self.hypothetical_exit_price,
            'hypothetical_pnl': self.hypothetical_pnl,
            'evaluated': self.evaluated
        }


class NoveltyDetector:
    """
    Detects novel market states and situations.
    
    Maintains a memory of seen states and identifies new ones.
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            self.state_memory: Dict[str, int] = {}  # state_hash -> visit_count
            self.novelty_threshold = config.get('novelty_threshold', 3)
            self.max_memory_size = config.get('max_memory_size', 100000)
        
            self.novelty_history: deque = deque(maxlen=10000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def _hash_state(self, state: Dict) -> str:
        """Create a hash of a market state"""
        # Discretize continuous values for hashing
        try:
            discretized = {}
        
            for key, value in state.items():
                if isinstance(value, float):
                    # Round to 2 decimal places
                    discretized[key] = round(value, 2)
                elif isinstance(value, (int, str, bool)):
                    discretized[key] = value
                elif isinstance(value, list):
                    discretized[key] = tuple(value[:10])  # First 10 elements
                else:
                    discretized[key] = str(value)[:50]
        
            state_str = str(sorted(discretized.items()))
            return hashlib.md5(state_str.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Error in _hash_state: {e}")
            raise
    
    def check_novelty(self, market_state: Dict) -> Tuple[bool, float, NoveltyType]:
        """
        Check if a market state is novel.
        
        Returns:
            Tuple of (is_novel, novelty_score, novelty_type)
        """
        try:
            state_hash = self._hash_state(market_state)
        
            # Get visit count
            visit_count = self.state_memory.get(state_hash, 0)
        
            # Update memory
            self.state_memory[state_hash] = visit_count + 1
        
            # Prune memory if too large
            if len(self.state_memory) > self.max_memory_size:
                # Remove least visited states
                sorted_states = sorted(self.state_memory.items(), key=lambda x: x[1])
                for state, _ in sorted_states[:len(sorted_states)//4]:
                    del self.state_memory[state]
        
            # Calculate novelty score (inverse of visit count)
            novelty_score = 1.0 / (1.0 + visit_count)
        
            is_novel = visit_count < self.novelty_threshold
        
            if is_novel:
                novelty_type = NoveltyType.NEW_MARKET_STATE
                self.novelty_history.append({
                    'state_hash': state_hash,
                    'novelty_score': novelty_score,
                    'timestamp': datetime.now().isoformat()
                })
                logger.debug(f"Novel state detected: {state_hash} (visits: {visit_count})")
            else:
                novelty_type = None
        
            return is_novel, novelty_score, novelty_type
        except Exception as e:
            logger.error(f"Error in check_novelty: {e}")
            raise
    
    def get_exploration_priority(self, states: List[Dict]) -> List[Tuple[int, float]]:
        """
        Rank states by exploration priority (novelty).
        
        Returns list of (index, novelty_score) sorted by priority.
        """
        try:
            priorities = []
        
            for i, state in enumerate(states):
                state_hash = self._hash_state(state)
                visit_count = self.state_memory.get(state_hash, 0)
                novelty_score = 1.0 / (1.0 + visit_count)
                priorities.append((i, novelty_score))
        
            # Sort by novelty score (highest first)
            priorities.sort(key=lambda x: x[1], reverse=True)
        
            return priorities
        except Exception as e:
            logger.error(f"Error in get_exploration_priority: {e}")
            raise


class IntrinsicMotivation:
    """
    Provides intrinsic motivation rewards for exploration.
    
    Traditional RL: Reward = Profit/Loss only
    Curiosity-Driven RL: Reward = Profit/Loss + Curiosity Bonus
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            self.novelty_bonus_weight = config.get('novelty_bonus_weight', 0.1)
            self.surprise_bonus_weight = config.get('surprise_bonus_weight', 0.05)
            self.contrarian_bonus_weight = config.get('contrarian_bonus_weight', 0.03)
        
            self.novelty_detector = NoveltyDetector(config)
            self.reward_history: deque = deque(maxlen=10000)
        
            self.prediction_errors: deque = deque(maxlen=1000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_reward(
        self,
        trade_pnl: float,
        risk: float,
        market_state: Dict,
        predicted_outcome: float,
        actual_outcome: float,
        was_contrarian: bool = False
    ) -> CuriosityReward:
        """
        Calculate total reward including curiosity bonuses.
        
        Args:
            trade_pnl: Actual profit/loss from trade
            risk: Risk taken on the trade
            market_state: Current market state
            predicted_outcome: What we expected
            actual_outcome: What actually happened
            was_contrarian: Whether this was a contrarian trade
        
        Returns:
            CuriosityReward with breakdown
        """
        # Base reward (normalized by risk)
        try:
            base_reward = trade_pnl / max(risk, 0.001)
        
            curiosity_bonus = 0.0
            bonus_descriptions = []
        
            # Bonus 1: Novel state exploration
            is_novel, novelty_score, novelty_type = self.novelty_detector.check_novelty(market_state)
            if is_novel:
                novelty_bonus = self.novelty_bonus_weight * novelty_score
                curiosity_bonus += novelty_bonus
                bonus_descriptions.append(f"Novelty: +{novelty_bonus:.4f}")
        
            # Bonus 2: Surprising outcome (good OR bad)
            surprise = abs(actual_outcome - predicted_outcome)
            std_dev = np.std(list(self.prediction_errors)) if len(self.prediction_errors) > 10 else 1.0
        
            self.prediction_errors.append(surprise)
        
            if surprise > 2 * std_dev:
                surprise_bonus = self.surprise_bonus_weight
                curiosity_bonus += surprise_bonus
                bonus_descriptions.append(f"Surprise: +{surprise_bonus:.4f}")
                logger.debug(f"Surprising outcome! Expected {predicted_outcome:.4f}, got {actual_outcome:.4f}")
        
            # Bonus 3: Contrarian success
            if was_contrarian and trade_pnl > 0:
                contrarian_bonus = self.contrarian_bonus_weight
                curiosity_bonus += contrarian_bonus
                bonus_descriptions.append(f"Contrarian: +{contrarian_bonus:.4f}")
        
            total_reward = base_reward + curiosity_bonus
        
            reward = CuriosityReward(
                reward_id=f"rew_{datetime.now().timestamp()}",
                novelty_type=novelty_type if is_novel else NoveltyType.SURPRISING_OUTCOME if surprise > 2 * std_dev else None,
                base_reward=base_reward,
                curiosity_bonus=curiosity_bonus,
                total_reward=total_reward,
                description="; ".join(bonus_descriptions) if bonus_descriptions else "Standard reward"
            )
        
            self.reward_history.append(reward)
        
            return reward
        except Exception as e:
            logger.error(f"Error in calculate_reward: {e}")
            raise
    
    def get_exploration_incentive(self, market_state: Dict) -> float:
        """
        Get exploration incentive for a given state.
        
        Higher values encourage exploration of this state.
        """
        try:
            is_novel, novelty_score, _ = self.novelty_detector.check_novelty(market_state)
            return novelty_score
        except Exception as e:
            logger.error(f"Error in get_exploration_incentive: {e}")
            raise


class CounterfactualLearner:
    """
    Learns from trades we DIDN'T make.
    
    "What if I had done something different?"
    
    This allows learning from missed opportunities and validates
    decisions to skip trades.
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            self.evaluation_delay_seconds = config.get('evaluation_delay_seconds', 3600)  # 1 hour
        
            self.virtual_trades: List[VirtualTrade] = []
            self.lessons_learned: List[Dict] = []
        
            # Thresholds for adjustments
            self.confidence_threshold = 0.5
            self.volatility_threshold = 0.02
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def log_skipped_signal(
        self,
        signal: Dict,
        current_price: float,
        reason: str
    ):
        """
        Record a signal we chose NOT to act on.
        """
        try:
            virtual_trade = VirtualTrade(
                signal_id=signal.get('signal_id', f"sig_{datetime.now().timestamp()}"),
                entry_price=current_price,
                direction=signal.get('direction', 'LONG'),
                reason_skipped=reason,
                timestamp=datetime.now()
            )
        
            self.virtual_trades.append(virtual_trade)
            logger.debug(f"Logged skipped signal: {reason}")
        except Exception as e:
            logger.error(f"Error in log_skipped_signal: {e}")
            raise
    
    def evaluate_counterfactuals(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Evaluate what WOULD have happened with skipped trades.
        
        Args:
            current_prices: Current prices for evaluation
        
        Returns:
            List of lessons learned from counterfactual analysis
        """
        try:
            lessons = []
            now = datetime.now()
        
            for vt in self.virtual_trades:
                if vt.evaluated:
                    continue
            
                # Check if enough time has passed
                elapsed = (now - vt.timestamp).total_seconds()
                if elapsed < self.evaluation_delay_seconds:
                    continue
            
                # Get current price (simplified - would need symbol tracking)
                current_price = current_prices.get('default', vt.entry_price)
            
                # Calculate hypothetical P&L
                if vt.direction == 'LONG':
                    hypothetical_pnl = (current_price - vt.entry_price) / vt.entry_price
                else:
                    hypothetical_pnl = (vt.entry_price - current_price) / vt.entry_price
            
                vt.hypothetical_exit_price = current_price
                vt.hypothetical_pnl = hypothetical_pnl
                vt.evaluated = True
            
                # Generate lesson
                if hypothetical_pnl > 0.01:  # Would have made > 1%
                    lesson = {
                        'type': 'REGRET',
                        'signal_id': vt.signal_id,
                        'reason_skipped': vt.reason_skipped,
                        'hypothetical_pnl': hypothetical_pnl,
                        'message': f"Skipped signal would have made {hypothetical_pnl*100:.2f}%",
                        'adjustment': self._get_regret_adjustment(vt.reason_skipped),
                        'timestamp': now.isoformat()
                    }
                    logger.info(f"REGRET: Skipped signal would have made {hypothetical_pnl*100:.2f}%")
                
                elif hypothetical_pnl < -0.01:  # Would have lost > 1%
                    lesson = {
                        'type': 'VALIDATION',
                        'signal_id': vt.signal_id,
                        'reason_skipped': vt.reason_skipped,
                        'hypothetical_pnl': hypothetical_pnl,
                        'message': f"Good decision to skip. Would have lost {abs(hypothetical_pnl)*100:.2f}%",
                        'adjustment': self._get_validation_adjustment(vt.reason_skipped),
                        'timestamp': now.isoformat()
                    }
                    logger.info(f"VALIDATION: Good skip. Would have lost {abs(hypothetical_pnl)*100:.2f}%")
                
                else:
                    lesson = {
                        'type': 'NEUTRAL',
                        'signal_id': vt.signal_id,
                        'reason_skipped': vt.reason_skipped,
                        'hypothetical_pnl': hypothetical_pnl,
                        'message': "Outcome was neutral",
                        'adjustment': None,
                        'timestamp': now.isoformat()
                    }
            
                lessons.append(lesson)
                self.lessons_learned.append(lesson)
        
            # Clean up old evaluated trades
            self.virtual_trades = [vt for vt in self.virtual_trades 
                                   if not vt.evaluated or 
                                   (now - vt.timestamp).days < 7]
        
            return lessons
        except Exception as e:
            logger.error(f"Error in evaluate_counterfactuals: {e}")
            raise
    
    def _get_regret_adjustment(self, reason: str) -> Dict:
        """Get adjustment for regretted skip"""
        try:
            adjustments = {
                'low_confidence': {'confidence_threshold': 0.95},  # Lower threshold
                'high_volatility': {'volatility_threshold': 1.05},  # Increase tolerance
                'risk_limit': {'position_size': 0.9},  # Slightly reduce to allow more trades
                'correlation': {'correlation_threshold': 1.05}
            }
            return adjustments.get(reason, {})
        except Exception as e:
            logger.error(f"Error in _get_regret_adjustment: {e}")
            raise
    
    def _get_validation_adjustment(self, reason: str) -> Dict:
        """Get adjustment for validated skip"""
        try:
            adjustments = {
                'low_confidence': {'confidence_threshold': 1.05},  # Raise threshold
                'high_volatility': {'volatility_threshold': 0.95},  # Decrease tolerance
                'risk_limit': None,  # Keep as is
                'correlation': {'correlation_threshold': 0.95}
            }
            return adjustments.get(reason, {})
        except Exception as e:
            logger.error(f"Error in _get_validation_adjustment: {e}")
            raise
    
    def get_skip_statistics(self) -> Dict:
        """Get statistics on skipped trades"""
        try:
            evaluated = [vt for vt in self.virtual_trades if vt.evaluated]
        
            if not evaluated:
                return {'total_skipped': len(self.virtual_trades), 'evaluated': 0}
        
            regrets = sum(1 for vt in evaluated if vt.hypothetical_pnl > 0.01)
            validations = sum(1 for vt in evaluated if vt.hypothetical_pnl < -0.01)
        
            return {
                'total_skipped': len(self.virtual_trades),
                'evaluated': len(evaluated),
                'regrets': regrets,
                'validations': validations,
                'regret_rate': regrets / len(evaluated) if evaluated else 0,
                'validation_rate': validations / len(evaluated) if evaluated else 0,
                'avg_hypothetical_pnl': np.mean([vt.hypothetical_pnl for vt in evaluated])
            }
        except Exception as e:
            logger.error(f"Error in get_skip_statistics: {e}")
            raise


class RegretMinimizer:
    """
    Minimizes regret over time by learning from both actions and inactions.
    
    Regret = What we could have earned - What we actually earned
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            self.regret_history: deque = deque(maxlen=10000)
            self.cumulative_regret: float = 0.0
            self.action_values: Dict[str, List[float]] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def update_regret(
        self,
        action_taken: str,
        reward_received: float,
        alternative_actions: Dict[str, float]
    ):
        """
        Update regret based on action taken vs alternatives.
        
        Args:
            action_taken: The action we took
            reward_received: Reward from our action
            alternative_actions: Dict of action -> hypothetical reward
        """
        # Find best alternative
        try:
            if alternative_actions:
                best_alternative = max(alternative_actions.values())
            else:
                best_alternative = reward_received
        
            # Calculate regret
            regret = max(0, best_alternative - reward_received)
        
            self.cumulative_regret += regret
            self.regret_history.append({
                'action': action_taken,
                'reward': reward_received,
                'best_alternative': best_alternative,
                'regret': regret,
                'timestamp': datetime.now().isoformat()
            })
        
            # Update action values
            if action_taken not in self.action_values:
                self.action_values[action_taken] = []
            self.action_values[action_taken].append(reward_received)
        
            if regret > 0:
                logger.debug(f"Regret: {regret:.4f} (took {action_taken}, best was {best_alternative:.4f})")
        except Exception as e:
            logger.error(f"Error in update_regret: {e}")
            raise
    
    def get_recommended_action(self, available_actions: List[str]) -> str:
        """
        Get recommended action based on regret minimization.
        
        Uses Upper Confidence Bound (UCB) algorithm.
        """
        try:
            total_plays = sum(len(v) for v in self.action_values.values())
        
            ucb_scores = {}
        
            for action in available_actions:
                if action not in self.action_values or len(self.action_values[action]) == 0:
                    # Unexplored action - high priority
                    ucb_scores[action] = float('inf')
                else:
                    values = self.action_values[action]
                    mean_value = np.mean(values)
                    exploration_bonus = np.sqrt(2 * np.log(total_plays + 1) / len(values))
                    ucb_scores[action] = mean_value + exploration_bonus
        
            return max(ucb_scores, key=ucb_scores.get)
        except Exception as e:
            logger.error(f"Error in get_recommended_action: {e}")
            raise
    
    def get_regret_summary(self) -> Dict:
        """Get summary of regret statistics"""
        try:
            if not self.regret_history:
                return {'cumulative_regret': 0, 'avg_regret': 0}
        
            regrets = [r['regret'] for r in self.regret_history]
        
            return {
                'cumulative_regret': self.cumulative_regret,
                'avg_regret': np.mean(regrets),
                'max_regret': np.max(regrets),
                'regret_trend': np.mean(regrets[-100:]) if len(regrets) >= 100 else np.mean(regrets),
                'total_decisions': len(self.regret_history)
            }
        except Exception as e:
            logger.error(f"Error in get_regret_summary: {e}")
            raise


class CuriosityDrivenExplorer:
    """
    Master system for curiosity-driven exploration.
    
    Combines:
    - Novelty detection
    - Intrinsic motivation
    - Counterfactual learning
    - Regret minimization
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            self.novelty_detector = NoveltyDetector(config)
            self.intrinsic_motivation = IntrinsicMotivation(config)
            self.counterfactual_learner = CounterfactualLearner(config)
            self.regret_minimizer = RegretMinimizer(config)
        
            self.exploration_rate = config.get('initial_exploration_rate', 0.3)
            self.min_exploration_rate = config.get('min_exploration_rate', 0.1)
        
            logger.info("CuriosityDrivenExplorer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def should_explore(self, market_state: Dict) -> Tuple[bool, str]:
        """
        Decide whether to explore or exploit.
        
        Returns:
            Tuple of (should_explore, reason)
        """
        # Check novelty
        try:
            is_novel, novelty_score, _ = self.novelty_detector.check_novelty(market_state)
        
            if is_novel and novelty_score > 0.8:
                return True, "High novelty state - explore to learn"
        
            # Random exploration
            if random.random() < self.exploration_rate:
                return True, "Random exploration"
        
            # Check regret - if high, explore more
            regret_summary = self.regret_minimizer.get_regret_summary()
            if regret_summary.get('regret_trend', 0) > 0.1:
                return True, "High recent regret - explore alternatives"
        
            return False, "Exploit known strategies"
        except Exception as e:
            logger.error(f"Error in should_explore: {e}")
            raise
    
    def calculate_total_reward(
        self,
        trade_pnl: float,
        risk: float,
        market_state: Dict,
        predicted_outcome: float,
        actual_outcome: float,
        was_contrarian: bool = False
    ) -> CuriosityReward:
        """Calculate total reward including curiosity bonuses"""
        return self.intrinsic_motivation.calculate_reward(
            trade_pnl=trade_pnl,
            risk=risk,
            market_state=market_state,
            predicted_outcome=predicted_outcome,
            actual_outcome=actual_outcome,
            was_contrarian=was_contrarian
        )
    
    def log_skipped_opportunity(self, signal: Dict, price: float, reason: str):
        """Log a skipped trading opportunity for counterfactual learning"""
        try:
            self.counterfactual_learner.log_skipped_signal(signal, price, reason)
        except Exception as e:
            logger.error(f"Error in log_skipped_opportunity: {e}")
            raise
    
    def evaluate_counterfactuals(self, current_prices: Dict[str, float]) -> List[Dict]:
        """Evaluate what would have happened with skipped trades"""
        return self.counterfactual_learner.evaluate_counterfactuals(current_prices)
    
    def update_regret(self, action: str, reward: float, alternatives: Dict[str, float]):
        """Update regret tracking"""
        try:
            self.regret_minimizer.update_regret(action, reward, alternatives)
        except Exception as e:
            logger.error(f"Error in update_regret: {e}")
            raise
    
    def get_exploration_status(self) -> Dict:
        """Get current exploration status"""
        return {
            'exploration_rate': self.exploration_rate,
            'novelty_states_seen': len(self.novelty_detector.state_memory),
            'skip_statistics': self.counterfactual_learner.get_skip_statistics(),
            'regret_summary': self.regret_minimizer.get_regret_summary(),
            'recent_rewards': [r.to_dict() for r in list(self.intrinsic_motivation.reward_history)[-10:]]
        }


# Export all classes
__all__ = [
    'NoveltyType',
    'CuriosityReward',
    'VirtualTrade',
    'NoveltyDetector',
    'IntrinsicMotivation',
    'CounterfactualLearner',
    'RegretMinimizer',
    'CuriosityDrivenExplorer'
]
