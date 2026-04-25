"""
Real-time Decision Governance Plane

Its job is narrow:
- Validate trade thesis structure
- Test evidence sufficiency
- Check regime fit
- Check execution feasibility
- Check hard risk constraints
- Estimate abstention
- Approve, resize, defer, or reject

This plane must be:
- Fast
- Deterministic where possible
- Bounded
- Auditable
- Unable to mutate itself
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import asyncio

from .core_types import (
    GovernanceDecision, DecisionRecord, MarketRegime, ExecutionFeasibility,
    ValidationError
)
from .layer1_claim_graph import ClaimGraphConstructor
from .layer2_evidence_auditor import EvidenceSufficiencyAuditor
from .layer4_regime_engine import RegimeApplicabilityEngine
from .layer6_uncertainty import UncertaintyCalibrationLayer
from .layer7_arbiter import GovernanceArbiter, GovernanceCriteria
from .memory_system import DecisionMemory

logger = logging.getLogger(__name__)


class RealtimeDecisionGovernancePlane:
    """
    Fast, deterministic governance for real-time trading decisions.
    Does not perform deep analysis - leaves that to offline plane.
    """
    
    def __init__(
        self,
        criteria: Optional[GovernanceCriteria] = None,
        decision_memory: Optional[DecisionMemory] = None,
        max_latency_ms: float = 100.0
    ):
        self.criteria = criteria or GovernanceCriteria()
        self.decision_memory = decision_memory or DecisionMemory()
        self.max_latency_ms = max_latency_ms
        
        # Components
        self.claim_constructor = ClaimGraphConstructor()
        self.evidence_auditor = EvidenceSufficiencyAuditor()
        self.regime_engine = RegimeApplicabilityEngine()
        self.uncertainty_layer = UncertaintyCalibrationLayer()
        self.arbiter = GovernanceArbiter(self.criteria)
        
        # Performance tracking
        self.latency_history: List[float] = []
        self.decision_counts = {d: 0 for d in GovernanceDecision}
        
    async def evaluate_signal(
        self,
        signal: Dict[str, Any],
        symbol: str,
        current_regime: Optional[MarketRegime],
        execution_feasibility: Optional[ExecutionFeasibility],
        hard_constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[GovernanceDecision, DecisionRecord, float]:
        """
        Evaluate a trading signal in real-time.
        
        Args:
            signal: The trading signal to evaluate
            symbol: Trading symbol
            current_regime: Current market regime
            execution_feasibility: Execution feasibility assessment
            hard_constraints: Hard risk constraints
            
        Returns:
            Tuple of (decision, record, latency_ms)
        """
        start_time = datetime.utcnow()
        
        try:
            # Layer 1: Construct claim graph (fast path)
            claims = self.claim_constructor.construct_claim_graph(
                agent_output=signal,
                source_agent=signal.get('source', 'unknown'),
                symbol=symbol
            )
            
            # Layer 2: Quick evidence audit
            evidence_coverage, evidence_gaps, contradictions = \
                self.evidence_auditor.audit_evidence(claims)
            
            coverage_score = self.evidence_auditor.compute_evidence_coverage_score(
                claims, evidence_coverage
            )
            
            # Layer 4: Regime fit check (fast)
            regime_fit_score = 0.5
            regime_underrepresented = False
            
            if current_regime:
                regime_fit_score, regime_underrepresented, _ = \
                    self.regime_engine.evaluate_regime_fit(claims, current_regime)
                    
            # Layer 6: Uncertainty calibration (fast)
            base_confidence = signal.get('confidence', 0.5)
            
            uncertainty_profile = self.uncertainty_layer.compute_uncertainty_profile(
                base_confidence=base_confidence,
                evidence_coverage=coverage_score,
                adversarial_challenges=[],  # Skip in real-time
                regime_fit_score=regime_fit_score,
                robustness_score=0.5,  # Default in real-time
                distribution_shift_detected=False
            )
            
            # Check hard constraints
            constraint_violations = self._check_hard_constraints(
                signal, hard_constraints or {}
            )
            
            # Layer 7: Quick arbitration
            decision, record = self.arbiter.arbitrate(
                claims=claims,
                evidence_coverage={
                    'coverage': evidence_coverage,
                    'coverage_score': coverage_score,
                    'gaps': evidence_gaps
                },
                adversarial_challenges=[],
                regime_fit_score=regime_fit_score,
                regime_underrepresented=regime_underrepresented,
                robustness_score=0.5,
                uncertainty_profile=uncertainty_profile,
                execution_feasibility=execution_feasibility,
                counterfactual_scenarios=[],
                symbol=symbol,
                proposed_size=signal.get('size', 1.0),
                signal_confidence=base_confidence
            )
            
            # Store decision
            self.decision_memory.store_decision(record)
            
            # Calculate latency
            end_time = datetime.utcnow()
            latency_ms = (end_time - start_time).total_seconds() * 1000
            self.latency_history.append(latency_ms)
            
            # Keep only recent history
            if len(self.latency_history) > 1000:
                self.latency_history = self.latency_history[-1000:]
                
            self.decision_counts[decision] += 1
            
            # Log if latency exceeds threshold
            if latency_ms > self.max_latency_ms:
                logger.warning(
                    f"Governance latency {latency_ms:.1f}ms exceeds threshold {self.max_latency_ms:.1f}ms"
                )
                
            return decision, record, latency_ms
            
        except Exception as e:
            logger.error(f"Error in real-time governance: {e}")
            
            # Return conservative decision on error
            error_record = DecisionRecord(
                id="",
                timestamp=datetime.utcnow(),
                symbol=symbol,
                signal_source=signal.get('source', 'unknown'),
                final_decision=GovernanceDecision.ABSTAIN,
                decision_reasoning=f"Error during evaluation: {str(e)}"
            )
            
            return GovernanceDecision.ABSTAIN, error_record, 0.0
            
    def _check_hard_constraints(
        self,
        signal: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> List[str]:
        """Check hard risk constraints"""
        
        violations = []
        
        # Position size limit
        max_size = constraints.get('max_position_size', 1.0)
        proposed_size = signal.get('size', 0)
        if proposed_size > max_size:
            violations.append(f"Position size {proposed_size} exceeds max {max_size}")
            
        # Daily loss limit
        daily_loss = constraints.get('daily_loss', 0)
        daily_limit = constraints.get('daily_loss_limit', float('inf'))
        if abs(daily_loss) > daily_limit:
            violations.append(f"Daily loss limit exceeded")
            
        # Max positions
        current_positions = constraints.get('current_positions', 0)
        max_positions = constraints.get('max_positions', 10)
        if current_positions >= max_positions:
            violations.append(f"Max positions ({max_positions}) reached")
            
        return violations
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get real-time plane performance metrics"""
        
        metrics = {
            'total_decisions': sum(self.decision_counts.values()),
            'decision_distribution': {
                d.value: count for d, count in self.decision_counts.items()
            }
        }
        
        if self.latency_history:
            metrics['avg_latency_ms'] = sum(self.latency_history) / len(self.latency_history)
            metrics['max_latency_ms'] = max(self.latency_history)
            metrics['p99_latency_ms'] = sorted(self.latency_history)[int(len(self.latency_history) * 0.99)]
            
        return metrics
        
    def generate_quick_audit(self, record: DecisionRecord) -> Dict[str, Any]:
        """Generate quick audit summary for a decision"""
        
        return {
            'decision_id': record.id,
            'symbol': record.symbol,
            'decision': record.final_decision.value,
            'timestamp': record.timestamp.isoformat(),
            'scores': {
                'evidence_coverage': record.evidence_coverage,
                'regime_fit': record.regime_applicability_score,
                'confidence': record.uncertainty_profile.overall_confidence if record.uncertainty_profile else 0
            },
            'flags': [
                'evidence_gaps' if record.evidence_gaps else None,
                'regime_underrepresented' if record.regime_underrepresentation_warning else None
            ]
        }
