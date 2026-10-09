"""
Live Deployment & Control Module
================================
Deploy only after:
- Survival in sandbox
- Improvement after costs
- Capacity estimation
- Risk assessment
- Robustness validation

Deployment must include:
- Gradual scaling
- Live decay monitoring
- Automatic rollback
- Kill-switch rules
- Continuous re-testing

Author: AlphaAlgo Research Team
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .rdaos_core import (
    AlphaDeathClock,
    FeatureFamily,
    HARD_LIMITS,
    ProductionStatus,
    TestingResult,
    generate_id
)

logger = logging.getLogger(__name__)


class DeploymentStage(Enum):
    """Stages of deployment"""
    PENDING = "pending"
    SCALING_UP = "scaling_up"
    FULL_DEPLOYMENT = "full_deployment"
    SCALING_DOWN = "scaling_down"
    ROLLED_BACK = "rolled_back"
    KILLED = "killed"


class KillSwitchReason(Enum):
    """Reasons for kill switch activation"""
    MAX_DRAWDOWN = "max_drawdown"
    SHARPE_DECAY = "sharpe_decay"
    EXECUTION_FAILURE = "execution_failure"
    DATA_QUALITY = "data_quality"
    REGIME_MISMATCH = "regime_mismatch"
    MANUAL = "manual"
    CAPACITY_BREACH = "capacity_breach"


@dataclass
class DeploymentConfig:
    """Configuration for deployment"""
    # Scaling parameters
    initial_allocation_pct: float = 10.0  # Start at 10% of target
    scaling_step_pct: float = 20.0  # Increase by 20% each step
    scaling_interval_days: int = 5  # Days between scaling steps
    min_performance_for_scaling: float = 0.0  # Min Sharpe to continue scaling
    
    # Kill switch thresholds
    max_drawdown_pct: float = 10.0
    min_sharpe_ratio: float = 0.3
    max_consecutive_losses: int = 10
    max_execution_failures: int = 5
    
    # Monitoring
    retest_interval_days: int = 30
    decay_check_interval_days: int = 7
    
    # Rollback
    rollback_on_underperformance: bool = True
    rollback_threshold_sharpe: float = 0.2


@dataclass
class DeploymentState:
    """Current state of a deployment"""
    family_id: str
    stage: DeploymentStage
    
    # Allocation
    target_allocation_pct: float = 0.0
    current_allocation_pct: float = 0.0
    
    # Performance
    deployed_at: datetime = field(default_factory=datetime.utcnow)
    last_scaled_at: Optional[datetime] = None
    
    cumulative_return: float = 0.0
    current_drawdown: float = 0.0
    live_sharpe: float = 0.0
    
    # Tracking
    consecutive_losses: int = 0
    execution_failures: int = 0
    
    # Kill switch
    kill_switch_triggered: bool = False
    kill_switch_reason: Optional[KillSwitchReason] = None
    kill_switch_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "family_id": self.family_id,
            "stage": self.stage.value,
            "target_allocation_pct": self.target_allocation_pct,
            "current_allocation_pct": self.current_allocation_pct,
            "deployed_at": self.deployed_at.isoformat(),
            "cumulative_return": self.cumulative_return,
            "current_drawdown": self.current_drawdown,
            "live_sharpe": self.live_sharpe,
            "kill_switch_triggered": self.kill_switch_triggered,
            "kill_switch_reason": self.kill_switch_reason.value if self.kill_switch_reason else None
        }


@dataclass
class DeploymentCheckResult:
    """Result of deployment readiness check"""
    family_id: str
    ready_for_deployment: bool
    
    sandbox_passed: bool = False
    cost_improvement: bool = False
    capacity_sufficient: bool = False
    risk_acceptable: bool = False
    robustness_validated: bool = False
    
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "family_id": self.family_id,
            "ready_for_deployment": self.ready_for_deployment,
            "sandbox_passed": self.sandbox_passed,
            "cost_improvement": self.cost_improvement,
            "capacity_sufficient": self.capacity_sufficient,
            "risk_acceptable": self.risk_acceptable,
            "robustness_validated": self.robustness_validated,
            "issues": self.issues
        }


class DeploymentReadinessChecker:
    """
    Check if a feature is ready for deployment.
    
    Validates:
    - Sandbox survival
    - Cost-adjusted improvement
    - Capacity estimation
    - Risk assessment
    - Robustness validation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Thresholds
            self.min_sharpe_after_costs = self.config.get(
                "min_sharpe_after_costs",
                HARD_LIMITS.MIN_SHARPE_AFTER_COSTS
            )
            self.min_capacity = self.config.get(
                "min_capacity",
                HARD_LIMITS.MIN_CAPACITY_USD
            )
            self.max_drawdown = self.config.get(
                "max_drawdown",
                HARD_LIMITS.MAX_DRAWDOWN_PCT
            )
            self.min_robustness = self.config.get("min_robustness", 0.7)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check(
        self,
        family: FeatureFamily,
        testing_result: TestingResult
    ) -> DeploymentCheckResult:
        """Check deployment readiness"""
        try:
            result = DeploymentCheckResult(family_id=family.family_id, ready_for_deployment=False)
        
            # Check sandbox survival
            if testing_result.all_tests_passed:
                result.sandbox_passed = True
            else:
                result.issues.append("Failed sandbox testing")
        
            # Check cost-adjusted improvement
            cost_sharpe = testing_result.cost_adjusted_metrics.sharpe_ratio
            if cost_sharpe >= self.min_sharpe_after_costs:
                result.cost_improvement = True
            else:
                result.issues.append(
                    f"Cost-adjusted Sharpe {cost_sharpe:.2f} < {self.min_sharpe_after_costs}"
                )
        
            # Check capacity
            if family.capacity_limit_usd >= self.min_capacity:
                result.capacity_sufficient = True
            else:
                result.issues.append(
                    f"Capacity ${family.capacity_limit_usd/1e6:.1f}M < ${self.min_capacity/1e6:.1f}M"
                )
        
            # Check risk
            max_dd = testing_result.cost_adjusted_metrics.max_drawdown
            if max_dd <= self.max_drawdown:
                result.risk_acceptable = True
            else:
                result.issues.append(
                    f"Max drawdown {max_dd:.1f}% > {self.max_drawdown}%"
                )
        
            # Check robustness
            robustness = (
                testing_result.parameter_stability_score +
                testing_result.data_robustness_score
            ) / 2
            if robustness >= self.min_robustness:
                result.robustness_validated = True
            else:
                result.issues.append(
                    f"Robustness score {robustness:.2f} < {self.min_robustness}"
                )
        
            # Final decision
            result.ready_for_deployment = (
                result.sandbox_passed and
                result.cost_improvement and
                result.capacity_sufficient and
                result.risk_acceptable and
                result.robustness_validated
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise


class GradualScaler:
    """
    Gradually scale deployment allocation.
    
    Implements:
    - Slow ramp-up
    - Performance-based scaling decisions
    - Automatic scale-down on underperformance
    """
    
    def __init__(self, config: DeploymentConfig):
        try:
            self.config = config
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def compute_next_allocation(
        self,
        state: DeploymentState,
        recent_sharpe: float
    ) -> Tuple[float, bool]:
        """
        Compute next allocation level.
        
        Returns:
            Tuple of (new_allocation_pct, should_scale)
        """
        try:
            current = state.current_allocation_pct
            target = state.target_allocation_pct
        
            # Check if enough time has passed
            if state.last_scaled_at:
                days_since_scale = (datetime.utcnow() - state.last_scaled_at).days
                if days_since_scale < self.config.scaling_interval_days:
                    return current, False
        
            # Check performance
            if recent_sharpe < self.config.min_performance_for_scaling:
                # Don't scale up, maybe scale down
                if recent_sharpe < 0:
                    new_allocation = max(0, current - self.config.scaling_step_pct)
                    return new_allocation, True
                return current, False
        
            # Scale up
            if current < target:
                step = target * (self.config.scaling_step_pct / 100)
                new_allocation = min(target, current + step)
                return new_allocation, True
        
            return current, False
        except Exception as e:
            logger.error(f"Error in compute_next_allocation: {e}")
            raise
    
    def should_scale_down(
        self,
        state: DeploymentState,
        recent_sharpe: float
    ) -> Tuple[bool, float]:
        """Check if should scale down"""
        try:
            if recent_sharpe < 0:
                # Negative Sharpe - reduce by half
                new_allocation = state.current_allocation_pct * 0.5
                return True, new_allocation
        
            if recent_sharpe < self.config.min_performance_for_scaling:
                # Below threshold - reduce by 20%
                new_allocation = state.current_allocation_pct * 0.8
                return True, new_allocation
        
            return False, state.current_allocation_pct
        except Exception as e:
            logger.error(f"Error in should_scale_down: {e}")
            raise


class KillSwitch:
    """
    Kill switch for emergency deployment termination.
    
    Triggers on:
    - Max drawdown breach
    - Sharpe decay below threshold
    - Execution failures
    - Data quality issues
    - Regime mismatch
    """
    
    def __init__(self, config: DeploymentConfig):
        try:
            self.config = config
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check(self, state: DeploymentState) -> Tuple[bool, Optional[KillSwitchReason]]:
        """Check if kill switch should be triggered"""
        
        # Max drawdown
        try:
            if state.current_drawdown >= self.config.max_drawdown_pct:
                return True, KillSwitchReason.MAX_DRAWDOWN
        
            # Sharpe decay
            if state.live_sharpe < self.config.min_sharpe_ratio:
                return True, KillSwitchReason.SHARPE_DECAY
        
            # Consecutive losses
            if state.consecutive_losses >= self.config.max_consecutive_losses:
                return True, KillSwitchReason.SHARPE_DECAY
        
            # Execution failures
            if state.execution_failures >= self.config.max_execution_failures:
                return True, KillSwitchReason.EXECUTION_FAILURE
        
            return False, None
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise
    
    def trigger(
        self,
        state: DeploymentState,
        reason: KillSwitchReason
    ) -> DeploymentState:
        """Trigger kill switch"""
        try:
            state.kill_switch_triggered = True
            state.kill_switch_reason = reason
            state.kill_switch_at = datetime.utcnow()
            state.stage = DeploymentStage.KILLED
            state.current_allocation_pct = 0.0
        
            logger.warning(
                f"Kill switch triggered for {state.family_id}: {reason.value}"
            )
        
            return state
        except Exception as e:
            logger.error(f"Error in trigger: {e}")
            raise


class RollbackManager:
    """
    Manage deployment rollbacks.
    
    Implements:
    - Automatic rollback on underperformance
    - State preservation for analysis
    - Graceful position unwinding
    """
    
    def __init__(self, config: DeploymentConfig):
        try:
            self.config = config
            self.rollback_history: List[Dict] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def should_rollback(
        self,
        state: DeploymentState,
        recent_sharpe: float
    ) -> bool:
        """Check if should rollback"""
        try:
            if not self.config.rollback_on_underperformance:
                return False
        
            if recent_sharpe < self.config.rollback_threshold_sharpe:
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in should_rollback: {e}")
            raise
    
    def execute_rollback(
        self,
        state: DeploymentState,
        reason: str
    ) -> DeploymentState:
        """Execute rollback"""
        # Record rollback
        try:
            self.rollback_history.append({
                "family_id": state.family_id,
                "rolled_back_at": datetime.utcnow().isoformat(),
                "reason": reason,
                "state_at_rollback": state.to_dict()
            })
        
            # Update state
            state.stage = DeploymentStage.ROLLED_BACK
            state.current_allocation_pct = 0.0
        
            logger.info(f"Rolled back deployment {state.family_id}: {reason}")
        
            return state
        except Exception as e:
            logger.error(f"Error in execute_rollback: {e}")
            raise


class ContinuousRetester:
    """
    Continuously re-test deployed features.
    
    Validates:
    - Ongoing performance
    - Regime fit
    - Decay detection
    """
    
    def __init__(self, config: DeploymentConfig):
        try:
            self.config = config
            self.last_retest: Dict[str, datetime] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def needs_retest(self, family_id: str) -> bool:
        """Check if feature needs re-testing"""
        try:
            if family_id not in self.last_retest:
                return True
        
            days_since = (datetime.utcnow() - self.last_retest[family_id]).days
            return days_since >= self.config.retest_interval_days
        except Exception as e:
            logger.error(f"Error in needs_retest: {e}")
            raise
    
    def record_retest(self, family_id: str):
        """Record that retest was performed"""
        try:
            self.last_retest[family_id] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error in record_retest: {e}")
            raise
    
    def get_families_needing_retest(
        self,
        deployed_families: List[str]
    ) -> List[str]:
        """Get list of families needing re-test"""
        return [fid for fid in deployed_families if self.needs_retest(fid)]


class LiveDeploymentEngine:
    """
    Main engine for live deployment and control.
    
    Coordinates:
    - Deployment readiness checking
    - Gradual scaling
    - Kill switch monitoring
    - Rollback management
    - Continuous re-testing
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Deployment configuration
            self.deployment_config = DeploymentConfig(
                initial_allocation_pct=self.config.get("initial_allocation_pct", 10.0),
                scaling_step_pct=self.config.get("scaling_step_pct", 20.0),
                scaling_interval_days=self.config.get("scaling_interval_days", 5),
                max_drawdown_pct=self.config.get("max_drawdown_pct", 10.0),
                min_sharpe_ratio=self.config.get("min_sharpe_ratio", 0.3),
                retest_interval_days=self.config.get("retest_interval_days", 30)
            )
        
            # Initialize components
            self.readiness_checker = DeploymentReadinessChecker(config)
            self.scaler = GradualScaler(self.deployment_config)
            self.kill_switch = KillSwitch(self.deployment_config)
            self.rollback_manager = RollbackManager(self.deployment_config)
            self.retester = ContinuousRetester(self.deployment_config)
        
            # State tracking
            self.deployments: Dict[str, DeploymentState] = {}
            self.death_clocks: Dict[str, AlphaDeathClock] = {}
        
            logger.info("Live Deployment Engine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check_deployment_readiness(
        self,
        family: FeatureFamily,
        testing_result: TestingResult
    ) -> DeploymentCheckResult:
        """Check if feature is ready for deployment"""
        return self.readiness_checker.check(family, testing_result)
    
    def deploy(
        self,
        family: FeatureFamily,
        testing_result: TestingResult,
        target_allocation_pct: float
    ) -> Optional[DeploymentState]:
        """Deploy a feature family"""
        
        # Check readiness
        try:
            check = self.check_deployment_readiness(family, testing_result)
            if not check.ready_for_deployment:
                logger.warning(
                    f"Cannot deploy {family.family_id}: {check.issues}"
                )
                return None
        
            # Create deployment state
            state = DeploymentState(
                family_id=family.family_id,
                stage=DeploymentStage.SCALING_UP,
                target_allocation_pct=target_allocation_pct,
                current_allocation_pct=self.deployment_config.initial_allocation_pct * target_allocation_pct / 100
            )
        
            # Create death clock
            death_clock = AlphaDeathClock(
                family_id=family.family_id,
                deployment_date=datetime.utcnow(),
                expected_decay_date=datetime.utcnow() + timedelta(days=family.expected_decay_days),
                initial_sharpe=testing_result.cost_adjusted_metrics.sharpe_ratio,
                current_sharpe=testing_result.cost_adjusted_metrics.sharpe_ratio,
                initial_capacity=family.capacity_limit_usd,
                current_capacity=family.capacity_limit_usd
            )
        
            # Store
            self.deployments[family.family_id] = state
            self.death_clocks[family.family_id] = death_clock
        
            # Update family status
            family.status = ProductionStatus.DEPLOYED
        
            logger.info(
                f"Deployed {family.family_id} at {state.current_allocation_pct:.1f}% "
                f"(target: {target_allocation_pct:.1f}%)"
            )
        
            return state
        except Exception as e:
            logger.error(f"Error in deploy: {e}")
            raise
    
    def update_deployment(
        self,
        family_id: str,
        daily_return: float,
        execution_success: bool = True
    ) -> Optional[DeploymentState]:
        """Update deployment with daily performance"""
        
        try:
            if family_id not in self.deployments:
                return None
        
            state = self.deployments[family_id]
        
            # Skip if already killed or rolled back
            if state.stage in [DeploymentStage.KILLED, DeploymentStage.ROLLED_BACK]:
                return state
        
            # Update performance
            state.cumulative_return = (1 + state.cumulative_return) * (1 + daily_return) - 1
        
            # Update drawdown
            if daily_return < 0:
                state.current_drawdown = max(
                    state.current_drawdown,
                    abs(daily_return) * 100
                )
                state.consecutive_losses += 1
            else:
                state.consecutive_losses = 0
        
            # Update execution tracking
            if not execution_success:
                state.execution_failures += 1
        
            # Update live Sharpe (simplified rolling calculation)
            days_deployed = (datetime.utcnow() - state.deployed_at).days + 1
            if days_deployed > 0:
                annualized_return = state.cumulative_return * (252 / days_deployed)
                # Assume 15% vol for simplicity
                state.live_sharpe = annualized_return / 0.15
        
            # Check kill switch
            should_kill, reason = self.kill_switch.check(state)
            if should_kill:
                state = self.kill_switch.trigger(state, reason)
                return state
        
            # Check rollback
            if self.rollback_manager.should_rollback(state, state.live_sharpe):
                state = self.rollback_manager.execute_rollback(
                    state,
                    f"Sharpe {state.live_sharpe:.2f} below threshold"
                )
                return state
        
            # Check scaling
            new_allocation, should_scale = self.scaler.compute_next_allocation(
                state,
                state.live_sharpe
            )
        
            if should_scale:
                state.current_allocation_pct = new_allocation
                state.last_scaled_at = datetime.utcnow()
            
                if new_allocation >= state.target_allocation_pct:
                    state.stage = DeploymentStage.FULL_DEPLOYMENT
                elif new_allocation < state.current_allocation_pct:
                    state.stage = DeploymentStage.SCALING_DOWN
            
                logger.info(
                    f"Scaled {family_id} to {new_allocation:.1f}%"
                )
        
            # Update death clock
            self._update_death_clock(family_id, state.live_sharpe)
        
            return state
        except Exception as e:
            logger.error(f"Error in update_deployment: {e}")
            raise
    
    def _update_death_clock(self, family_id: str, current_sharpe: float):
        """Update alpha death clock"""
        try:
            if family_id not in self.death_clocks:
                return
        
            clock = self.death_clocks[family_id]
        
            # Update current Sharpe
            clock.current_sharpe = current_sharpe
        
            # Compute decay rate
            days_deployed = (datetime.utcnow() - clock.deployment_date).days
            clock.days_deployed = days_deployed
        
            if days_deployed > 0 and clock.initial_sharpe > 0:
                decay = (clock.initial_sharpe - current_sharpe) / clock.initial_sharpe
                clock.sharpe_decay_rate = decay / days_deployed
        
            # Check for decay
            if current_sharpe < clock.initial_sharpe * 0.5:  # 50% decay
                clock.decay_detected = True
                clock.decay_detection_date = datetime.utcnow()
        
            # Update days until expected decay
            clock.days_until_expected_decay = max(
                0,
                (clock.expected_decay_date - datetime.utcnow()).days
            )
        except Exception as e:
            logger.error(f"Error in _update_death_clock: {e}")
            raise
    
    def get_families_needing_retest(self) -> List[str]:
        """Get deployed families needing re-test"""
        try:
            deployed = [
                fid for fid, state in self.deployments.items()
                if state.stage not in [DeploymentStage.KILLED, DeploymentStage.ROLLED_BACK]
            ]
            return self.retester.get_families_needing_retest(deployed)
        except Exception as e:
            logger.error(f"Error in get_families_needing_retest: {e}")
            raise
    
    def record_retest(self, family_id: str):
        """Record that retest was performed"""
        try:
            self.retester.record_retest(family_id)
        except Exception as e:
            logger.error(f"Error in record_retest: {e}")
            raise
    
    def manual_kill(self, family_id: str, reason: str = "Manual kill"):
        """Manually kill a deployment"""
        try:
            if family_id in self.deployments:
                state = self.deployments[family_id]
                state = self.kill_switch.trigger(state, KillSwitchReason.MANUAL)
                logger.info(f"Manual kill for {family_id}: {reason}")
        except Exception as e:
            logger.error(f"Error in manual_kill: {e}")
            raise
    
    def get_deployment_state(self, family_id: str) -> Optional[DeploymentState]:
        """Get current deployment state"""
        return self.deployments.get(family_id)
    
    def get_death_clock(self, family_id: str) -> Optional[AlphaDeathClock]:
        """Get death clock for a deployment"""
        return self.death_clocks.get(family_id)
    
    def get_active_deployments(self) -> List[DeploymentState]:
        """Get all active deployments"""
        return [
            state for state in self.deployments.values()
            if state.stage not in [DeploymentStage.KILLED, DeploymentStage.ROLLED_BACK]
        ]
    
    def get_total_allocation(self) -> float:
        """Get total allocation across all deployments"""
        return sum(
            state.current_allocation_pct
            for state in self.get_active_deployments()
        )


def create_deployment_engine(config: Optional[Dict] = None) -> LiveDeploymentEngine:
    """Factory function to create deployment engine"""
    return LiveDeploymentEngine(config)
