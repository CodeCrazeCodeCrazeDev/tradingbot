"""
Adversarial Decision Engine - Main Orchestrator

Implements the complete 9-step adversarial decision framework:
1. Hard Reality Pre-Check
2. Claim Decomposition
3. Orthogonal Verification
4. Adversarial Kill Phase
5. Confidence Vector Calculation
6. Failure Mode Matching
7. Decision Gate
8. Position Sizing
9. Post-Decision Rules
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .claim_system import ClaimDecomposer, TradeClaim, ClaimType
from .verification_system import OrthogonalVerifier, VerificationResult
from .adversarial_roles import AdversarialKillPhase
from .confidence_vector import ConfidenceCalculator, ConfidenceVector
from .failure_matcher import FailureMatcher, FailureCategory
from .decision_gate import DecisionGate, EmergencyGate, GateDecision
from .position_sizer import AdversarialPositionSizer, SizingFactors

logger = logging.getLogger(__name__)


class DecisionOutcome(Enum):
    """Final decision outcomes"""
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    REDUCED_SIZE = "reduced_size"
    EMERGENCY_HALT = "emergency_halt"


class RejectionReason(Enum):
    """Categorized rejection reasons"""
    HARD_REALITY_FAILED = "hard_reality_failed"
    CLAIMS_INVALID = "claims_invalid"
    KILLER_OBJECTION = "killer_objection"
    CONFIDENCE_LOW = "confidence_low"
    HISTORICAL_FAILURE = "historical_failure"
    GATE_CONDITION_FAILED = "gate_condition_failed"
    EMERGENCY_CONDITION = "emergency_condition"


@dataclass
class TradeDecision:
    """Complete trade decision with all reasoning"""
    outcome: DecisionOutcome
    symbol: str
    direction: str
    approved: bool
    position_size: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    
    # Step results
    hard_reality_passed: bool = False
    claims: List[TradeClaim] = field(default_factory=list)
    verification_results: Dict[ClaimType, List[VerificationResult]] = field(default_factory=dict)
    kill_phase_result: Dict[str, Any] = field(default_factory=dict)
    confidence_vector: Optional[ConfidenceVector] = None
    failure_match_result: Dict[str, Any] = field(default_factory=dict)
    gate_result: Any = None
    sizing_factors: Optional[SizingFactors] = None
    
    # Rejection details
    rejection_category: Optional[RejectionReason] = None
    rejection_reasons: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        if self.approved:
            return (
                f"APPROVED: {self.direction.upper()} {self.position_size:.4f} {self.symbol} "
                f"@ {self.entry_price:.4f}, SL={self.stop_loss:.4f}, "
                f"Confidence={self.confidence_vector.get_minimum():.2f}"
            )
        else:
            reasons = "; ".join(self.rejection_reasons[:3])
            return f"REJECTED: {self.symbol} - {reasons}"


class AdversarialDecisionEngine:
    """
    Main adversarial decision engine implementing all 9 steps.
    
    PRINCIPLE: Reject by default, approve only when ALL conditions pass.
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Initialize all components
        self.claim_decomposer = ClaimDecomposer(config)
        self.verifier = OrthogonalVerifier(config)
        self.kill_phase = AdversarialKillPhase(config)
        self.confidence_calculator = ConfidenceCalculator(config)
        self.failure_matcher = FailureMatcher(config)
        self.decision_gate = DecisionGate(config)
        self.emergency_gate = EmergencyGate(config)
        self.position_sizer = AdversarialPositionSizer(config)
        
        # Statistics
        self.total_evaluations = 0
        self.total_approved = 0
        self.total_rejected = 0
        self.rejection_stats = {reason: 0 for reason in RejectionReason}
        
    def evaluate_trade(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        market_data: Dict[str, Any],
        signal_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> TradeDecision:
        """
        Evaluate trade through complete 9-step adversarial framework.
        
        Returns:
            TradeDecision with complete reasoning chain
        """
        start_time = datetime.utcnow()
        self.total_evaluations += 1
        
        decision = TradeDecision(
            outcome=DecisionOutcome.REJECTED,
            symbol=symbol,
            direction=direction,
            approved=False,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        try:
            # STEP 1: Hard Reality Pre-Check
            logger.info(f"[STEP 1] Hard Reality Pre-Check for {symbol}")
            if not self._step1_hard_reality_check(market_data, signal_data):
                decision.rejection_category = RejectionReason.HARD_REALITY_FAILED
                decision.rejection_reasons.append("Failed hard reality pre-check")
                self._finalize_decision(decision, start_time)
                return decision
            decision.hard_reality_passed = True
            
            # STEP 2: Claim Decomposition
            logger.info(f"[STEP 2] Claim Decomposition for {symbol}")
            claims = self.claim_decomposer.decompose_trade(
                symbol, direction, market_data, signal_data, portfolio_state
            )
            if not claims:
                decision.rejection_category = RejectionReason.CLAIMS_INVALID
                decision.rejection_reasons.append("Failed to decompose into valid claims")
                self._finalize_decision(decision, start_time)
                return decision
            decision.claims = claims
            
            # STEP 3: Orthogonal Verification
            logger.info(f"[STEP 3] Orthogonal Verification for {symbol}")
            verification_results = {}
            for claim in claims:
                results = self.verifier.verify_claim(claim, market_data, historical_data)
                verification_results[claim.claim_type] = results
                
                # Update claim with verification
                if results:
                    claim.verified = all(r.is_valid() for r in results)
                    claim.verification_score = sum(r.score for r in results) / len(results)
                    claim.verification_methods = [r.method.value for r in results]
            
            decision.verification_results = verification_results
            
            # Check if all claims are valid
            if not all(claim.is_valid() for claim in claims):
                decision.rejection_category = RejectionReason.CLAIMS_INVALID
                invalid_claims = [c.claim_type.value for c in claims if not c.is_valid()]
                decision.rejection_reasons.append(f"Invalid claims: {', '.join(invalid_claims)}")
                self._finalize_decision(decision, start_time)
                return decision
            
            # STEP 4: Adversarial Kill Phase
            logger.info(f"[STEP 4] Adversarial Kill Phase for {symbol}")
            kill_result = self.kill_phase.execute_kill_phase(
                claims, market_data, signal_data, portfolio_state, historical_data
            )
            decision.kill_phase_result = kill_result
            
            if kill_result.get('should_kill', False):
                decision.rejection_category = RejectionReason.KILLER_OBJECTION
                decision.rejection_reasons.append(kill_result.get('kill_reason', 'Killer objection raised'))
                self._finalize_decision(decision, start_time)
                return decision
            
            # STEP 5: Confidence Vector
            logger.info(f"[STEP 5] Confidence Vector Calculation for {symbol}")
            confidence_vector = self.confidence_calculator.calculate_confidence_vector(
                claims, verification_results, market_data, signal_data, historical_data
            )
            decision.confidence_vector = confidence_vector
            
            # STEP 6: Failure Mode Matching
            logger.info(f"[STEP 6] Failure Mode Matching for {symbol}")
            failure_match = self.failure_matcher.check_failure_match(
                market_data, signal_data, portfolio_state, historical_data
            )
            decision.failure_match_result = failure_match
            
            if failure_match.get('should_reject', False):
                decision.rejection_category = RejectionReason.HISTORICAL_FAILURE
                decision.rejection_reasons.append(failure_match.get('rejection_reason', 'Historical failure match'))
                self._finalize_decision(decision, start_time)
                return decision
            
            # Check for emergency conditions
            emergency_reason = self.emergency_gate.check_emergency_conditions(
                market_data, portfolio_state
            )
            if emergency_reason:
                decision.outcome = DecisionOutcome.EMERGENCY_HALT
                decision.rejection_category = RejectionReason.EMERGENCY_CONDITION
                decision.rejection_reasons.append(emergency_reason)
                self._finalize_decision(decision, start_time)
                return decision
            
            # STEP 7: Decision Gate
            logger.info(f"[STEP 7] Decision Gate for {symbol}")
            gate_result = self.decision_gate.evaluate_trade(
                claims, confidence_vector, kill_result, failure_match,
                market_data, portfolio_state
            )
            decision.gate_result = gate_result
            
            # STEP 8: Position Sizing
            logger.info(f"[STEP 8] Position Sizing for {symbol}")
            sizing_factors = self.position_sizer.calculate_position_size(
                symbol, direction, entry_price, stop_loss,
                confidence_vector, market_data, portfolio_state, historical_data
            )
            
            # Adjust for gate decision
            if gate_result.decision == GateDecision.REDUCE_SIZE:
                sizing_factors = self.position_sizer.adjust_for_gate_decision(
                    sizing_factors, gate_result.size_reduction_factor
                )
            
            decision.sizing_factors = sizing_factors
            
            # Make final decision based on gate
            if gate_result.decision == GateDecision.APPROVE:
                # Validate position size
                is_valid, validation_reason = self.position_sizer.validate_position_size(
                    sizing_factors.final_position_size, symbol, entry_price, portfolio_state
                )
                
                if is_valid:
                    decision.outcome = DecisionOutcome.APPROVED
                    decision.approved = True
                    decision.position_size = sizing_factors.final_position_size
                    self.total_approved += 1
                    logger.info(f"✓ APPROVED: {symbol} with size {decision.position_size:.4f}")
                else:
                    decision.outcome = DecisionOutcome.REJECTED
                    decision.rejection_category = RejectionReason.GATE_CONDITION_FAILED
                    decision.rejection_reasons.append(f"Position size validation failed: {validation_reason}")
                    
            elif gate_result.decision == GateDecision.REDUCE_SIZE:
                decision.outcome = DecisionOutcome.REDUCED_SIZE
                decision.approved = True
                decision.position_size = sizing_factors.final_position_size
                self.total_approved += 1
                logger.info(f"✓ APPROVED (REDUCED): {symbol} with size {decision.position_size:.4f}")
                
            elif gate_result.decision == GateDecision.DEFER:
                decision.outcome = DecisionOutcome.DEFERRED
                decision.rejection_category = RejectionReason.CONFIDENCE_LOW
                decision.rejection_reasons.extend(gate_result.rejection_reasons)
                
            else:  # REJECT
                decision.outcome = DecisionOutcome.REJECTED
                decision.rejection_category = RejectionReason.GATE_CONDITION_FAILED
                decision.rejection_reasons.extend(gate_result.rejection_reasons)
            
        except Exception as e:
            logger.error(f"Error in adversarial evaluation: {e}", exc_info=True)
            decision.outcome = DecisionOutcome.REJECTED
            decision.rejection_category = RejectionReason.GATE_CONDITION_FAILED
            decision.rejection_reasons.append(f"Evaluation error: {str(e)}")
        
        self._finalize_decision(decision, start_time)
        return decision
    
    def _step1_hard_reality_check(
        self,
        market_data: Dict[str, Any],
        signal_data: Dict[str, Any]
    ) -> bool:
        """
        STEP 1: Hard Reality Pre-Check
        
        Checks:
        - Edge density above minimum viable threshold
        - Multiple strategies performing simultaneously
        - Market behavior consistent with profitable regime
        """
        # Check edge density
        edge_density = signal_data.get('edge_density', 0.0)
        if edge_density < 0.3:
            logger.warning(f"Edge density below threshold: {edge_density:.4f} < 0.3")
            return False
        
        # Check strategy dispersion
        active_strategies = signal_data.get('active_strategies', 0)
        if active_strategies < 2:
            logger.warning(f"Strategy dispersion collapsed: {active_strategies} < 2")
            return False
        
        # Check regime consistency
        regime = market_data.get('regime', 'UNKNOWN')
        profitable_regimes = signal_data.get('profitable_regimes', [])
        if regime not in profitable_regimes and regime != 'UNKNOWN':
            logger.warning(f"Regime '{regime}' not in profitable regimes: {profitable_regimes}")
            return False
        
        return True
    
    def _finalize_decision(self, decision: TradeDecision, start_time: datetime):
        """Finalize decision with metadata and statistics"""
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        decision.processing_time_ms = processing_time
        
        # Update statistics
        if not decision.approved:
            self.total_rejected += 1
            if decision.rejection_category:
                self.rejection_stats[decision.rejection_category] += 1
        
        # STEP 9: Post-Decision Rules (logging only, not used for decision)
        logger.info(f"Decision finalized in {processing_time:.2f}ms: {decision.get_summary()}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get decision statistics"""
        approval_rate = self.total_approved / max(self.total_evaluations, 1)
        
        return {
            'total_evaluations': self.total_evaluations,
            'total_approved': self.total_approved,
            'total_rejected': self.total_rejected,
            'approval_rate': approval_rate,
            'rejection_stats': {k.value: v for k, v in self.rejection_stats.items()},
        }
    
    def learn_from_outcome(
        self,
        decision: TradeDecision,
        actual_pnl: float,
        actual_pnl_percent: float
    ):
        """
        STEP 9: Learn from trade outcome.
        
        Updates failure database if trade was a loss.
        """
        if actual_pnl < 0:
            # Determine failure category
            if abs(actual_pnl_percent) > 0.05:
                category = FailureCategory.TAIL_EVENT
            elif decision.confidence_vector and decision.confidence_vector.get_minimum() < 0.7:
                category = FailureCategory.MODEL_DEGRADATION
            else:
                category = FailureCategory.LOSS_CLUSTERING
            
            # Extract conditions from decision
            conditions = {}
            if decision.claims:
                for claim in decision.claims:
                    conditions.update(claim.evidence)
            
            # Add to failure database
            self.failure_matcher.add_new_failure(
                category=category,
                conditions=conditions,
                loss_amount=actual_pnl,
                loss_percentage=actual_pnl_percent,
                description=f"Loss on {decision.symbol} {decision.direction}",
                lessons_learned=[
                    f"Confidence was {decision.confidence_vector.get_minimum():.2f}",
                    f"Failed at step: {decision.rejection_category.value if decision.rejection_category else 'execution'}"
                ]
            )
            
            logger.info(f"Learned from loss: {category.value} - {actual_pnl_percent:.2%}")
