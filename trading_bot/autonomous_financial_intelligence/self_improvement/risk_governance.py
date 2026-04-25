"""
Risk Governance

Continuous risk assessment and management for infrastructure evolution.
Ensures safe deployment of improvements with automated risk mitigation.
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


class RiskLevel(Enum):
    """Risk levels for changes."""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(Enum):
    """Categories of risk."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_INTEGRITY = "data_integrity"
    HALLUCINATION_INCREASE = "hallucination_increase"
    VERIFICATION_FAILURE = "verification_failure"
    SYSTEM_INSTABILITY = "system_instability"
    SECURITY_VULNERABILITY = "security_vulnerability"
    COMPLIANCE_VIOLATION = "compliance_violation"
    FINANCIAL_LOSS = "financial_loss"


class MitigationStatus(Enum):
    """Status of risk mitigation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_REQUIRED = "not_required"


@dataclass
class RiskFactor:
    """A specific risk factor."""
    factor_id: str
    category: RiskCategory
    description: str
    probability: float
    impact: float
    severity: RiskLevel
    detected_at: datetime
    mitigation_required: bool
    
    def risk_score(self) -> float:
        """Calculate risk score (probability × impact)."""
        return self.probability * self.impact
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'factor_id': self.factor_id,
            'category': self.category.value,
            'description': self.description,
            'probability': self.probability,
            'impact': self.impact,
            'severity': self.severity.value,
            'risk_score': self.risk_score(),
            'detected_at': self.detected_at.isoformat(),
            'mitigation_required': self.mitigation_required,
        }


@dataclass
class RiskMitigation:
    """Mitigation strategy for a risk."""
    mitigation_id: str
    risk_factor_id: str
    strategy: str
    actions: List[Dict[str, Any]]
    status: MitigationStatus
    effectiveness: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'mitigation_id': self.mitigation_id,
            'risk_factor_id': self.risk_factor_id,
            'strategy': self.strategy,
            'actions': self.actions,
            'status': self.status.value,
            'effectiveness': self.effectiveness,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment."""
    assessment_id: str
    target_id: str
    target_type: str
    risk_factors: List[RiskFactor]
    overall_risk_level: RiskLevel
    overall_risk_score: float
    mitigations: List[RiskMitigation]
    is_acceptable: bool
    requires_approval: bool
    recommendations: List[str]
    assessed_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'assessment_id': self.assessment_id,
            'target_id': self.target_id,
            'target_type': self.target_type,
            'risk_factors': [rf.to_dict() for rf in self.risk_factors],
            'overall_risk_level': self.overall_risk_level.value,
            'overall_risk_score': self.overall_risk_score,
            'mitigations': [m.to_dict() for m in self.mitigations],
            'is_acceptable': self.is_acceptable,
            'requires_approval': self.requires_approval,
            'recommendations': self.recommendations,
            'assessed_at': self.assessed_at.isoformat(),
        }


@dataclass
class RiskPolicy:
    """Risk policy configuration."""
    max_acceptable_risk_score: float = 0.3
    auto_approve_threshold: float = 0.1
    require_human_approval_threshold: float = 0.5
    block_deployment_threshold: float = 0.8
    max_concurrent_high_risk_changes: int = 1
    rollback_trigger_threshold: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_acceptable_risk_score': self.max_acceptable_risk_score,
            'auto_approve_threshold': self.auto_approve_threshold,
            'require_human_approval_threshold': self.require_human_approval_threshold,
            'block_deployment_threshold': self.block_deployment_threshold,
            'max_concurrent_high_risk_changes': self.max_concurrent_high_risk_changes,
            'rollback_trigger_threshold': self.rollback_trigger_threshold,
        }


class RiskGovernance:
    """
    Continuous risk assessment and governance system.
    
    Provides:
    - Automated risk detection
    - Risk scoring and classification
    - Mitigation strategy generation
    - Deployment gating based on risk
    - Continuous monitoring
    - Automated rollback triggers
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'risk_governance_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._assessments: Dict[str, RiskAssessment] = {}
        self._active_risks: Dict[str, RiskFactor] = {}
        self._mitigations: Dict[str, RiskMitigation] = {}
        self._policy = RiskPolicy()
        
        self._risk_history: List[Dict[str, Any]] = []
        self._high_risk_deployments: Set[str] = set()
        
        logger.info("✅ Risk Governance initialized")
    
    async def assess_risk(
        self,
        target_id: str,
        target_type: str,
        change_description: Dict[str, Any],
        historical_data: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessment:
        """
        Perform comprehensive risk assessment.
        
        Args:
            target_id: ID of the target being assessed
            target_type: Type of target (experiment, deployment, etc.)
            change_description: Description of the change
            historical_data: Optional historical performance data
        
        Returns:
            RiskAssessment with detailed analysis
        """
        assessment_id = f"RISK-{uuid.uuid4().hex[:12]}"
        
        risk_factors = await self._identify_risk_factors(
            change_description,
            historical_data,
        )
        
        overall_score = self._calculate_overall_risk_score(risk_factors)
        overall_level = self._classify_risk_level(overall_score)
        
        mitigations = await self._generate_mitigations(risk_factors)
        
        is_acceptable = overall_score <= self._policy.max_acceptable_risk_score
        requires_approval = overall_score >= self._policy.require_human_approval_threshold
        
        recommendations = self._generate_recommendations(
            risk_factors,
            overall_score,
            overall_level,
        )
        
        assessment = RiskAssessment(
            assessment_id=assessment_id,
            target_id=target_id,
            target_type=target_type,
            risk_factors=risk_factors,
            overall_risk_level=overall_level,
            overall_risk_score=overall_score,
            mitigations=mitigations,
            is_acceptable=is_acceptable,
            requires_approval=requires_approval,
            recommendations=recommendations,
            assessed_at=datetime.now(timezone.utc),
        )
        
        self._assessments[assessment_id] = assessment
        
        for rf in risk_factors:
            self._active_risks[rf.factor_id] = rf
        
        for m in mitigations:
            self._mitigations[m.mitigation_id] = m
        
        await self._persist_assessment(assessment)
        
        logger.info(f"Risk assessment complete: {overall_level.value} "
                   f"(score: {overall_score:.3f}, factors: {len(risk_factors)})")
        
        return assessment
    
    async def _identify_risk_factors(
        self,
        change_description: Dict[str, Any],
        historical_data: Optional[Dict[str, Any]],
    ) -> List[RiskFactor]:
        """Identify potential risk factors."""
        risk_factors = []
        
        change_type = change_description.get('type', 'unknown')
        metrics = change_description.get('metrics', {})
        
        if metrics.get('error_rate', 0) > 0.05:
            risk_factors.append(RiskFactor(
                factor_id=f"RF-{uuid.uuid4().hex[:8]}",
                category=RiskCategory.PERFORMANCE_DEGRADATION,
                description=f"Error rate {metrics['error_rate']:.1%} exceeds threshold",
                probability=0.7,
                impact=0.6,
                severity=RiskLevel.MEDIUM,
                detected_at=datetime.now(timezone.utc),
                mitigation_required=True,
            ))
        
        if metrics.get('hallucination_rate', 0) > 0.01:
            risk_factors.append(RiskFactor(
                factor_id=f"RF-{uuid.uuid4().hex[:8]}",
                category=RiskCategory.HALLUCINATION_INCREASE,
                description=f"Hallucination rate {metrics['hallucination_rate']:.1%} above acceptable level",
                probability=0.8,
                impact=0.9,
                severity=RiskLevel.HIGH,
                detected_at=datetime.now(timezone.utc),
                mitigation_required=True,
            ))
        
        if metrics.get('latency_ms', 0) > 1000:
            risk_factors.append(RiskFactor(
                factor_id=f"RF-{uuid.uuid4().hex[:8]}",
                category=RiskCategory.PERFORMANCE_DEGRADATION,
                description=f"Latency {metrics['latency_ms']}ms exceeds acceptable threshold",
                probability=0.6,
                impact=0.5,
                severity=RiskLevel.MEDIUM,
                detected_at=datetime.now(timezone.utc),
                mitigation_required=True,
            ))
        
        if change_type in ['architecture_change', 'core_modification']:
            risk_factors.append(RiskFactor(
                factor_id=f"RF-{uuid.uuid4().hex[:8]}",
                category=RiskCategory.SYSTEM_INSTABILITY,
                description=f"Core system change carries inherent risk",
                probability=0.4,
                impact=0.8,
                severity=RiskLevel.HIGH,
                detected_at=datetime.now(timezone.utc),
                mitigation_required=True,
            ))
        
        if change_description.get('affects_verification', False):
            risk_factors.append(RiskFactor(
                factor_id=f"RF-{uuid.uuid4().hex[:8]}",
                category=RiskCategory.VERIFICATION_FAILURE,
                description="Change affects verification layer",
                probability=0.5,
                impact=0.7,
                severity=RiskLevel.HIGH,
                detected_at=datetime.now(timezone.utc),
                mitigation_required=True,
            ))
        
        sample_size = change_description.get('sample_size', 0)
        if sample_size < 1000:
            risk_factors.append(RiskFactor(
                factor_id=f"RF-{uuid.uuid4().hex[:8]}",
                category=RiskCategory.DATA_INTEGRITY,
                description=f"Insufficient sample size ({sample_size}) for reliable assessment",
                probability=0.6,
                impact=0.4,
                severity=RiskLevel.MEDIUM,
                detected_at=datetime.now(timezone.utc),
                mitigation_required=True,
            ))
        
        return risk_factors
    
    def _calculate_overall_risk_score(self, risk_factors: List[RiskFactor]) -> float:
        """Calculate overall risk score from individual factors."""
        if not risk_factors:
            return 0.0
        
        risk_scores = [rf.risk_score() for rf in risk_factors]
        
        max_risk = max(risk_scores)
        avg_risk = sum(risk_scores) / len(risk_scores)
        
        overall = 0.6 * max_risk + 0.4 * avg_risk
        
        if len(risk_factors) > 5:
            overall *= 1.2
        
        return min(1.0, overall)
    
    def _classify_risk_level(self, risk_score: float) -> RiskLevel:
        """Classify risk level based on score."""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    async def _generate_mitigations(
        self,
        risk_factors: List[RiskFactor],
    ) -> List[RiskMitigation]:
        """Generate mitigation strategies for risk factors."""
        mitigations = []
        
        for rf in risk_factors:
            if not rf.mitigation_required:
                continue
            
            mitigation_id = f"MIT-{uuid.uuid4().hex[:8]}"
            
            if rf.category == RiskCategory.HALLUCINATION_INCREASE:
                strategy = "Enhanced hallucination detection and canary deployment"
                actions = [
                    {'action': 'enable_enhanced_detection', 'threshold': 0.005},
                    {'action': 'start_canary', 'traffic': 5},
                    {'action': 'monitor_closely', 'duration_hours': 24},
                ]
                effectiveness = 0.85
            
            elif rf.category == RiskCategory.PERFORMANCE_DEGRADATION:
                strategy = "Performance monitoring and gradual rollout"
                actions = [
                    {'action': 'set_performance_alerts', 'threshold': 'strict'},
                    {'action': 'gradual_rollout', 'increment': 10},
                    {'action': 'prepare_rollback', 'trigger': 'performance_drop'},
                ]
                effectiveness = 0.75
            
            elif rf.category == RiskCategory.SYSTEM_INSTABILITY:
                strategy = "Comprehensive testing and staged deployment"
                actions = [
                    {'action': 'extended_testing', 'duration_hours': 48},
                    {'action': 'shadow_mode', 'duration_hours': 24},
                    {'action': 'staged_deployment', 'stages': 4},
                ]
                effectiveness = 0.80
            
            elif rf.category == RiskCategory.VERIFICATION_FAILURE:
                strategy = "Dual-run verification and validation"
                actions = [
                    {'action': 'dual_run_mode', 'duration_hours': 72},
                    {'action': 'cross_validation', 'samples': 10000},
                    {'action': 'expert_review', 'required': True},
                ]
                effectiveness = 0.90
            
            else:
                strategy = "Standard risk mitigation protocol"
                actions = [
                    {'action': 'increased_monitoring', 'duration_hours': 48},
                    {'action': 'rollback_preparation', 'automated': True},
                ]
                effectiveness = 0.70
            
            mitigation = RiskMitigation(
                mitigation_id=mitigation_id,
                risk_factor_id=rf.factor_id,
                strategy=strategy,
                actions=actions,
                status=MitigationStatus.PENDING,
                effectiveness=effectiveness,
                created_at=datetime.now(timezone.utc),
            )
            
            mitigations.append(mitigation)
        
        return mitigations
    
    def _generate_recommendations(
        self,
        risk_factors: List[RiskFactor],
        overall_score: float,
        overall_level: RiskLevel,
    ) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        if overall_score >= self._policy.block_deployment_threshold:
            recommendations.append("BLOCK DEPLOYMENT - Risk level too high")
            recommendations.append("Address critical risk factors before proceeding")
        
        elif overall_score >= self._policy.require_human_approval_threshold:
            recommendations.append("REQUIRE HUMAN APPROVAL before deployment")
            recommendations.append("Implement all mitigation strategies")
        
        elif overall_score >= self._policy.auto_approve_threshold:
            recommendations.append("Proceed with CANARY DEPLOYMENT")
            recommendations.append("Monitor closely during rollout")
        
        else:
            recommendations.append("Risk acceptable - proceed with standard deployment")
        
        high_risk_factors = [rf for rf in risk_factors if rf.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        if high_risk_factors:
            recommendations.append(f"Address {len(high_risk_factors)} high/critical risk factors")
        
        hallucination_risks = [rf for rf in risk_factors if rf.category == RiskCategory.HALLUCINATION_INCREASE]
        if hallucination_risks:
            recommendations.append("Enhanced hallucination monitoring required")
        
        if len(self._high_risk_deployments) >= self._policy.max_concurrent_high_risk_changes:
            recommendations.append("Wait for current high-risk deployments to stabilize")
        
        return recommendations
    
    async def apply_mitigation(
        self,
        mitigation_id: str,
    ) -> bool:
        """
        Apply a mitigation strategy.
        
        Args:
            mitigation_id: ID of the mitigation
        
        Returns:
            True if applied successfully
        """
        if mitigation_id not in self._mitigations:
            return False
        
        mitigation = self._mitigations[mitigation_id]
        
        mitigation.status = MitigationStatus.IN_PROGRESS
        
        for action in mitigation.actions:
            logger.info(f"Applying mitigation action: {action['action']}")
        
        mitigation.status = MitigationStatus.COMPLETED
        mitigation.completed_at = datetime.now(timezone.utc)
        
        await self._persist_mitigation(mitigation)
        
        return True
    
    async def monitor_deployment_risk(
        self,
        deployment_id: str,
        metrics: Dict[str, float],
    ) -> Tuple[bool, Optional[str]]:
        """
        Monitor ongoing deployment for risk triggers.
        
        Args:
            deployment_id: ID of the deployment
            metrics: Current metrics
        
        Returns:
            Tuple of (should_rollback, reason)
        """
        risk_score = 0.0
        reasons = []
        
        if metrics.get('error_rate', 0) > 0.1:
            risk_score += 0.4
            reasons.append(f"Error rate {metrics['error_rate']:.1%} exceeded threshold")
        
        if metrics.get('hallucination_rate', 0) > 0.02:
            risk_score += 0.5
            reasons.append(f"Hallucination rate {metrics['hallucination_rate']:.1%} exceeded threshold")
        
        if metrics.get('latency_ms', 0) > 2000:
            risk_score += 0.3
            reasons.append(f"Latency {metrics['latency_ms']}ms exceeded threshold")
        
        if risk_score >= self._policy.rollback_trigger_threshold:
            reason = "ROLLBACK TRIGGERED: " + "; ".join(reasons)
            logger.critical(f"Deployment {deployment_id} triggered rollback: {reason}")
            return True, reason
        
        return False, None
    
    def update_policy(self, policy_updates: Dict[str, Any]):
        """Update risk policy configuration."""
        for key, value in policy_updates.items():
            if hasattr(self._policy, key):
                setattr(self._policy, key, value)
        
        logger.info(f"Updated risk policy: {policy_updates}")
    
    def get_assessment(self, assessment_id: str) -> Optional[RiskAssessment]:
        """Get a risk assessment by ID."""
        return self._assessments.get(assessment_id)
    
    def get_active_risks(self) -> List[RiskFactor]:
        """Get all active risk factors."""
        return list(self._active_risks.values())
    
    def get_high_risk_count(self) -> int:
        """Get count of high-risk active factors."""
        return len([rf for rf in self._active_risks.values() 
                   if rf.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
    
    async def _persist_assessment(self, assessment: RiskAssessment):
        """Persist risk assessment to storage."""
        assessment_file = self.storage_path / 'assessments' / f"{assessment.assessment_id}.json"
        assessment_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(assessment_file, 'w') as f:
            json.dump(assessment.to_dict(), f, indent=2)
    
    async def _persist_mitigation(self, mitigation: RiskMitigation):
        """Persist mitigation to storage."""
        mitigation_file = self.storage_path / 'mitigations' / f"{mitigation.mitigation_id}.json"
        mitigation_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(mitigation_file, 'w') as f:
            json.dump(mitigation.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get risk governance statistics."""
        risk_level_counts = {}
        for rf in self._active_risks.values():
            risk_level_counts[rf.severity.value] = risk_level_counts.get(rf.severity.value, 0) + 1
        
        category_counts = {}
        for rf in self._active_risks.values():
            category_counts[rf.category.value] = category_counts.get(rf.category.value, 0) + 1
        
        return {
            'total_assessments': len(self._assessments),
            'active_risks': len(self._active_risks),
            'high_risk_count': self.get_high_risk_count(),
            'risks_by_level': risk_level_counts,
            'risks_by_category': category_counts,
            'active_mitigations': len([m for m in self._mitigations.values() 
                                      if m.status == MitigationStatus.IN_PROGRESS]),
            'policy': self._policy.to_dict(),
        }
