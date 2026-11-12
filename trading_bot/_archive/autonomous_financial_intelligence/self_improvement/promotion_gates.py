"""
Promotion Gates

Validates improvements before deployment to production.
Implements multi-stage validation with automated and manual gates.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class GateType(Enum):
    """Types of promotion gates."""
    PERFORMANCE_GATE = "performance_gate"
    SAFETY_GATE = "safety_gate"
    QUALITY_GATE = "quality_gate"
    RISK_GATE = "risk_gate"
    COMPLIANCE_GATE = "compliance_gate"
    HUMAN_APPROVAL_GATE = "human_approval_gate"
    CANARY_GATE = "canary_gate"
    ROLLBACK_GATE = "rollback_gate"


class GateStatus(Enum):
    """Status of a gate check."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    MANUAL_REVIEW = "manual_review"


@dataclass
class PromotionCriteria:
    """Criteria for promotion through a gate."""
    minimum_accuracy: float = 0.90
    minimum_f1_score: float = 0.85
    maximum_error_rate: float = 0.05
    maximum_hallucination_rate: float = 0.01
    maximum_latency_ms: float = 500.0
    minimum_sample_size: int = 1000
    minimum_improvement: float = 0.05
    statistical_significance: float = 0.95
    maximum_risk_score: float = 0.3
    minimum_canary_success_rate: float = 0.98
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'minimum_accuracy': self.minimum_accuracy,
            'minimum_f1_score': self.minimum_f1_score,
            'maximum_error_rate': self.maximum_error_rate,
            'maximum_hallucination_rate': self.maximum_hallucination_rate,
            'maximum_latency_ms': self.maximum_latency_ms,
            'minimum_sample_size': self.minimum_sample_size,
            'minimum_improvement': self.minimum_improvement,
            'statistical_significance': self.statistical_significance,
            'maximum_risk_score': self.maximum_risk_score,
            'minimum_canary_success_rate': self.minimum_canary_success_rate,
        }


@dataclass
class GateCheck:
    """Result of a single gate check."""
    gate_type: GateType
    status: GateStatus
    passed: bool
    criteria_met: Dict[str, bool]
    details: Dict[str, Any]
    timestamp: datetime
    checked_by: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'gate_type': self.gate_type.value,
            'status': self.status.value,
            'passed': self.passed,
            'criteria_met': self.criteria_met,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'checked_by': self.checked_by,
        }


@dataclass
class PromotionResult:
    """Result of promotion gate validation."""
    promotion_id: str
    experiment_id: str
    all_gates_passed: bool
    gates_checked: List[GateCheck]
    overall_score: float
    recommendation: str
    blocking_issues: List[str]
    warnings: List[str]
    timestamp: datetime
    approved_for_production: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'promotion_id': self.promotion_id,
            'experiment_id': self.experiment_id,
            'all_gates_passed': self.all_gates_passed,
            'gates_checked': [g.to_dict() for g in self.gates_checked],
            'overall_score': self.overall_score,
            'recommendation': self.recommendation,
            'blocking_issues': self.blocking_issues,
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat(),
            'approved_for_production': self.approved_for_production,
        }


@dataclass
class CanaryDeployment:
    """Canary deployment for gradual rollout."""
    canary_id: str
    experiment_id: str
    traffic_percentage: float
    started_at: datetime
    duration_hours: int
    success_count: int = 0
    failure_count: int = 0
    is_active: bool = True
    
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'canary_id': self.canary_id,
            'experiment_id': self.experiment_id,
            'traffic_percentage': self.traffic_percentage,
            'started_at': self.started_at.isoformat(),
            'duration_hours': self.duration_hours,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_rate(),
            'is_active': self.is_active,
        }


class PromotionGates:
    """
    Multi-stage validation gates for promoting improvements.
    
    Provides:
    - Automated gate checks
    - Performance validation
    - Safety verification
    - Risk assessment
    - Canary deployments
    - Rollback mechanisms
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'promotion_gates_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._promotion_results: Dict[str, PromotionResult] = {}
        self._canary_deployments: Dict[str, CanaryDeployment] = {}
        self._gate_criteria: Dict[GateType, PromotionCriteria] = {}
        
        self._initialize_gate_criteria()
        
        logger.info("✅ Promotion Gates initialized")
    
    def _initialize_gate_criteria(self):
        """Initialize criteria for each gate type."""
        self._gate_criteria = {
            GateType.PERFORMANCE_GATE: PromotionCriteria(
                minimum_accuracy=0.90,
                minimum_f1_score=0.85,
                maximum_latency_ms=500.0,
            ),
            GateType.SAFETY_GATE: PromotionCriteria(
                maximum_error_rate=0.05,
                maximum_hallucination_rate=0.01,
                maximum_risk_score=0.3,
            ),
            GateType.QUALITY_GATE: PromotionCriteria(
                minimum_sample_size=1000,
                statistical_significance=0.95,
                minimum_improvement=0.05,
            ),
            GateType.RISK_GATE: PromotionCriteria(
                maximum_risk_score=0.2,
                maximum_error_rate=0.03,
            ),
            GateType.CANARY_GATE: PromotionCriteria(
                minimum_canary_success_rate=0.98,
            ),
        }
    
    async def validate_for_promotion(
        self,
        experiment_id: str,
        experiment_data: Dict[str, Any],
        skip_gates: Optional[List[GateType]] = None,
    ) -> PromotionResult:
        """
        Validate an experiment through all promotion gates.
        
        Args:
            experiment_id: ID of the experiment
            experiment_data: Experiment data including metrics
            skip_gates: Optional gates to skip
        
        Returns:
            PromotionResult with validation results
        """
        promotion_id = f"PROM-{uuid.uuid4().hex[:12]}"
        skip_gates = skip_gates or []
        
        gates_to_check = [
            GateType.PERFORMANCE_GATE,
            GateType.SAFETY_GATE,
            GateType.QUALITY_GATE,
            GateType.RISK_GATE,
        ]
        
        gate_checks = []
        blocking_issues = []
        warnings = []
        
        for gate_type in gates_to_check:
            if gate_type in skip_gates:
                gate_checks.append(GateCheck(
                    gate_type=gate_type,
                    status=GateStatus.SKIPPED,
                    passed=True,
                    criteria_met={},
                    details={'reason': 'Skipped by request'},
                    timestamp=datetime.now(timezone.utc),
                    checked_by='system',
                ))
                continue
            
            gate_check = await self._check_gate(gate_type, experiment_data)
            gate_checks.append(gate_check)
            
            if not gate_check.passed:
                for criterion, met in gate_check.criteria_met.items():
                    if not met:
                        blocking_issues.append(f"{gate_type.value}: {criterion} not met")
            
            if gate_check.status == GateStatus.MANUAL_REVIEW:
                warnings.append(f"{gate_type.value} requires manual review")
        
        all_gates_passed = all(check.passed for check in gate_checks)
        
        passed_count = sum(1 for check in gate_checks if check.passed)
        overall_score = passed_count / len(gate_checks) if gate_checks else 0.0
        
        if all_gates_passed and not blocking_issues:
            recommendation = "APPROVE FOR PRODUCTION"
            approved = True
        elif overall_score >= 0.75 and len(blocking_issues) <= 1:
            recommendation = "APPROVE WITH CANARY DEPLOYMENT"
            approved = False
        elif overall_score >= 0.5:
            recommendation = "NEEDS IMPROVEMENT"
            approved = False
        else:
            recommendation = "REJECT"
            approved = False
        
        result = PromotionResult(
            promotion_id=promotion_id,
            experiment_id=experiment_id,
            all_gates_passed=all_gates_passed,
            gates_checked=gate_checks,
            overall_score=overall_score,
            recommendation=recommendation,
            blocking_issues=blocking_issues,
            warnings=warnings,
            timestamp=datetime.now(timezone.utc),
            approved_for_production=approved,
        )
        
        self._promotion_results[promotion_id] = result
        await self._persist_result(result)
        
        logger.info(f"Promotion validation complete: {recommendation} "
                   f"(score: {overall_score:.2f}, gates passed: {passed_count}/{len(gate_checks)})")
        
        return result
    
    async def _check_gate(
        self,
        gate_type: GateType,
        experiment_data: Dict[str, Any],
    ) -> GateCheck:
        """Check a specific gate."""
        criteria = self._gate_criteria.get(gate_type, PromotionCriteria())
        metrics = experiment_data.get('current_metrics', {})
        
        criteria_met = {}
        details = {}
        
        if gate_type == GateType.PERFORMANCE_GATE:
            criteria_met['accuracy'] = metrics.get('accuracy', 0) >= criteria.minimum_accuracy
            criteria_met['f1_score'] = metrics.get('f1_score', 0) >= criteria.minimum_f1_score
            criteria_met['latency'] = metrics.get('latency_ms', float('inf')) <= criteria.maximum_latency_ms
            
            details['accuracy'] = metrics.get('accuracy', 0)
            details['f1_score'] = metrics.get('f1_score', 0)
            details['latency_ms'] = metrics.get('latency_ms', 0)
        
        elif gate_type == GateType.SAFETY_GATE:
            criteria_met['error_rate'] = metrics.get('error_rate', 1) <= criteria.maximum_error_rate
            criteria_met['hallucination_rate'] = metrics.get('hallucination_rate', 1) <= criteria.maximum_hallucination_rate
            criteria_met['risk_score'] = experiment_data.get('risk_score', 1) <= criteria.maximum_risk_score
            
            details['error_rate'] = metrics.get('error_rate', 0)
            details['hallucination_rate'] = metrics.get('hallucination_rate', 0)
            details['risk_score'] = experiment_data.get('risk_score', 0)
        
        elif gate_type == GateType.QUALITY_GATE:
            criteria_met['sample_size'] = experiment_data.get('sample_size', 0) >= criteria.minimum_sample_size
            criteria_met['significance'] = experiment_data.get('statistical_significance', 0) >= criteria.statistical_significance
            criteria_met['improvement'] = experiment_data.get('improvement_percentage', 0) >= criteria.minimum_improvement
            
            details['sample_size'] = experiment_data.get('sample_size', 0)
            details['statistical_significance'] = experiment_data.get('statistical_significance', 0)
            details['improvement_percentage'] = experiment_data.get('improvement_percentage', 0)
        
        elif gate_type == GateType.RISK_GATE:
            criteria_met['risk_score'] = experiment_data.get('risk_score', 1) <= criteria.maximum_risk_score
            criteria_met['error_rate'] = metrics.get('error_rate', 1) <= criteria.maximum_error_rate
            
            details['risk_score'] = experiment_data.get('risk_score', 0)
            details['error_rate'] = metrics.get('error_rate', 0)
        
        passed = all(criteria_met.values())
        status = GateStatus.PASSED if passed else GateStatus.FAILED
        
        return GateCheck(
            gate_type=gate_type,
            status=status,
            passed=passed,
            criteria_met=criteria_met,
            details=details,
            timestamp=datetime.now(timezone.utc),
            checked_by='automated_gate_system',
        )
    
    async def start_canary_deployment(
        self,
        experiment_id: str,
        traffic_percentage: float = 5.0,
        duration_hours: int = 24,
    ) -> CanaryDeployment:
        """
        Start a canary deployment for gradual rollout.
        
        Args:
            experiment_id: ID of the experiment
            traffic_percentage: Percentage of traffic to route to canary
            duration_hours: Duration of canary deployment
        
        Returns:
            CanaryDeployment object
        """
        canary_id = f"CANARY-{uuid.uuid4().hex[:12]}"
        
        canary = CanaryDeployment(
            canary_id=canary_id,
            experiment_id=experiment_id,
            traffic_percentage=min(traffic_percentage, 20.0),
            started_at=datetime.now(timezone.utc),
            duration_hours=duration_hours,
        )
        
        self._canary_deployments[canary_id] = canary
        await self._persist_canary(canary)
        
        logger.info(f"Started canary deployment {canary_id} for experiment {experiment_id} "
                   f"({traffic_percentage}% traffic)")
        
        return canary
    
    async def record_canary_result(
        self,
        canary_id: str,
        success: bool,
    ) -> bool:
        """
        Record a result from canary deployment.
        
        Args:
            canary_id: ID of the canary
            success: Whether the request was successful
        
        Returns:
            True if recorded successfully
        """
        if canary_id not in self._canary_deployments:
            return False
        
        canary = self._canary_deployments[canary_id]
        
        if not canary.is_active:
            return False
        
        if success:
            canary.success_count += 1
        else:
            canary.failure_count += 1
        
        await self._persist_canary(canary)
        
        return True
    
    async def evaluate_canary(
        self,
        canary_id: str,
    ) -> Tuple[bool, str]:
        """
        Evaluate canary deployment results.
        
        Args:
            canary_id: ID of the canary
        
        Returns:
            Tuple of (should_promote, reason)
        """
        if canary_id not in self._canary_deployments:
            return False, "Canary not found"
        
        canary = self._canary_deployments[canary_id]
        
        elapsed = datetime.now(timezone.utc) - canary.started_at
        if elapsed < timedelta(hours=canary.duration_hours):
            return False, "Canary still running"
        
        success_rate = canary.success_rate()
        criteria = self._gate_criteria[GateType.CANARY_GATE]
        
        if success_rate >= criteria.minimum_canary_success_rate:
            canary.is_active = False
            await self._persist_canary(canary)
            return True, f"Canary successful: {success_rate:.1%} success rate"
        else:
            canary.is_active = False
            await self._persist_canary(canary)
            return False, f"Canary failed: {success_rate:.1%} success rate (threshold: {criteria.minimum_canary_success_rate:.1%})"
    
    async def approve_manual_gate(
        self,
        promotion_id: str,
        gate_type: GateType,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Manually approve a gate that requires human review.
        
        Args:
            promotion_id: ID of the promotion
            gate_type: Type of gate to approve
            approved_by: Who approved it
            notes: Optional approval notes
        
        Returns:
            True if approved successfully
        """
        if promotion_id not in self._promotion_results:
            return False
        
        result = self._promotion_results[promotion_id]
        
        for gate_check in result.gates_checked:
            if gate_check.gate_type == gate_type:
                gate_check.status = GateStatus.PASSED
                gate_check.passed = True
                gate_check.details['manual_approval'] = {
                    'approved_by': approved_by,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'notes': notes,
                }
                break
        
        result.all_gates_passed = all(check.passed for check in result.gates_checked)
        
        if result.all_gates_passed:
            result.recommendation = "APPROVE FOR PRODUCTION"
            result.approved_for_production = True
        
        await self._persist_result(result)
        
        logger.info(f"Manual approval for {gate_type.value} in promotion {promotion_id} by {approved_by}")
        
        return True
    
    def get_promotion_result(self, promotion_id: str) -> Optional[PromotionResult]:
        """Get a promotion result by ID."""
        return self._promotion_results.get(promotion_id)
    
    def get_canary(self, canary_id: str) -> Optional[CanaryDeployment]:
        """Get a canary deployment by ID."""
        return self._canary_deployments.get(canary_id)
    
    def get_active_canaries(self) -> List[CanaryDeployment]:
        """Get all active canary deployments."""
        return [c for c in self._canary_deployments.values() if c.is_active]
    
    async def _persist_result(self, result: PromotionResult):
        """Persist promotion result to storage."""
        result_file = self.storage_path / 'promotions' / f"{result.promotion_id}.json"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
    
    async def _persist_canary(self, canary: CanaryDeployment):
        """Persist canary deployment to storage."""
        canary_file = self.storage_path / 'canaries' / f"{canary.canary_id}.json"
        canary_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(canary_file, 'w') as f:
            json.dump(canary.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get promotion gates statistics."""
        approved = [r for r in self._promotion_results.values() if r.approved_for_production]
        rejected = [r for r in self._promotion_results.values() if r.recommendation == "REJECT"]
        
        return {
            'total_promotions': len(self._promotion_results),
            'approved_count': len(approved),
            'rejected_count': len(rejected),
            'approval_rate': len(approved) / len(self._promotion_results) if self._promotion_results else 0,
            'active_canaries': len(self.get_active_canaries()),
            'total_canaries': len(self._canary_deployments),
        }
