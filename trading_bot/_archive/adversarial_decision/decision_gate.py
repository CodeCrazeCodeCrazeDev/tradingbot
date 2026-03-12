"""
Decision Gate - STEP 7

Authorizes trade only if ALL conditions are met:
- All mandatory claims valid
- No unresolved killer objections
- min(confidence_vector) ≥ threshold
- Expected drawdown ≤ risk budget
- Irreversibility score acceptable
- Portfolio correlation within limits

Otherwise: Reject, Defer, or Reduce Size
Doing nothing is preferred over forced action.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .claim_system import TradeClaim, ClaimType
from .confidence_vector import ConfidenceVector, ConfidenceThresholds

logger = logging.getLogger(__name__)


class GateCondition(Enum):
    """Gate conditions that must pass"""
    ALL_CLAIMS_VALID = "all_claims_valid"
    NO_KILLER_OBJECTIONS = "no_killer_objections"
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    DRAWDOWN_BUDGET = "drawdown_budget"
    IRREVERSIBILITY_ACCEPTABLE = "irreversibility_acceptable"
    CORRELATION_LIMITS = "correlation_limits"


class GateDecision(Enum):
    """Gate decision outcomes"""
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"
    REDUCE_SIZE = "reduce_size"


@dataclass
class GateResult:
    """Result from decision gate"""
    decision: GateDecision
    passed_conditions: List[GateCondition]
    failed_conditions: List[GateCondition]
    rejection_reasons: List[str]
    size_reduction_factor: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def is_approved(self) -> bool:
        """Check if trade is approved"""
        return self.decision == GateDecision.APPROVE
    
    def get_primary_rejection_reason(self) -> Optional[str]:
        """Get primary rejection reason"""
        if self.rejection_reasons:
            return self.rejection_reasons[0]
        return None


class DecisionGate:
    """
    Decision gate that enforces ALL conditions.
    
    RULE: Doing nothing is preferred over forced action
    RULE: All conditions must pass for approval
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Thresholds
        self.confidence_thresholds = ConfidenceThresholds()
        self.max_expected_drawdown = self.config.get('max_expected_drawdown', 0.05)
        self.max_irreversibility_score = self.config.get('max_irreversibility_score', 0.7)
        self.max_portfolio_correlation = self.config.get('max_portfolio_correlation', 0.7)
        self.max_portfolio_concentration = self.config.get('max_portfolio_concentration', 0.3)
        
    def evaluate_trade(
        self,
        claims: List[TradeClaim],
        confidence_vector: ConfidenceVector,
        kill_phase_result: Dict[str, Any],
        failure_match_result: Dict[str, Any],
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> GateResult:
        """
        Evaluate trade through decision gate.
        
        Returns:
            GateResult with decision and reasons
        """
        passed_conditions = []
        failed_conditions = []
        rejection_reasons = []
        
        # CONDITION 1: All mandatory claims valid
        if self._check_all_claims_valid(claims):
            passed_conditions.append(GateCondition.ALL_CLAIMS_VALID)
        else:
            failed_conditions.append(GateCondition.ALL_CLAIMS_VALID)
            invalid_claims = [c.claim_type.value for c in claims if not c.is_valid()]
            rejection_reasons.append(f"Invalid claims: {', '.join(invalid_claims)}")
        
        # CONDITION 2: No unresolved killer objections
        if self._check_no_killer_objections(kill_phase_result):
            passed_conditions.append(GateCondition.NO_KILLER_OBJECTIONS)
        else:
            failed_conditions.append(GateCondition.NO_KILLER_OBJECTIONS)
            kill_reason = kill_phase_result.get('kill_reason', 'Unknown')
            rejection_reasons.append(f"Killer objection: {kill_reason}")
        
        # CONDITION 3: Confidence threshold
        if self._check_confidence_threshold(confidence_vector):
            passed_conditions.append(GateCondition.CONFIDENCE_THRESHOLD)
        else:
            failed_conditions.append(GateCondition.CONFIDENCE_THRESHOLD)
            min_conf = confidence_vector.get_minimum()
            weakest = confidence_vector.get_weakest_dimension()
            rejection_reasons.append(
                f"Confidence below threshold: min={min_conf:.2f} "
                f"(weakest: {weakest})"
            )
        
        # CONDITION 4: Expected drawdown ≤ risk budget
        if self._check_drawdown_budget(portfolio_state):
            passed_conditions.append(GateCondition.DRAWDOWN_BUDGET)
        else:
            failed_conditions.append(GateCondition.DRAWDOWN_BUDGET)
            expected_dd = portfolio_state.get('expected_drawdown', 0.0)
            rejection_reasons.append(
                f"Expected drawdown exceeds budget: {expected_dd:.2%} > {self.max_expected_drawdown:.2%}"
            )
        
        # CONDITION 5: Irreversibility score acceptable
        if self._check_irreversibility(market_data):
            passed_conditions.append(GateCondition.IRREVERSIBILITY_ACCEPTABLE)
        else:
            failed_conditions.append(GateCondition.IRREVERSIBILITY_ACCEPTABLE)
            irreversibility = market_data.get('irreversibility_score', 0.0)
            rejection_reasons.append(
                f"Irreversibility too high: {irreversibility:.2f} > {self.max_irreversibility_score:.2f}"
            )
        
        # CONDITION 6: Portfolio correlation within limits
        if self._check_correlation_limits(portfolio_state):
            passed_conditions.append(GateCondition.CORRELATION_LIMITS)
        else:
            failed_conditions.append(GateCondition.CORRELATION_LIMITS)
            max_corr = portfolio_state.get('correlations', {}).get('max', 0.0)
            concentration = portfolio_state.get('concentration', 0.0)
            rejection_reasons.append(
                f"Correlation/concentration limits exceeded: "
                f"corr={max_corr:.2f}, conc={concentration:.2%}"
            )
        
        # CONDITION 7: No historical failure match
        if failure_match_result.get('should_reject', False):
            rejection_reasons.append(failure_match_result.get('rejection_reason', 'Historical failure match'))
        
        # Make decision
        decision, size_reduction = self._make_decision(
            passed_conditions,
            failed_conditions,
            rejection_reasons,
            confidence_vector,
            portfolio_state
        )
        
        return GateResult(
            decision=decision,
            passed_conditions=passed_conditions,
            failed_conditions=failed_conditions,
            rejection_reasons=rejection_reasons,
            size_reduction_factor=size_reduction
        )
    
    def _check_all_claims_valid(self, claims: List[TradeClaim]) -> bool:
        """Check if all mandatory claims are valid"""
        return all(claim.is_valid() for claim in claims)
    
    def _check_no_killer_objections(self, kill_phase_result: Dict[str, Any]) -> bool:
        """Check if there are no killer objections"""
        return not kill_phase_result.get('should_kill', False)
    
    def _check_confidence_threshold(self, confidence_vector: ConfidenceVector) -> bool:
        """Check if confidence passes thresholds"""
        return confidence_vector.passes_thresholds(self.confidence_thresholds)
    
    def _check_drawdown_budget(self, portfolio_state: Dict[str, Any]) -> bool:
        """Check if expected drawdown is within budget"""
        expected_dd = portfolio_state.get('expected_drawdown', 0.0)
        return expected_dd <= self.max_expected_drawdown
    
    def _check_irreversibility(self, market_data: Dict[str, Any]) -> bool:
        """Check if irreversibility score is acceptable"""
        irreversibility = market_data.get('irreversibility_score', 0.5)
        return irreversibility <= self.max_irreversibility_score
    
    def _check_correlation_limits(self, portfolio_state: Dict[str, Any]) -> bool:
        """Check if portfolio correlation is within limits"""
        max_corr = portfolio_state.get('correlations', {}).get('max', 0.0)
        concentration = portfolio_state.get('concentration', 0.0)
        
        return (
            max_corr <= self.max_portfolio_correlation and
            concentration <= self.max_portfolio_concentration
        )
    
    def _make_decision(
        self,
        passed_conditions: List[GateCondition],
        failed_conditions: List[GateCondition],
        rejection_reasons: List[str],
        confidence_vector: ConfidenceVector,
        portfolio_state: Dict[str, Any]
    ) -> tuple[GateDecision, float]:
        """
        Make final decision based on conditions.
        
        Returns:
            (decision, size_reduction_factor)
        """
        # If all conditions passed, APPROVE
        if len(failed_conditions) == 0:
            return GateDecision.APPROVE, 1.0
        
        # If critical conditions failed, REJECT
        critical_conditions = [
            GateCondition.ALL_CLAIMS_VALID,
            GateCondition.NO_KILLER_OBJECTIONS,
        ]
        
        if any(cond in failed_conditions for cond in critical_conditions):
            return GateDecision.REJECT, 0.0
        
        # If confidence is close but not quite there, DEFER
        min_conf = confidence_vector.get_minimum()
        if min_conf >= 0.5 and min_conf < self.confidence_thresholds.minimum_acceptable:
            return GateDecision.DEFER, 0.0
        
        # If only minor conditions failed, REDUCE_SIZE
        if len(failed_conditions) <= 2:
            # Calculate size reduction based on confidence
            size_reduction = min_conf / self.confidence_thresholds.minimum_acceptable
            size_reduction = max(size_reduction, 0.25)  # Minimum 25% size
            return GateDecision.REDUCE_SIZE, size_reduction
        
        # Otherwise, REJECT
        return GateDecision.REJECT, 0.0


class EmergencyGate:
    """
    Emergency gate for extreme market conditions.
    Overrides all other decisions.
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
    def check_emergency_conditions(
        self,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> Optional[str]:
        """
        Check for emergency conditions that override all decisions.
        
        Returns:
            Emergency reason if triggered, None otherwise
        """
        # Check for flash crash
        price_change = market_data.get('price_change_1min', 0.0)
        if abs(price_change) > 0.05:  # 5% in 1 minute
            return f"Flash crash detected: {price_change:.2%} in 1 minute"
        
        # Check for circuit breaker
        if market_data.get('circuit_breaker', False):
            return "Market circuit breaker triggered"
        
        # Check for extreme volatility
        volatility_regime = market_data.get('volatility_regime', 'NORMAL')
        if volatility_regime == 'CRISIS':
            return "Crisis-level volatility detected"
        
        # Check for portfolio emergency
        current_drawdown = portfolio_state.get('current_drawdown', 0.0)
        if current_drawdown > 0.15:  # 15% drawdown
            return f"Emergency drawdown: {current_drawdown:.2%}"
        
        # Check for margin call risk
        margin_usage = portfolio_state.get('margin_usage', 0.0)
        if margin_usage > 0.8:  # 80% margin usage
            return f"Margin call risk: {margin_usage:.2%} usage"
        
        return None
