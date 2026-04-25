"""
Meta-Learning Judge

Evaluates and learns from governance decisions to improve the system itself.
Operates at three levels:
- Level 1: Prompt optimizer
- Level 2: Workflow optimizer  
- Level 3: System optimizer
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """Levels of meta-learning optimization"""
    PROMPT = "prompt"  # Level 1
    WORKFLOW = "workflow"  # Level 2
    SYSTEM = "system"  # Level 3


@dataclass
class PerformancePattern:
    """Pattern detected in governance performance"""
    pattern_type: str
    description: str
    affected_components: List[str]
    frequency: int
    severity: float
    suggested_optimization: str
    expected_improvement: float


@dataclass
class OptimizationProposal:
    """Proposal for system optimization"""
    id: str
    level: OptimizationLevel
    target_component: str
    current_state: Dict[str, Any]
    proposed_change: Dict[str, Any]
    rationale: str
    expected_metrics: Dict[str, float]
    validation_results: Optional[Dict] = None
    approved: bool = False


class MetaLearningJudge:
    """
    Meta-learning system that improves governance performance.
    
    Operates at three levels:
    1. Prompt: Improves instructions and examples
    2. Workflow: Changes how agents plan, delegate, verify
    3. System: Redesigns agent topology, adds critics/verifiers
    """
    
    def __init__(self):
        self.performance_history: List[Dict] = []
        self.detected_patterns: List[PerformancePattern] = []
        self.optimization_proposals: List[OptimizationProposal] = []
        self.applied_optimizations: List[OptimizationProposal] = []
        
        # Component performance tracking
        self.component_metrics: Dict[str, List[Dict]] = defaultdict(list)
        
    def analyze_governance_performance(
        self,
        decisions: List[Dict],
        outcomes: List[Dict],
        time_window: Optional[timedelta] = None
    ) -> List[PerformancePattern]:
        """
        Analyze governance performance to detect patterns.
        
        Returns:
            List of detected performance patterns
        """
        if time_window is None:
            time_window = timedelta(days=30)
            
        cutoff = datetime.utcnow() - time_window
        
        # Filter recent data
        recent_decisions = [
            d for d in decisions
            if d.get('timestamp', datetime.utcnow()) > cutoff
        ]
        
        recent_outcomes = [
            o for o in outcomes
            if o.get('timestamp', datetime.utcnow()) > cutoff
        ]
        
        patterns = []
        
        # Pattern 1: Overconfidence detection
        overconfidence = self._detect_overconfidence(recent_decisions, recent_outcomes)
        if overconfidence:
            patterns.append(overconfidence)
            
        # Pattern 2: Calibration drift
        calibration_drift = self._detect_calibration_drift(recent_outcomes)
        if calibration_drift:
            patterns.append(calibration_drift)
            
        # Pattern 3: Regime-specific failures
        regime_failures = self._detect_regime_failures(recent_outcomes)
        if regime_failures:
            patterns.append(regime_failures)
            
        # Pattern 4: Component-specific degradation
        component_issues = self._detect_component_issues(recent_decisions, recent_outcomes)
        patterns.extend(component_issues)
        
        # Pattern 5: False positive/negative patterns
        error_patterns = self._detect_error_patterns(recent_decisions, recent_outcomes)
        patterns.extend(error_patterns)
        
        self.detected_patterns.extend(patterns)
        
        return patterns
    
    def _detect_overconfidence(
        self,
        decisions: List[Dict],
        outcomes: List[Dict]
    ) -> Optional[PerformancePattern]:
        """Detect systematic overconfidence in predictions"""
        
        # Match decisions to outcomes
        matched = self._match_decisions_outcomes(decisions, outcomes)
        
        high_conf_wrong = [
            (d, o) for d, o in matched
            if d.get('confidence', 0) > 0.8 and o.get('pnl', 0) < 0
        ]
        
        if len(high_conf_wrong) > len(matched) * 0.3:  # >30% high-conf wrong
            return PerformancePattern(
                pattern_type="overconfidence",
                description=f"{len(high_conf_wrong)} high-confidence predictions were wrong",
                affected_components=["uncertainty_layer", "calibration"],
                frequency=len(high_conf_wrong),
                severity=0.7,
                suggested_optimization="Implement temperature scaling for confidence calibration",
                expected_improvement=0.15
            )
            
        return None
    
    def _detect_calibration_drift(
        self,
        outcomes: List[Dict]
    ) -> Optional[PerformancePattern]:
        """Detect calibration quality degradation"""
        
        if len(outcomes) < 10:
            return None
            
        # Calculate recent Brier score
        recent_brier = sum(
            o.get('calibration_error', 0) ** 2 for o in outcomes[-20:]
        ) / min(len(outcomes), 20)
        
        if recent_brier > 0.25:  # Worse than random
            return PerformancePattern(
                pattern_type="calibration_drift",
                description=f"Calibration degraded: Brier score {recent_brier:.3f}",
                affected_components=["uncertainty_layer"],
                frequency=len(outcomes),
                severity=0.8,
                suggested_optimization="Recalibrate using recent outcome data",
                expected_improvement=0.20
            )
            
        return None
    
    def _detect_regime_failures(
        self,
        outcomes: List[Dict]
    ) -> Optional[PerformancePattern]:
        """Detect failures in specific market regimes"""
        
        regime_losses = defaultdict(list)
        
        for o in outcomes:
            regime = o.get('regime', 'unknown')
            if o.get('pnl', 0) < 0:
                regime_losses[regime].append(o)
                
        # Find regime with excessive losses
        for regime, losses in regime_losses.items():
            total_in_regime = sum(
                1 for o in outcomes if o.get('regime') == regime
            )
            if total_in_regime > 5 and len(losses) / total_in_regime > 0.6:
                return PerformancePattern(
                    pattern_type="regime_failure",
                    description=f"Excessive losses in {regime} regime: {len(losses)}/{total_in_regime}",
                    affected_components=["regime_engine"],
                    frequency=len(losses),
                    severity=0.75,
                    suggested_optimization=f"Add regime-specific constraints for {regime}",
                    expected_improvement=0.10
                )
                
        return None
    
    def _detect_component_issues(
        self,
        decisions: List[Dict],
        outcomes: List[Dict]
    ) -> List[PerformancePattern]:
        """Detect issues in specific governance components"""
        
        patterns = []
        
        # Check evidence auditor performance
        low_evidence_approved = [
            d for d in decisions
            if d.get('decision') in ['approve', 'resize']
            and d.get('evidence_coverage', 1.0) < 0.5
        ]
        
        if len(low_evidence_approved) > len(decisions) * 0.2:
            patterns.append(PerformancePattern(
                pattern_type="evidence_auditor_weakness",
                description=f"{len(low_evidence_approved)} low-evidence trades approved",
                affected_components=["evidence_auditor", "layer2"],
                frequency=len(low_evidence_approved),
                severity=0.6,
                suggested_optimization="Raise minimum evidence coverage threshold",
                expected_improvement=0.12
            ))
            
        # Check adversarial coverage
        no_challenges = [
            d for d in decisions
            if d.get('adversarial_challenges_count', 0) == 0
        ]
        
        if len(no_challenges) > len(decisions) * 0.1:
            patterns.append(PerformancePattern(
                pattern_type="adversarial_gaps",
                description=f"{len(no_challenges)} decisions without adversarial challenges",
                affected_components=["adversarial_analyst", "layer3"],
                frequency=len(no_challenges),
                severity=0.5,
                suggested_optimization="Ensure adversarial challenges on all significant decisions",
                expected_improvement=0.08
            ))
            
        return patterns
    
    def _detect_error_patterns(
        self,
        decisions: List[Dict],
        outcomes: List[Dict]
    ) -> List[PerformancePattern]:
        """Detect false positive and false negative patterns"""
        
        patterns = []
        
        matched = self._match_decisions_outcomes(decisions, outcomes)
        
        # False negatives (rejected but would have won)
        false_negatives = [
            (d, o) for d, o in matched
            if d.get('decision') == 'reject' and o.get('pnl', 0) > 0
        ]
        
        if len(false_negatives) > 5:
            patterns.append(PerformancePattern(
                pattern_type="false_negatives",
                description=f"{len(false_negatives)} profitable trades rejected",
                affected_components=["governance_arbiter", "layer7"],
                frequency=len(false_negatives),
                severity=0.4,
                suggested_optimization="Tune rejection thresholds for better recall",
                expected_improvement=0.05
            ))
            
        return patterns
    
    def generate_optimization_proposals(
        self,
        patterns: List[PerformancePattern]
    ) -> List[OptimizationProposal]:
        """Generate optimization proposals from detected patterns"""
        
        proposals = []
        
        for pattern in patterns:
            # Level 1: Prompt optimizations
            if pattern.pattern_type in ['overconfidence', 'calibration_drift']:
                proposal = self._create_prompt_optimization(pattern)
                if proposal:
                    proposals.append(proposal)
                    
            # Level 2: Workflow optimizations
            if pattern.pattern_type in ['evidence_auditor_weakness', 'adversarial_gaps']:
                proposal = self._create_workflow_optimization(pattern)
                if proposal:
                    proposals.append(proposal)
                    
            # Level 3: System optimizations
            if pattern.pattern_type in ['regime_failure', 'false_negatives']:
                proposal = self._create_system_optimization(pattern)
                if proposal:
                    proposals.append(proposal)
                    
        self.optimization_proposals.extend(proposals)
        
        return proposals
    
    def _create_prompt_optimization(
        self,
        pattern: PerformancePattern
    ) -> Optional[OptimizationProposal]:
        """Create Level 1 (prompt) optimization"""
        
        if pattern.pattern_type == 'overconfidence':
            return OptimizationProposal(
                id=f"opt_prompt_{len(self.optimization_proposals)}",
                level=OptimizationLevel.PROMPT,
                target_component="uncertainty_layer",
                current_state={'calibration_method': 'default'},
                proposed_change={
                    'calibration_method': 'temperature_scaling',
                    'temperature': 1.5  # Soften confidence
                },
                rationale="Reduce overconfidence by temperature scaling",
                expected_metrics={'calibration_error_reduction': 0.15}
            )
        elif pattern.pattern_type == 'calibration_drift':
            return OptimizationProposal(
                id=f"opt_prompt_{len(self.optimization_proposals)}",
                level=OptimizationLevel.PROMPT,
                target_component="uncertainty_layer",
                current_state={'recalibration_frequency': 'monthly'},
                proposed_change={'recalibration_frequency': 'weekly'},
                rationale="More frequent recalibration to track drift",
                expected_metrics={'calibration_stability': 0.20}
            )
            
        return None
    
    def _create_workflow_optimization(
        self,
        pattern: PerformancePattern
    ) -> Optional[OptimizationProposal]:
        """Create Level 2 (workflow) optimization"""
        
        if pattern.pattern_type == 'evidence_auditor_weakness':
            return OptimizationProposal(
                id=f"opt_workflow_{len(self.optimization_proposals)}",
                level=OptimizationLevel.WORKFLOW,
                target_component="evidence_auditor",
                current_state={'min_coverage': 0.5, 'auto_approve': True},
                proposed_change={
                    'min_coverage': 0.7,
                    'auto_approve': False,
                    'require_human_review': True
                },
                rationale="Require stronger evidence and human review for marginal cases",
                expected_metrics={'false_positive_reduction': 0.25}
            )
        elif pattern.pattern_type == 'adversarial_gaps':
            return OptimizationProposal(
                id=f"opt_workflow_{len(self.optimization_proposals)}",
                level=OptimizationLevel.WORKFLOW,
                target_component="governance_pipeline",
                current_state={'adversarial_depth': 3},
                proposed_change={
                    'adversarial_depth': 5,
                    'require_challenges': True,
                    'challenge_coverage_threshold': 0.8
                },
                rationale="Increase adversarial depth and enforce challenge coverage",
                expected_metrics={'thesis_robustness': 0.15}
            )
            
        return None
    
    def _create_system_optimization(
        self,
        pattern: PerformancePattern
    ) -> Optional[OptimizationProposal]:
        """Create Level 3 (system) optimization"""
        
        if pattern.pattern_type == 'regime_failure':
            return OptimizationProposal(
                id=f"opt_system_{len(self.optimization_proposals)}",
                level=OptimizationLevel.SYSTEM,
                target_component="agent_topology",
                current_state={'regime_agents': 1, 'specialist_agents': 0},
                proposed_change={
                    'regime_agents': 3,  # Split into specialists
                    'specialist_agents': 2,  # Add low-vol and high-vol specialists
                    'add_verifier': True
                },
                rationale="Split regime detection into specialists with verifier",
                expected_metrics={'regime_accuracy': 0.20}
            )
        elif pattern.pattern_type == 'false_negatives':
            return OptimizationProposal(
                id=f"opt_system_{len(self.optimization_proposals)}",
                level=OptimizationLevel.SYSTEM,
                target_component="governance_arbiter",
                current_state={'decision_modes': 1},
                proposed_change={
                    'decision_modes': 2,  # Conservative and aggressive
                    'mode_router': 'dynamic',
                    'add_critic_agent': True
                },
                rationale="Add dual-mode arbiter with critic for borderline cases",
                expected_metrics={'recall_improvement': 0.10}
            )
            
        return None
    
    def evaluate_proposal(
        self,
        proposal: OptimizationProposal,
        validation_data: List[Dict]
    ) -> Dict[str, Any]:
        """Validate an optimization proposal on held-out data"""
        
        # Simulated validation
        # In practice, this would run actual A/B tests
        
        validation_result = {
            'proposal_id': proposal.id,
            'validation_samples': len(validation_data),
            'improvement_achieved': proposal.expected_metrics,
            'statistical_significance': 0.03,  # Simulated p-value
            'recommendation': 'APPROVE' if proposal.expected_metrics else 'REJECT'
        }
        
        proposal.validation_results = validation_result
        
        return validation_result
    
    def apply_optimization(
        self,
        proposal_id: str,
        with_rollback: bool = True
    ) -> Dict[str, Any]:
        """Apply an approved optimization"""
        
        proposal = next(
            (p for p in self.optimization_proposals if p.id == proposal_id),
            None
        )
        
        if not proposal:
            return {'success': False, 'error': 'Proposal not found'}
            
        if not proposal.validation_results:
            return {'success': False, 'error': 'Proposal not validated'}
            
        if proposal.validation_results.get('recommendation') != 'APPROVE':
            return {'success': False, 'error': 'Proposal not approved for application'}
            
        proposal.approved = True
        self.applied_optimizations.append(proposal)
        
        logger.info(f"Applied {proposal.level.value} optimization: {proposal.id}")
        
        return {
            'success': True,
            'proposal_id': proposal_id,
            'level': proposal.level.value,
            'component': proposal.target_component,
            'rollback_available': with_rollback
        }
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        
        by_level = defaultdict(list)
        for opt in self.applied_optimizations:
            by_level[opt.level.value].append(opt)
            
        return {
            'total_patterns_detected': len(self.detected_patterns),
            'total_proposals_generated': len(self.optimization_proposals),
            'proposals_applied': len(self.applied_optimizations),
            'by_level': {
                level: len(opts) for level, opts in by_level.items()
            },
            'recent_patterns': [
                {
                    'type': p.pattern_type,
                    'severity': p.severity,
                    'suggestion': p.suggested_optimization[:50]
                }
                for p in self.detected_patterns[-5:]
            ]
        }
    
    def _match_decisions_outcomes(
        self,
        decisions: List[Dict],
        outcomes: List[Dict]
    ) -> List[Tuple[Dict, Dict]]:
        """Match decisions to their outcomes"""
        
        outcome_map = {o.get('decision_id'): o for o in outcomes}
        
        matched = []
        for d in decisions:
            outcome = outcome_map.get(d.get('id'))
            if outcome:
                matched.append((d, outcome))
                
        return matched
