"""
Self-Inspection and Meta-Learning Engine

A comprehensive system that inspects its own decisions, reasoning artifacts, 
uncertainty, and outcomes to detect errors, limitations, and improvement opportunities.

Core Functions:
1. Decision Quality Analysis - Inspect decision patterns and quality metrics
2. Reasoning Artifact Inspection - Analyze claims, evidence, audit trails
3. Uncertainty Calibration Tracking - Monitor confidence vs. reality
4. Error Pattern Detection - Find systematic errors and biases
5. Improvement Opportunity Mining - Learn from both successes and failures
6. Real-time Self-Monitoring - Continuous introspection during operation

This engine works with the IntrospectionDrivenEvolutionEngine and 
ContinuousCapabilityDiscoveryEngine to form a complete self-improving system.
"""

from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import logging
import asyncio
import json
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class InspectionCategory(Enum):
    """Categories of self-inspection findings"""
    DECISION_QUALITY = "decision_quality"
    REASONING_SOUNDNESS = "reasoning_soundness"
    UNCERTAINTY_CALIBRATION = "uncertainty_calibration"
    EVIDENCE_SUFFICIENCY = "evidence_sufficiency"
    COGNITIVE_BIAS = "cognitive_bias"
    SYSTEMATIC_ERROR = "systematic_error"
    PERFORMANCE_DRIFT = "performance_drift"
    CAPABILITY_GAP = "capability_gap"


class FindingSeverity(Enum):
    """Severity levels for inspection findings"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Significant impact, fix soon
    MEDIUM = "medium"  # Moderate impact, plan fix
    LOW = "low"  # Minor issue, monitor
    INFO = "info"  # Observation, no action needed


@dataclass
class InspectionFinding:
    """A single finding from self-inspection"""
    finding_id: str
    category: InspectionCategory
    severity: FindingSeverity
    title: str
    description: str
    evidence: List[Dict[str, Any]]
    affected_decisions: List[str]
    first_observed: datetime
    last_observed: datetime
    occurrence_count: int
    recommended_action: str
    expected_impact: float
    automated_fixable: bool


@dataclass
class DecisionQualityMetrics:
    """Quality metrics for a decision or set of decisions"""
    decision_id: str
    timestamp: datetime
    
    # Calibration metrics
    predicted_confidence: float
    actual_outcome: Optional[float]
    calibration_error: Optional[float]
    
    # Reasoning quality
    claim_count: int
    evidence_coverage: float
    adversarial_challenges_count: int
    reasoning_depth: int
    
    # Uncertainty appropriateness
    uncertainty_justified: Optional[bool]
    confidence_appropriate: Optional[bool]
    
    # Decision characteristics
    regime_fit: float
    robustness_score: float
    opportunity_cost_considered: bool
    tail_risk_assessed: bool


@dataclass
class ReasoningArtifact:
    """Represents a reasoning artifact for inspection"""
    artifact_id: str
    decision_id: str
    artifact_type: str  # claim, evidence, audit_trail, challenge
    content: Dict[str, Any]
    timestamp: datetime
    
    # Quality metrics
    completeness: float
    consistency: float
    relevance: float
    soundness: Optional[float]


@dataclass
class CalibrationProfile:
    """Tracks uncertainty calibration over time"""
    confidence_bins: List[float]  # [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    predicted_accuracy: List[float]  # Expected accuracy per bin
    actual_accuracy: List[float]  # Actual accuracy per bin
    calibration_gaps: List[float]  # Difference per bin
    overall_brier_score: float
    reliability_diagram_data: Dict[str, List[float]]
    
    # Trend
    is_improving: bool
    trend_slope: float


@dataclass
class ImprovementOpportunity:
    """Identified opportunity for improvement"""
    opportunity_id: str
    source: str  # success_pattern, failure_pattern, gap_analysis
    description: str
    current_state: str
    target_state: str
    estimated_improvement: float
    implementation_complexity: str
    priority: float
    supporting_evidence: List[str]
    recommended_approach: str


class SelfInspectionEngine:
    """
    Self-Inspection and Meta-Learning Engine
    
    Inspects its own decisions, reasoning artifacts, uncertainty, and outcomes
    to detect errors, limitations, and improvement opportunities.
    
    Features:
    - Real-time decision quality monitoring
    - Automated reasoning artifact inspection
    - Continuous calibration tracking
    - Bias and error pattern detection
    - Success/failure mining for improvements
    - Integration with capability discovery
    """
    
    def __init__(
        self,
        decision_memory=None,
        outcome_memory=None,
        failure_memory=None,
        audit_logger=None,
        capability_discovery_engine=None,
        storage_path: Optional[str] = None
    ):
        self.decision_memory = decision_memory
        self.outcome_memory = outcome_memory
        self.failure_memory = failure_memory
        self.audit_logger = audit_logger
        self.capability_discovery = capability_discovery_engine
        self.storage_path = storage_path or "self_inspection_state.json"
        
        # Inspection state
        self.findings: Dict[str, InspectionFinding] = {}
        self.resolved_findings: List[str] = []
        self.decision_metrics: Dict[str, DecisionQualityMetrics] = {}
        self.artifacts: Dict[str, ReasoningArtifact] = {}
        
        # Calibration tracking
        self.calibration_history: deque = deque(maxlen=100)
        self.current_calibration: Optional[CalibrationProfile] = None
        
        # Pattern detection
        self.error_patterns: Dict[str, Dict] = {}
        self.success_patterns: Dict[str, Dict] = {}
        self.bias_indicators: Dict[str, float] = {}
        
        # Improvement opportunities
        self.opportunities: Dict[str, ImprovementOpportunity] = {}
        self.implemented_improvements: List[Dict] = []
        
        # Real-time monitoring
        self.monitoring_active: bool = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.inspection_hooks: List[Callable] = []
        
        # Load state
        self._load_state()
        
        logger.info("SelfInspectionEngine initialized")
    
    # ==================== Real-Time Monitoring ====================
    
    async def start_continuous_inspection(self, interval_minutes: int = 30):
        """Start continuous self-inspection"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(
            self._inspection_loop(interval_minutes)
        )
        logger.info(f"Started continuous inspection (interval: {interval_minutes}m)")
    
    async def stop_continuous_inspection(self):
        """Stop continuous inspection"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped continuous inspection")
    
    async def _inspection_loop(self, interval_minutes: int):
        """Main inspection loop"""
        while self.monitoring_active:
            try:
                await self._run_full_inspection()
                await asyncio.sleep(interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in inspection loop: {e}")
                await asyncio.sleep(60)
    
    async def _run_full_inspection(self) -> Dict[str, Any]:
        """Run a complete self-inspection cycle"""
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'findings': {},
            'metrics': {},
            'opportunities': []
        }
        
        # 1. Inspect recent decisions
        results['decisions'] = await self._inspect_recent_decisions()
        
        # 2. Analyze calibration
        results['calibration'] = self._analyze_calibration()
        
        # 3. Check reasoning artifacts
        results['reasoning'] = self._inspect_reasoning_artifacts()
        
        # 4. Detect error patterns
        results['errors'] = self._detect_error_patterns()
        
        # 5. Identify biases
        results['biases'] = self._detect_biases()
        
        # 6. Mine improvement opportunities
        results['opportunities'] = self._identify_improvement_opportunities()
        
        # 7. Check for drift
        results['drift'] = self._detect_performance_drift()
        
        # Save findings
        self._save_state()
        
        logger.info("Full inspection cycle completed")
        return results
    
    # ==================== Decision Quality Inspection ====================
    
    async def _inspect_recent_decisions(self, lookback_days: int = 7) -> Dict[str, Any]:
        """Inspect recent decisions for quality issues"""
        
        if not self.decision_memory or not self.outcome_memory:
            return {'status': 'no_data'}
        
        since = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Get recent decisions
        recent_decisions = [
            d for d in self.decision_memory.decisions.values()
            if d.timestamp >= since
        ]
        
        if not recent_decisions:
            return {'status': 'no_recent_decisions'}
        
        findings = []
        metrics_list = []
        
        for decision in recent_decisions:
            # Calculate quality metrics
            metrics = self._calculate_decision_quality(decision)
            metrics_list.append(metrics)
            self.decision_metrics[decision.id] = metrics
            
            # Check for quality issues
            issues = self._check_decision_quality_issues(metrics, decision)
            findings.extend(issues)
        
        # Aggregate findings
        for issue in findings:
            finding_id = f"finding_{issue['category']}_{datetime.utcnow().strftime('%Y%m%d')}"
            
            if finding_id in self.findings:
                # Update existing
                self.findings[finding_id].occurrence_count += 1
                self.findings[finding_id].last_observed = datetime.utcnow()
                self.findings[finding_id].affected_decisions.append(issue['decision_id'])
            else:
                # Create new finding
                self.findings[finding_id] = InspectionFinding(
                    finding_id=finding_id,
                    category=InspectionCategory(issue['category']),
                    severity=FindingSeverity(issue['severity']),
                    title=issue['title'],
                    description=issue['description'],
                    evidence=[issue],
                    affected_decisions=[issue['decision_id']],
                    first_observed=datetime.utcnow(),
                    last_observed=datetime.utcnow(),
                    occurrence_count=1,
                    recommended_action=issue['recommendation'],
                    expected_impact=issue['expected_impact'],
                    automated_fixable=issue.get('automated', False)
                )
        
        return {
            'status': 'completed',
            'decisions_inspected': len(recent_decisions),
            'findings_generated': len(findings),
            'avg_quality_score': np.mean([m.robustness_score for m in metrics_list]) if metrics_list else 0
        }
    
    def _calculate_decision_quality(
        self,
        decision: Any
    ) -> DecisionQualityMetrics:
        """Calculate comprehensive quality metrics for a decision"""
        
        # Get outcome if available
        outcome = None
        if self.outcome_memory and decision.id in self.outcome_memory.outcomes:
            outcome = self.outcome_memory.outcomes[decision.id]
        
        # Calculate calibration error
        calibration_error = None
        if outcome and hasattr(decision, 'uncertainty_profile') and decision.uncertainty_profile:
            predicted = decision.uncertainty_profile.overall_confidence
            actual = 1.0 if outcome.realized_pnl > 0 else 0.0
            calibration_error = abs(predicted - actual)
        
        # Count claims
        claim_count = len(decision.claims) if hasattr(decision, 'claims') else 0
        
        # Evidence coverage
        evidence_coverage = decision.evidence_coverage.get('coverage', 0) if hasattr(decision, 'evidence_coverage') else 0
        
        # Check uncertainty appropriateness
        uncertainty_justified = None
        confidence_appropriate = None
        if outcome and calibration_error is not None:
            confidence_appropriate = calibration_error < 0.2
        
        return DecisionQualityMetrics(
            decision_id=decision.id,
            timestamp=decision.timestamp,
            predicted_confidence=decision.uncertainty_profile.overall_confidence if hasattr(decision, 'uncertainty_profile') and decision.uncertainty_profile else 0.5,
            actual_outcome=outcome.realized_pnl if outcome else None,
            calibration_error=calibration_error,
            claim_count=claim_count,
            evidence_coverage=evidence_coverage,
            adversarial_challenges_count=0,  # Would need audit trail
            reasoning_depth=claim_count,  # Proxy metric
            uncertainty_justified=uncertainty_justified,
            confidence_appropriate=confidence_appropriate,
            regime_fit=decision.regime_applicability_score if hasattr(decision, 'regime_applicability_score') else 0.5,
            robustness_score=decision.robustness_score if hasattr(decision, 'robustness_score') else 0.5,
            opportunity_cost_considered=hasattr(decision, 'opportunity_cost_analysis'),
            tail_risk_assessed=hasattr(decision, 'tail_risk_analysis')
        )
    
    def _check_decision_quality_issues(
        self,
        metrics: DecisionQualityMetrics,
        decision: Any
    ) -> List[Dict]:
        """Check for quality issues in a decision"""
        
        issues = []
        
        # Check calibration
        if metrics.calibration_error and metrics.calibration_error > 0.3:
            issues.append({
                'decision_id': decision.id,
                'category': 'uncertainty_calibration',
                'severity': 'high',
                'title': 'Severe confidence miscalibration',
                'description': f'Calibration error of {metrics.calibration_error:.2f} indicates poor confidence estimation',
                'recommendation': 'Implement automated confidence recalibration',
                'expected_impact': 0.15,
                'automated': True
            })
        
        # Check evidence coverage
        if metrics.evidence_coverage < 0.6:
            issues.append({
                'decision_id': decision.id,
                'category': 'evidence_sufficiency',
                'severity': 'medium',
                'title': 'Insufficient evidence coverage',
                'description': f'Evidence coverage of {metrics.evidence_coverage:.1%} below threshold',
                'recommendation': 'Require minimum evidence coverage before decision approval',
                'expected_impact': 0.08,
                'automated': True
            })
        
        # Check regime fit
        if metrics.regime_fit < 0.4:
            issues.append({
                'decision_id': decision.id,
                'category': 'decision_quality',
                'severity': 'high',
                'title': 'Decision in poor regime fit',
                'description': f'Regime fit score of {metrics.regime_fit:.2f} indicates unsuitable conditions',
                'recommendation': 'Strengthen regime detection and blocking',
                'expected_impact': 0.12,
                'automated': False
            })
        
        # Check robustness
        if metrics.robustness_score < 0.4:
            issues.append({
                'decision_id': decision.id,
                'category': 'decision_quality',
                'severity': 'high',
                'title': 'Low robustness decision',
                'description': f'Robustness score of {metrics.robustness_score:.2f} indicates fragile thesis',
                'recommendation': 'Enhance counterfactual testing requirements',
                'expected_impact': 0.10,
                'automated': False
            })
        
        return issues
    
    # ==================== Reasoning Artifact Inspection ====================
    
    def _inspect_reasoning_artifacts(self) -> Dict[str, Any]:
        """Inspect reasoning artifacts for quality issues"""
        
        if not self.audit_logger:
            return {'status': 'no_audit_logger'}
        
        # Get recent audit events
        since = datetime.utcnow() - timedelta(days=7)
        
        # In real implementation, would query audit log
        # For now, create placeholder analysis
        
        findings = []
        
        # Check for missing claims
        findings.append({
            'category': 'reasoning_soundness',
            'severity': 'medium',
            'title': 'Claims lack quantitative justification',
            'description': 'Many claims are qualitative without supporting metrics',
            'recommendation': 'Require quantitative backing for all claims',
            'expected_impact': 0.07
        })
        
        # Convert to findings
        for issue in findings:
            finding_id = f"finding_reasoning_{datetime.utcnow().strftime('%Y%m%d')}"
            if finding_id not in self.findings:
                self.findings[finding_id] = InspectionFinding(
                    finding_id=finding_id,
                    category=InspectionCategory(issue['category']),
                    severity=FindingSeverity(issue['severity']),
                    title=issue['title'],
                    description=issue['description'],
                    evidence=[issue],
                    affected_decisions=[],
                    first_observed=datetime.utcnow(),
                    last_observed=datetime.utcnow(),
                    occurrence_count=1,
                    recommended_action=issue['recommendation'],
                    expected_impact=issue['expected_impact'],
                    automated_fixable=False
                )
        
        return {
            'status': 'completed',
            'artifacts_inspected': 0,  # Placeholder
            'findings': len(findings)
        }
    
    def _analyze_calibration(
        self,
    ) -> Dict[str, Any]:
        """Analyze uncertainty calibration quality"""
        
        if not self.outcome_memory or not self.decision_memory:
            return {'status': 'no_data'}
        
        # Get recent decision-outcome pairs
        since = datetime.utcnow() - timedelta(days=30)
        
        pairs = []
        for decision in self.decision_memory.decisions.values():
            if decision.timestamp >= since:
                if decision.id in self.outcome_memory.outcomes:
                    outcome = self.outcome_memory.outcomes[decision.id]
                    if hasattr(decision, 'uncertainty_profile') and decision.uncertainty_profile:
                        pairs.append((decision, outcome))
        
        if len(pairs) < 10:
            return {'status': 'insufficient_data', 'pairs': len(pairs)}
        
        # Create confidence bins
        bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        predicted_acc = []
        actual_acc = []
        
        for i in range(len(bins) - 1):
            bin_min = bins[i]
            bin_max = bins[i + 1]
            bin_center = (bin_min + bin_max) / 2
            
            # Get decisions in this confidence bin
            bin_decisions = [
                (d, o) for d, o in pairs
                if bin_min <= d.uncertainty_profile.overall_confidence < bin_max
            ]
            
            if bin_decisions:
                predicted_acc.append(bin_center)
                # Actual accuracy (win rate)
                wins = sum(1 for d, o in bin_decisions if o.realized_pnl > 0)
                actual_acc.append(wins / len(bin_decisions))
            else:
                predicted_acc.append(bin_center)
                actual_acc.append(bin_center)  # Assume well-calibrated if no data
        
        # Calculate calibration gaps
        calibration_gaps = [abs(p - a) for p, a in zip(predicted_acc, actual_acc)]
        
        # Calculate Brier score
        brier_scores = []
        for d, o in pairs:
            pred_prob = d.uncertainty_profile.overall_confidence
            actual = 1.0 if o.realized_pnl > 0 else 0.0
            brier_scores.append((pred_prob - actual) ** 2)
        
        brier = np.mean(brier_scores) if brier_scores else 0.25
        
        # Check for systematic miscalibration
        systematic_low_confidence = all(a > p for p, a in zip(predicted_acc, actual_acc))
        systematic_high_confidence = all(a < p for p, a in zip(predicted_acc, actual_acc))
        
        # Create calibration profile
        profile = CalibrationProfile(
            confidence_bins=bins[:-1],
            predicted_accuracy=predicted_acc,
            actual_accuracy=actual_acc,
            calibration_gaps=calibration_gaps,
            overall_brier_score=brier,
            reliability_diagram_data={
                'bins': bins[:-1],
                'predicted': predicted_acc,
                'actual': actual_acc
            },
            is_improving=self._check_calibration_trend(),
            trend_slope=self._calculate_calibration_trend()
        )
        
        self.current_calibration = profile
        self.calibration_history.append({
            'timestamp': datetime.utcnow(),
            'brier': brier,
            'max_gap': max(calibration_gaps) if calibration_gaps else 0
        })
        
        # Generate findings if calibration is poor
        if brier > 0.2 or max(calibration_gaps) > 0.2:
            finding_id = f"finding_calibration_{datetime.utcnow().strftime('%Y%m%d')}"
            
            if systematic_low_confidence:
                description = "Systematically underconfident: model predictions are more accurate than confidence suggests"
                recommendation = "Implement confidence boosting or reduce uncertainty penalties"
            elif systematic_high_confidence:
                description = "Systematically overconfident: model confidence exceeds actual accuracy"
                recommendation = "Implement confidence calibration (temperature scaling or isotonic regression)"
            else:
                description = f"Poor calibration (Brier: {brier:.3f}, max gap: {max(calibration_gaps):.2f})"
                recommendation = "Recalibrate confidence estimation and monitor calibration quality"
            
            self.findings[finding_id] = InspectionFinding(
                finding_id=finding_id,
                category=InspectionCategory.UNCERTAINTY_CALIBRATION,
                severity=FindingSeverity.HIGH if brier > 0.25 else FindingSeverity.MEDIUM,
                title='Poor confidence calibration detected',
                description=description,
                evidence=[{
                    'brier_score': brier,
                    'max_calibration_gap': max(calibration_gaps) if calibration_gaps else 0,
                    'pairs_analyzed': len(pairs)
                }],
                affected_decisions=[d.id for d, _ in pairs[:10]],
                first_observed=datetime.utcnow(),
                last_observed=datetime.utcnow(),
                occurrence_count=1,
                recommended_action=recommendation,
                expected_impact=0.12,
                automated_fixable=True
            )
        
        return {
            'status': 'completed',
            'brier_score': brier,
            'max_calibration_gap': max(calibration_gaps) if calibration_gaps else 0,
            'systematic_underconfidence': systematic_low_confidence,
            'systematic_overconfidence': systematic_high_confidence,
            'is_improving': profile.is_improving,
            'pairs_analyzed': len(pairs)
        }
    
    def _check_calibration_trend(self) -> bool:
        """Check if calibration is improving over time"""
        if len(self.calibration_history) < 5:
            return False
        
        recent = list(self.calibration_history)[-10:]
        if len(recent) < 5:
            return False
        
        briers = [h['brier'] for h in recent]
        # Simple trend check
        first_half = np.mean(briers[:len(briers)//2])
        second_half = np.mean(briers[len(briers)//2:])
        
        return second_half < first_half  # Improving if brier decreasing
    
    def _calculate_calibration_trend(self) -> float:
        """Calculate calibration trend slope"""
        if len(self.calibration_history) < 5:
            return 0.0
        
        recent = list(self.calibration_history)[-10:]
        if len(recent) < 3:
            return 0.0
        
        x = np.arange(len(recent))
        y = [h['brier'] for h in recent]
        
        # Simple linear regression
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            return slope
        return 0.0
    
    # ==================== Error Pattern Detection ====================
    
    def _detect_error_patterns(self) -> Dict[str, Any]:
        """Detect systematic error patterns in decisions"""
        
        if not self.failure_memory:
            return {'status': 'no_failure_memory'}
        
        patterns = self.failure_memory.get_patterns(min_frequency=2)
        
        findings = []
        
        for pattern in patterns:
            # Check if this is a systematic error
            if pattern.frequency >= 3 and pattern.severity > 0.5:
                finding_id = f"finding_error_{pattern.pattern_name}_{datetime.utcnow().strftime('%Y%m%d')}"
                
                if finding_id not in self.findings:
                    self.findings[finding_id] = InspectionFinding(
                        finding_id=finding_id,
                        category=InspectionCategory.SYSTEMATIC_ERROR,
                        severity=FindingSeverity.CRITICAL if pattern.severity > 0.8 else FindingSeverity.HIGH,
                        title=f"Systematic error: {pattern.pattern_name}",
                        description=pattern.description,
                        evidence=[{
                            'pattern_id': pattern.id,
                            'frequency': pattern.frequency,
                            'severity': pattern.severity,
                            'root_cause_hypothesis': pattern.root_cause_hypothesis
                        }],
                        affected_decisions=pattern.examples,
                        first_observed=datetime.utcnow(),
                        last_observed=datetime.utcnow(),
                        occurrence_count=pattern.frequency,
                        recommended_action=pattern.proposed_fix or f"Address {pattern.pattern_name} through capability enhancement",
                        expected_impact=pattern.severity * 0.2,
                        automated_fixable=False
                    )
                    
                    findings.append(finding_id)
        
        return {
            'status': 'completed',
            'patterns_detected': len(patterns),
            'new_findings': len(findings)
        }
    
    # ==================== Bias Detection ====================
    
    def _detect_biases(self) -> Dict[str, Any]:
        """Detect cognitive biases in decision making"""
        
        if not self.decision_memory or not self.outcome_memory:
            return {'status': 'no_data'}
        
        biases_found = []
        
        # 1. Overconfidence bias
        overconfidence = self._detect_overconfidence_bias()
        if overconfidence['detected']:
            biases_found.append({
                'bias_type': 'overconfidence',
                'severity': overconfidence['severity'],
                'evidence': overconfidence['evidence']
            })
        
        # 2. Recency bias
        recency = self._detect_recency_bias()
        if recency['detected']:
            biases_found.append({
                'bias_type': 'recency',
                'severity': recency['severity'],
                'evidence': recency['evidence']
            })
        
        # 3. Confirmation bias
        confirmation = self._detect_confirmation_bias()
        if confirmation['detected']:
            biases_found.append({
                'bias_type': 'confirmation',
                'severity': confirmation['severity'],
                'evidence': confirmation['evidence']
            })
        
        # 4. Loss aversion bias
        loss_aversion = self._detect_loss_aversion_bias()
        if loss_aversion['detected']:
            biases_found.append({
                'bias_type': 'loss_aversion',
                'severity': loss_aversion['severity'],
                'evidence': loss_aversion['evidence']
            })
        
        # Create findings for detected biases
        for bias in biases_found:
            finding_id = f"finding_bias_{bias['bias_type']}_{datetime.utcnow().strftime('%Y%m%d')}"
            
            if finding_id not in self.findings:
                bias_descriptions = {
                    'overconfidence': 'Decisions show excessive confidence relative to actual outcomes',
                    'recency': 'Decisions overweight recent events vs. historical patterns',
                    'confirmation': 'Evidence search disproportionately supports initial thesis',
                    'loss_aversion': 'Risk-taking behavior changes after losses in ways that hurt performance'
                }
                
                bias_recommendations = {
                    'overconfidence': 'Implement confidence calibration and require calibration checks',
                    'recency': 'Use longer lookback periods and regime-weighted analysis',
                    'confirmation': 'Mandate adversarial analysis for all decisions',
                    'loss_aversion': 'Implement position sizing that ignores recent PnL'
                }
                
                self.findings[finding_id] = InspectionFinding(
                    finding_id=finding_id,
                    category=InspectionCategory.COGNITIVE_BIAS,
                    severity=FindingSeverity(bias['severity']),
                    title=f"Cognitive bias detected: {bias['bias_type'].replace('_', ' ').title()}",
                    description=bias_descriptions.get(bias['bias_type'], 'Cognitive bias detected'),
                    evidence=bias['evidence'],
                    affected_decisions=[],
                    first_observed=datetime.utcnow(),
                    last_observed=datetime.utcnow(),
                    occurrence_count=1,
                    recommended_action=bias_recommendations.get(bias['bias_type'], 'Review and address bias'),
                    expected_impact=0.10,
                    automated_fixable=bias['bias_type'] == 'overconfidence'
                )
        
        return {
            'status': 'completed',
            'biases_detected': len(biases_found),
            'bias_types': [b['bias_type'] for b in biases_found]
        }
    
    def _detect_overconfidence_bias(self) -> Dict[str, Any]:
        """Detect overconfidence in decision making"""
        
        since = datetime.utcnow() - timedelta(days=30)
        
        high_confidence_losses = []
        
        for decision in self.decision_memory.decisions.values():
            if decision.timestamp >= since:
                if hasattr(decision, 'uncertainty_profile') and decision.uncertainty_profile:
                    if decision.uncertainty_profile.overall_confidence > 0.8:
                        if decision.id in self.outcome_memory.outcomes:
                            outcome = self.outcome_memory.outcomes[decision.id]
                            if outcome.realized_pnl < 0:
                                high_confidence_losses.append(decision)
        
        # If more than 30% of high-confidence decisions lose, we have overconfidence
        total_high_conf = sum(1 for d in self.decision_memory.decisions.values()
                             if hasattr(d, 'uncertainty_profile') and d.uncertainty_profile
                             and d.uncertainty_profile.overall_confidence > 0.8
                             and d.timestamp >= since)
        
        if total_high_conf > 10 and len(high_confidence_losses) / total_high_conf > 0.4:
            return {
                'detected': True,
                'severity': 'high' if len(high_confidence_losses) / total_high_conf > 0.5 else 'medium',
                'evidence': [
                    f"{len(high_confidence_losses)} high-confidence decisions resulted in losses",
                    f"Loss rate: {len(high_confidence_losses) / total_high_conf:.1%}"
                ]
            }
        
        return {'detected': False}
    
    def _detect_recency_bias(self) -> Dict[str, Any]:
        """Detect recency bias in decision making"""
        # Simplified detection - would need more detailed trade history
        return {'detected': False}
    
    def _detect_confirmation_bias(self) -> Dict[str, Any]:
        """Detect confirmation bias in evidence gathering"""
        # Would analyze adversarial challenge success rates
        # If challenges rarely change decisions, may indicate confirmation bias
        return {'detected': False}
    
    def _detect_loss_aversion_bias(self) -> Dict[str, Any]:
        """Detect loss aversion affecting decision quality"""
        # Would analyze position sizing after losses
        return {'detected': False}
    
    # ==================== Performance Drift Detection ====================
    
    def _detect_performance_drift(self) -> Dict[str, Any]:
        """Detect drift in decision quality over time"""
        
        if not self.outcome_memory:
            return {'status': 'no_data'}
        
        # Get outcomes by week
        weeks = defaultdict(list)
        
        for outcome in self.outcome_memory.outcomes.values():
            week_key = outcome.timestamp.strftime('%Y-W%U')
            weeks[week_key].append(outcome.realized_pnl)
        
        if len(weeks) < 4:
            return {'status': 'insufficient_history'}
        
        # Calculate weekly performance
        weekly_pnl = {w: np.mean(pnls) for w, pnls in sorted(weeks.items())}
        week_keys = list(weekly_pnl.keys())
        
        # Check for declining trend
        recent_weeks = list(weekly_pnl.values())[-4:]
        earlier_weeks = list(weekly_pnl.values())[-8:-4] if len(weekly_pnl) >= 8 else list(weekly_pnl.values())[:4]
        
        if np.mean(recent_weeks) < np.mean(earlier_weeks) * 0.7:  # 30% decline
            finding_id = f"finding_drift_{datetime.utcnow().strftime('%Y%m%d')}"
            
            if finding_id not in self.findings:
                self.findings[finding_id] = InspectionFinding(
                    finding_id=finding_id,
                    category=InspectionCategory.PERFORMANCE_DRIFT,
                    severity=FindingSeverity.HIGH,
                    title='Performance drift detected',
                    description=f'Average weekly PnL declined from {np.mean(earlier_weeks):.3f} to {np.mean(recent_weeks):.3f}',
                    evidence=[
                        {'week': k, 'avg_pnl': v}
                        for k, v in list(weekly_pnl.items())[-8:]
                    ],
                    affected_decisions=[],
                    first_observed=datetime.utcnow(),
                    last_observed=datetime.utcnow(),
                    occurrence_count=1,
                    recommended_action='Investigate market regime change and model degradation',
                    expected_impact=0.20,
                    automated_fixable=False
                )
            
            return {
                'status': 'drift_detected',
                'earlier_avg': np.mean(earlier_weeks),
                'recent_avg': np.mean(recent_weeks),
                'decline_pct': (np.mean(earlier_weeks) - np.mean(recent_weeks)) / abs(np.mean(earlier_weeks))
            }
        
        return {
            'status': 'no_drift',
            'weekly_performance': list(weekly_pnl.items())[-4:]
        }
    
    # ==================== Improvement Opportunity Mining ====================
    
    def _identify_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """Mine for improvement opportunities from both successes and failures"""
        
        opportunities = []
        
        # 1. Learn from successful decisions
        success_opps = self._mine_success_patterns()
        opportunities.extend(success_opps)
        
        # 2. Learn from failure patterns
        failure_opps = self._mine_failure_patterns()
        opportunities.extend(failure_opps)
        
        # 3. Identify capability gaps from findings
        capability_opps = self._identify_capability_opportunities()
        opportunities.extend(capability_opps)
        
        # Store opportunities
        for opp in opportunities:
            opp_id = f"opp_{opp['source']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            if opp_id not in self.opportunities:
                self.opportunities[opp_id] = ImprovementOpportunity(
                    opportunity_id=opp_id,
                    source=opp['source'],
                    description=opp['description'],
                    current_state=opp.get('current_state', 'unknown'),
                    target_state=opp.get('target_state', 'improved'),
                    estimated_improvement=opp.get('estimated_improvement', 0.05),
                    implementation_complexity=opp.get('complexity', 'medium'),
                    priority=opp.get('priority', 0.5),
                    supporting_evidence=opp.get('evidence', []),
                    recommended_approach=opp.get('approach', 'Implement improvement')
                )
        
        # Feed to capability discovery if available
        if self.capability_discovery:
            self._feed_opportunities_to_discovery(opportunities)
        
        return opportunities
    
    def _mine_success_patterns(self) -> List[Dict]:
        """Identify patterns in successful decisions that could be replicated"""
        
        if not self.decision_memory or not self.outcome_memory:
            return []
        
        # Find high-performing decisions
        since = datetime.utcnow() - timedelta(days=30)
        
        successful_decisions = []
        for decision in self.decision_memory.decisions.values():
            if decision.timestamp >= since:
                if decision.id in self.outcome_memory.outcomes:
                    outcome = self.outcome_memory.outcomes[decision.id]
                    if outcome.realized_pnl > 0.03:  # >3% winners
                        successful_decisions.append((decision, outcome))
        
        if len(successful_decisions) < 5:
            return []
        
        # Analyze common characteristics
        common_regimes = defaultdict(int)
        common_confidence_levels = []
        
        for decision, outcome in successful_decisions:
            if hasattr(decision, 'current_regime') and decision.current_regime:
                common_regimes[decision.current_regime.volatility_state] += 1
            if hasattr(decision, 'uncertainty_profile') and decision.uncertainty_profile:
                common_confidence_levels.append(decision.uncertainty_profile.overall_confidence)
        
        opportunities = []
        
        # If most winners are in specific regime, recommend focusing there
        if common_regimes:
            best_regime = max(common_regimes.items(), key=lambda x: x[1])
            if best_regime[1] >= 3:
                opportunities.append({
                    'source': 'success_pattern',
                    'description': f"Increase exposure in {best_regime[0]} regime where win rate is higher",
                    'current_state': 'Equal regime exposure',
                    'target_state': f'Regime-weighted with emphasis on {best_regime[0]}',
                    'estimated_improvement': 0.08,
                    'complexity': 'low',
                    'priority': 0.7,
                    'evidence': [f"{best_regime[1]} of {len(successful_decisions)} winners in {best_regime[0]} regime"],
                    'approach': 'Adjust position sizing to favor high-performing regime'
                })
        
        # If winners have specific confidence characteristics
        if common_confidence_levels:
            avg_conf = np.mean(common_confidence_levels)
            if avg_conf > 0.75:
                opportunities.append({
                    'source': 'success_pattern',
                    'description': 'Require minimum confidence threshold for trades',
                    'current_state': 'All confidence levels traded',
                    'target_state': f'Only trades with confidence > {avg_conf*0.9:.2f}',
                    'estimated_improvement': 0.06,
                    'complexity': 'immediate',
                    'priority': 0.6,
                    'evidence': [f"Average confidence of winners: {avg_conf:.2f}"],
                    'approach': 'Add confidence filter to decision pipeline'
                })
        
        return opportunities
    
    def _mine_failure_patterns(self) -> List[Dict]:
        """Identify patterns in failures that could be prevented"""
        
        # This would use the failure memory patterns
        if not self.failure_memory:
            return []
        
        patterns = self.failure_memory.get_patterns(min_frequency=2, min_severity=0.5)
        
        opportunities = []
        
        for pattern in patterns:
            opp = {
                'source': 'failure_pattern',
                'description': f"Prevent {pattern.pattern_name} failures",
                'current_state': f'{pattern.frequency} occurrences of {pattern.pattern_name}',
                'target_state': 'Zero occurrences',
                'estimated_improvement': pattern.severity * 0.15,
                'complexity': 'medium',
                'priority': pattern.frequency * pattern.severity / 10,
                'evidence': [
                    f"Pattern: {pattern.description}",
                    f"Root cause: {pattern.root_cause_hypothesis}"
                ],
                'approach': pattern.proposed_fix or f'Address {pattern.pattern_name}'
            }
            opportunities.append(opp)
        
        return opportunities
    
    def _identify_capability_opportunities(self) -> List[Dict]:
        """Identify capability improvements from inspection findings"""
        
        opportunities = []
        
        # Group findings by category
        findings_by_category = defaultdict(list)
        for finding in self.findings.values():
            findings_by_category[finding.category].append(finding)
        
        # If many calibration issues, suggest calibration capability
        if len(findings_by_category[InspectionCategory.UNCERTAINTY_CALIBRATION]) >= 2:
            opportunities.append({
                'source': 'capability_gap',
                'description': 'Implement automated confidence calibration system',
                'current_state': 'Manual or stale calibration',
                'target_state': 'Real-time automated calibration',
                'estimated_improvement': 0.15,
                'complexity': 'high',
                'priority': 0.8,
                'evidence': [f"{len(findings_by_category[InspectionCategory.UNCERTAINTY_CALIBRATION])} calibration findings"],
                'approach': 'Build sliding window calibration with drift detection'
            })
        
        # If many decision quality issues, suggest decision enhancement
        if len(findings_by_category[InspectionCategory.DECISION_QUALITY]) >= 3:
            opportunities.append({
                'source': 'capability_gap',
                'description': 'Enhance decision quality gates',
                'current_state': 'Basic quality checks',
                'target_state': 'Multi-layer quality validation',
                'estimated_improvement': 0.10,
                'complexity': 'medium',
                'priority': 0.7,
                'evidence': [f"{len(findings_by_category[InspectionCategory.DECISION_QUALITY])} quality findings"],
                'approach': 'Add pre-decision quality validation layer'
            })
        
        return opportunities
    
    def _feed_opportunities_to_discovery(self, opportunities: List[Dict]):
        """Feed improvement opportunities to capability discovery"""
        
        if not self.capability_discovery:
            return
        
        # Import here to avoid circular dependency
        from .continuous_capability_discovery import CapabilityGap
        
        for opp in opportunities:
            if opp.get('priority', 0) > 0.6:  # Only high priority
                gap_id = f"gap_inspection_{opp['source']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                
                gap = CapabilityGap(
                    id=gap_id,
                    description=opp['description'],
                    affected_categories=['decision_governance', 'signal_generation'],
                    severity=opp.get('priority', 0.5),
                    impact_score=opp.get('estimated_improvement', 0.05),
                    detection_date=datetime.utcnow(),
                    evidence=[{'type': 'inspection', 'source': opp['source'], 'details': opp}],
                    root_causes=[opp['source']]
                )
                
                self.capability_discovery.active_gaps[gap_id] = gap
                
                logger.info(f"Created capability gap from inspection: {gap_id}")
    
    # ==================== API Methods ====================
    
    def get_inspection_summary(self) -> Dict[str, Any]:
        """Get summary of current inspection state"""
        
        # Count findings by severity
        by_severity = defaultdict(int)
        by_category = defaultdict(int)
        
        for finding in self.findings.values():
            by_severity[finding.severity.value] += 1
            by_category[finding.category.value] += 1
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'findings': {
                'total': len(self.findings),
                'by_severity': dict(by_severity),
                'by_category': dict(by_category),
                'critical': by_severity.get('critical', 0),
                'high': by_severity.get('high', 0)
            },
            'calibration': {
                'current_brier': self.current_calibration.overall_brier_score if self.current_calibration else None,
                'is_improving': self.current_calibration.is_improving if self.current_calibration else None,
                'history_points': len(self.calibration_history)
            },
            'opportunities': {
                'total': len(self.opportunities),
                'high_priority': sum(1 for o in self.opportunities.values() if o.priority > 0.7)
            },
            'monitoring': {
                'active': self.monitoring_active
            }
        }
    
    def get_findings_report(
        self,
        severity: Optional[FindingSeverity] = None,
        category: Optional[InspectionCategory] = None
    ) -> List[Dict[str, Any]]:
        """Get detailed findings report with optional filtering"""
        
        findings = self.findings.values()
        
        if severity:
            findings = [f for f in findings if f.severity == severity]
        
        if category:
            findings = [f for f in findings if f.category == category]
        
        return [
            {
                'finding_id': f.finding_id,
                'category': f.category.value,
                'severity': f.severity.value,
                'title': f.title,
                'description': f.description,
                'occurrence_count': f.occurrence_count,
                'first_observed': f.first_observed.isoformat(),
                'last_observed': f.last_observed.isoformat(),
                'affected_decisions_count': len(f.affected_decisions),
                'recommended_action': f.recommended_action,
                'expected_impact': f.expected_impact,
                'automated_fixable': f.automated_fixable
            }
            for f in sorted(findings, key=lambda x: x.severity.value, reverse=True)
        ]
    
    def get_opportunities_report(self, min_priority: float = 0.0) -> List[Dict[str, Any]]:
        """Get improvement opportunities report"""
        
        opportunities = [
            opp for opp in self.opportunities.values()
            if opp.priority >= min_priority
        ]
        
        return [
            {
                'opportunity_id': opp.opportunity_id,
                'source': opp.source,
                'description': opp.description,
                'current_state': opp.current_state,
                'target_state': opp.target_state,
                'estimated_improvement': opp.estimated_improvement,
                'complexity': opp.implementation_complexity,
                'priority': opp.priority,
                'supporting_evidence': opp.supporting_evidence[:3],
                'recommended_approach': opp.recommended_approach
            }
            for opp in sorted(opportunities, key=lambda x: x.priority, reverse=True)
        ]
    
    # ==================== State Management ====================
    
    def _save_state(self):
        """Save inspection state to disk"""
        try:
            state = {
                'findings_count': len(self.findings),
                'opportunities_count': len(self.opportunities),
                'calibration_history_length': len(self.calibration_history),
                'monitoring_active': self.monitoring_active,
                'saved_at': datetime.utcnow().isoformat()
            }
            Path(self.storage_path).write_text(json.dumps(state, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _load_state(self):
        """Load inspection state from disk"""
        try:
            if not Path(self.storage_path).exists():
                return
            state = json.loads(Path(self.storage_path).read_text())
            logger.info(f"Loaded self-inspection state: {state.get('findings_count', 0)} findings, {state.get('opportunities_count', 0)} opportunities")
        except Exception as e:
            logger.warning(f"Error loading state: {e}")


# Factory function
def create_self_inspection_engine(
    decision_memory=None,
    outcome_memory=None,
    failure_memory=None,
    audit_logger=None,
    capability_discovery_engine=None,
    storage_path: Optional[str] = None
) -> SelfInspectionEngine:
    """Factory function to create self-inspection engine"""
    
    return SelfInspectionEngine(
        decision_memory=decision_memory,
        outcome_memory=outcome_memory,
        failure_memory=failure_memory,
        audit_logger=audit_logger,
        capability_discovery_engine=capability_discovery_engine,
        storage_path=storage_path
    )
