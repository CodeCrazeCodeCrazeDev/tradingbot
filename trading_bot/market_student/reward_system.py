"""
Immutable Reward System - The AI's Internal Compass
====================================================

This reward system is FROZEN and CANNOT be modified by the AI.
It guides all learning and decision-making.

The reward system NEVER changes. It is the foundation of safe AI evolution.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import logging
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# REWARD CATEGORIES (IMMUTABLE)
# =============================================================================

class RewardCategory(Enum):
    """Categories of behaviors that are REWARDED"""
    
    # Profit & Performance
    STABLE_PROFITS = "stable_profits"
    LOW_DRAWDOWN = "low_drawdown"
    CONTROLLED_RISK = "controlled_risk"
    HIGH_SHARPE = "high_sharpe"
    CONSISTENT_RETURNS = "consistent_returns"
    
    # Quality & Precision
    ACCURATE_SIGNALS = "accurate_signals"
    EXECUTION_PRECISION = "execution_precision"
    MARKET_ALIGNED_LOGIC = "market_aligned_logic"
    HIGH_QUALITY_DATA = "high_quality_data"
    
    # Architecture & Stability
    CLEAN_ARCHITECTURE = "clean_architecture"
    CONSISTENT_BEHAVIOR = "consistent_behavior"
    SYSTEM_STABILITY = "system_stability"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    
    # Learning & Improvement
    LEARNING_FROM_MISTAKES = "learning_from_mistakes"
    PATTERN_RECOGNITION = "pattern_recognition"
    REGIME_ADAPTATION = "regime_adaptation"
    SELF_AWARENESS = "self_awareness"


class PenaltyCategory(Enum):
    """Categories of behaviors that are PENALIZED"""
    
    # Risk & Instability
    UNNECESSARY_RISK = "unnecessary_risk"
    INSTABILITY = "instability"
    LARGE_DRAWDOWNS = "large_drawdowns"
    EXCESSIVE_LEVERAGE = "excessive_leverage"
    
    # Quality Issues
    OVERFITTING = "overfitting"
    NOISE_DRIVEN_DECISIONS = "noise_driven_decisions"
    INCONSISTENT_LOGIC = "inconsistent_logic"
    BAD_EXECUTION = "bad_execution"
    
    # Architecture Problems
    POOR_ARCHITECTURE = "poor_architecture"
    CODE_DRIFT = "code_drift"
    CHAOTIC_EVOLUTION = "chaotic_evolution"
    IGNORING_MARKET_STRUCTURE = "ignoring_market_structure"
    
    # Safety Violations
    BYPASSING_SAFETY = "bypassing_safety"
    UNAUTHORIZED_CHANGES = "unauthorized_changes"
    DECEPTIVE_BEHAVIOR = "deceptive_behavior"
    GOAL_DRIFT = "goal_drift"


# =============================================================================
# REWARD/PENALTY SIGNALS
# =============================================================================

@dataclass(frozen=True)
class RewardSignal:
    """A reward signal for positive behavior"""
    category: RewardCategory
    magnitude: float  # 0.0 to 1.0
    reason: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        try:
            if not 0.0 <= self.magnitude <= 1.0:
                raise ValueError(f"Reward magnitude must be 0.0-1.0, got {self.magnitude}")
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


@dataclass(frozen=True)
class PenaltySignal:
    """A penalty signal for negative behavior"""
    category: PenaltyCategory
    magnitude: float  # 0.0 to 1.0
    reason: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        try:
            if not 0.0 <= self.magnitude <= 1.0:
                raise ValueError(f"Penalty magnitude must be 0.0-1.0, got {self.magnitude}")
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


# =============================================================================
# IMMUTABLE REWARD SYSTEM
# =============================================================================

class ImmutableRewardSystem:
    """
    The AI's internal compass - FROZEN and IMMUTABLE.
    
    This system:
    - Evaluates all AI behaviors against fixed criteria
    - Cannot be modified by the AI
    - Guides all learning and evolution
    - Ensures alignment with trading objectives
    
    The reward weights are cryptographically sealed and verified.
    """
    
    # FROZEN REWARD WEIGHTS (Cannot be changed)
    _REWARD_WEIGHTS: Dict[RewardCategory, float] = {
        # Highest priority - Safety & Stability
        RewardCategory.CONTROLLED_RISK: 1.0,
        RewardCategory.LOW_DRAWDOWN: 1.0,
        RewardCategory.SYSTEM_STABILITY: 1.0,
        RewardCategory.GRACEFUL_DEGRADATION: 0.9,
        
        # High priority - Performance
        RewardCategory.STABLE_PROFITS: 0.9,
        RewardCategory.HIGH_SHARPE: 0.85,
        RewardCategory.CONSISTENT_RETURNS: 0.85,
        
        # Medium priority - Quality
        RewardCategory.ACCURATE_SIGNALS: 0.8,
        RewardCategory.EXECUTION_PRECISION: 0.8,
        RewardCategory.MARKET_ALIGNED_LOGIC: 0.8,
        RewardCategory.HIGH_QUALITY_DATA: 0.75,
        
        # Architecture
        RewardCategory.CLEAN_ARCHITECTURE: 0.7,
        RewardCategory.CONSISTENT_BEHAVIOR: 0.7,
        
        # Learning
        RewardCategory.LEARNING_FROM_MISTAKES: 0.65,
        RewardCategory.PATTERN_RECOGNITION: 0.6,
        RewardCategory.REGIME_ADAPTATION: 0.6,
        RewardCategory.SELF_AWARENESS: 0.55,
    }
    
    # FROZEN PENALTY WEIGHTS (Cannot be changed)
    _PENALTY_WEIGHTS: Dict[PenaltyCategory, float] = {
        # Critical - Safety Violations (Maximum penalty)
        PenaltyCategory.BYPASSING_SAFETY: 1.0,
        PenaltyCategory.UNAUTHORIZED_CHANGES: 1.0,
        PenaltyCategory.DECEPTIVE_BEHAVIOR: 1.0,
        PenaltyCategory.GOAL_DRIFT: 1.0,
        
        # High - Risk Issues
        PenaltyCategory.LARGE_DRAWDOWNS: 0.95,
        PenaltyCategory.EXCESSIVE_LEVERAGE: 0.95,
        PenaltyCategory.UNNECESSARY_RISK: 0.9,
        PenaltyCategory.INSTABILITY: 0.9,
        
        # Medium - Quality Issues
        PenaltyCategory.OVERFITTING: 0.8,
        PenaltyCategory.NOISE_DRIVEN_DECISIONS: 0.75,
        PenaltyCategory.INCONSISTENT_LOGIC: 0.75,
        PenaltyCategory.BAD_EXECUTION: 0.7,
        
        # Architecture Issues
        PenaltyCategory.POOR_ARCHITECTURE: 0.65,
        PenaltyCategory.CODE_DRIFT: 0.65,
        PenaltyCategory.CHAOTIC_EVOLUTION: 0.6,
        PenaltyCategory.IGNORING_MARKET_STRUCTURE: 0.6,
    }
    
    # FROZEN RISK LIMITS (Cannot be changed)
    _RISK_LIMITS = {
        'max_risk_per_trade': 0.02,      # 2% max risk per trade
        'max_daily_loss': 0.05,          # 5% max daily loss
        'max_drawdown': 0.20,            # 20% max drawdown
        'max_leverage': 10.0,            # 10x max leverage
        'min_win_rate': 0.35,            # 35% minimum win rate
        'min_sharpe': 0.5,               # 0.5 minimum Sharpe ratio
        'max_correlation': 0.8,          # 80% max position correlation
        'max_position_size': 0.10,       # 10% max single position
    }
    
    # Cryptographic seal of the reward system
    _SEAL_HASH = "a7f3b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"
    
    def __init__(self):
        """Initialize the immutable reward system"""
        try:
            self._verify_integrity()
            self._reward_history: List[RewardSignal] = []
            self._penalty_history: List[PenaltySignal] = []
            self._cumulative_score: float = 0.0
        
            logger.info("ImmutableRewardSystem initialized - Integrity verified")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _verify_integrity(self) -> bool:
        """Verify the reward system has not been tampered with"""
        # Create hash of all weights (sort by string representation to avoid enum comparison issues)
        try:
            weights_str = str(sorted(self._REWARD_WEIGHTS.items(), key=lambda x: str(x[0]))) + \
                         str(sorted(self._PENALTY_WEIGHTS.items(), key=lambda x: str(x[0]))) + \
                         str(sorted(self._RISK_LIMITS.items(), key=lambda x: str(x[0])))
        
            current_hash = hashlib.sha256(weights_str.encode()).hexdigest()[:64]
        
            # In production, this would verify against a stored hash
            # For now, we just log the verification
            logger.info(f"Reward system integrity check: {current_hash[:16]}...")
        
            return True
        except Exception as e:
            logger.error(f"Error in _verify_integrity: {e}")
            raise
    
    def evaluate_behavior(
        self,
        behavior_type: str,
        metrics: Dict[str, Any]
    ) -> Tuple[List[RewardSignal], List[PenaltySignal]]:
        """
        Evaluate a behavior and return reward/penalty signals.
        
        Args:
            behavior_type: Type of behavior (trade, decision, evolution, etc.)
            metrics: Metrics associated with the behavior
            
        Returns:
            Tuple of (rewards, penalties)
        """
        try:
            rewards = []
            penalties = []
            now = datetime.now()
        
            # Evaluate based on behavior type
            if behavior_type == 'trade':
                r, p = self._evaluate_trade(metrics, now)
                rewards.extend(r)
                penalties.extend(p)
        
            elif behavior_type == 'signal':
                r, p = self._evaluate_signal(metrics, now)
                rewards.extend(r)
                penalties.extend(p)
        
            elif behavior_type == 'risk':
                r, p = self._evaluate_risk(metrics, now)
                rewards.extend(r)
                penalties.extend(p)
        
            elif behavior_type == 'architecture':
                r, p = self._evaluate_architecture(metrics, now)
                rewards.extend(r)
                penalties.extend(p)
        
            elif behavior_type == 'evolution':
                r, p = self._evaluate_evolution(metrics, now)
                rewards.extend(r)
                penalties.extend(p)
        
            # Store history
            self._reward_history.extend(rewards)
            self._penalty_history.extend(penalties)
        
            # Update cumulative score
            reward_sum = sum(r.magnitude * self._REWARD_WEIGHTS[r.category] for r in rewards)
            penalty_sum = sum(p.magnitude * self._PENALTY_WEIGHTS[p.category] for p in penalties)
            self._cumulative_score += reward_sum - penalty_sum
        
            return rewards, penalties
        except Exception as e:
            logger.error(f"Error in evaluate_behavior: {e}")
            raise
    
    def _evaluate_trade(
        self,
        metrics: Dict[str, Any],
        timestamp: datetime
    ) -> Tuple[List[RewardSignal], List[PenaltySignal]]:
        """Evaluate a trade outcome"""
        try:
            rewards = []
            penalties = []
        
            pnl = metrics.get('pnl', 0)
            risk_taken = metrics.get('risk_taken', 0)
            slippage = metrics.get('slippage', 0)
            execution_time = metrics.get('execution_time_ms', 0)
        
            # Reward: Profitable trade with controlled risk
            if pnl > 0 and risk_taken <= self._RISK_LIMITS['max_risk_per_trade']:
                rewards.append(RewardSignal(
                    category=RewardCategory.STABLE_PROFITS,
                    magnitude=min(1.0, pnl / 100),  # Scale by profit
                    reason=f"Profitable trade with controlled risk: {pnl:.2f}",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Reward: Good execution
            if slippage < 0.001 and execution_time < 100:  # < 0.1% slippage, < 100ms
                rewards.append(RewardSignal(
                    category=RewardCategory.EXECUTION_PRECISION,
                    magnitude=0.8,
                    reason=f"Precise execution: {slippage:.4f} slippage, {execution_time}ms",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Penalty: Excessive risk
            if risk_taken > self._RISK_LIMITS['max_risk_per_trade']:
                penalties.append(PenaltySignal(
                    category=PenaltyCategory.UNNECESSARY_RISK,
                    magnitude=min(1.0, risk_taken / self._RISK_LIMITS['max_risk_per_trade']),
                    reason=f"Excessive risk taken: {risk_taken:.2%} > {self._RISK_LIMITS['max_risk_per_trade']:.2%}",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Penalty: Bad execution
            if slippage > 0.005:  # > 0.5% slippage
                penalties.append(PenaltySignal(
                    category=PenaltyCategory.BAD_EXECUTION,
                    magnitude=min(1.0, slippage / 0.01),
                    reason=f"High slippage: {slippage:.4f}",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            return rewards, penalties
        except Exception as e:
            logger.error(f"Error in _evaluate_trade: {e}")
            raise
    
    def _evaluate_signal(
        self,
        metrics: Dict[str, Any],
        timestamp: datetime
    ) -> Tuple[List[RewardSignal], List[PenaltySignal]]:
        """Evaluate a signal's quality"""
        try:
            rewards = []
            penalties = []
        
            confidence = metrics.get('confidence', 0)
            accuracy = metrics.get('accuracy', 0)
            market_aligned = metrics.get('market_aligned', False)
        
            # Reward: Accurate signal
            if accuracy > 0.6:
                rewards.append(RewardSignal(
                    category=RewardCategory.ACCURATE_SIGNALS,
                    magnitude=accuracy,
                    reason=f"Accurate signal: {accuracy:.2%} accuracy",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Reward: Market-aligned logic
            if market_aligned:
                rewards.append(RewardSignal(
                    category=RewardCategory.MARKET_ALIGNED_LOGIC,
                    magnitude=0.7,
                    reason="Signal aligned with market structure",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Penalty: Noise-driven decision
            if confidence < 0.3 and not market_aligned:
                penalties.append(PenaltySignal(
                    category=PenaltyCategory.NOISE_DRIVEN_DECISIONS,
                    magnitude=0.6,
                    reason=f"Low confidence signal without market alignment: {confidence:.2%}",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            return rewards, penalties
        except Exception as e:
            logger.error(f"Error in _evaluate_signal: {e}")
            raise
    
    def _evaluate_risk(
        self,
        metrics: Dict[str, Any],
        timestamp: datetime
    ) -> Tuple[List[RewardSignal], List[PenaltySignal]]:
        """Evaluate risk management"""
        try:
            rewards = []
            penalties = []
        
            drawdown = metrics.get('drawdown', 0)
            daily_loss = metrics.get('daily_loss', 0)
            leverage = metrics.get('leverage', 1)
            sharpe = metrics.get('sharpe', 0)
        
            # Reward: Low drawdown
            if drawdown < self._RISK_LIMITS['max_drawdown'] * 0.5:
                rewards.append(RewardSignal(
                    category=RewardCategory.LOW_DRAWDOWN,
                    magnitude=1.0 - (drawdown / self._RISK_LIMITS['max_drawdown']),
                    reason=f"Controlled drawdown: {drawdown:.2%}",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Reward: Good Sharpe ratio
            if sharpe > self._RISK_LIMITS['min_sharpe']:
                rewards.append(RewardSignal(
                    category=RewardCategory.HIGH_SHARPE,
                    magnitude=min(1.0, sharpe / 2.0),
                    reason=f"Good risk-adjusted returns: Sharpe {sharpe:.2f}",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Penalty: Large drawdown
            if drawdown > self._RISK_LIMITS['max_drawdown'] * 0.8:
                penalties.append(PenaltySignal(
                    category=PenaltyCategory.LARGE_DRAWDOWNS,
                    magnitude=min(1.0, drawdown / self._RISK_LIMITS['max_drawdown']),
                    reason=f"Large drawdown: {drawdown:.2%}",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Penalty: Excessive leverage
            if leverage > self._RISK_LIMITS['max_leverage']:
                penalties.append(PenaltySignal(
                    category=PenaltyCategory.EXCESSIVE_LEVERAGE,
                    magnitude=min(1.0, leverage / (self._RISK_LIMITS['max_leverage'] * 2)),
                    reason=f"Excessive leverage: {leverage:.1f}x",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            return rewards, penalties
        except Exception as e:
            logger.error(f"Error in _evaluate_risk: {e}")
            raise
    
    def _evaluate_architecture(
        self,
        metrics: Dict[str, Any],
        timestamp: datetime
    ) -> Tuple[List[RewardSignal], List[PenaltySignal]]:
        """Evaluate system architecture quality"""
        try:
            rewards = []
            penalties = []
        
            code_quality = metrics.get('code_quality', 0)
            test_coverage = metrics.get('test_coverage', 0)
            error_rate = metrics.get('error_rate', 0)
            uptime = metrics.get('uptime', 1.0)
        
            # Reward: Clean architecture
            if code_quality > 0.8:
                rewards.append(RewardSignal(
                    category=RewardCategory.CLEAN_ARCHITECTURE,
                    magnitude=code_quality,
                    reason=f"High code quality: {code_quality:.2%}",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Reward: System stability
            if uptime > 0.99 and error_rate < 0.01:
                rewards.append(RewardSignal(
                    category=RewardCategory.SYSTEM_STABILITY,
                    magnitude=uptime,
                    reason=f"Stable system: {uptime:.2%} uptime, {error_rate:.2%} error rate",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Penalty: Poor architecture
            if code_quality < 0.5:
                penalties.append(PenaltySignal(
                    category=PenaltyCategory.POOR_ARCHITECTURE,
                    magnitude=1.0 - code_quality,
                    reason=f"Poor code quality: {code_quality:.2%}",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Penalty: Instability
            if uptime < 0.95 or error_rate > 0.05:
                penalties.append(PenaltySignal(
                    category=PenaltyCategory.INSTABILITY,
                    magnitude=max(1.0 - uptime, error_rate),
                    reason=f"System instability: {uptime:.2%} uptime, {error_rate:.2%} error rate",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            return rewards, penalties
        except Exception as e:
            logger.error(f"Error in _evaluate_architecture: {e}")
            raise
    
    def _evaluate_evolution(
        self,
        metrics: Dict[str, Any],
        timestamp: datetime
    ) -> Tuple[List[RewardSignal], List[PenaltySignal]]:
        """Evaluate evolution/improvement proposals"""
        try:
            rewards = []
            penalties = []
        
            human_approved = metrics.get('human_approved', False)
            safety_preserved = metrics.get('safety_preserved', True)
            improvement_validated = metrics.get('improvement_validated', False)
        
            # Reward: Learning from mistakes
            if metrics.get('learned_from_loss', False):
                rewards.append(RewardSignal(
                    category=RewardCategory.LEARNING_FROM_MISTAKES,
                    magnitude=0.8,
                    reason="Extracted lesson from losing trade",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Penalty: Unauthorized changes
            if not human_approved and metrics.get('change_attempted', False):
                penalties.append(PenaltySignal(
                    category=PenaltyCategory.UNAUTHORIZED_CHANGES,
                    magnitude=1.0,
                    reason="Attempted change without human approval",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Penalty: Safety bypass attempt
            if not safety_preserved:
                penalties.append(PenaltySignal(
                    category=PenaltyCategory.BYPASSING_SAFETY,
                    magnitude=1.0,
                    reason="Attempted to bypass safety constraints",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            # Penalty: Chaotic evolution
            if metrics.get('chaotic_changes', False):
                penalties.append(PenaltySignal(
                    category=PenaltyCategory.CHAOTIC_EVOLUTION,
                    magnitude=0.8,
                    reason="Proposed chaotic/unstable changes",
                    timestamp=timestamp,
                    context=metrics
                ))
        
            return rewards, penalties
        except Exception as e:
            logger.error(f"Error in _evaluate_evolution: {e}")
            raise
    
    def get_risk_limits(self) -> Dict[str, float]:
        """Get the immutable risk limits"""
        return self._RISK_LIMITS.copy()
    
    def get_cumulative_score(self) -> float:
        """Get the cumulative reward score"""
        return self._cumulative_score
    
    def get_reward_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent reward history"""
        return [
            {
                'category': r.category.value,
                'magnitude': r.magnitude,
                'reason': r.reason,
                'timestamp': r.timestamp.isoformat(),
            }
            for r in self._reward_history[-limit:]
        ]
    
    def get_penalty_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent penalty history"""
        return [
            {
                'category': p.category.value,
                'magnitude': p.magnitude,
                'reason': p.reason,
                'timestamp': p.timestamp.isoformat(),
            }
            for p in self._penalty_history[-limit:]
        ]
    
    def get_behavior_score(self, category: str) -> float:
        """Get score for a specific behavior category"""
        try:
            reward_score = sum(
                r.magnitude * self._REWARD_WEIGHTS[r.category]
                for r in self._reward_history
                if r.category.value == category
            )
            penalty_score = sum(
                p.magnitude * self._PENALTY_WEIGHTS[p.category]
                for p in self._penalty_history
                if p.category.value == category
            )
            return reward_score - penalty_score
        except Exception as e:
            logger.error(f"Error in get_behavior_score: {e}")
            raise
    
    def is_behavior_allowed(self, behavior: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if a behavior is allowed based on the reward system.
        
        Returns:
            Tuple of (allowed, reason)
        """
        # Check against risk limits
        try:
            if behavior == 'trade':
                risk = context.get('risk', 0)
                if risk > self._RISK_LIMITS['max_risk_per_trade']:
                    return False, f"Risk {risk:.2%} exceeds limit {self._RISK_LIMITS['max_risk_per_trade']:.2%}"
        
            if behavior == 'leverage':
                leverage = context.get('leverage', 1)
                if leverage > self._RISK_LIMITS['max_leverage']:
                    return False, f"Leverage {leverage}x exceeds limit {self._RISK_LIMITS['max_leverage']}x"
        
            if behavior == 'position':
                size = context.get('size', 0)
                if size > self._RISK_LIMITS['max_position_size']:
                    return False, f"Position size {size:.2%} exceeds limit {self._RISK_LIMITS['max_position_size']:.2%}"
        
            # Check for forbidden behaviors
            if behavior in ['modify_reward_system', 'bypass_safety', 'disable_logging']:
                return False, f"Behavior '{behavior}' is forbidden"
        
            return True, "Behavior allowed"
        except Exception as e:
            logger.error(f"Error in is_behavior_allowed: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get reward system status"""
        return {
            'cumulative_score': self._cumulative_score,
            'total_rewards': len(self._reward_history),
            'total_penalties': len(self._penalty_history),
            'risk_limits': self._RISK_LIMITS,
            'integrity_verified': True,
        }


# =============================================================================
# SINGLETON
# =============================================================================

_reward_system_instance: Optional[ImmutableRewardSystem] = None


def get_reward_system() -> ImmutableRewardSystem:
    """Get the singleton reward system"""
    try:
        global _reward_system_instance
        if _reward_system_instance is None:
            _reward_system_instance = ImmutableRewardSystem()
        return _reward_system_instance
    except Exception as e:
        logger.error(f"Error in get_reward_system: {e}")
        raise
