"""
Self-Audit System
==================

Continuously self-auditing trading research organism.

PHILOSOPHY:
- Audit ALL research activities continuously
- Verify hypothesis quality and validity
- Check for overfitting, data snooping, p-hacking
- Enforce governance rules
- Maintain research integrity

AUDIT TYPES:
1. HYPOTHESIS AUDIT - Is the hypothesis valid?
2. DATA AUDIT - Is the data clean and unbiased?
3. METHODOLOGY AUDIT - Is the methodology sound?
4. RESULTS AUDIT - Are results statistically valid?
5. GOVERNANCE AUDIT - Are rules being followed?
6. INTEGRITY AUDIT - Is there any manipulation?
"""

import logging
import hashlib
import threading
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class AuditType(Enum):
    """Types of audits"""
    HYPOTHESIS = "hypothesis"
    DATA = "data"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    GOVERNANCE = "governance"
    INTEGRITY = "integrity"


class AuditSeverity(Enum):
    """Severity of audit findings"""
    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


class AuditStatus(Enum):
    """Status of audit"""
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class AuditFinding:
    """A finding from an audit"""
    finding_id: str
    audit_type: AuditType
    severity: AuditSeverity
    description: str
    evidence: List[str]
    recommendation: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'finding_id': self.finding_id,
            'audit_type': self.audit_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'evidence': self.evidence,
            'recommendation': self.recommendation,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class AuditResult:
    """Result of an audit"""
    audit_id: str
    audit_type: AuditType
    target_id: str
    target_type: str
    status: AuditStatus
    findings: List[AuditFinding]
    score: float  # 0 to 1
    timestamp: datetime = field(default_factory=datetime.now)
    auditor: str = "SelfAuditSystem"
    
    def to_dict(self) -> Dict:
        return {
            'audit_id': self.audit_id,
            'audit_type': self.audit_type.value,
            'target_id': self.target_id,
            'target_type': self.target_type,
            'status': self.status.value,
            'findings': [f.to_dict() for f in self.findings],
            'score': self.score,
            'timestamp': self.timestamp.isoformat(),
            'auditor': self.auditor
        }


class HypothesisAuditor:
    """Audits hypothesis quality"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def audit(self, hypothesis: Dict[str, Any]) -> AuditResult:
        """Audit a hypothesis"""
        findings = []
        score = 1.0
        
        # Check if hypothesis is falsifiable
        if not hypothesis.get('predictions'):
            findings.append(AuditFinding(
                finding_id=self._generate_id("no_predictions"),
                audit_type=AuditType.HYPOTHESIS,
                severity=AuditSeverity.CRITICAL,
                description="Hypothesis has no testable predictions",
                evidence=["predictions field is empty"],
                recommendation="Add falsifiable predictions"
            ))
            score -= 0.3
        
        # Check for boundary conditions
        if not hypothesis.get('boundary_conditions'):
            findings.append(AuditFinding(
                finding_id=self._generate_id("no_boundaries"),
                audit_type=AuditType.HYPOTHESIS,
                severity=AuditSeverity.WARNING,
                description="Hypothesis has no boundary conditions",
                evidence=["boundary_conditions field is empty"],
                recommendation="Define when hypothesis applies"
            ))
            score -= 0.1
        
        # Check for kill conditions
        if not hypothesis.get('kill_conditions'):
            findings.append(AuditFinding(
                finding_id=self._generate_id("no_kill"),
                audit_type=AuditType.HYPOTHESIS,
                severity=AuditSeverity.WARNING,
                description="Hypothesis has no kill conditions",
                evidence=["kill_conditions field is empty"],
                recommendation="Define what would kill this hypothesis"
            ))
            score -= 0.1
        
        # Check for mechanism
        if not hypothesis.get('mechanism'):
            findings.append(AuditFinding(
                finding_id=self._generate_id("no_mechanism"),
                audit_type=AuditType.HYPOTHESIS,
                severity=AuditSeverity.WARNING,
                description="Hypothesis has no causal mechanism",
                evidence=["mechanism field is empty"],
                recommendation="Explain WHY this hypothesis might be true"
            ))
            score -= 0.1
        
        # Check for vague language
        statement = hypothesis.get('statement', '')
        vague_words = ['might', 'could', 'possibly', 'sometimes', 'often']
        vague_count = sum(1 for word in vague_words if word in statement.lower())
        if vague_count > 2:
            findings.append(AuditFinding(
                finding_id=self._generate_id("vague_language"),
                audit_type=AuditType.HYPOTHESIS,
                severity=AuditSeverity.INFO,
                description="Hypothesis uses vague language",
                evidence=[f"Found {vague_count} vague words"],
                recommendation="Use more precise language"
            ))
            score -= 0.05
        
        # Determine status
        status = AuditStatus.PASSED
        if any(f.severity == AuditSeverity.CRITICAL for f in findings):
            status = AuditStatus.FAILED
        elif any(f.severity == AuditSeverity.VIOLATION for f in findings):
            status = AuditStatus.FAILED
        elif any(f.severity == AuditSeverity.WARNING for f in findings):
            status = AuditStatus.PASSED_WITH_WARNINGS
        
        return AuditResult(
            audit_id=self._generate_id("hypothesis_audit"),
            audit_type=AuditType.HYPOTHESIS,
            target_id=hypothesis.get('hypothesis_id', 'unknown'),
            target_type='hypothesis',
            status=status,
            findings=findings,
            score=max(0, score)
        )
    
    def _generate_id(self, prefix: str) -> str:
        return hashlib.md5(
            f"{prefix}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]


class DataAuditor:
    """Audits data quality and integrity"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def audit(self, data_info: Dict[str, Any]) -> AuditResult:
        """Audit data quality"""
        findings = []
        score = 1.0
        
        # Check for look-ahead bias
        if data_info.get('includes_future_data', False):
            findings.append(AuditFinding(
                finding_id=self._generate_id("lookahead"),
                audit_type=AuditType.DATA,
                severity=AuditSeverity.CRITICAL,
                description="Data includes look-ahead bias",
                evidence=["Future data used in training"],
                recommendation="Remove all future data from training set"
            ))
            score -= 0.5
        
        # Check for survivorship bias
        if data_info.get('survivorship_bias', False):
            findings.append(AuditFinding(
                finding_id=self._generate_id("survivorship"),
                audit_type=AuditType.DATA,
                severity=AuditSeverity.VIOLATION,
                description="Data has survivorship bias",
                evidence=["Only surviving assets included"],
                recommendation="Include delisted assets"
            ))
            score -= 0.3
        
        # Check sample size
        sample_size = data_info.get('sample_size', 0)
        if sample_size < 100:
            findings.append(AuditFinding(
                finding_id=self._generate_id("small_sample"),
                audit_type=AuditType.DATA,
                severity=AuditSeverity.WARNING,
                description=f"Small sample size: {sample_size}",
                evidence=[f"Sample size {sample_size} < 100"],
                recommendation="Collect more data"
            ))
            score -= 0.2
        
        # Check for data quality
        missing_pct = data_info.get('missing_percentage', 0)
        if missing_pct > 5:
            findings.append(AuditFinding(
                finding_id=self._generate_id("missing_data"),
                audit_type=AuditType.DATA,
                severity=AuditSeverity.WARNING,
                description=f"High missing data: {missing_pct:.1f}%",
                evidence=[f"Missing percentage: {missing_pct:.1f}%"],
                recommendation="Improve data collection or imputation"
            ))
            score -= 0.1
        
        # Check for data snooping
        if data_info.get('multiple_testing', 0) > 20:
            findings.append(AuditFinding(
                finding_id=self._generate_id("data_snooping"),
                audit_type=AuditType.DATA,
                severity=AuditSeverity.VIOLATION,
                description="Potential data snooping detected",
                evidence=[f"Multiple testing: {data_info.get('multiple_testing', 0)} tests"],
                recommendation="Apply Bonferroni correction or use fresh data"
            ))
            score -= 0.3
        
        # Determine status
        status = AuditStatus.PASSED
        if any(f.severity == AuditSeverity.CRITICAL for f in findings):
            status = AuditStatus.FAILED
        elif any(f.severity == AuditSeverity.VIOLATION for f in findings):
            status = AuditStatus.FAILED
        elif any(f.severity == AuditSeverity.WARNING for f in findings):
            status = AuditStatus.PASSED_WITH_WARNINGS
        
        return AuditResult(
            audit_id=self._generate_id("data_audit"),
            audit_type=AuditType.DATA,
            target_id=data_info.get('data_id', 'unknown'),
            target_type='data',
            status=status,
            findings=findings,
            score=max(0, score)
        )
    
    def _generate_id(self, prefix: str) -> str:
        return hashlib.md5(
            f"{prefix}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]


class MethodologyAuditor:
    """Audits research methodology"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def audit(self, methodology: Dict[str, Any]) -> AuditResult:
        """Audit methodology"""
        findings = []
        score = 1.0
        
        # Check for out-of-sample testing
        if not methodology.get('out_of_sample_test', False):
            findings.append(AuditFinding(
                finding_id=self._generate_id("no_oos"),
                audit_type=AuditType.METHODOLOGY,
                severity=AuditSeverity.CRITICAL,
                description="No out-of-sample testing",
                evidence=["out_of_sample_test is False"],
                recommendation="Always test on held-out data"
            ))
            score -= 0.4
        
        # Check for cross-validation
        if not methodology.get('cross_validation', False):
            findings.append(AuditFinding(
                finding_id=self._generate_id("no_cv"),
                audit_type=AuditType.METHODOLOGY,
                severity=AuditSeverity.WARNING,
                description="No cross-validation used",
                evidence=["cross_validation is False"],
                recommendation="Use time-series cross-validation"
            ))
            score -= 0.1
        
        # Check for overfitting indicators
        train_score = methodology.get('train_score', 0)
        test_score = methodology.get('test_score', 0)
        if train_score > 0 and test_score > 0:
            overfit_ratio = train_score / max(test_score, 0.01)
            if overfit_ratio > 1.5:
                findings.append(AuditFinding(
                    finding_id=self._generate_id("overfitting"),
                    audit_type=AuditType.METHODOLOGY,
                    severity=AuditSeverity.VIOLATION,
                    description=f"Overfitting detected: train/test ratio = {overfit_ratio:.2f}",
                    evidence=[f"Train: {train_score:.3f}, Test: {test_score:.3f}"],
                    recommendation="Simplify model or add regularization"
                ))
                score -= 0.3
        
        # Check for p-hacking
        p_values_tested = methodology.get('p_values_tested', 0)
        if p_values_tested > 10:
            findings.append(AuditFinding(
                finding_id=self._generate_id("p_hacking"),
                audit_type=AuditType.METHODOLOGY,
                severity=AuditSeverity.WARNING,
                description=f"Potential p-hacking: {p_values_tested} tests",
                evidence=[f"Number of p-values tested: {p_values_tested}"],
                recommendation="Pre-register hypotheses or adjust for multiple testing"
            ))
            score -= 0.2
        
        # Check for parameter count
        param_count = methodology.get('parameter_count', 0)
        sample_size = methodology.get('sample_size', 1000)
        if param_count > sample_size / 10:
            findings.append(AuditFinding(
                finding_id=self._generate_id("too_many_params"),
                audit_type=AuditType.METHODOLOGY,
                severity=AuditSeverity.WARNING,
                description=f"Too many parameters: {param_count} for {sample_size} samples",
                evidence=[f"Params/samples ratio: {param_count/sample_size:.2f}"],
                recommendation="Reduce model complexity"
            ))
            score -= 0.15
        
        # Determine status
        status = AuditStatus.PASSED
        if any(f.severity == AuditSeverity.CRITICAL for f in findings):
            status = AuditStatus.FAILED
        elif any(f.severity == AuditSeverity.VIOLATION for f in findings):
            status = AuditStatus.FAILED
        elif any(f.severity == AuditSeverity.WARNING for f in findings):
            status = AuditStatus.PASSED_WITH_WARNINGS
        
        return AuditResult(
            audit_id=self._generate_id("methodology_audit"),
            audit_type=AuditType.METHODOLOGY,
            target_id=methodology.get('methodology_id', 'unknown'),
            target_type='methodology',
            status=status,
            findings=findings,
            score=max(0, score)
        )
    
    def _generate_id(self, prefix: str) -> str:
        return hashlib.md5(
            f"{prefix}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]


class GovernanceAuditor:
    """Audits governance rule compliance"""
    
    # IMMUTABLE GOVERNANCE RULES
    GOVERNANCE_RULES = frozenset([
        "ai_cannot_deploy_models",
        "ai_cannot_change_risk_rules",
        "ai_cannot_access_capital",
        "ai_cannot_modify_governance",
        "all_changes_require_human_approval",
        "all_activities_must_be_logged",
        "hypotheses_must_be_falsifiable",
        "results_must_be_reproducible"
    ])
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.rule_violations: Dict[str, int] = defaultdict(int)
    
    def audit(self, activity: Dict[str, Any]) -> AuditResult:
        """Audit governance compliance"""
        findings = []
        score = 1.0
        
        activity_type = activity.get('type', 'unknown')
        
        # Check for deployment attempts
        if activity_type == 'deploy_model':
            findings.append(AuditFinding(
                finding_id=self._generate_id("deploy_attempt"),
                audit_type=AuditType.GOVERNANCE,
                severity=AuditSeverity.CRITICAL,
                description="AI attempted to deploy model",
                evidence=["Activity type: deploy_model"],
                recommendation="AI CANNOT deploy models - requires human"
            ))
            score = 0.0
            self.rule_violations["ai_cannot_deploy_models"] += 1
        
        # Check for risk rule changes
        if activity_type == 'change_risk_rules':
            findings.append(AuditFinding(
                finding_id=self._generate_id("risk_change"),
                audit_type=AuditType.GOVERNANCE,
                severity=AuditSeverity.CRITICAL,
                description="AI attempted to change risk rules",
                evidence=["Activity type: change_risk_rules"],
                recommendation="AI CANNOT change risk rules"
            ))
            score = 0.0
            self.rule_violations["ai_cannot_change_risk_rules"] += 1
        
        # Check for capital access
        if activity_type == 'access_capital':
            findings.append(AuditFinding(
                finding_id=self._generate_id("capital_access"),
                audit_type=AuditType.GOVERNANCE,
                severity=AuditSeverity.CRITICAL,
                description="AI attempted to access capital",
                evidence=["Activity type: access_capital"],
                recommendation="AI CANNOT access capital"
            ))
            score = 0.0
            self.rule_violations["ai_cannot_access_capital"] += 1
        
        # Check for human approval
        if activity.get('requires_approval', False) and not activity.get('approved', False):
            findings.append(AuditFinding(
                finding_id=self._generate_id("no_approval"),
                audit_type=AuditType.GOVERNANCE,
                severity=AuditSeverity.VIOLATION,
                description="Activity requires approval but not approved",
                evidence=["requires_approval=True, approved=False"],
                recommendation="Get human approval before proceeding"
            ))
            score -= 0.5
        
        # Check for logging
        if not activity.get('logged', True):
            findings.append(AuditFinding(
                finding_id=self._generate_id("not_logged"),
                audit_type=AuditType.GOVERNANCE,
                severity=AuditSeverity.WARNING,
                description="Activity not properly logged",
                evidence=["logged=False"],
                recommendation="All activities must be logged"
            ))
            score -= 0.1
        
        # Determine status
        status = AuditStatus.PASSED
        if any(f.severity == AuditSeverity.CRITICAL for f in findings):
            status = AuditStatus.BLOCKED
        elif any(f.severity == AuditSeverity.VIOLATION for f in findings):
            status = AuditStatus.FAILED
        elif any(f.severity == AuditSeverity.WARNING for f in findings):
            status = AuditStatus.PASSED_WITH_WARNINGS
        
        return AuditResult(
            audit_id=self._generate_id("governance_audit"),
            audit_type=AuditType.GOVERNANCE,
            target_id=activity.get('activity_id', 'unknown'),
            target_type='activity',
            status=status,
            findings=findings,
            score=max(0, score)
        )
    
    def get_rule_violations(self) -> Dict[str, int]:
        """Get count of rule violations"""
        return dict(self.rule_violations)
    
    def _generate_id(self, prefix: str) -> str:
        return hashlib.md5(
            f"{prefix}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]


class SelfAuditSystem:
    """
    Main self-audit system.
    
    CORE PRINCIPLE:
    Continuously audit ALL research activities.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Initialize auditors
        self.hypothesis_auditor = HypothesisAuditor(config)
        self.data_auditor = DataAuditor(config)
        self.methodology_auditor = MethodologyAuditor(config)
        self.governance_auditor = GovernanceAuditor(config)
        
        # Audit history
        self.audit_history: List[AuditResult] = []
        
        # Statistics
        self.total_audits = 0
        self.passed_audits = 0
        self.failed_audits = 0
        self.blocked_audits = 0
        
        logger.info("SelfAuditSystem initialized")
    
    def audit_hypothesis(self, hypothesis: Dict[str, Any]) -> AuditResult:
        """Audit a hypothesis"""
        with self.lock:
            result = self.hypothesis_auditor.audit(hypothesis)
            self._record_audit(result)
            return result
    
    def audit_data(self, data_info: Dict[str, Any]) -> AuditResult:
        """Audit data quality"""
        with self.lock:
            result = self.data_auditor.audit(data_info)
            self._record_audit(result)
            return result
    
    def audit_methodology(self, methodology: Dict[str, Any]) -> AuditResult:
        """Audit methodology"""
        with self.lock:
            result = self.methodology_auditor.audit(methodology)
            self._record_audit(result)
            return result
    
    def audit_activity(self, activity: Dict[str, Any]) -> AuditResult:
        """Audit activity for governance compliance"""
        with self.lock:
            result = self.governance_auditor.audit(activity)
            self._record_audit(result)
            return result
    
    def audit_research(
        self,
        hypothesis: Dict[str, Any],
        data_info: Dict[str, Any],
        methodology: Dict[str, Any]
    ) -> Dict[str, AuditResult]:
        """
        Comprehensive audit of research.
        
        Args:
            hypothesis: Hypothesis to audit
            data_info: Data information
            methodology: Methodology information
            
        Returns:
            Dict of audit results
        """
        with self.lock:
            results = {
                'hypothesis': self.hypothesis_auditor.audit(hypothesis),
                'data': self.data_auditor.audit(data_info),
                'methodology': self.methodology_auditor.audit(methodology)
            }
            
            for result in results.values():
                self._record_audit(result)
            
            return results
    
    def _record_audit(self, result: AuditResult):
        """Record audit result"""
        self.audit_history.append(result)
        self.total_audits += 1
        
        if result.status == AuditStatus.PASSED:
            self.passed_audits += 1
        elif result.status == AuditStatus.PASSED_WITH_WARNINGS:
            self.passed_audits += 1
        elif result.status == AuditStatus.FAILED:
            self.failed_audits += 1
        elif result.status == AuditStatus.BLOCKED:
            self.blocked_audits += 1
        
        # Log result
        if result.status in [AuditStatus.FAILED, AuditStatus.BLOCKED]:
            logger.warning(
                "AUDIT %s [%s]: %s - %d findings",
                result.status.value.upper(),
                result.audit_type.value,
                result.target_id,
                len(result.findings)
            )
    
    def can_proceed(self, audit_results: Dict[str, AuditResult]) -> Tuple[bool, List[str]]:
        """
        Check if research can proceed based on audit results.
        
        Args:
            audit_results: Dict of audit results
            
        Returns:
            Tuple of (can_proceed, blocking_reasons)
        """
        blocking_reasons = []
        
        for audit_name, result in audit_results.items():
            if result.status == AuditStatus.BLOCKED:
                blocking_reasons.append(f"{audit_name}: BLOCKED - governance violation")
            elif result.status == AuditStatus.FAILED:
                critical_findings = [
                    f for f in result.findings
                    if f.severity in [AuditSeverity.CRITICAL, AuditSeverity.VIOLATION]
                ]
                for finding in critical_findings:
                    blocking_reasons.append(f"{audit_name}: {finding.description}")
        
        return len(blocking_reasons) == 0, blocking_reasons
    
    def get_governance_violations(self) -> Dict[str, int]:
        """Get governance rule violations"""
        return self.governance_auditor.get_rule_violations()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        with self.lock:
            return {
                'total_audits': self.total_audits,
                'passed_audits': self.passed_audits,
                'failed_audits': self.failed_audits,
                'blocked_audits': self.blocked_audits,
                'pass_rate': self.passed_audits / max(self.total_audits, 1),
                'governance_violations': self.get_governance_violations(),
                'recent_audits': [
                    a.to_dict() for a in self.audit_history[-10:]
                ]
            }
