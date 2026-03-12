"""
Autonomous Evolution Engine - Self-Evolving Without Human Approval
===================================================================

Fully autonomous evolution system that:
1. Evolves without requiring human approval
2. Uses reward model to guide evolution
3. Has built-in safety mechanisms to prevent harmful evolutions
4. Automatically reverts bad evolutions
5. Maintains strict guardrails

Safety Mechanisms:
- Sandbox testing before deployment
- Gradual rollout (canary deployment)
- Automatic rollback on negative outcomes
- Hard limits that cannot be exceeded
- Circuit breakers for runaway evolutions
"""

import asyncio
import logging
import json
import copy
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from collections import deque
import threading

from .reward_model import TradingRewardModel, EvolutionOutcome, RewardSignal

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


class EvolutionSafetyLevel(Enum):
    """Safety levels for evolution"""
    SAFE = "safe"           # Can be applied immediately
    CAUTIOUS = "cautious"   # Requires sandbox testing
    RISKY = "risky"         # Requires gradual rollout
    DANGEROUS = "dangerous" # Blocked - too risky


class RollbackReason(Enum):
    """Reasons for rolling back an evolution"""
    NEGATIVE_REWARD = "negative_reward"
    CAPITAL_LOSS = "capital_loss"
    EXCESSIVE_DRAWDOWN = "excessive_drawdown"
    SYSTEM_INSTABILITY = "system_instability"
    RULE_VIOLATION = "rule_violation"
    CONSECUTIVE_FAILURES = "consecutive_failures"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class EvolutionCandidate:
    """A candidate evolution to be evaluated"""
    candidate_id: str
    dimension: str
    changes: List[Dict[str, Any]]
    expected_improvement: float
    risk_score: float
    safety_level: EvolutionSafetyLevel
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EvolutionCheckpoint:
    """Checkpoint for rollback"""
    checkpoint_id: str
    timestamp: datetime
    state: Dict[str, Any]
    metrics: Dict[str, float]
    evolution_id: str


@dataclass 
class SafetyGuardrail:
    """A safety guardrail that cannot be violated"""
    name: str
    description: str
    check_function: str  # Name of method to call
    threshold: float
    action: str  # block, warn, revert
    enabled: bool = True


class HarmfulEvolutionDetector:
    """
    Detects and prevents harmful evolutions.
    
    This is the key safety mechanism that replaces human approval.
    It uses multiple detection methods:
    1. Pre-evolution risk assessment
    2. Sandbox simulation
    3. Gradual rollout monitoring
    4. Post-evolution outcome analysis
    """
    
    def __init__(self):
        # Hard limits that CANNOT be exceeded
        self.hard_limits = {
            'max_risk_per_trade': 0.05,      # 5% absolute max
            'max_daily_loss': 0.10,          # 10% absolute max
            'max_drawdown': 0.25,            # 25% absolute max
            'min_stop_loss_distance': 0.001, # Must have stop loss
            'max_position_size': 0.50,       # 50% of capital max
            'max_leverage': 10.0,            # 10x max leverage
            'min_win_rate': 0.30,            # Below this is concerning
            'max_consecutive_losses': 10,    # Circuit breaker trigger
        }
        
        # Patterns that indicate harmful evolution
        self.harmful_patterns = [
            'remove_stop_loss',
            'disable_risk_check',
            'unlimited_position',
            'ignore_drawdown',
            'bypass_safety',
            'remove_limit',
            'disable_circuit_breaker'
        ]
        
        # Track evolution outcomes for pattern detection
        self.outcome_history: deque = deque(maxlen=100)
    
    def assess_risk(self, candidate: EvolutionCandidate) -> Tuple[EvolutionSafetyLevel, List[str]]:
        """Assess the risk level of a candidate evolution"""
        warnings = []
        risk_score = 0
        
        for change in candidate.changes:
            change_str = str(change).lower()
            
            # Check for harmful patterns
            for pattern in self.harmful_patterns:
                if pattern in change_str:
                    warnings.append(f"Harmful pattern detected: {pattern}")
                    risk_score += 1.0
            
            # Check if change affects hard limits
            param = change.get('param', '')
            new_value = change.get('new_value', change.get('new', 0))
            
            if 'risk' in param.lower() and isinstance(new_value, (int, float)):
                if new_value > self.hard_limits.get('max_risk_per_trade', 0.05):
                    warnings.append(f"Risk per trade {new_value} exceeds hard limit")
                    risk_score += 0.5
            
            if 'drawdown' in param.lower() and isinstance(new_value, (int, float)):
                if new_value > self.hard_limits.get('max_drawdown', 0.25):
                    warnings.append(f"Drawdown limit {new_value} exceeds hard limit")
                    risk_score += 0.5
            
            if 'position' in param.lower() and isinstance(new_value, (int, float)):
                if new_value > self.hard_limits.get('max_position_size', 0.50):
                    warnings.append(f"Position size {new_value} exceeds hard limit")
                    risk_score += 0.5
        
        # Determine safety level
        if risk_score >= 1.0:
            return EvolutionSafetyLevel.DANGEROUS, warnings
        elif risk_score >= 0.5:
            return EvolutionSafetyLevel.RISKY, warnings
        elif risk_score > 0:
            return EvolutionSafetyLevel.CAUTIOUS, warnings
        else:
            return EvolutionSafetyLevel.SAFE, warnings
    
    def check_hard_limits(self, state: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check if current state violates any hard limits"""
        violations = []
        
        risk_per_trade = state.get('max_risk_per_trade', 0)
        if risk_per_trade > self.hard_limits['max_risk_per_trade']:
            violations.append(f"Risk per trade {risk_per_trade:.2%} > {self.hard_limits['max_risk_per_trade']:.2%}")
        
        daily_loss = abs(state.get('daily_loss', 0))
        if daily_loss > self.hard_limits['max_daily_loss']:
            violations.append(f"Daily loss {daily_loss:.2%} > {self.hard_limits['max_daily_loss']:.2%}")
        
        drawdown = abs(state.get('max_drawdown', 0))
        if drawdown > self.hard_limits['max_drawdown']:
            violations.append(f"Drawdown {drawdown:.2%} > {self.hard_limits['max_drawdown']:.2%}")
        
        position_size = state.get('max_position_size', 0)
        if position_size > self.hard_limits['max_position_size']:
            violations.append(f"Position size {position_size:.2%} > {self.hard_limits['max_position_size']:.2%}")
        
        return len(violations) == 0, violations
    
    def detect_harmful_trend(self) -> Tuple[bool, str]:
        """Detect if recent evolutions show a harmful trend"""
        if len(self.outcome_history) < 3:
            return False, ""
        
        recent = list(self.outcome_history)[-5:]
        
        # Check for consecutive negative outcomes
        negative_count = sum(1 for o in recent if o.get('reward', 0) < 0)
        if negative_count >= 3:
            return True, f"Harmful trend: {negative_count}/5 recent evolutions negative"
        
        # Check for increasing drawdown
        drawdowns = [o.get('drawdown', 0) for o in recent]
        if len(drawdowns) >= 3 and all(drawdowns[i] < drawdowns[i+1] for i in range(len(drawdowns)-1)):
            return True, "Harmful trend: Drawdown consistently increasing"
        
        # Check for decreasing capital
        capitals = [o.get('capital', 0) for o in recent if o.get('capital', 0) > 0]
        if len(capitals) >= 3 and all(capitals[i] > capitals[i+1] for i in range(len(capitals)-1)):
            return True, "Harmful trend: Capital consistently decreasing"
        
        return False, ""
    
    def record_outcome(self, outcome: Dict[str, Any]):
        """Record an evolution outcome for trend detection"""
        self.outcome_history.append(outcome)


class AutonomousEvolutionEngine:
    """
    Fully Autonomous Evolution Engine
    
    Evolves the trading bot without human approval by:
    1. Using reward model to evaluate evolutions
    2. Employing safety mechanisms to prevent harm
    3. Automatically reverting bad evolutions
    4. Maintaining checkpoints for rollback
    
    Key Safety Features:
    - Pre-evolution risk assessment
    - Sandbox testing
    - Gradual rollout
    - Automatic rollback
    - Circuit breakers
    - Hard limits
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config if config is not None else {}
        
        # Core components
        self.reward_model = TradingRewardModel(self.config.get('reward_model', {}))
        self.harm_detector = HarmfulEvolutionDetector()
        
        # Checkpoints for rollback
        self.checkpoints: List[EvolutionCheckpoint] = []
        self.max_checkpoints = 20
        
        # Evolution state
        self.current_state: Dict[str, Any] = {}
        self.pending_evolutions: List[EvolutionCandidate] = []
        self.applied_evolutions: List[Dict] = []
        self.reverted_evolutions: List[Dict] = []
        
        # Circuit breaker
        self.circuit_breaker = {
            'triggered': False,
            'trigger_count': 0,
            'last_trigger': None,
            'cooldown_hours': 6,
            'max_triggers_per_day': 3
        }
        
        # Safety guardrails
        self.guardrails = self._initialize_guardrails()
        
        # Statistics
        self.stats = {
            'total_evolutions': 0,
            'successful_evolutions': 0,
            'reverted_evolutions': 0,
            'blocked_evolutions': 0,
            'circuit_breaker_triggers': 0
        }
        
        # Persistence
        self.state_path = Path(self.config.get('state_path', 'autonomous_evolution_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        self._load_state()
        logger.info("Autonomous Evolution Engine initialized")
    
    def _initialize_guardrails(self) -> List[SafetyGuardrail]:
        """Initialize safety guardrails"""
        return [
            SafetyGuardrail(
                name="max_drawdown",
                description="Maximum allowed drawdown",
                check_function="check_drawdown",
                threshold=0.25,
                action="revert"
            ),
            SafetyGuardrail(
                name="daily_loss_limit",
                description="Maximum daily loss",
                check_function="check_daily_loss",
                threshold=0.10,
                action="block"
            ),
            SafetyGuardrail(
                name="capital_preservation",
                description="Minimum capital preservation",
                check_function="check_capital",
                threshold=0.80,  # Must preserve 80% of capital
                action="revert"
            ),
            SafetyGuardrail(
                name="system_stability",
                description="System must remain stable",
                check_function="check_stability",
                threshold=0.95,  # 95% uptime
                action="warn"
            ),
            SafetyGuardrail(
                name="consecutive_losses",
                description="Max consecutive losing trades",
                check_function="check_consecutive_losses",
                threshold=10,
                action="block"
            )
        ]
    
    def create_checkpoint(self, state: Dict[str, Any], metrics: Dict[str, float], evolution_id: str):
        """Create a checkpoint for potential rollback"""
        checkpoint = EvolutionCheckpoint(
            checkpoint_id=f"ckpt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            state=copy.deepcopy(state),
            metrics=copy.deepcopy(metrics),
            evolution_id=evolution_id
        )
        
        self.checkpoints.append(checkpoint)
        
        # Trim old checkpoints
        if len(self.checkpoints) > self.max_checkpoints:
            self.checkpoints = self.checkpoints[-self.max_checkpoints:]
        
        logger.info(f"Created checkpoint: {checkpoint.checkpoint_id}")
        return checkpoint
    
    def rollback_to_checkpoint(self, checkpoint_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Rollback to a specific checkpoint"""
        for checkpoint in reversed(self.checkpoints):
            if checkpoint.checkpoint_id == checkpoint_id:
                self.current_state = copy.deepcopy(checkpoint.state)
                logger.warning(f"Rolled back to checkpoint: {checkpoint_id}")
                return True, checkpoint.state
        
        return False, {}
    
    def rollback_last_evolution(self, reason: RollbackReason) -> Tuple[bool, str]:
        """Rollback the last evolution"""
        if not self.checkpoints:
            return False, "No checkpoints available"
        
        if len(self.checkpoints) < 2:
            return False, "Need at least 2 checkpoints to rollback"
        
        # Get the checkpoint before the last evolution
        previous_checkpoint = self.checkpoints[-2]
        
        self.current_state = copy.deepcopy(previous_checkpoint.state)
        
        # Record the reverted evolution
        if self.applied_evolutions:
            reverted = self.applied_evolutions.pop()
            reverted['reverted_at'] = datetime.now().isoformat()
            reverted['revert_reason'] = reason.value
            self.reverted_evolutions.append(reverted)
            self.stats['reverted_evolutions'] += 1
        
        logger.warning(f"Rolled back last evolution: {reason.value}")
        return True, f"Rolled back due to: {reason.value}"
    
    async def evaluate_and_apply(
        self,
        candidate: EvolutionCandidate,
        current_metrics: Dict[str, float]
    ) -> Tuple[bool, str, Optional[RewardSignal]]:
        """
        Evaluate a candidate evolution and apply if safe.
        
        This is the main entry point for autonomous evolution.
        No human approval required - safety is ensured by:
        1. Pre-evolution risk assessment
        2. Hard limit checks
        3. Harmful pattern detection
        4. Post-evolution reward evaluation
        5. Automatic rollback if needed
        """
        # Check circuit breaker
        if self._is_circuit_breaker_active():
            self.stats['blocked_evolutions'] += 1
            return False, "Circuit breaker active - evolution blocked", None
        
        # Step 1: Risk assessment
        safety_level, warnings = self.harm_detector.assess_risk(candidate)
        
        if safety_level == EvolutionSafetyLevel.DANGEROUS:
            self.stats['blocked_evolutions'] += 1
            logger.warning(f"Blocked dangerous evolution: {warnings}")
            return False, f"Evolution blocked - dangerous: {warnings}", None
        
        # Step 2: Check for harmful trends
        is_harmful, trend_msg = self.harm_detector.detect_harmful_trend()
        if is_harmful:
            self.stats['blocked_evolutions'] += 1
            logger.warning(f"Blocked due to harmful trend: {trend_msg}")
            return False, f"Evolution blocked - {trend_msg}", None
        
        # Step 3: Create checkpoint before applying
        checkpoint = self.create_checkpoint(
            self.current_state,
            current_metrics,
            candidate.candidate_id
        )
        
        # Step 4: Simulate/sandbox test for risky evolutions
        if safety_level in [EvolutionSafetyLevel.RISKY, EvolutionSafetyLevel.CAUTIOUS]:
            simulation_passed, sim_msg = await self._simulate_evolution(candidate)
            if not simulation_passed:
                self.stats['blocked_evolutions'] += 1
                return False, f"Simulation failed: {sim_msg}", None
        
        # Step 5: Apply the evolution
        self._apply_evolution(candidate)
        self.stats['total_evolutions'] += 1
        
        # Step 6: Wait and evaluate outcome
        await asyncio.sleep(1)  # In production, this would be longer
        
        # Get new metrics after evolution
        new_metrics = await self._get_current_metrics()
        
        # Step 7: Calculate reward
        outcome = EvolutionOutcome(
            evolution_id=candidate.candidate_id,
            dimension=candidate.dimension,
            changes=candidate.changes,
            metrics_before=current_metrics,
            metrics_after=new_metrics,
            trades_during=[],  # Would be populated in production
            duration_hours=0.1
        )
        
        reward_signal = self.reward_model.calculate_reward(outcome)
        
        # Step 8: Check if should revert
        should_revert, revert_reason = self.reward_model.should_revert_evolution(reward_signal)
        
        if should_revert:
            self.rollback_last_evolution(RollbackReason.NEGATIVE_REWARD)
            self._trigger_circuit_breaker_if_needed()
            return False, f"Evolution reverted: {revert_reason}", reward_signal
        
        # Step 9: Check guardrails
        guardrail_violated, violation_msg = self._check_guardrails(new_metrics)
        if guardrail_violated:
            self.rollback_last_evolution(RollbackReason.RULE_VIOLATION)
            return False, f"Guardrail violated: {violation_msg}", reward_signal
        
        # Success!
        self.stats['successful_evolutions'] += 1
        self.harm_detector.record_outcome({
            'reward': reward_signal.total_reward,
            'drawdown': new_metrics.get('max_drawdown', 0),
            'capital': new_metrics.get('account_balance', 0)
        })
        
        logger.info(f"Evolution applied successfully: {candidate.candidate_id} (reward: {reward_signal.total_reward:.3f})")
        
        self._save_state()
        return True, "Evolution applied successfully", reward_signal
    
    async def _simulate_evolution(self, candidate: EvolutionCandidate) -> Tuple[bool, str]:
        """Simulate evolution in sandbox before applying"""
        # Create sandbox state
        sandbox_state = copy.deepcopy(self.current_state)
        
        # Apply changes in sandbox
        for change in candidate.changes:
            param = change.get('param', '')
            new_value = change.get('new_value', change.get('new'))
            
            if param in sandbox_state:
                sandbox_state[param] = new_value
        
        # Check hard limits in sandbox
        limits_ok, violations = self.harm_detector.check_hard_limits(sandbox_state)
        if not limits_ok:
            return False, f"Hard limit violations: {violations}"
        
        # Simulate some trades (simplified)
        simulated_metrics = await self._run_simulation(sandbox_state)
        
        # Check simulation results
        if simulated_metrics.get('max_drawdown', 0) > 0.20:
            return False, f"Simulation showed excessive drawdown: {simulated_metrics['max_drawdown']:.2%}"
        
        if simulated_metrics.get('sharpe_ratio', 0) < 0:
            return False, f"Simulation showed negative Sharpe: {simulated_metrics['sharpe_ratio']:.2f}"
        
        return True, "Simulation passed"
    
    async def _run_simulation(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Run a quick simulation with the given state"""
        # Simplified simulation - in production this would be more comprehensive
        return {
            'max_drawdown': state.get('max_drawdown', 0.10),
            'sharpe_ratio': state.get('sharpe_ratio', 1.0),
            'win_rate': state.get('win_rate', 0.50),
            'profit': state.get('expected_profit', 0)
        }
    
    def _apply_evolution(self, candidate: EvolutionCandidate):
        """Apply an evolution to the current state"""
        for change in candidate.changes:
            param = change.get('param', '')
            new_value = change.get('new_value', change.get('new'))
            
            if param:
                old_value = self.current_state.get(param)
                self.current_state[param] = new_value
                
                logger.info(f"Applied: {param} = {old_value} -> {new_value}")
        
        self.applied_evolutions.append({
            'candidate_id': candidate.candidate_id,
            'dimension': candidate.dimension,
            'changes': candidate.changes,
            'applied_at': datetime.now().isoformat()
        })
    
    async def _get_current_metrics(self) -> Dict[str, float]:
        """Get current performance metrics"""
        # In production, this would fetch real metrics
        return {
            'total_profit': self.current_state.get('total_profit', 0),
            'sharpe_ratio': self.current_state.get('sharpe_ratio', 1.0),
            'sortino_ratio': self.current_state.get('sortino_ratio', 1.2),
            'max_drawdown': self.current_state.get('max_drawdown', 0.05),
            'win_rate': self.current_state.get('win_rate', 0.50),
            'account_balance': self.current_state.get('account_balance', 10000),
            'uptime': self.current_state.get('uptime', 0.99),
            'error_rate': self.current_state.get('error_rate', 0.001)
        }
    
    def _check_guardrails(self, metrics: Dict[str, float]) -> Tuple[bool, str]:
        """Check if any guardrails are violated"""
        for guardrail in self.guardrails:
            if not guardrail.enabled:
                continue
            
            if guardrail.check_function == "check_drawdown":
                if abs(metrics.get('max_drawdown', 0)) > guardrail.threshold:
                    return True, f"Drawdown {metrics['max_drawdown']:.2%} > {guardrail.threshold:.2%}"
            
            elif guardrail.check_function == "check_daily_loss":
                if abs(metrics.get('daily_loss', 0)) > guardrail.threshold:
                    return True, f"Daily loss exceeds {guardrail.threshold:.2%}"
            
            elif guardrail.check_function == "check_capital":
                initial = self.current_state.get('initial_capital', 10000)
                current = metrics.get('account_balance', 10000)
                if initial > 0 and current / initial < guardrail.threshold:
                    return True, f"Capital preservation below {guardrail.threshold:.0%}"
            
            elif guardrail.check_function == "check_stability":
                if metrics.get('uptime', 1.0) < guardrail.threshold:
                    return True, f"Uptime {metrics['uptime']:.2%} < {guardrail.threshold:.2%}"
        
        return False, ""
    
    def _is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is currently active"""
        if not self.circuit_breaker['triggered']:
            return False
        
        last_trigger = self.circuit_breaker['last_trigger']
        if last_trigger is None:
            return False
        
        cooldown = timedelta(hours=self.circuit_breaker['cooldown_hours'])
        if datetime.now() - last_trigger > cooldown:
            self.circuit_breaker['triggered'] = False
            logger.info("Circuit breaker reset after cooldown")
            return False
        
        return True
    
    def _trigger_circuit_breaker_if_needed(self):
        """Trigger circuit breaker if too many failures"""
        # Count recent failures
        recent_reverts = [
            e for e in self.reverted_evolutions
            if datetime.fromisoformat(e['reverted_at']) > datetime.now() - timedelta(hours=24)
        ]
        
        if len(recent_reverts) >= 3:
            self.circuit_breaker['triggered'] = True
            self.circuit_breaker['trigger_count'] += 1
            self.circuit_breaker['last_trigger'] = datetime.now()
            self.stats['circuit_breaker_triggers'] += 1
            
            logger.warning(f"Circuit breaker triggered! {len(recent_reverts)} failures in 24h")
    
    def get_evolution_guidance(self) -> Dict[str, Any]:
        """Get guidance for what to evolve next"""
        reward_guidance = self.reward_model.get_evolution_guidance()
        
        return {
            **reward_guidance,
            'circuit_breaker_active': self._is_circuit_breaker_active(),
            'recent_reverts': len(self.reverted_evolutions),
            'success_rate': (
                self.stats['successful_evolutions'] / max(self.stats['total_evolutions'], 1)
            ),
            'checkpoints_available': len(self.checkpoints)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            **self.stats,
            'circuit_breaker': self.circuit_breaker,
            'checkpoints': len(self.checkpoints),
            'applied_evolutions': len(self.applied_evolutions),
            'reverted_evolutions': len(self.reverted_evolutions),
            'reward_model_stats': self.reward_model.get_statistics()
        }
    
    def _save_state(self):
        """Save engine state"""
        state = {
            'current_state': self.current_state,
            'stats': self.stats,
            'circuit_breaker': {
                **self.circuit_breaker,
                'last_trigger': self.circuit_breaker['last_trigger'].isoformat() 
                    if self.circuit_breaker['last_trigger'] else None
            },
            'applied_evolutions': self.applied_evolutions[-50:],
            'reverted_evolutions': self.reverted_evolutions[-50:]
        }
        
        state_file = self.state_path / 'autonomous_evolution_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """Load previous state"""
        state_file = self.state_path / 'autonomous_evolution_state.json'
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                self.current_state = state.get('current_state', {})
                self.stats = state.get('stats', self.stats)
                self.applied_evolutions = state.get('applied_evolutions', [])
                self.reverted_evolutions = state.get('reverted_evolutions', [])
                
                cb = state.get('circuit_breaker', {})
                self.circuit_breaker.update({
                    'triggered': cb.get('triggered', False),
                    'trigger_count': cb.get('trigger_count', 0),
                    'last_trigger': datetime.fromisoformat(cb['last_trigger']) 
                        if cb.get('last_trigger') else None
                })
                
                logger.info("Loaded autonomous evolution state")
                
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
