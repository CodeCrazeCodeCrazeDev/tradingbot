"""
NEUROS-FI Region 6: Basal Ganglia - Reinforcement Learning and Action Selection
================================================================================

Biological Basis:
The basal ganglia implement reinforcement learning in biological hardware.
The striatum evaluates options and encodes action-value functions.
The dopaminergic neurons of the SNc and VTA compute and broadcast reward
prediction error signals. The globus pallidus and subthalamic nucleus
implement the Go/NoGo gating mechanism.

This architecture is mathematically identical to the actor-critic RL algorithm.

Citations:
- Schultz, Dayan & Montague (1997) - A neural substrate of prediction and reward
- Doya (2000) - Complementary roles of basal ganglia and cerebellum
- Frank (2005) - Dynamic dopamine modulation in the basal ganglia
- Hikosaka et al. (2006) - Basal ganglia orient eyes to reward

Constitutional Version: 5.0
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions the basal ganglia can select."""
    
    EXECUTE_ORDER = auto()
    HOLD_POSITION = auto()
    CLOSE_POSITION = auto()
    ADJUST_SIZE = auto()
    CHANGE_VENUE = auto()
    MODIFY_ALGORITHM = auto()


class GatingDecision(Enum):
    """Go/NoGo gating decisions."""
    
    GO = "go"
    NO_GO = "no_go"
    HOLD = "hold"  # Wait for more information


class DopamineState(Enum):
    """Dopamine system states."""
    
    DEPLETED = "depleted"      # Chronic negative RPE
    LOW = "low"
    NORMAL = "normal"
    ELEVATED = "elevated"
    BURST = "burst"            # Strong positive RPE


@dataclass
class ActionValue:
    """Q-value for a state-action pair."""
    
    state_hash: str
    action: ActionType
    q_value: float
    visit_count: int
    last_update: datetime
    confidence: float  # Based on visit count
    
    def get_ucb_value(self, total_visits: int, exploration_constant: float = 1.414) -> float:
        """Get Upper Confidence Bound value for exploration."""
        if self.visit_count == 0:
            return float('inf')
        
        exploitation = self.q_value
        exploration = exploration_constant * np.sqrt(np.log(total_visits) / self.visit_count)
        
        return exploitation + exploration


@dataclass
class RewardPredictionError:
    """Dopamine reward prediction error signal."""
    
    timestamp: datetime
    predicted_reward: float
    actual_reward: float
    rpe: float  # δ = r + γV(s') - V(s)
    state_hash: str
    action: ActionType
    next_state_hash: str
    
    @property
    def is_positive(self) -> bool:
        return self.rpe > 0
    
    @property
    def is_negative(self) -> bool:
        return self.rpe < 0


@dataclass
class ExecutionHabit:
    """A learned execution habit (automatic policy)."""
    
    habit_id: str
    state_pattern: Dict[str, Any]
    action: ActionType
    action_params: Dict[str, Any]
    reinforcement_count: int
    success_rate: float
    avg_reward: float
    is_automatic: bool  # True if habit runs without cortical involvement
    last_execution: datetime


class Striatum:
    """
    Striatum - Action-Value Function (Q-function)
    
    Maintains Q(s,a) for all execution decisions:
    - Which venue to route to
    - What order size to submit
    - What algorithm to use
    - When to be aggressive vs passive
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Q-table: state_hash -> action -> ActionValue
        self._q_table: Dict[str, Dict[ActionType, ActionValue]] = {}
        
        # Learning parameters
        self._learning_rate = 0.1
        self._discount_factor = 0.95
        
        # Visit tracking
        self._total_visits = 0
        
        # State encoding
        self._state_features = [
            'spread', 'volatility', 'volume', 'order_imbalance',
            'time_of_day', 'venue_liquidity', 'urgency'
        ]
    
    def encode_state(self, state: Dict[str, Any]) -> str:
        """Encode market state into a hash for Q-table lookup."""
        # Discretize continuous features
        discretized = []
        
        for feature in self._state_features:
            value = state.get(feature, 0)
            if isinstance(value, float):
                # Discretize to bins
                bin_value = int(value * 10) / 10
                discretized.append(f"{feature}:{bin_value}")
            else:
                discretized.append(f"{feature}:{value}")
        
        return "|".join(discretized)
    
    def get_q_value(self, state_hash: str, action: ActionType) -> float:
        """Get Q-value for state-action pair."""
        with self._lock:
            if state_hash not in self._q_table:
                return 0.0
            
            if action not in self._q_table[state_hash]:
                return 0.0
            
            return self._q_table[state_hash][action].q_value
    
    def get_action_values(self, state_hash: str) -> Dict[ActionType, ActionValue]:
        """Get all action values for a state."""
        with self._lock:
            if state_hash not in self._q_table:
                # Initialize with zeros
                self._q_table[state_hash] = {}
                for action in ActionType:
                    self._q_table[state_hash][action] = ActionValue(
                        state_hash=state_hash,
                        action=action,
                        q_value=0.0,
                        visit_count=0,
                        last_update=datetime.utcnow(),
                        confidence=0.0,
                    )
            
            return self._q_table[state_hash].copy()
    
    def update_q_value(
        self,
        state_hash: str,
        action: ActionType,
        reward: float,
        next_state_hash: str
    ) -> RewardPredictionError:
        """
        Update Q-value using TD learning.
        
        Q(s,a) ← Q(s,a) + α[r + γ·max_a'Q(s',a') - Q(s,a)]
        
        Returns the reward prediction error (dopamine signal).
        """
        with self._lock:
            self._total_visits += 1
            
            # Ensure state exists
            self.get_action_values(state_hash)
            self.get_action_values(next_state_hash)
            
            # Current Q-value
            current_q = self._q_table[state_hash][action].q_value
            
            # Max Q-value for next state
            next_q_values = [av.q_value for av in self._q_table[next_state_hash].values()]
            max_next_q = max(next_q_values) if next_q_values else 0.0
            
            # TD target
            td_target = reward + self._discount_factor * max_next_q
            
            # Reward prediction error (dopamine signal)
            rpe = td_target - current_q
            
            # Update Q-value
            new_q = current_q + self._learning_rate * rpe
            
            # Update action value
            av = self._q_table[state_hash][action]
            av.q_value = new_q
            av.visit_count += 1
            av.last_update = datetime.utcnow()
            av.confidence = min(1.0, av.visit_count / 100)
            
            return RewardPredictionError(
                timestamp=datetime.utcnow(),
                predicted_reward=current_q,
                actual_reward=reward,
                rpe=rpe,
                state_hash=state_hash,
                action=action,
                next_state_hash=next_state_hash,
            )
    
    def select_action(
        self,
        state_hash: str,
        exploration_rate: float = 0.1
    ) -> Tuple[ActionType, float]:
        """
        Select action using epsilon-greedy with UCB.
        
        Returns (action, q_value).
        """
        with self._lock:
            action_values = self.get_action_values(state_hash)
            
            # Epsilon-greedy exploration
            if np.random.random() < exploration_rate:
                action = np.random.choice(list(ActionType))
                return action, action_values[action].q_value
            
            # UCB-based selection
            best_action = None
            best_ucb = float('-inf')
            
            for action, av in action_values.items():
                ucb = av.get_ucb_value(self._total_visits)
                if ucb > best_ucb:
                    best_ucb = ucb
                    best_action = action
            
            return best_action, action_values[best_action].q_value
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get striatum statistics."""
        with self._lock:
            total_states = len(self._q_table)
            total_actions = sum(len(actions) for actions in self._q_table.values())
            
            return {
                'total_states': total_states,
                'total_state_actions': total_actions,
                'total_visits': self._total_visits,
                'learning_rate': self._learning_rate,
                'discount_factor': self._discount_factor,
            }


class DopamineCircuit:
    """
    Dopamine Circuit (SNc/VTA) - Reward Prediction Error Signal
    
    The RPE δ = r_t + γ·V(s_{t+1}) − V(s_t) is computed after every
    execution and broadcast as the training signal.
    
    Three states:
    - δ > 0: Better than expected (dopamine burst) → strengthen policy
    - δ = 0: As expected → no learning
    - δ < 0: Worse than expected (dopamine dip) → weaken policy
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # RPE history
        self._rpe_history: List[RewardPredictionError] = []
        
        # Dopamine state
        self._dopamine_state = DopamineState.NORMAL
        self._chronic_rpe: float = 0.0  # Running average
        
        # Thresholds
        self._burst_threshold = 0.5
        self._dip_threshold = -0.3
        self._depletion_threshold = -0.1  # Chronic negative
        
        # Callbacks for broadcasting
        self._broadcast_callbacks: List[Callable] = []
    
    def compute_rpe(
        self,
        predicted_value: float,
        actual_reward: float,
        next_state_value: float,
        discount_factor: float = 0.95
    ) -> float:
        """
        Compute reward prediction error.
        
        δ = r + γV(s') - V(s)
        """
        return actual_reward + discount_factor * next_state_value - predicted_value
    
    def process_rpe(self, rpe: RewardPredictionError):
        """Process and broadcast an RPE signal."""
        with self._lock:
            self._rpe_history.append(rpe)
            
            # Trim history
            if len(self._rpe_history) > 10000:
                self._rpe_history = self._rpe_history[-5000:]
            
            # Update chronic RPE (exponential moving average)
            self._chronic_rpe = 0.95 * self._chronic_rpe + 0.05 * rpe.rpe
            
            # Update dopamine state
            self._update_dopamine_state(rpe.rpe)
            
            # Broadcast to all registered listeners
            self._broadcast(rpe)
    
    def _update_dopamine_state(self, rpe: float):
        """Update dopamine state based on RPE."""
        if rpe > self._burst_threshold:
            self._dopamine_state = DopamineState.BURST
        elif rpe > 0.1:
            self._dopamine_state = DopamineState.ELEVATED
        elif rpe < self._dip_threshold:
            self._dopamine_state = DopamineState.LOW
        elif self._chronic_rpe < self._depletion_threshold:
            self._dopamine_state = DopamineState.DEPLETED
        else:
            self._dopamine_state = DopamineState.NORMAL
    
    def _broadcast(self, rpe: RewardPredictionError):
        """Broadcast RPE to all registered callbacks."""
        for callback in self._broadcast_callbacks:
            try:
                callback(rpe)
            except Exception as e:
                logger.error(f"RPE broadcast failed: {e}")
    
    def register_callback(self, callback: Callable[[RewardPredictionError], None]):
        """Register callback for RPE broadcasts."""
        self._broadcast_callbacks.append(callback)
    
    def get_dopamine_state(self) -> DopamineState:
        """Get current dopamine state."""
        with self._lock:
            return self._dopamine_state
    
    def get_chronic_rpe(self) -> float:
        """Get chronic (running average) RPE."""
        with self._lock:
            return self._chronic_rpe
    
    def get_rpe_statistics(self) -> Dict[str, Any]:
        """Get RPE statistics."""
        with self._lock:
            if not self._rpe_history:
                return {'count': 0}
            
            rpes = [r.rpe for r in self._rpe_history[-1000:]]
            
            return {
                'count': len(self._rpe_history),
                'mean': np.mean(rpes),
                'std': np.std(rpes),
                'positive_rate': sum(1 for r in rpes if r > 0) / len(rpes),
                'chronic_rpe': self._chronic_rpe,
                'dopamine_state': self._dopamine_state.value,
            }


class GoNoGoGate:
    """
    Go/NoGo Gating Mechanism (Globus Pallidus / Subthalamic Nucleus)
    
    Every order submission passes through a Go/NoGo gate.
    The STN implements a hold signal that pauses execution when
    conditions are unfamiliar and Q-function confidence is low.
    """
    
    def __init__(self, striatum: Striatum, dopamine: DopamineCircuit):
        self._striatum = striatum
        self._dopamine = dopamine
        self._lock = threading.RLock()
        
        # Gating thresholds
        self._confidence_threshold = 0.3  # Min confidence to GO
        self._novelty_threshold = 0.5     # Max novelty to GO
        
        # Gating history
        self._decisions: List[Dict[str, Any]] = []
    
    def evaluate(
        self,
        state_hash: str,
        proposed_action: ActionType,
        urgency: float = 0.5
    ) -> Tuple[GatingDecision, str]:
        """
        Evaluate whether to GO or NO_GO on a proposed action.
        
        Returns (decision, reason).
        """
        with self._lock:
            action_values = self._striatum.get_action_values(state_hash)
            av = action_values.get(proposed_action)
            
            if av is None:
                return GatingDecision.HOLD, "Unknown action"
            
            # Check confidence
            if av.confidence < self._confidence_threshold:
                # Low confidence - check urgency
                if urgency > 0.8:
                    # High urgency overrides low confidence
                    decision = GatingDecision.GO
                    reason = "Low confidence but high urgency"
                else:
                    decision = GatingDecision.HOLD
                    reason = f"Confidence {av.confidence:.2f} < {self._confidence_threshold}"
            
            # Check dopamine state
            elif self._dopamine.get_dopamine_state() == DopamineState.DEPLETED:
                # Dopamine depletion - reduce risk appetite
                if av.q_value > 0.5:  # Only high-value actions
                    decision = GatingDecision.GO
                    reason = "Dopamine depleted but high Q-value"
                else:
                    decision = GatingDecision.NO_GO
                    reason = "Dopamine depleted - risk appetite reduced"
            
            # Check Q-value
            elif av.q_value < 0:
                decision = GatingDecision.NO_GO
                reason = f"Negative Q-value: {av.q_value:.3f}"
            
            else:
                decision = GatingDecision.GO
                reason = f"Q-value: {av.q_value:.3f}, confidence: {av.confidence:.2f}"
            
            # Record decision
            self._decisions.append({
                'timestamp': datetime.utcnow(),
                'state_hash': state_hash,
                'action': proposed_action.name,
                'decision': decision.value,
                'reason': reason,
                'q_value': av.q_value,
                'confidence': av.confidence,
            })
            
            if len(self._decisions) > 10000:
                self._decisions = self._decisions[-5000:]
            
            return decision, reason
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gating statistics."""
        with self._lock:
            if not self._decisions:
                return {'total': 0}
            
            recent = self._decisions[-1000:]
            decisions = [d['decision'] for d in recent]
            
            return {
                'total': len(self._decisions),
                'go_rate': decisions.count('go') / len(decisions),
                'no_go_rate': decisions.count('no_go') / len(decisions),
                'hold_rate': decisions.count('hold') / len(decisions),
            }


class HabitFormation:
    """
    Habit Formation System
    
    Execution patterns reinforced thousands of times become encoded
    as fast, automatic habits — running without cortical involvement.
    """
    
    HABIT_THRESHOLD = 1000  # Reinforcements needed for habit
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Habit library
        self._habits: Dict[str, ExecutionHabit] = {}
        
        # Pending habits (being learned)
        self._pending: Dict[str, Dict[str, Any]] = {}
    
    def reinforce(
        self,
        state_pattern: Dict[str, Any],
        action: ActionType,
        action_params: Dict[str, Any],
        reward: float
    ):
        """Reinforce a state-action pattern."""
        with self._lock:
            pattern_hash = self._hash_pattern(state_pattern)
            
            if pattern_hash not in self._pending:
                self._pending[pattern_hash] = {
                    'state_pattern': state_pattern,
                    'action': action,
                    'action_params': action_params,
                    'reinforcements': 0,
                    'total_reward': 0.0,
                    'successes': 0,
                }
            
            pending = self._pending[pattern_hash]
            pending['reinforcements'] += 1
            pending['total_reward'] += reward
            if reward > 0:
                pending['successes'] += 1
            
            # Check if habit threshold reached
            if pending['reinforcements'] >= self.HABIT_THRESHOLD:
                self._promote_to_habit(pattern_hash, pending)
    
    def _promote_to_habit(self, pattern_hash: str, pending: Dict[str, Any]):
        """Promote a pending pattern to a full habit."""
        habit = ExecutionHabit(
            habit_id=f"habit_{pattern_hash}",
            state_pattern=pending['state_pattern'],
            action=pending['action'],
            action_params=pending['action_params'],
            reinforcement_count=pending['reinforcements'],
            success_rate=pending['successes'] / pending['reinforcements'],
            avg_reward=pending['total_reward'] / pending['reinforcements'],
            is_automatic=True,
            last_execution=datetime.utcnow(),
        )
        
        self._habits[pattern_hash] = habit
        del self._pending[pattern_hash]
        
        logger.info(f"Habit formed: {habit.habit_id} (success_rate={habit.success_rate:.2f})")
    
    def _hash_pattern(self, pattern: Dict[str, Any]) -> str:
        """Hash a state pattern for lookup."""
        import hashlib
        import json
        
        # Discretize for matching
        discretized = {}
        for key, value in sorted(pattern.items()):
            if isinstance(value, float):
                discretized[key] = round(value, 1)
            else:
                discretized[key] = value
        
        content = json.dumps(discretized, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def get_habit(self, state_pattern: Dict[str, Any]) -> Optional[ExecutionHabit]:
        """Get habit for a state pattern if one exists."""
        with self._lock:
            pattern_hash = self._hash_pattern(state_pattern)
            return self._habits.get(pattern_hash)
    
    def execute_habit(self, habit: ExecutionHabit) -> Dict[str, Any]:
        """Execute a habit (automatic, no cortical involvement)."""
        with self._lock:
            habit.last_execution = datetime.utcnow()
            
            return {
                'habit_id': habit.habit_id,
                'action': habit.action,
                'params': habit.action_params,
                'automatic': True,
            }
    
    def get_habits(self) -> List[ExecutionHabit]:
        """Get all formed habits."""
        with self._lock:
            return list(self._habits.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get habit formation statistics."""
        with self._lock:
            return {
                'formed_habits': len(self._habits),
                'pending_habits': len(self._pending),
                'avg_success_rate': np.mean([h.success_rate for h in self._habits.values()]) if self._habits else 0,
            }


class ReinforcementLearning:
    """Combined RL system for the basal ganglia."""
    
    def __init__(self):
        self.striatum = Striatum()
        self.dopamine = DopamineCircuit()
        self.go_nogo = GoNoGoGate(self.striatum, self.dopamine)
        self.habits = HabitFormation()
        
        # Register dopamine callback for learning
        self.dopamine.register_callback(self._on_rpe)
    
    def _on_rpe(self, rpe: RewardPredictionError):
        """Handle RPE signal for learning."""
        # RPE drives learning in striatum (already done in update_q_value)
        pass
    
    def learn(
        self,
        state: Dict[str, Any],
        action: ActionType,
        reward: float,
        next_state: Dict[str, Any],
        action_params: Optional[Dict[str, Any]] = None
    ) -> RewardPredictionError:
        """
        Learn from an experience tuple.
        
        Returns the RPE signal.
        """
        state_hash = self.striatum.encode_state(state)
        next_state_hash = self.striatum.encode_state(next_state)
        
        # Update Q-value and get RPE
        rpe = self.striatum.update_q_value(state_hash, action, reward, next_state_hash)
        
        # Process RPE through dopamine circuit
        self.dopamine.process_rpe(rpe)
        
        # Reinforce habit
        self.habits.reinforce(state, action, action_params or {}, reward)
        
        return rpe
    
    def select_action(
        self,
        state: Dict[str, Any],
        exploration_rate: float = 0.1
    ) -> Tuple[ActionType, GatingDecision, str]:
        """
        Select and gate an action.
        
        Returns (action, gating_decision, reason).
        """
        state_hash = self.striatum.encode_state(state)
        
        # Check for automatic habit first
        habit = self.habits.get_habit(state)
        if habit and habit.is_automatic:
            # Execute habit without deliberation
            return habit.action, GatingDecision.GO, "Automatic habit"
        
        # Select action from Q-function
        action, q_value = self.striatum.select_action(state_hash, exploration_rate)
        
        # Gate the action
        urgency = state.get('urgency', 0.5)
        decision, reason = self.go_nogo.evaluate(state_hash, action, urgency)
        
        return action, decision, reason


class BasalGanglia:
    """
    The complete Basal Ganglia - reinforcement learning and action selection.
    
    Implements:
    - Striatum (Q-function / action-value)
    - Dopamine circuit (RPE signal)
    - Go/NoGo gating
    - Habit formation
    """
    
    def __init__(self):
        # Initialize RL system
        self.rl = ReinforcementLearning()
        
        self._lock = threading.RLock()
        
        # Execution history
        self._executions: List[Dict[str, Any]] = []
        
        logger.info("Basal Ganglia initialized - RL and action selection active")
    
    def select_execution_action(
        self,
        market_state: Dict[str, Any],
        order_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Select an execution action for an order.
        
        Returns action decision with gating result.
        """
        with self._lock:
            # Combine state
            state = {**market_state, **order_context}
            
            # Get exploration rate based on dopamine state
            dopamine_state = self.rl.dopamine.get_dopamine_state()
            if dopamine_state == DopamineState.DEPLETED:
                exploration_rate = 0.05  # Less exploration when depleted
            elif dopamine_state == DopamineState.BURST:
                exploration_rate = 0.2   # More exploration when things are good
            else:
                exploration_rate = 0.1
            
            # Select action
            action, decision, reason = self.rl.select_action(state, exploration_rate)
            
            result = {
                'action': action,
                'action_name': action.name,
                'gating_decision': decision.value,
                'gating_reason': reason,
                'dopamine_state': dopamine_state.value,
                'timestamp': datetime.utcnow(),
            }
            
            self._executions.append(result)
            if len(self._executions) > 10000:
                self._executions = self._executions[-5000:]
            
            return result
    
    def process_execution_outcome(
        self,
        state: Dict[str, Any],
        action: ActionType,
        outcome: Dict[str, Any],
        next_state: Dict[str, Any]
    ) -> RewardPredictionError:
        """
        Process execution outcome and learn.
        
        Returns the RPE signal.
        """
        with self._lock:
            # Calculate reward from outcome
            reward = self._calculate_reward(outcome)
            
            # Learn from experience
            rpe = self.rl.learn(state, action, reward, next_state, outcome.get('params'))
            
            return rpe
    
    def _calculate_reward(self, outcome: Dict[str, Any]) -> float:
        """Calculate reward from execution outcome."""
        # Reward based on execution quality
        slippage = outcome.get('slippage', 0)
        fill_rate = outcome.get('fill_rate', 1.0)
        market_impact = outcome.get('market_impact', 0)
        
        # Negative slippage and impact, positive fill rate
        reward = fill_rate - abs(slippage) * 10 - abs(market_impact) * 5
        
        # Normalize to [-1, 1]
        return max(-1.0, min(1.0, reward))
    
    def get_dopamine_state(self) -> DopamineState:
        """Get current dopamine state."""
        return self.rl.dopamine.get_dopamine_state()
    
    def get_habits(self) -> List[ExecutionHabit]:
        """Get all formed execution habits."""
        return self.rl.habits.get_habits()
    
    def get_status(self) -> Dict[str, Any]:
        """Get basal ganglia status."""
        return {
            'striatum': self.rl.striatum.get_statistics(),
            'dopamine': self.rl.dopamine.get_rpe_statistics(),
            'gating': self.rl.go_nogo.get_statistics(),
            'habits': self.rl.habits.get_statistics(),
            'total_executions': len(self._executions),
        }
