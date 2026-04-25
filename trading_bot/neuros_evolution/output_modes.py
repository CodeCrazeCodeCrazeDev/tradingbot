"""
Standardized Output Modes
========================

Per Section 13: Required output format for candidate assessment.

When asked to assess a candidate model, route, or behavior, output in this format:

A. Capability Mapping
B. Candidate Fingerprint
C. Evaluation Verdict
D. Control Policies
E. Distillation Decision
F. Deployment Decision
G. Monitoring Requirements
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class EvaluationVerdict(Enum):
    """Evaluation verdict options"""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL = "conditional"


class DeploymentDecision(Enum):
    """Deployment decision options"""
    REJECT = "reject"
    SANDBOX_ONLY = "sandbox_only"
    CANARY = "canary"
    LIMITED_PRODUCTION = "limited_production"
    ROLLBACK = "rollback"


class DistillationDecision(Enum):
    """Distillation decision options"""
    DISTILL_NOW = "distill_now"
    OBSERVE_LONGER = "observe_longer"
    REJECT = "reject"
    ARCHIVE = "archive"


@dataclass
class CapabilityMappingSection:
    """
    A. Capability Mapping
    
    - capability IDs
    - task family
    - risk tier
    - regime assumptions
    """
    capability_ids: List[str]
    task_family: str
    risk_tier: str
    regime_assumptions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": "A. Capability Mapping",
            "capability_ids": self.capability_ids,
            "task_family": self.task_family,
            "risk_tier": self.risk_tier,
            "regime_assumptions": self.regime_assumptions
        }


@dataclass
class CandidateFingerprintSection:
    """
    B. Candidate Fingerprint
    
    - strengths
    - weaknesses
    - forbidden-use zones
    - cost/latency profile
    - integration difficulty
    """
    strengths: List[str]
    weaknesses: List[str]
    forbidden_use_zones: List[str]
    cost_profile: Dict[str, float]
    latency_profile_ms: Dict[str, float]
    integration_difficulty: str  # 'low', 'medium', 'high'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": "B. Candidate Fingerprint",
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "forbidden_use_zones": self.forbidden_use_zones,
            "cost_profile": self.cost_profile,
            "latency_profile_ms": self.latency_profile_ms,
            "integration_difficulty": self.integration_difficulty
        }


@dataclass
class EvaluationVerdictSection:
    """
    C. Evaluation Verdict
    
    - pass / fail / conditional
    - evidence summary
    - statistical confidence
    - key failure risks
    """
    verdict: EvaluationVerdict
    evidence_summary: str
    statistical_confidence: float  # 0-1
    key_failure_risks: List[str]
    evaluation_metrics: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": "C. Evaluation Verdict",
            "verdict": self.verdict.value,
            "evidence_summary": self.evidence_summary,
            "statistical_confidence": self.statistical_confidence,
            "key_failure_risks": self.key_failure_risks,
            "evaluation_metrics": self.evaluation_metrics
        }


@dataclass
class ControlPoliciesSection:
    """
    D. Control Policies
    
    - required guardrails
    - verifier requirements
    - fallback requirements
    - deployment restrictions
    """
    required_guardrails: List[str]
    verifier_requirements: List[str]
    fallback_requirements: List[str]
    deployment_restrictions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": "D. Control Policies",
            "required_guardrails": self.required_guardrails,
            "verifier_requirements": self.verifier_requirements,
            "fallback_requirements": self.fallback_requirements,
            "deployment_restrictions": self.deployment_restrictions
        }


@dataclass
class DistillationDecisionSection:
    """
    E. Distillation Decision
    
    - distill now / observe longer / reject / archive
    - reason
    - expected internalization target
    """
    decision: DistillationDecision
    reason: str
    expected_internalization_target: Optional[str]
    estimated_cost_savings: Optional[float]
    estimated_performance_degradation: Optional[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": "E. Distillation Decision",
            "decision": self.decision.value,
            "reason": self.reason,
            "expected_internalization_target": self.expected_internalization_target,
            "estimated_cost_savings": self.estimated_cost_savings,
            "estimated_performance_degradation": self.estimated_performance_degradation
        }


@dataclass
class DeploymentDecisionSection:
    """
    F. Deployment Decision
    
    - reject
    - sandbox only
    - canary
    - limited production
    - rollback
    """
    decision: DeploymentDecision
    rollout_percentage: Optional[float]  # For canary/limited
    rollback_target: Optional[str]
    deployment_scope: Dict[str, Any]  # capability, regime, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": "F. Deployment Decision",
            "decision": self.decision.value,
            "rollout_percentage": self.rollout_percentage,
            "rollback_target": self.rollback_target,
            "deployment_scope": self.deployment_scope
        }


@dataclass
class MonitoringRequirementsSection:
    """
    G. Monitoring Requirements
    
    - what to track
    - failure thresholds
    - rollback triggers
    """
    metrics_to_track: List[str]
    failure_thresholds: Dict[str, float]
    rollback_triggers: List[str]
    review_schedule: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": "G. Monitoring Requirements",
            "metrics_to_track": self.metrics_to_track,
            "failure_thresholds": self.failure_thresholds,
            "rollback_triggers": self.rollback_triggers,
            "review_schedule": self.review_schedule
        }


@dataclass
class AssessmentReport:
    """
    Complete assessment report per Section 13.
    
    Final question is always:
    "Does this capability, in this configuration, under these controls, 
    improve AlphaAlgo's objective more reliably than the current alternative?"
    
    If the answer is not clearly yes, do not promote.
    """
    report_id: str
    timestamp: str
    candidate_id: str
    
    # All sections
    capability_mapping: CapabilityMappingSection
    candidate_fingerprint: CandidateFingerprintSection
    evaluation_verdict: EvaluationVerdictSection
    control_policies: ControlPoliciesSection
    distillation_decision: DistillationDecisionSection
    deployment_decision: DeploymentDecisionSection
    monitoring_requirements: MonitoringRequirementsSection
    
    # Final decision
    final_answer: str  # "yes" or "not_clearly_yes"
    final_rationale: str
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "candidate_id": self.candidate_id,
            "sections": [
                self.capability_mapping.to_dict(),
                self.candidate_fingerprint.to_dict(),
                self.evaluation_verdict.to_dict(),
                self.control_policies.to_dict(),
                self.distillation_decision.to_dict(),
                self.deployment_decision.to_dict(),
                self.monitoring_requirements.to_dict()
            ],
            "final_answer": self.final_answer,
            "final_rationale": self.final_rationale,
            "metadata": self.metadata
        }
    
    def to_markdown(self) -> str:
        """Convert report to markdown format"""
        lines = [
            f"# Assessment Report: {self.candidate_id}",
            f"**Report ID:** {self.report_id}  ",
            f"**Timestamp:** {self.timestamp}  ",
            "",
            "## A. Capability Mapping",
            f"- **Capability IDs:** {', '.join(self.capability_mapping.capability_ids)}",
            f"- **Task Family:** {self.capability_mapping.task_family}",
            f"- **Risk Tier:** {self.capability_mapping.risk_tier}",
            f"- **Regime Assumptions:** {', '.join(self.capability_mapping.regime_assumptions)}",
            "",
            "## B. Candidate Fingerprint",
            "### Strengths",
        ]
        
        for strength in self.candidate_fingerprint.strengths:
            lines.append(f"- {strength}")
        
        lines.extend(["", "### Weaknesses"])
        for weakness in self.candidate_fingerprint.weaknesses:
            lines.append(f"- {weakness}")
        
        lines.extend([
            "",
            "### Forbidden-Use Zones",
        ])
        for zone in self.candidate_fingerprint.forbidden_use_zones:
            lines.append(f"- {zone}")
        
        lines.extend([
            "",
            f"### Cost Profile",
            f"- Token cost: ${self.candidate_fingerprint.cost_profile.get('token_cost_per_1k', 0):.4f}/1K",
            f"- Compute cost: ${self.candidate_fingerprint.cost_profile.get('compute_cost_per_hour', 0):.2f}/hour",
            "",
            f"### Latency Profile",
            f"- P50: {self.candidate_fingerprint.latency_profile_ms.get('p50', 0):.0f}ms",
            f"- P95: {self.candidate_fingerprint.latency_profile_ms.get('p95', 0):.0f}ms",
            "",
            f"### Integration Difficulty: {self.candidate_fingerprint.integration_difficulty}",
            "",
            "## C. Evaluation Verdict",
            f"**Verdict:** {self.evaluation_verdict.verdict.value.upper()}",
            f"**Statistical Confidence:** {self.evaluation_verdict.statistical_confidence:.1%}",
            "",
            f"**Evidence Summary:** {self.evaluation_verdict.evidence_summary}",
            "",
            "### Key Failure Risks",
        ])
        
        for risk in self.evaluation_verdict.key_failure_risks:
            lines.append(f"- {risk}")
        
        lines.extend([
            "",
            "## D. Control Policies",
            "### Required Guardrails",
        ])
        for guardrail in self.control_policies.required_guardrails:
            lines.append(f"- {guardrail}")
        
        lines.extend(["", "### Verifier Requirements"])
        for verifier in self.control_policies.verifier_requirements:
            lines.append(f"- {verifier}")
        
        lines.extend(["", "### Deployment Restrictions"])
        for restriction in self.control_policies.deployment_restrictions:
            lines.append(f"- {restriction}")
        
        lines.extend([
            "",
            "## E. Distillation Decision",
            f"**Decision:** {self.distillation_decision.decision.value}",
            f"**Reason:** {self.distillation_decision.reason}",
        ])
        
        if self.distillation_decision.expected_internalization_target:
            lines.append(f"**Expected Target:** {self.distillation_decision.expected_internalization_target}")
        
        lines.extend([
            "",
            "## F. Deployment Decision",
            f"**Decision:** {self.deployment_decision.decision.value}",
        ])
        
        if self.deployment_decision.rollout_percentage is not None:
            lines.append(f"**Rollout Percentage:** {self.deployment_decision.rollout_percentage:.1%}")
        
        if self.deployment_decision.rollback_target:
            lines.append(f"**Rollback Target:** {self.deployment_decision.rollback_target}")
        
        lines.extend([
            "",
            "## G. Monitoring Requirements",
            "### Metrics to Track",
        ])
        
        for metric in self.monitoring_requirements.metrics_to_track:
            lines.append(f"- {metric}")
        
        lines.extend(["", "### Failure Thresholds"])
        for metric, threshold in self.monitoring_requirements.failure_thresholds.items():
            lines.append(f"- {metric}: {threshold}")
        
        lines.extend(["", "### Rollback Triggers"])
        for trigger in self.monitoring_requirements.rollback_triggers:
            lines.append(f"- {trigger}")
        
        lines.extend([
            "",
            "---",
            "",
            "## Final Decision",
            f"**Question:** Does this capability improve AlphaAlgo's objective more reliably than the current alternative?",
            f"**Answer:** {self.final_answer.upper()}",
            "",
            f"**Rationale:** {self.final_rationale}",
        ])
        
        return '\n'.join(lines)


class AssessmentReportGenerator:
    """Generator for standardized assessment reports"""
    
    def __init__(self):
        self.reports: List[AssessmentReport] = []
        logger.info("AssessmentReportGenerator initialized")
    
    def generate_report(self,
                       candidate_id: str,
                       capability_mapping: CapabilityMappingSection,
                       fingerprint: CandidateFingerprintSection,
                       verdict: EvaluationVerdictSection,
                       controls: ControlPoliciesSection,
                       distillation: DistillationDecisionSection,
                       deployment: DeploymentDecisionSection,
                       monitoring: MonitoringRequirementsSection) -> AssessmentReport:
        """
        Generate a complete assessment report.
        
        The final answer is determined by:
        - verdict must be PASS or CONDITIONAL
        - statistical_confidence must be > 0.7
        - key_failure_risks must be controllable
        """
        # Determine final answer
        if verdict.verdict == EvaluationVerdict.FAIL:
            final_answer = "not_clearly_yes"
            final_rationale = f"Evaluation verdict is FAIL: {verdict.evidence_summary}"
        elif verdict.statistical_confidence < 0.7:
            final_answer = "not_clearly_yes"
            final_rationale = f"Insufficient statistical confidence ({verdict.statistical_confidence:.1%} < 70%)"
        elif len(verdict.key_failure_risks) > 3:
            final_answer = "not_clearly_yes"
            final_rationale = f"Too many uncontrolled failure risks ({len(verdict.key_failure_risks)})"
        else:
            final_answer = "yes"
            final_rationale = "All criteria met for promotion"
        
        report = AssessmentReport(
            report_id=f"assess_{datetime.utcnow().timestamp()}",
            timestamp=datetime.utcnow().isoformat(),
            candidate_id=candidate_id,
            capability_mapping=capability_mapping,
            candidate_fingerprint=fingerprint,
            evaluation_verdict=verdict,
            control_policies=controls,
            distillation_decision=distillation,
            deployment_decision=deployment,
            monitoring_requirements=monitoring,
            final_answer=final_answer,
            final_rationale=final_rationale
        )
        
        self.reports.append(report)
        logger.info(f"Generated assessment report for {candidate_id}: {final_answer}")
        
        return report
    
    def should_promote(self, report: AssessmentReport) -> bool:
        """
        Determine if report recommends promotion.
        
        Only promotes if final_answer is "yes".
        """
        return report.final_answer == "yes"
    
    def get_report_history(self, candidate_id: Optional[str] = None) -> List[AssessmentReport]:
        """Get report history"""
        if candidate_id:
            return [r for r in self.reports if r.candidate_id == candidate_id]
        return self.reports
    
    def get_promotion_statistics(self) -> Dict[str, Any]:
        """Get statistics on promotion decisions"""
        total = len(self.reports)
        if total == 0:
            return {"total": 0}
        
        promoted = sum(1 for r in self.reports if r.final_answer == "yes")
        rejected = total - promoted
        
        by_verdict = {}
        for r in self.reports:
            v = r.evaluation_verdict.verdict.value
            by_verdict[v] = by_verdict.get(v, 0) + 1
        
        return {
            "total_reports": total,
            "promoted": promoted,
            "rejected": rejected,
            "promotion_rate": promoted / total,
            "by_verdict": by_verdict
        }


# Convenience function
def create_assessment_generator() -> AssessmentReportGenerator:
    """Factory function to create assessment report generator"""
    return AssessmentReportGenerator()
