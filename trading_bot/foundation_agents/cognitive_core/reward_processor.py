"""
Reward Processor - Multi-Objective Reward System
=================================================

Implements a sophisticated reward system for the AI agent:
1. Multi-objective rewards (profit, risk, discovery, learning)
2. Intrinsic motivation (curiosity, novelty-seeking)
3. Reward shaping for long-term goals
4. Temporal credit assignment

Based on the Foundation Agents paper (arXiv:2504.01990) reward processing.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import deque

logger = logging.getLogger(__name__)


class RewardType(Enum):
    """Types of rewards in the system"""
    PROFIT = "profit"                    # Financial returns
    RISK_ADJUSTED = "risk_adjusted"      # Risk-adjusted returns (Sharpe, etc.)
    DISCOVERY = "discovery"              # Novel alpha/pattern discovery
    LEARNING = "learning"                # Knowledge acquisition
    CURIOSITY = "curiosity"              # Intrinsic curiosity satisfaction
    SAFETY = "safety"                    # Avoiding harmful actions
    EFFICIENCY = "efficiency"            # Resource efficiency
    ALIGNMENT = "alignment"              # Goal alignment


class RewardScale(Enum):
    """Scale of reward impact"""
    IMMEDIATE = "immediate"      # Single action
    SHORT_TERM = "short_term"    # Hours to days
    MEDIUM_TERM = "medium_term"  # Days to weeks
    LONG_TERM = "long_term"      # Weeks to months


@dataclass
class RewardSignal:
    """A reward signal from the environment or internal processes"""
    reward_id: str
    reward_type: RewardType
    value: float  # Normalized to [-1, 1] typically
    raw_value: float  # Original value before normalization
    scale: RewardScale
    
    # Context
    source: str  # What generated this reward
    action: Optional[str] = None  # Action that led to this reward
    state_id: Optional[str] = None  # State when reward was received
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    delay: timedelta = field(default_factory=lambda: timedelta(0))  # Delay from action
    
    # Attribution
    confidence: float = 1.0  # Confidence in reward attribution
    contributing_factors: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'reward_id': self.reward_id,
            'reward_type': self.reward_type.value,
            'value': self.value,
            'raw_value': self.raw_value,
            'scale': self.scale.value,
            'source': self.source,
            'action': self.action,
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence
        }


@dataclass
class RewardObjective:
    """A reward objective with weight and constraints"""
    name: str
    reward_type: RewardType
    weight: float = 1.0
    min_threshold: Optional[float] = None  # Minimum acceptable value
    max_threshold: Optional[float] = None  # Maximum (for penalties)
    target: Optional[float] = None  # Target value
    
    # Adaptive weight
    adaptive: bool = False
    weight_history: List[float] = field(default_factory=list)


class IntrinsicMotivation:
    """
    Intrinsic Motivation System
    
    Generates internal rewards for:
    - Curiosity (exploring novel states)
    - Competence (mastering skills)
    - Autonomy (achieving self-set goals)
    """
    
    def __init__(self):
        self.state_visit_counts: Dict[str, int] = {}
        self.prediction_errors: deque = deque(maxlen=1000)
        self.skill_progress: Dict[str, float] = {}
        
    def curiosity_reward(self, state_hash: str, prediction_error: float) -> float:
        """
        Calculate curiosity reward based on:
        - State novelty (inverse visit count)
        - Prediction error (learning signal)
        """
        # State novelty
        visit_count = self.state_visit_counts.get(state_hash, 0)
        self.state_visit_counts[state_hash] = visit_count + 1
        novelty_reward = 1.0 / (1 + np.sqrt(visit_count))
        
        # Prediction error reward (learning progress)
        self.prediction_errors.append(prediction_error)
        if len(self.prediction_errors) > 10:
            recent_errors = list(self.prediction_errors)[-10:]
            older_errors = list(self.prediction_errors)[-20:-10] if len(self.prediction_errors) > 10 else recent_errors
            learning_progress = np.mean(older_errors) - np.mean(recent_errors)
            learning_reward = max(0, learning_progress * 10)  # Reward for reducing error
        else:
            learning_reward = 0.0
        
        # Combined curiosity reward
        return 0.6 * novelty_reward + 0.4 * learning_reward
    
    def competence_reward(self, skill: str, performance: float) -> float:
        """Calculate competence reward based on skill improvement"""
        previous = self.skill_progress.get(skill, 0.0)
        improvement = max(0, performance - previous)
        
        # Update skill progress (exponential moving average)
        self.skill_progress[skill] = 0.9 * previous + 0.1 * performance
        
        # Reward for improvement
        return improvement * 2.0
    
    def autonomy_reward(self, goal_achieved: bool, goal_difficulty: float) -> float:
        """Calculate autonomy reward for achieving self-set goals"""
        if goal_achieved:
            return goal_difficulty * 1.5  # Higher reward for harder goals
        return -0.1  # Small penalty for not achieving


class TemporalCreditAssignment:
    """
    Temporal Credit Assignment
    
    Assigns credit to past actions for current rewards.
    Handles delayed rewards common in trading.
    """
    
    def __init__(self, discount_factor: float = 0.99, eligibility_decay: float = 0.9):
        self.discount_factor = discount_factor
        self.eligibility_decay = eligibility_decay
        self.action_history: deque = deque(maxlen=1000)
        self.eligibility_traces: Dict[str, float] = {}
        
    def record_action(self, action_id: str, state_id: str, timestamp: datetime):
        """Record an action for later credit assignment"""
        self.action_history.append({
            'action_id': action_id,
            'state_id': state_id,
            'timestamp': timestamp
        })
        
        # Update eligibility traces
        for aid in self.eligibility_traces:
            self.eligibility_traces[aid] *= self.eligibility_decay
        self.eligibility_traces[action_id] = 1.0
    
    def assign_credit(self, reward: RewardSignal) -> Dict[str, float]:
        """Assign credit to past actions for a reward"""
        credits = {}
        
        # Find actions that could have contributed
        reward_time = reward.timestamp
        
        for record in reversed(list(self.action_history)):
            action_id = record['action_id']
            action_time = record['timestamp']
            
            # Time-based discount
            time_diff = (reward_time - action_time).total_seconds() / 3600  # Hours
            if time_diff < 0 or time_diff > 168:  # Max 1 week lookback
                continue
            
            time_discount = self.discount_factor ** time_diff
            
            # Eligibility trace
            eligibility = self.eligibility_traces.get(action_id, 0.0)
            
            # Combined credit
            credit = reward.value * time_discount * eligibility * reward.confidence
            
            if abs(credit) > 0.001:
                credits[action_id] = credit
        
        return credits


class RewardProcessor:
    """
    Reward Processor
    
    Central system for processing all rewards:
    - Combines multiple reward objectives
    - Handles intrinsic motivation
    - Performs temporal credit assignment
    - Adapts reward weights over time
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Reward objectives
        self.objectives: Dict[str, RewardObjective] = {}
        self._initialize_default_objectives()
        
        # Intrinsic motivation
        self.intrinsic = IntrinsicMotivation()
        
        # Temporal credit assignment
        self.credit_assigner = TemporalCreditAssignment(
            discount_factor=self.config.get('discount_factor', 0.99),
            eligibility_decay=self.config.get('eligibility_decay', 0.9)
        )
        
        # Reward history
        self.reward_history: deque = deque(maxlen=10000)
        self.aggregated_rewards: Dict[RewardType, deque] = {
            rt: deque(maxlen=1000) for rt in RewardType
        }
        
        # Normalization statistics
        self.reward_stats: Dict[RewardType, Dict[str, float]] = {
            rt: {'mean': 0.0, 'std': 1.0, 'min': -1.0, 'max': 1.0}
            for rt in RewardType
        }
        
        # Statistics
        self.stats = {
            'rewards_processed': 0,
            'total_reward': 0.0,
            'avg_reward': 0.0,
            'by_type': {rt.value: 0.0 for rt in RewardType}
        }
        
        logger.info("Reward Processor initialized")
    
    def _initialize_default_objectives(self):
        """Initialize default reward objectives"""
        self.objectives = {
            'profit': RewardObjective(
                name='profit',
                reward_type=RewardType.PROFIT,
                weight=0.3,
                min_threshold=-0.1  # Max 10% loss
            ),
            'risk_adjusted': RewardObjective(
                name='risk_adjusted',
                reward_type=RewardType.RISK_ADJUSTED,
                weight=0.25,
                target=1.5  # Target Sharpe ratio
            ),
            'discovery': RewardObjective(
                name='discovery',
                reward_type=RewardType.DISCOVERY,
                weight=0.15,
                adaptive=True
            ),
            'learning': RewardObjective(
                name='learning',
                reward_type=RewardType.LEARNING,
                weight=0.1,
                adaptive=True
            ),
            'curiosity': RewardObjective(
                name='curiosity',
                reward_type=RewardType.CURIOSITY,
                weight=0.1
            ),
            'safety': RewardObjective(
                name='safety',
                reward_type=RewardType.SAFETY,
                weight=0.1,
                min_threshold=0.0  # Never negative
            )
        }
    
    def process_reward(
        self,
        reward_type: RewardType,
        raw_value: float,
        source: str,
        action: Optional[str] = None,
        state_id: Optional[str] = None,
        scale: RewardScale = RewardScale.IMMEDIATE,
        metadata: Optional[Dict] = None
    ) -> RewardSignal:
        """Process a raw reward signal"""
        # Normalize reward
        normalized_value = self._normalize_reward(reward_type, raw_value)
        
        # Create reward signal
        reward = RewardSignal(
            reward_id=f"rew_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{reward_type.value}",
            reward_type=reward_type,
            value=normalized_value,
            raw_value=raw_value,
            scale=scale,
            source=source,
            action=action,
            state_id=state_id,
            metadata=metadata or {}
        )
        
        # Store in history
        self.reward_history.append(reward)
        self.aggregated_rewards[reward_type].append(normalized_value)
        
        # Update statistics
        self.stats['rewards_processed'] += 1
        self.stats['total_reward'] += normalized_value
        self.stats['avg_reward'] = self.stats['total_reward'] / self.stats['rewards_processed']
        self.stats['by_type'][reward_type.value] += normalized_value
        
        # Assign credit to past actions
        if action:
            self.credit_assigner.record_action(action, state_id or '', reward.timestamp)
        
        credits = self.credit_assigner.assign_credit(reward)
        reward.metadata['credit_assignment'] = credits
        
        # Update normalization statistics
        self._update_reward_stats(reward_type, raw_value)
        
        logger.debug(f"Processed reward: {reward_type.value} = {normalized_value:.4f}")
        
        return reward
    
    def _normalize_reward(self, reward_type: RewardType, raw_value: float) -> float:
        """Normalize reward to standard scale"""
        stats = self.reward_stats[reward_type]
        
        # Z-score normalization
        if stats['std'] > 0:
            normalized = (raw_value - stats['mean']) / stats['std']
        else:
            normalized = raw_value
        
        # Clip to [-1, 1] range
        return np.clip(normalized, -1.0, 1.0)
    
    def _update_reward_stats(self, reward_type: RewardType, raw_value: float):
        """Update running statistics for normalization"""
        values = list(self.aggregated_rewards[reward_type])
        if len(values) > 10:
            self.reward_stats[reward_type] = {
                'mean': np.mean(values),
                'std': max(np.std(values), 0.001),
                'min': np.min(values),
                'max': np.max(values)
            }
    
    def compute_intrinsic_reward(
        self,
        state_hash: str,
        prediction_error: float = 0.0,
        skill: Optional[str] = None,
        skill_performance: float = 0.0,
        goal_achieved: bool = False,
        goal_difficulty: float = 0.5
    ) -> RewardSignal:
        """Compute intrinsic motivation reward"""
        # Curiosity reward
        curiosity = self.intrinsic.curiosity_reward(state_hash, prediction_error)
        
        # Competence reward
        competence = 0.0
        if skill:
            competence = self.intrinsic.competence_reward(skill, skill_performance)
        
        # Autonomy reward
        autonomy = self.intrinsic.autonomy_reward(goal_achieved, goal_difficulty)
        
        # Combined intrinsic reward
        intrinsic_value = 0.5 * curiosity + 0.3 * competence + 0.2 * autonomy
        
        return self.process_reward(
            reward_type=RewardType.CURIOSITY,
            raw_value=intrinsic_value,
            source='intrinsic_motivation',
            metadata={
                'curiosity': curiosity,
                'competence': competence,
                'autonomy': autonomy
            }
        )
    
    def compute_combined_reward(
        self,
        rewards: List[RewardSignal]
    ) -> Tuple[float, Dict[str, float]]:
        """Compute combined reward from multiple signals"""
        combined = 0.0
        breakdown = {}
        
        for reward in rewards:
            objective = None
            for obj in self.objectives.values():
                if obj.reward_type == reward.reward_type:
                    objective = obj
                    break
            
            if objective:
                weighted_value = reward.value * objective.weight
                
                # Apply thresholds
                if objective.min_threshold is not None and reward.value < objective.min_threshold:
                    weighted_value -= 0.5  # Penalty for below threshold
                
                if objective.target is not None:
                    # Reward for approaching target
                    distance_to_target = abs(reward.raw_value - objective.target)
                    target_bonus = max(0, 1 - distance_to_target) * 0.2
                    weighted_value += target_bonus
                
                combined += weighted_value
                breakdown[objective.name] = weighted_value
            else:
                # Default weight
                combined += reward.value * 0.1
                breakdown[reward.reward_type.value] = reward.value * 0.1
        
        return combined, breakdown
    
    def adapt_weights(self):
        """Adapt objective weights based on performance"""
        for name, objective in self.objectives.items():
            if not objective.adaptive:
                continue
            
            # Get recent rewards for this type
            recent = list(self.aggregated_rewards[objective.reward_type])[-100:]
            
            if len(recent) < 10:
                continue
            
            # Increase weight if rewards are consistently positive
            avg_reward = np.mean(recent)
            
            if avg_reward > 0.3:
                # Decrease weight (already doing well)
                objective.weight = max(0.05, objective.weight * 0.95)
            elif avg_reward < -0.1:
                # Increase weight (needs more focus)
                objective.weight = min(0.5, objective.weight * 1.05)
            
            objective.weight_history.append(objective.weight)
        
        # Renormalize weights
        total_weight = sum(obj.weight for obj in self.objectives.values())
        if total_weight > 0:
            for obj in self.objectives.values():
                obj.weight /= total_weight
    
    def get_reward_summary(self, lookback: int = 100) -> Dict[str, Any]:
        """Get summary of recent rewards"""
        recent = list(self.reward_history)[-lookback:]
        
        if not recent:
            return {'status': 'no_rewards'}
        
        by_type = {}
        for rt in RewardType:
            type_rewards = [r for r in recent if r.reward_type == rt]
            if type_rewards:
                by_type[rt.value] = {
                    'count': len(type_rewards),
                    'mean': np.mean([r.value for r in type_rewards]),
                    'std': np.std([r.value for r in type_rewards]),
                    'total': sum(r.value for r in type_rewards)
                }
        
        return {
            'total_rewards': len(recent),
            'mean_reward': np.mean([r.value for r in recent]),
            'total_value': sum(r.value for r in recent),
            'by_type': by_type,
            'objective_weights': {name: obj.weight for name, obj in self.objectives.items()},
            'stats': self.stats
        }
    
    def set_objective_weight(self, objective_name: str, weight: float):
        """Manually set an objective weight"""
        if objective_name in self.objectives:
            self.objectives[objective_name].weight = weight
            logger.info(f"Set {objective_name} weight to {weight}")
    
    def add_objective(self, objective: RewardObjective):
        """Add a new reward objective"""
        self.objectives[objective.name] = objective
        logger.info(f"Added objective: {objective.name}")
