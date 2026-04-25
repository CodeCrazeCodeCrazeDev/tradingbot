"""
Controlled Evolution Plane

Its job:
- Mutate prompts, workflows, feature sets, model routing, or agent topology
- Validate on held-out data and regime slices
- Score against baseline on robustness, calibration, drawdown, and cost-adjusted expectancy
- Promote only with hard gates and rollback hooks

This plane must NEVER directly affect live decisions.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import copy

from .core_types import CapabilityHypothesis
from .memory_system import DecisionMemory, OutcomeMemory, FailureMemory

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status of capability validation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ValidationResult:
    """Result of validating a capability hypothesis"""
    hypothesis_id: str
    status: ValidationStatus
    sandbox_tests_passed: int
    sandbox_tests_failed: int
    statistical_significance: float  # p-value
    vs_baseline_improvement: float  # % improvement over baseline
    robustness_score: float
    calibration_score: float
    max_drawdown: float
    cost_adjusted_expectancy: float
    validation_errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PromotionGate:
    """Hard gates for capability promotion"""
    min_statistical_significance: float = 0.05  # p-value threshold
    min_improvement_threshold: float = 0.05  # 5% improvement required
    min_robustness: float = 0.6
    max_drawdown_increase: float = 0.02  # Can't increase drawdown by more than 2%
    min_calibration_quality: float = 0.6
    min_backtest_months: int = 6


class ControlledEvolutionPlane:
    """
    Controlled evolution system for capability improvements.
    Validates changes before promoting to production.
    """
    
    def __init__(
        self,
        decision_memory: DecisionMemory,
        outcome_memory: OutcomeMemory,
        failure_memory: FailureMemory,
        promotion_gates: Optional[PromotionGate] = None
    ):
        self.decision_memory = decision_memory
        self.outcome_memory = outcome_memory
        self.failure_memory = failure_memory
        self.promotion_gates = promotion_gates or PromotionGate()
        
        # Capability registry
        self.capability_registry: Dict[str, CapabilityHypothesis] = {}
        self.validation_results: Dict[str, List[ValidationResult]] = {}
        self.promoted_capabilities: List[str] = []
        self.rolled_back_capabilities: List[str] = []
        
    def submit_capability_hypothesis(
        self,
        hypothesis: CapabilityHypothesis
    ) -> str:
        """
        Submit a new capability hypothesis for evaluation.
        
        Returns:
            Capability ID
        """
        self.capability_registry[hypothesis.id] = hypothesis
        self.validation_results[hypothesis.id] = []
        
        logger.info(
            f"Submitted capability hypothesis: {hypothesis.id} - {hypothesis.capability_type}"
        )
        
        return hypothesis.id
    
    async def validate_in_sandbox(
        self,
        capability_id: str,
        sandbox_config: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate a capability in sandbox environment.
        
        Args:
            capability_id: ID of capability to validate
            sandbox_config: Configuration for sandbox testing
            
        Returns:
            Validation result
        """
        hypothesis = self.capability_registry.get(capability_id)
        if not hypothesis:
            raise ValueError(f"Capability {capability_id} not found")
            
        logger.info(f"Starting sandbox validation for {capability_id}")
        
        # Simulate sandbox testing
        # In real implementation, this would run actual backtests
        tests_passed = 0
        tests_failed = 0
        
        # Test 1: Historical backtest
        backtest_result = await self._run_historical_backtest(hypothesis, sandbox_config)
        if backtest_result['improved']:
            tests_passed += 1
        else:
            tests_failed += 1
            
        # Test 2: Stress test
        stress_result = await self._run_stress_test(hypothesis, sandbox_config)
        if stress_result['survived']:
            tests_passed += 1
        else:
            tests_failed += 1
            
        # Test 3: Regime-specific validation
        regime_results = await self._run_regime_validation(hypothesis, sandbox_config)
        tests_passed += regime_results['passed']
        tests_failed += regime_results['failed']
        
        # Calculate metrics
        improvement = backtest_result.get('improvement', 0)
        robustness = stress_result.get('robustness', 0.5)
        calibration = backtest_result.get('calibration', 0.5)
        drawdown = backtest_result.get('max_drawdown', 0.1)
        expectancy = backtest_result.get('cost_adjusted_expectancy', 0)
        
        # Statistical significance (simulated)
        significance = 0.03 if improvement > 0.1 else 0.12
        
        result = ValidationResult(
            hypothesis_id=capability_id,
            status=ValidationStatus.PASSED if tests_failed == 0 else ValidationStatus.FAILED,
            sandbox_tests_passed=tests_passed,
            sandbox_tests_failed=tests_failed,
            statistical_significance=significance,
            vs_baseline_improvement=improvement,
            robustness_score=robustness,
            calibration_score=calibration,
            max_drawdown=drawdown,
            cost_adjusted_expectancy=expectancy
        )
        
        self.validation_results[capability_id].append(result)
        hypothesis.tested = True
        hypothesis.test_results = {
            'tests_passed': tests_passed,
            'tests_failed': tests_failed,
            'improvement': improvement
        }
        
        logger.info(
            f"Sandbox validation complete for {capability_id}: "
            f"{tests_passed} passed, {tests_failed} failed"
        )
        
        return result
    
    async def _run_historical_backtest(
        self,
        hypothesis: CapabilityHypothesis,
        config: Optional[Dict]
    ) -> Dict[str, Any]:
        """Run historical backtest for capability"""
        
        # Simulated backtest
        # In real implementation, this would run actual backtests
        expected_improvement = hypothesis.expected_improvement
        
        # Add noise to simulate realistic results
        import random
        actual_improvement = expected_improvement * random.uniform(0.5, 1.2)
        
        return {
            'improved': actual_improvement > 0.02,
            'improvement': actual_improvement,
            'calibration': 0.7 + random.uniform(-0.1, 0.1),
            'max_drawdown': 0.08 + random.uniform(-0.02, 0.05),
            'cost_adjusted_expectancy': actual_improvement * 0.8
        }
    
    async def _run_stress_test(
        self,
        hypothesis: CapabilityHypothesis,
        config: Optional[Dict]
    ) -> Dict[str, Any]:
        """Run stress test for capability"""
        
        import random
        
        # Simulate stress test
        survival_prob = 0.8 if hypothesis.capability_type == 'model' else 0.9
        survived = random.random() < survival_prob
        
        return {
            'survived': survived,
            'robustness': 0.7 + random.uniform(-0.15, 0.15) if survived else 0.4
        }
    
    async def _run_regime_validation(
        self,
        hypothesis: CapabilityHypothesis,
        config: Optional[Dict]
    ) -> Dict[str, Any]:
        """Validate capability across different market regimes"""
        
        import random
        
        # Test in different regimes
        regimes = ['low_vol', 'high_vol', 'trending', 'mean_reverting']
        passed = 0
        failed = 0
        
        for regime in regimes:
            # Simulate regime test
            if random.random() > 0.3:  # 70% pass rate
                passed += 1
            else:
                failed += 1
                
        return {'passed': passed, 'failed': failed}
    
    def check_promotion_gates(self, capability_id: str) -> Tuple[bool, List[str]]:
        """
        Check if capability meets all promotion gates.
        
        Returns:
            Tuple of (can_promote, list of gate violations)
        """
        hypothesis = self.capability_registry.get(capability_id)
        if not hypothesis:
            return False, ["Capability not found"]
            
        if not hypothesis.tested:
            return False, ["Capability has not been tested"]
            
        violations = []
        
        # Get latest validation result
        results = self.validation_results.get(capability_id, [])
        if not results:
            return False, ["No validation results available"]
            
        latest = results[-1]
        
        # Check statistical significance
        if latest.statistical_significance > self.promotion_gates.min_statistical_significance:
            violations.append(
                f"Statistical significance {latest.statistical_significance:.3f} > "
                f"threshold {self.promotion_gates.min_statistical_significance}"
            )
            
        # Check improvement threshold
        if latest.vs_baseline_improvement < self.promotion_gates.min_improvement_threshold:
            violations.append(
                f"Improvement {latest.vs_baseline_improvement:.1%} < "
                f"threshold {self.promotion_gates.min_improvement_threshold:.1%}"
            )
            
        # Check robustness
        if latest.robustness_score < self.promotion_gates.min_robustness:
            violations.append(
                f"Robustness {latest.robustness_score:.2f} < "
                f"threshold {self.promotion_gates.min_robustness}"
            )
            
        # Check drawdown
        if latest.max_drawdown > self.promotion_gates.max_drawdown_increase:
            violations.append(
                f"Drawdown {latest.max_drawdown:.1%} exceeds max increase "
                f"{self.promotion_gates.max_drawdown_increase:.1%}"
            )
            
        # Check calibration
        if latest.calibration_score < self.promotion_gates.min_calibration_quality:
            violations.append(
                f"Calibration {latest.calibration_score:.2f} < "
                f"threshold {self.promotion_gates.min_calibration_quality}"
            )
            
        can_promote = len(violations) == 0
        
        return can_promote, violations
    
    def promote_capability(
        self,
        capability_id: str,
        with_rollback_hook: bool = True
    ) -> Dict[str, Any]:
        """
        Promote a capability to production.
        
        Returns:
            Promotion result
        """
        can_promote, violations = self.check_promotion_gates(capability_id)
        
        if not can_promote:
            return {
                'success': False,
                'reason': 'Gate violations',
                'violations': violations
            }
            
        hypothesis = self.capability_registry[capability_id]
        hypothesis.promoted = True
        self.promoted_capabilities.append(capability_id)
        
        result = {
            'success': True,
            'capability_id': capability_id,
            'capability_type': hypothesis.capability_type,
            'timestamp': datetime.utcnow().isoformat(),
            'rollback_hook_active': with_rollback_hook
        }
        
        logger.info(f"Promoted capability {capability_id} to production")
        
        return result
    
    def rollback_capability(self, capability_id: str, reason: str) -> Dict[str, Any]:
        """
        Rollback a promoted capability.
        
        Returns:
            Rollback result
        """
        hypothesis = self.capability_registry.get(capability_id)
        if not hypothesis:
            return {'success': False, 'reason': 'Capability not found'}
            
        if not hypothesis.promoted:
            return {'success': False, 'reason': 'Capability was not promoted'}
            
        hypothesis.promoted = False
        self.rolled_back_capabilities.append(capability_id)
        
        # Remove from promoted list
        if capability_id in self.promoted_capabilities:
            self.promoted_capabilities.remove(capability_id)
            
        logger.warning(f"Rolled back capability {capability_id}: {reason}")
        
        return {
            'success': True,
            'capability_id': capability_id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_evolution_status(self) -> Dict[str, Any]:
        """Get current evolution status"""
        
        return {
            'total_hypotheses': len(self.capability_registry),
            'tested': sum(1 for h in self.capability_registry.values() if h.tested),
            'promoted': len(self.promoted_capabilities),
            'rolled_back': len(self.rolled_back_capabilities),
            'awaiting_validation': sum(
                1 for h in self.capability_registry.values()
                if not h.tested and not h.promoted
            ),
            'promotion_gates': {
                'min_improvement': self.promotion_gates.min_improvement_threshold,
                'min_robustness': self.promotion_gates.min_robustness
            }
        }
        
    def generate_evolution_report(self) -> Dict[str, Any]:
        """Generate comprehensive evolution report"""
        
        return {
            'status': self.get_evolution_status(),
            'promoted_capabilities': [
                {
                    'id': cid,
                    'type': self.capability_registry[cid].capability_type,
                    'improvement': self.capability_registry[cid].expected_improvement
                }
                for cid in self.promoted_capabilities
            ],
            'rolled_back_capabilities': [
                {
                    'id': cid,
                    'type': self.capability_registry[cid].capability_type
                }
                for cid in self.rolled_back_capabilities
            ],
            'pending_validations': [
                {
                    'id': h.id,
                    'type': h.capability_type,
                    'gap': h.gap_description[:50]
                }
                for h in self.capability_registry.values()
                if not h.tested
            ]
        }
