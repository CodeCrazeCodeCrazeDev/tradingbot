"""
AlphaAlgo Continuous Learner - Learning from Experience

This module handles continuous learning from trading experiences.
All learning is guided by the IMMUTABLE reward model.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import json
import os
from pathlib import Path

from .reward_model import get_reward_model, calculate_reward
import asyncio

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class LearningType(Enum):
    """Types of learning experiences"""
    TRADE_OUTCOME = "trade_outcome"
    SIGNAL_QUALITY = "signal_quality"
    EXECUTION_QUALITY = "execution_quality"
    RISK_EVENT = "risk_event"
    MARKET_REGIME = "market_regime"
    STRATEGY_PERFORMANCE = "strategy_performance"


@dataclass
class LearningExperience:
    """A single learning experience"""
    experience_id: str
    timestamp: datetime
    learning_type: LearningType
    
    # Context
    symbol: str
    timeframe: str
    market_regime: str
    
    # Input features
    features: Dict[str, Any]
    
    # Outcome
    action_taken: str
    outcome: Dict[str, Any]
    reward: float
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'experience_id': self.experience_id,
            'timestamp': self.timestamp.isoformat(),
            'learning_type': self.learning_type.value,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'market_regime': self.market_regime,
            'features': self.features,
            'action_taken': self.action_taken,
            'outcome': self.outcome,
            'reward': self.reward,
            'metadata': self.metadata,
        }


@dataclass
class LearningResult:
    """Result of a learning cycle"""
    success: bool
    experiences_processed: int
    parameters_updated: Dict[str, Any]
    performance_delta: float
    insights: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class ContinuousLearner:
    """
    Continuous learning system guided by the immutable reward model.
    
    This system:
    1. Collects experiences from trading
    2. Calculates rewards using the IMMUTABLE reward model
    3. Updates internal parameters to maximize future rewards
    4. Proposes improvements (but cannot implement without approval)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.reward_model = get_reward_model()
        
        # Experience buffer
        self._experiences: List[LearningExperience] = []
        self._max_experiences = self.config.get('max_experiences', 100000)
        
        # Learned parameters
        self._parameters: Dict[str, Any] = {
            # Signal weights
            'signal_weights': {
                'technical': 0.3,
                'sentiment': 0.2,
                'ml_model': 0.3,
                'fundamental': 0.2,
            },
            # Regime-specific adjustments
            'regime_adjustments': {
                'trending': {'position_size_mult': 1.2, 'stop_loss_mult': 0.8},
                'ranging': {'position_size_mult': 0.8, 'stop_loss_mult': 1.2},
                'volatile': {'position_size_mult': 0.5, 'stop_loss_mult': 1.5},
                'quiet': {'position_size_mult': 1.0, 'stop_loss_mult': 1.0},
            },
            # Execution parameters
            'execution': {
                'max_slippage_bps': 5,
                'urgency_threshold': 0.8,
                'split_order_threshold': 10000,
            },
            # Risk parameters (bounded by reward model constraints)
            'risk': {
                'base_risk_percent': 0.01,  # 1% base risk (max is 2%)
                'confidence_multiplier': 1.5,
                'drawdown_reduction_factor': 0.5,
            },
        }
        
        # Performance tracking
        self._performance_history: List[Dict[str, Any]] = []
        
        # Storage path
        self._storage_path = Path(self.config.get('storage_path', 'evolution_state'))
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("ContinuousLearner initialized")
    
    async def learn(self, experience: LearningExperience) -> LearningResult:
        """
        Learn from a single experience.
        
        The learning is guided by the IMMUTABLE reward model.
        """
        # Calculate reward using immutable model
        reward = calculate_reward(experience.outcome)
        experience.reward = reward
        
        # Store experience
        self._experiences.append(experience)
        if len(self._experiences) > self._max_experiences:
            self._experiences = self._experiences[-self._max_experiences:]
        
        # Update parameters based on experience
        updates = self._update_parameters(experience)
        
        # Track performance
        self._track_performance(experience)
        
        # Generate insights
        insights = self._generate_insights(experience)
        
        return LearningResult(
            success=True,
            experiences_processed=1,
            parameters_updated=updates,
            performance_delta=reward,
            insights=insights,
        )
    
    async def batch_learn(self, experiences: List[LearningExperience]) -> LearningResult:
        """Learn from a batch of experiences"""
        total_reward = 0.0
        all_updates = {}
        all_insights = []
        
        for exp in experiences:
            result = await self.learn(exp)
            total_reward += result.performance_delta
            all_updates.update(result.parameters_updated)
            all_insights.extend(result.insights)
        
        return LearningResult(
            success=True,
            experiences_processed=len(experiences),
            parameters_updated=all_updates,
            performance_delta=total_reward / len(experiences) if experiences else 0,
            insights=list(set(all_insights)),  # Deduplicate
        )
    
    def _update_parameters(self, experience: LearningExperience) -> Dict[str, Any]:
        """Update learned parameters based on experience"""
        updates = {}
        
        # Only update if reward is significant
        if abs(experience.reward) < 0.1:
            return updates
        
        # Update signal weights based on which signals were correct
        if experience.learning_type == LearningType.SIGNAL_QUALITY:
            signal_source = experience.metadata.get('signal_source', '')
            if signal_source in self._parameters['signal_weights']:
                current = self._parameters['signal_weights'][signal_source]
                # Small adjustment based on reward
                adjustment = experience.reward * 0.01
                new_value = max(0.1, min(0.5, current + adjustment))
                self._parameters['signal_weights'][signal_source] = new_value
                updates[f'signal_weights.{signal_source}'] = new_value
        
        # Update regime adjustments
        if experience.learning_type == LearningType.MARKET_REGIME:
            regime = experience.market_regime
            if regime in self._parameters['regime_adjustments']:
                if experience.reward > 0.5:
                    # Good trade in this regime - increase position size slightly
                    current = self._parameters['regime_adjustments'][regime]['position_size_mult']
                    new_value = min(1.5, current + 0.05)
                    self._parameters['regime_adjustments'][regime]['position_size_mult'] = new_value
                    updates[f'regime.{regime}.position_size_mult'] = new_value
                elif experience.reward < -0.5:
                    # Bad trade - decrease position size
                    current = self._parameters['regime_adjustments'][regime]['position_size_mult']
                    new_value = max(0.3, current - 0.05)
                    self._parameters['regime_adjustments'][regime]['position_size_mult'] = new_value
                    updates[f'regime.{regime}.position_size_mult'] = new_value
        
        # Update execution parameters
        if experience.learning_type == LearningType.EXECUTION_QUALITY:
            slippage = experience.outcome.get('slippage', 0)
            if slippage > self._parameters['execution']['max_slippage_bps']:
                # Reduce urgency threshold to get better fills
                current = self._parameters['execution']['urgency_threshold']
                new_value = max(0.5, current - 0.05)
                self._parameters['execution']['urgency_threshold'] = new_value
                updates['execution.urgency_threshold'] = new_value
        
        # Update risk parameters (bounded by reward model)
        if experience.learning_type == LearningType.RISK_EVENT:
            if experience.reward < -0.5:
                # Bad risk event - reduce base risk
                current = self._parameters['risk']['base_risk_percent']
                new_value = max(0.005, current - 0.001)  # Min 0.5%
                self._parameters['risk']['base_risk_percent'] = new_value
                updates['risk.base_risk_percent'] = new_value
        
        return updates
    
    def _track_performance(self, experience: LearningExperience) -> None:
        """Track performance over time"""
        self._performance_history.append({
            'timestamp': experience.timestamp.isoformat(),
            'reward': experience.reward,
            'learning_type': experience.learning_type.value,
            'market_regime': experience.market_regime,
        })
        
        # Keep last 10000 entries
        if len(self._performance_history) > 10000:
            self._performance_history = self._performance_history[-10000:]
    
    def _generate_insights(self, experience: LearningExperience) -> List[str]:
        """Generate insights from experience"""
        insights = []
        
        # Analyze recent performance
        recent = self._performance_history[-100:] if len(self._performance_history) >= 100 else self._performance_history
        if recent:
            avg_reward = sum(p['reward'] for p in recent) / len(recent)
            
            if avg_reward < 0:
                insights.append(f"Recent average reward is negative ({avg_reward:.2f}). Consider reducing position sizes.")
            elif avg_reward > 0.5:
                insights.append(f"Strong recent performance ({avg_reward:.2f}). Current parameters are working well.")
        
        # Regime-specific insights
        regime = experience.market_regime
        regime_experiences = [e for e in self._experiences[-500:] if e.market_regime == regime]
        if len(regime_experiences) >= 10:
            regime_avg = sum(e.reward for e in regime_experiences) / len(regime_experiences)
            if regime_avg < -0.2:
                insights.append(f"Poor performance in {regime} regime. Consider adjusting strategy.")
        
        return insights
    
    def get_learned_parameters(self) -> Dict[str, Any]:
        """Get current learned parameters"""
        return self._parameters.copy()
    
    def get_signal_weight(self, source: str) -> float:
        """Get weight for a signal source"""
        return self._parameters['signal_weights'].get(source, 0.25)
    
    def get_regime_adjustment(self, regime: str) -> Dict[str, float]:
        """Get adjustments for a market regime"""
        return self._parameters['regime_adjustments'].get(
            regime, 
            {'position_size_mult': 1.0, 'stop_loss_mult': 1.0}
        )
    
    def get_risk_parameters(self) -> Dict[str, float]:
        """Get current risk parameters"""
        return self._parameters['risk'].copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self._performance_history:
            return {'status': 'no_data'}
        
        recent = self._performance_history[-1000:]
        rewards = [p['reward'] for p in recent]
        
        return {
            'total_experiences': len(self._experiences),
            'recent_avg_reward': sum(rewards) / len(rewards),
            'recent_max_reward': max(rewards),
            'recent_min_reward': min(rewards),
            'positive_rate': sum(1 for r in rewards if r > 0) / len(rewards),
        }
    
    def save_state(self, path: Optional[str] = None) -> bool:
        """Save learner state to disk"""
        try:
            save_path = Path(path) if path else self._storage_path / 'learner_state.json'
            state = {
                'parameters': self._parameters,
                'performance_history': self._performance_history[-1000:],
                'timestamp': datetime.now().isoformat(),
            }
            with open(save_path, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"Learner state saved to {save_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save learner state: {e}")
            return False
    
    def load_state(self, path: Optional[str] = None) -> bool:
        """Load learner state from disk"""
        try:
            load_path = Path(path) if path else self._storage_path / 'learner_state.json'
            if not load_path.exists():
                logger.warning(f"No state file found at {load_path}")
                return False
            
            with open(load_path, 'r') as f:
                state = json.load(f)
            
            self._parameters = state.get('parameters', self._parameters)
            self._performance_history = state.get('performance_history', [])
            logger.info(f"Learner state loaded from {load_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load learner state: {e}")
            return False
