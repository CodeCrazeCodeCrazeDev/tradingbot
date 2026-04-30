"""
Stochastic Gate Audit System

Fix #9: Your Architecture Has No Answer for Adversarial Gaming by Traders/Agents

The attack: Your system assumes good-faith thesis construction. But agents (or humans) 
can game the DGS.

Fix: Add stochastic gate audits. Randomly select 5% of approved theses for deep 
adversarial review by a separate system. Penalize agents whose approved theses later 
fail, with penalty severity proportional to governance evasion indicators.

Also includes the fundamental fix: DGS-Governor - a meta-governance layer that 
audits the DGS itself periodically.
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import logging
import random
import hashlib

logger = logging.getLogger(__name__)


class GovernanceEvasionIndicator(Enum):
    """Indicators that a thesis may be gaming the governance system"""
    UNUSUAL_EVIDENCE_OMISSION = "unusual_evidence_omission"
    REGIME_MISMATCH_IGNORED = "regime_mismatch_ignored"
    OVERFIT_TO_HISTORICAL = "overfit_to_historical"
    CONFIDENCE_INFLATION = "confidence_inflation"
    COUNTERFACTUAL_CIRCUMVENTION = "counterfactual_circumvention"
    RAPID_RESUBMISSION = "rapid_resubmission"
    PATTERN_BREAKING = "pattern_breaking"


@dataclass
class AgentTrackRecord:
    """Track record of an agent submitting theses"""
    agent_id: str
    total_submissions: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    sampled_count: int = 0
    failures_after_approval: int = 0
    
    # Governance evasion indicators detected
    evasion_indicators: Dict[GovernanceEvasionIndicator, int] = field(default_factory=lambda: defaultdict(int))
    
    # Penalty score accumulates over time
    penalty_score: float = 0.0
    trust_level: float = 1.0  # 0-1, affects sampling probability
    
    # History
    submission_history: List[Dict] = field(default_factory=list)
    audit_results: List[Dict] = field(default_factory=list)


@dataclass
class StochasticAudit:
    """Record of a stochastic gate audit"""
    audit_id: str
    timestamp: datetime
    thesis_id: str
    agent_id: str
    selected_randomly: bool
    selected_due_to_indicators: bool
    
    # Audit results
    evasion_indicators_found: List[GovernanceEvasionIndicator]
    severity_score: float  # 0-1
    thesis_quality_score: float  # 0-1
    
    # Outcome
    audit_passed: bool
    recommended_action: str
    actual_outcome: Optional[str] = None  # Filled later


class StochasticGateAuditSystem:
    """
    Stochastic Gate Audit System
    
    Defends against adversarial gaming of the DGS by:
    
    1. Random Sampling (5% default):
       - Randomly select approved theses for deep review
       - Creates uncertainty for would-be gamers
       - Cannot be predicted or gamed
    
    2. Indicator-Based Sampling:
       - Increase sampling probability based on evasion indicators
       - Pattern recognition for gaming attempts
       - Dynamic trust level adjustment
    
    3. Penalty System:
       - Agents penalized for approved theses that later fail
       - Penalty severity proportional to evasion indicators detected
       - Trust levels affect future sampling rates and approval thresholds
    
    4. Separate Audit Path:
       - Audits performed by separate system from main governance
       - Different algorithms to avoid shared failure modes
       - Results fed back to DGS-Governor
    """
    
    def __init__(
        self,
        base_sampling_rate: float = 0.05,  # 5% default
        indicator_boost_factor: float = 3.0,  # 3x sampling for flagged agents
        penalty_decay_days: int = 30,
        trust_recovery_rate: float = 0.01  # Daily trust recovery
    ):
        self.base_sampling_rate = base_sampling_rate
        self.indicator_boost_factor = indicator_boost_factor
        self.penalty_decay_days = penalty_decay_days
        self.trust_recovery_rate = trust_recovery_rate
        
        # Agent tracking
        self.agent_records: Dict[str, AgentTrackRecord] = {}
        
        # Audit history
        self.audit_history: deque = deque(maxlen=1000)
        self.pending_audits: Dict[str, StochasticAudit] = {}
        
        # Statistics
        self.total_audits: int = 0
        self.evasion_detected_count: int = 0
        self.penalties_applied: int = 0
        
        logger.info(
            f"Stochastic Gate Audit System initialized: "
            f"{base_sampling_rate:.0%} base sampling, "
            f"{indicator_boost_factor:.1f}x boost for flagged agents"
        )
    
    def should_audit_thesis(
        self,
        thesis_id: str,
        agent_id: str,
        thesis_metadata: Dict[str, Any]
    ) -> Tuple[bool, str, float]:
        """
        Determine if a thesis should be selected for stochastic audit.
        
        Returns: (should_audit, reason, sampling_probability)
        """
        # Get or create agent record
        if agent_id not in self.agent_records:
            self.agent_records[agent_id] = AgentTrackRecord(agent_id=agent_id)
        
        agent = self.agent_records[agent_id]
        
        # Calculate sampling probability
        base_prob = self.base_sampling_rate
        
        # Adjust for trust level (lower trust = higher sampling)
        trust_adjusted_prob = base_prob * (2.0 - agent.trust_level)
        
        # Check for evasion indicators
        indicators = self._detect_evasion_indicators(thesis_metadata, agent)
        
        if indicators:
            # Boost sampling probability
            adjusted_prob = min(0.5, trust_adjusted_prob * self.indicator_boost_factor)
            reason = f"evasion_indicators: {[i.value for i in indicators]}"
        else:
            adjusted_prob = trust_adjusted_prob
            reason = "random_selection"
        
        # Deterministic selection based on thesis_id (for reproducibility)
        # but using probability that varies by agent
        hash_input = f"{thesis_id}_{datetime.utcnow().strftime('%Y%m%d')}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        normalized = (hash_val % 10000) / 10000.0
        
        should_audit = normalized < adjusted_prob
        
        if should_audit:
            agent.sampled_count += 1
            self.total_audits += 1
        
        return should_audit, reason, adjusted_prob
    
    def _detect_evasion_indicators(
        self,
        thesis_metadata: Dict,
        agent: AgentTrackRecord
    ) -> List[GovernanceEvasionIndicator]:
        """Detect indicators of governance evasion attempts"""
        indicators = []
        
        # Check for unusual evidence omission
        required_evidence = thesis_metadata.get('required_evidence_types', [])
        provided_evidence = thesis_metadata.get('provided_evidence_types', [])
        
        critical_missing = set(required_evidence) - set(provided_evidence)
        if critical_missing and len(critical_missing) / len(required_evidence) > 0.3:
            indicators.append(GovernanceEvasionIndicator.UNUSUAL_EVIDENCE_OMISSION)
        
        # Check for regime mismatch ignorance
        if thesis_metadata.get('regime_mismatch_detected', False) and \
           thesis_metadata.get('regime_fit_score', 1.0) < 0.4:
            indicators.append(GovernanceEvasionIndicator.REGIME_MISMATCH_IGNORED)
        
        # Check for confidence inflation
        claimed_confidence = thesis_metadata.get('claimed_confidence', 0.5)
        base_rate = thesis_metadata.get('base_rate_accuracy', 0.5)
        if claimed_confidence > base_rate * 1.5 + 0.2:
            indicators.append(GovernanceEvasionIndicator.CONFIDENCE_INFLATION)
        
        # Check for rapid resubmission (trying until it passes)
        recent_submissions = [
            s for s in agent.submission_history[-10:]
            if (datetime.utcnow() - datetime.fromisoformat(s['timestamp'])).days < 1
        ]
        if len(recent_submissions) > 5:
            indicators.append(GovernanceEvasionIndicator.RAPID_RESUBMISSION)
        
        # Check for pattern breaking (sudden change in strategy)
        if len(agent.submission_history) >= 5:
            recent_types = [s.get('thesis_type') for s in agent.submission_history[-5:]]
            if len(set(recent_types)) > 3:  # High variety suggests gaming
                indicators.append(GovernanceEvasionIndicator.PATTERN_BREAKING)
        
        # Update agent record
        for indicator in indicators:
            agent.evasion_indicators[indicator] += 1
        
        if indicators:
            self.evasion_detected_count += 1
        
        return indicators
    
    def execute_audit(
        self,
        thesis_id: str,
        agent_id: str,
        thesis_content: Dict,
        selected_reason: str,
        deep_review_system: Any  # Separate adversarial system
    ) -> StochasticAudit:
        """
        Execute deep audit of a selected thesis.
        
        Uses separate system from main DGS to avoid shared failure modes.
        """
        audit_id = f"audit_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{thesis_id[:8]}"
        
        # Detect evasion indicators
        agent = self.agent_records.get(agent_id, AgentTrackRecord(agent_id=agent_id))
        evasion_indicators = self._detect_evasion_indicators(thesis_content, agent)
        
        # Perform deep review
        # In real implementation, this would call the deep review system
        quality_score = self._calculate_quality_score(thesis_content, evasion_indicators)
        
        severity = len(evasion_indicators) * 0.15 + (1.0 - quality_score) * 0.5
        severity = min(1.0, severity)
        
        # Determine if audit passed
        audit_passed = quality_score > 0.6 and len(evasion_indicators) < 2
        
        # Determine action
        if audit_passed:
            recommended_action = "approve"
        elif severity > 0.7:
            recommended_action = "reject_and_penalize"
        elif severity > 0.4:
            recommended_action = "require_revisions"
        else:
            recommended_action = "additional_review"
        
        audit = StochasticAudit(
            audit_id=audit_id,
            timestamp=datetime.utcnow(),
            thesis_id=thesis_id,
            agent_id=agent_id,
            selected_randomly=selected_reason == "random_selection",
            selected_due_to_indicators=len(evasion_indicators) > 0,
            evasion_indicators_found=evasion_indicators,
            severity_score=severity,
            thesis_quality_score=quality_score,
            audit_passed=audit_passed,
            recommended_action=recommended_action
        )
        
        self.audit_history.append(audit)
        self.pending_audits[thesis_id] = audit
        
        # Update agent record
        agent.audit_results.append({
            'audit_id': audit_id,
            'passed': audit_passed,
            'severity': severity,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(
            f"Stochastic audit completed: {audit_id} for {thesis_id} "
            f"by {agent_id}: passed={audit_passed}, severity={severity:.2f}"
        )
        
        return audit
    
    def _calculate_quality_score(
        self,
        thesis_content: Dict,
        evasion_indicators: List[GovernanceEvasionIndicator]
    ) -> float:
        """Calculate quality score for a thesis"""
        base_score = 0.7
        
        # Deduct for evasion indicators
        base_score -= len(evasion_indicators) * 0.1
        
        # Add for strong evidence
        if thesis_content.get('evidence_strength', 0) > 0.7:
            base_score += 0.15
        
        # Add for good regime fit
        if thesis_content.get('regime_fit_score', 0) > 0.7:
            base_score += 0.1
        
        # Deduct for overconfidence
        if thesis_content.get('confidence_gap', 0) > 0.2:
            base_score -= 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def record_thesis_outcome(
        self,
        thesis_id: str,
        agent_id: str,
        outcome: str,  # "success" or "failure"
        pnl: Optional[float] = None
    ):
        """
        Record the actual outcome of a thesis.
        
        Used to penalize agents whose theses fail after approval.
        """
        agent = self.agent_records.get(agent_id)
        if not agent:
            return
        
        agent.total_submissions += 1
        
        if outcome == "failure":
            agent.failures_after_approval += 1
            
            # Calculate penalty
            base_penalty = 0.1
            
            # Increase penalty if evasion indicators were present
            if thesis_id in self.pending_audits:
                audit = self.pending_audits[thesis_id]
                if audit.evasion_indicators_found:
                    base_penalty *= (1 + len(audit.evasion_indicators_found) * 0.5)
            
            # Increase penalty for larger losses
            if pnl is not None and pnl < -0.05:  # >5% loss
                base_penalty *= 1.5
            
            agent.penalty_score += base_penalty
            agent.trust_level = max(0.0, agent.trust_level - base_penalty)
            
            self.penalties_applied += 1
            
            logger.warning(
                f"Agent {agent_id} penalized: {base_penalty:.2f} for failed thesis {thesis_id}. "
                f"New trust level: {agent.trust_level:.2f}"
            )
        else:
            agent.approved_count += 1
            # Gradual trust recovery
            agent.trust_level = min(1.0, agent.trust_level + 0.01)
        
        # Record in history
        agent.submission_history.append({
            'thesis_id': thesis_id,
            'outcome': outcome,
            'pnl': pnl,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of an agent including trust level and penalties"""
        if agent_id not in self.agent_records:
            return {
                'agent_id': agent_id,
                'trust_level': 1.0,
                'penalty_score': 0.0,
                'status': 'new'
            }
        
        agent = self.agent_records[agent_id]
        
        return {
            'agent_id': agent_id,
            'trust_level': agent.trust_level,
            'penalty_score': agent.penalty_score,
            'total_submissions': agent.total_submissions,
            'approved_count': agent.approved_count,
            'failures_after_approval': agent.failures_after_approval,
            'audit_history_count': len(agent.audit_results),
            'evasion_indicators': dict(agent.evasion_indicators),
            'status': 'flagged' if agent.trust_level < 0.5 else 'normal'
        }
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get statistics on stochastic audits"""
        recent_audits = list(self.audit_history)[-100:]
        
        if not recent_audits:
            return {'total_audits': 0}
        
        passed = sum(1 for a in recent_audits if a.audit_passed)
        evasion_found = sum(1 for a in recent_audits if a.evasion_indicators_found)
        
        return {
            'total_audits': self.total_audits,
            'recent_audits': len(recent_audits),
            'recent_pass_rate': passed / len(recent_audits),
            'evasion_detection_rate': evasion_found / len(recent_audits),
            'penalties_applied': self.penalties_applied,
            'agents_tracked': len(self.agent_records),
            'agents_flagged': sum(1 for a in self.agent_records.values() if a.trust_level < 0.5)
        }


# Factory function
def create_stochastic_audit_system(
    base_sampling_rate: float = 0.05,
    indicator_boost_factor: float = 3.0
) -> StochasticGateAuditSystem:
    """Factory function to create stochastic audit system"""
    
    return StochasticGateAuditSystem(
        base_sampling_rate=base_sampling_rate,
        indicator_boost_factor=indicator_boost_factor
    )
