"""
Layer 7: Governance Arbiter

Final gate. Does not ask "Is this clever?" It asks:
- Is this valid?
- Is this sufficiently evidenced?
- Is this robust under challenge?
- Is this within hard risk bounds?
- Is this executable after costs?
- Is uncertainty low enough to permit action?

Makes final decision: APPROVE, RESIZE, DEFER, REJECT, or ABSTAIN.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

from .core_types import (
    GovernanceDecision, DecisionRecord, UncertaintyProfile,
    ExecutionFeasibility, MarketRegime
)

logger = logging.getLogger(__name__)


@dataclass
class GovernanceCriteria:
    """Criteria for governance decisions"""
    min_evidence_coverage: float = 0.6
    max_adversarial_severity: float = 0.8
    min_regime_fit: float = 0.5
    min_robustness: float = 0.5
    min_confidence: float = 0.55
    max_abstention_probability: float = 0.5
    max_position_size: float = 1.0  # As fraction of portfolio
    max_risk_per_trade: float = 0.02  # 2% risk per trade


class GovernanceArbiter:
    """
    Final decision authority for the governance system.
    Evaluates all layers and makes final trading decision.
    """
    
    def __init__(
        self,
        criteria: Optional[GovernanceCriteria] = None,
        risk_manager: Optional[Any] = None
    ):
        self.criteria = criteria or GovernanceCriteria()
        self.risk_manager = risk_manager
        
        # Decision statistics
        self.decision_stats = {
            'total_evaluated': 0,
            'approved': 0,
            'resized': 0,
            'deferred': 0,
            'rejected': 0,
            'abstained': 0
        }
        
    def arbitrate(
        self,
        claims: List[Any],
        evidence_coverage: Dict[str, Any],
        adversarial_challenges: List[Any],
        regime_fit_score: float,
        regime_underrepresented: bool,
        robustness_score: float,
        uncertainty_profile: UncertaintyProfile,
        execution_feasibility: Optional[ExecutionFeasibility],
        counterfactual_scenarios: List[Any],
        symbol: str,
        proposed_size: float,
        signal_confidence: float
    ) -> Tuple[GovernanceDecision, DecisionRecord]:
        """
        Make final governance decision.
        
        Returns:
            Tuple of (decision, decision_record)
        """
        self.decision_stats['total_evaluated'] += 1
        
        # Build decision record
        record = DecisionRecord(
            id="",
            timestamp=datetime.utcnow(),
            symbol=symbol,
            signal_source="agent",
            claims=claims,
            evidence_coverage=evidence_coverage.get('coverage', {}),
            evidence_gaps=evidence_coverage.get('gaps', []),
            adversarial_challenges=adversarial_challenges,
            regime_applicability_score=regime_fit_score,
            regime_underrepresentation_warning=regime_underrepresented,
            robustness_score=robustness_score,
            uncertainty_profile=uncertainty_profile,
            counterfactual_scenarios=[
                {
                    'name': s.name,
                    'survives': s.thesis_survives,
                    'impact': s.expected_outcome_change
                }
                for s in counterfactual_scenarios
            ]
        )
        
        # Check each criterion
        violations = []
        
        # 1. Validity check (basic structural integrity)
        if not claims:
            violations.append("No claims to evaluate")
        if not any(c.claim_type.value == 'thesis' for c in claims):
            violations.append("No thesis claim found")
            
        # 2. Evidence sufficiency
        coverage_score = evidence_coverage.get('coverage_score', 0)
        if coverage_score < self.criteria.min_evidence_coverage:
            violations.append(
                f"Evidence coverage {coverage_score:.2f} below minimum {self.criteria.min_evidence_coverage}"
            )
            
        # 3. Robustness under challenge
        if adversarial_challenges:
            max_severity = max(c.severity for c in adversarial_challenges)
            if max_severity > self.criteria.max_adversarial_severity:
                violations.append(
                    f"Adversarial challenge severity {max_severity:.2f} exceeds maximum {self.criteria.max_adversarial_severity}"
                )
                
        if robustness_score < self.criteria.min_robustness:
            violations.append(
                f"Robustness score {robustness_score:.2f} below minimum {self.criteria.min_robustness}"
            )
            
        # 4. Regime fit
        if regime_fit_score < self.criteria.min_regime_fit:
            violations.append(
                f"Regime fit {regime_fit_score:.2f} below minimum {self.criteria.min_regime_fit}"
            )
            
        if regime_underrepresented:
            violations.append("Regime underrepresented in historical data")
            
        # 5. Uncertainty bounds
        if uncertainty_profile.abstention_probability > self.criteria.max_abstention_probability:
            violations.append(
                f"Abstention probability {uncertainty_profile.abstention_probability:.2f} too high"
            )
            
        if uncertainty_profile.overall_confidence < self.criteria.min_confidence:
            violations.append(
                f"Confidence {uncertainty_profile.overall_confidence:.2f} below minimum {self.criteria.min_confidence}"
            )
            
        # 6. Execution feasibility
        if execution_feasibility and not execution_feasibility.feasible:
            violations.append(f"Execution not feasible: {execution_feasibility.constraints}")
            
        # Determine decision
        decision, reasoning = self._determine_decision(
            violations,
            uncertainty_profile,
            robustness_score,
            coverage_score,
            regime_fit_score,
            proposed_size
        )
        
        record.final_decision = decision
        record.decision_reasoning = reasoning
        
        # Calculate approved size
        record.approved_size = proposed_size
        record.risk_adjusted_size = self._calculate_risk_adjusted_size(
            proposed_size,
            uncertainty_profile,
            robustness_score,
            regime_fit_score,
            adversarial_challenges
        )
        
        if decision == GovernanceDecision.RESIZE:
            record.approved_size = record.risk_adjusted_size
            
        # Update stats
        self._update_stats(decision)
        
        logger.info(
            f"Governance decision for {symbol}: {decision.value} - {reasoning[:100]}"
        )
        
        return decision, record
    
    def _determine_decision(
        self,
        violations: List[str],
        uncertainty_profile: UncertaintyProfile,
        robustness_score: float,
        coverage_score: float,
        regime_fit_score: float,
        proposed_size: float
    ) -> Tuple[GovernanceDecision, str]:
        """Determine final decision based on violations and scores"""
        
        # Critical violations -> REJECT
        critical_patterns = [
            "No claims",
            "No thesis",
            "not feasible"
        ]
        
        for violation in violations:
            if any(pattern in violation for pattern in critical_patterns):
                return GovernanceDecision.REJECT, f"Critical violation: {violation}"
                
        # High uncertainty -> ABSTAIN
        if uncertainty_profile.abstention_probability > 0.7:
            return GovernanceDecision.ABSTAIN, "Excessive uncertainty"
            
        # Multiple violations or major concerns -> DEFER
        if len(violations) >= 3:
            return GovernanceDecision.DEFER, f"Multiple violations ({len(violations)}): {', '.join(violations[:2])}"
            
        # Some concerns but thesis is sound -> RESIZE
        if violations or uncertainty_profile.abstention_probability > 0.4:
            if robustness_score > 0.6 and coverage_score > 0.5:
                return GovernanceDecision.RESIZE, f"Concerns present but manageable: {violations[0] if violations else 'uncertainty elevated'}"
            else:
                return GovernanceDecision.DEFER, "Insufficient robustness with concerns present"
                
        # No violations, good scores -> APPROVE
        if not violations and robustness_score > 0.7 and coverage_score > 0.7:
            return GovernanceDecision.APPROVE, "All criteria satisfied"
            
        # Borderline case
        if robustness_score > 0.6 and regime_fit_score > 0.6:
            return GovernanceDecision.RESIZE, "Borderline case - proceeding with caution"
            
        return GovernanceDecision.DEFER, "Insufficient confidence for approval"
    
    def _calculate_risk_adjusted_size(
        self,
        proposed_size: float,
        uncertainty_profile: UncertaintyProfile,
        robustness_score: float,
        regime_fit_score: float,
        adversarial_challenges: List[Any]
    ) -> float:
        """Calculate risk-adjusted position size"""
        
        # Start with proposed size
        adjusted = proposed_size
        
        # Reduce for uncertainty
        confidence_factor = uncertainty_profile.overall_confidence
        adjusted *= (0.5 + 0.5 * confidence_factor)  # Scale 0.5x to 1.0x
        
        # Reduce for robustness concerns
        adjusted *= (0.3 + 0.7 * robustness_score)  # Scale 0.3x to 1.0x
        
        # Reduce for regime fit
        adjusted *= (0.4 + 0.6 * regime_fit_score)  # Scale 0.4x to 1.0x
        
        # Reduce for adversarial challenges
        if adversarial_challenges:
            avg_severity = sum(c.severity for c in adversarial_challenges) / len(adversarial_challenges)
            challenge_factor = 1 - (avg_severity * 0.3)  # Up to 30% reduction
            adjusted *= challenge_factor
            
        # Ensure within hard limits
        adjusted = min(adjusted, self.criteria.max_position_size)
        
        return round(adjusted, 4)
    
    def _update_stats(self, decision: GovernanceDecision) -> None:
        """Update decision statistics"""
        
        if decision == GovernanceDecision.APPROVE:
            self.decision_stats['approved'] += 1
        elif decision == GovernanceDecision.RESIZE:
            self.decision_stats['resized'] += 1
        elif decision == GovernanceDecision.DEFER:
            self.decision_stats['deferred'] += 1
        elif decision == GovernanceDecision.REJECT:
            self.decision_stats['rejected'] += 1
        elif decision == GovernanceDecision.ABSTAIN:
            self.decision_stats['abstained'] += 1
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get decision statistics"""
        
        stats = self.decision_stats.copy()
        total = stats['total_evaluated']
        
        if total > 0:
            stats['approval_rate'] = stats['approved'] / total
            stats['rejection_rate'] = (stats['rejected'] + stats['abstained']) / total
            stats['modification_rate'] = (stats['resized'] + stats['deferred']) / total
        else:
            stats['approval_rate'] = 0
            stats['rejection_rate'] = 0
            stats['modification_rate'] = 0
            
        return stats
    
    def generate_audit_report(
        self,
        decision_record: DecisionRecord
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report for a decision"""
        
        return {
            'decision_id': decision_record.id,
            'timestamp': decision_record.timestamp.isoformat(),
            'symbol': decision_record.symbol,
            'decision': decision_record.final_decision.value,
            'reasoning': decision_record.decision_reasoning,
            'approved_size': decision_record.approved_size,
            'risk_adjusted_size': decision_record.risk_adjusted_size,
            
            'scores': {
                'evidence_coverage': self._calculate_evidence_coverage_summary(decision_record),
                'regime_fit': decision_record.regime_applicability_score,
                'robustness': decision_record.robustness_score,
                'confidence': decision_record.uncertainty_profile.overall_confidence if decision_record.uncertainty_profile else 0
            },
            
            'flags': {
                'regime_underrepresented': decision_record.regime_underrepresentation_warning,
                'evidence_gaps': len(decision_record.evidence_gaps) > 0,
                'adversarial_challenges': len(decision_record.adversarial_challenges) > 0,
                'counterfactual_failures': sum(
                    1 for s in decision_record.counterfactual_scenarios
                    if not s.get('survives', True)
                )
            }
        }
    
    def _calculate_evidence_coverage_summary(
        self,
        record: DecisionRecord
    ) -> float:
        """Calculate summary evidence coverage score"""
        
        if not record.evidence_coverage:
            return 0.0
            
        scores = {'present': 1.0, 'insufficient': 0.5, 'stale': 0.3, 'missing': 0.0, 'conflicting': 0.0}
        total = sum(scores.get(status.value, 0) for status in record.evidence_coverage.values())
        return total / len(record.evidence_coverage)
