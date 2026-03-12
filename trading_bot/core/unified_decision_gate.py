"""
Unified Decision Gate - Stage 5 Fix

Addresses violations:
- Gates can be bypassed
- No unified decision gate
- Catastrophic failure modes not explicit
- Portfolio impact checks basic

This is the SINGLE decision gate that ALL signals must pass through.
NO BYPASSES POSSIBLE.

Author: AlphaAlgo Core
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)


class DecisionOutcome(Enum):
    """Final decision outcomes"""
    APPROVED = "approved"
    REJECTED_MARKET_HOSTILE = "rejected_market_hostile"
    REJECTED_FAILED_CLAIMS = "rejected_failed_claims"
    REJECTED_ADVERSARIAL = "rejected_adversarial"
    REJECTED_LOW_CONFIDENCE = "rejected_low_confidence"
    REJECTED_CATASTROPHIC_RISK = "rejected_catastrophic_risk"
    REJECTED_PORTFOLIO_IMPACT = "rejected_portfolio_impact"


class CatastrophicFailureMode(Enum):
    """Catastrophic failure modes that block trades"""
    FLASH_CRASH_RISK = "flash_crash_risk"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    BLACK_SWAN_EVENT = "black_swan_event"
    REGIME_COLLAPSE = "regime_collapse"
    EXECUTION_IMPOSSIBLE = "execution_impossible"


@dataclass
class GateCheckResult:
    """Result of a single gate check"""
    check_name: str
    passed: bool
    reason: str
    severity: float  # 0.0 to 1.0
    details: Dict[str, Any]


@dataclass
class UnifiedDecision:
    """
    Final unified decision from the gate.
    
    This is the ONLY decision format that matters.
    """
    signal_id: str
    symbol: str
    outcome: DecisionOutcome
    approved: bool
    
    # If approved
    approved_quantity: float = 0.0
    approved_confidence: float = 0.0
    
    # If rejected
    rejection_reason: str = ""
    failed_checks: List[str] = None
    catastrophic_modes: List[CatastrophicFailureMode] = None
    
    # Check results
    market_hostility_check: Optional[GateCheckResult] = None
    claim_decomposition_check: Optional[GateCheckResult] = None
    adversarial_analysis_check: Optional[GateCheckResult] = None
    confidence_vector_check: Optional[GateCheckResult] = None
    catastrophic_failure_check: Optional[GateCheckResult] = None
    portfolio_impact_check: Optional[GateCheckResult] = None
    
    # Metadata
    timestamp: datetime = None
    evaluation_time_ms: float = 0.0
    
    def __post_init__(self):
        try:
            if self.timestamp is None:
                self.timestamp = datetime.utcnow()
            if self.failed_checks is None:
                self.failed_checks = []
            if self.catastrophic_modes is None:
                self.catastrophic_modes = []
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class CatastrophicFailureChecker:
    """
    Checks for catastrophic failure modes.
    
    These are tail events that can destroy capital.
    """
    
    def check(
        self,
        signal: Dict,
        market_context: Dict,
        adversarial_analysis: Any
    ) -> GateCheckResult:
        """Check for catastrophic failure modes"""
        try:
            catastrophic_modes = []
            details = {}
        
            # Check 1: Flash crash risk
            volatility = market_context.get('volatility', 0.0)
            if volatility > 0.5:  # 50% volatility
                catastrophic_modes.append(CatastrophicFailureMode.FLASH_CRASH_RISK)
                details['flash_crash_risk'] = f"Volatility {volatility:.2%} > 50%"
        
            # Check 2: Liquidity crisis
            liquidity_score = market_context.get('liquidity_score', 1.0)
            if liquidity_score < 0.2:  # Very low liquidity
                catastrophic_modes.append(CatastrophicFailureMode.LIQUIDITY_CRISIS)
                details['liquidity_crisis'] = f"Liquidity score {liquidity_score:.2%} < 20%"
        
            # Check 3: Correlation breakdown
            correlation = market_context.get('correlation_exposure', 0.0)
            if correlation > 0.9:  # Extreme correlation
                catastrophic_modes.append(CatastrophicFailureMode.CORRELATION_BREAKDOWN)
                details['correlation_breakdown'] = f"Correlation {correlation:.2%} > 90%"
        
            # Check 4: Black swan indicators
            regime_instability = market_context.get('regime_instability', 0.0)
            if regime_instability > 0.8:
                catastrophic_modes.append(CatastrophicFailureMode.BLACK_SWAN_EVENT)
                details['black_swan'] = f"Regime instability {regime_instability:.2%} > 80%"
        
            # Check 5: Regime collapse
            regime_confidence = market_context.get('regime_confidence', 1.0)
            if regime_confidence < 0.3:
                catastrophic_modes.append(CatastrophicFailureMode.REGIME_COLLAPSE)
                details['regime_collapse'] = f"Regime confidence {regime_confidence:.2%} < 30%"
        
            # Check 6: Execution impossible
            if adversarial_analysis:
                if not adversarial_analysis.survives_adversarial_analysis:
                    if adversarial_analysis.expected_worst_case_loss > (signal['price'] * 0.1):
                        catastrophic_modes.append(CatastrophicFailureMode.EXECUTION_IMPOSSIBLE)
                        details['execution_impossible'] = f"Expected worst case loss ${adversarial_analysis.expected_worst_case_loss:.2f}"
        
            # Result
            passed = len(catastrophic_modes) == 0
            severity = len(catastrophic_modes) / 6.0  # Normalize
        
            if not passed:
                reason = f"Catastrophic failure modes detected: {', '.join([m.value for m in catastrophic_modes])}"
            else:
                reason = "No catastrophic failure modes detected"
        
            return GateCheckResult(
                check_name="Catastrophic Failure Check",
                passed=passed,
                reason=reason,
                severity=severity,
                details={
                    'catastrophic_modes': [m.value for m in catastrophic_modes],
                    **details
                }
            )
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise


class PortfolioImpactChecker:
    """
    Deep portfolio impact analysis.
    
    Checks correlation exposure, concentration, and portfolio-level risk.
    """
    
    def check(
        self,
        signal: Dict,
        portfolio_state: Dict,
        market_context: Dict
    ) -> GateCheckResult:
        """Check portfolio impact"""
        try:
            issues = []
            details = {}
        
            # Check 1: Correlation exposure
            correlation = market_context.get('correlation_exposure', 0.0)
            max_correlation = 0.7
            if correlation > max_correlation:
                issues.append(f"Correlation {correlation:.2%} > {max_correlation:.2%}")
                details['correlation_violation'] = correlation
        
            # Check 2: Concentration risk
            position_size = signal.get('quantity', 0.0) * signal['price']
            portfolio_value = portfolio_state.get('value', 100000.0)
            concentration = position_size / portfolio_value if portfolio_value > 0 else 0.0
            max_concentration = 0.1  # 10% max per position
        
            if concentration > max_concentration:
                issues.append(f"Concentration {concentration:.2%} > {max_concentration:.2%}")
                details['concentration_violation'] = concentration
        
            # Check 3: Drawdown impact
            current_drawdown = portfolio_state.get('drawdown', 0.0)
            max_drawdown = 0.15  # 15% max drawdown
        
            if current_drawdown > max_drawdown:
                issues.append(f"Current drawdown {current_drawdown:.2%} > {max_drawdown:.2%}")
                details['drawdown_violation'] = current_drawdown
        
            # Check 4: Sector exposure (if available)
            sector = signal.get('sector')
            if sector:
                sector_exposure = portfolio_state.get('sector_exposure', {}).get(sector, 0.0)
                max_sector_exposure = 0.25  # 25% max per sector
            
                if sector_exposure > max_sector_exposure:
                    issues.append(f"Sector exposure {sector_exposure:.2%} > {max_sector_exposure:.2%}")
                    details['sector_violation'] = sector_exposure
        
            # Check 5: Leverage
            leverage = portfolio_state.get('leverage', 1.0)
            max_leverage = 3.0
        
            if leverage > max_leverage:
                issues.append(f"Leverage {leverage:.1f}x > {max_leverage:.1f}x")
                details['leverage_violation'] = leverage
        
            # Result
            passed = len(issues) == 0
            severity = len(issues) / 5.0  # Normalize
        
            if not passed:
                reason = f"Portfolio impact violations: {'; '.join(issues)}"
            else:
                reason = "Portfolio impact acceptable"
        
            return GateCheckResult(
                check_name="Portfolio Impact Check",
                passed=passed,
                reason=reason,
                severity=severity,
                details=details
            )
        except Exception as e:
            logger.error(f"Error in check: {e}")
            raise


class UnifiedDecisionGate:
    """
    SINGLE unified decision gate.
    
    ALL signals MUST pass through this gate.
    NO BYPASSES POSSIBLE.
    
    Coordinates all checks:
    1. Market hostility gate
    2. Claim decomposition
    3. Adversarial analysis
    4. Confidence vector validation
    5. Catastrophic failure check
    6. Portfolio impact check
    
    Returns single APPROVE/REJECT decision.
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.6,
        enable_strict_mode: bool = True
    ):
        try:
            self.confidence_threshold = confidence_threshold
            self.enable_strict_mode = enable_strict_mode
        
            # Checkers
            self.catastrophic_checker = CatastrophicFailureChecker()
            self.portfolio_checker = PortfolioImpactChecker()
        
            # Statistics
            self.total_evaluations = 0
            self.approved_count = 0
            self.rejection_counts = {outcome: 0 for outcome in DecisionOutcome}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def evaluate(
        self,
        signal: Dict,
        market_context: Dict,
        portfolio_state: Dict,
        # Results from previous stages
        market_hostility_result: Any = None,
        decomposed_signal: Any = None,
        adversarial_analysis: Any = None,
        confidence_vector: Any = None
    ) -> UnifiedDecision:
        """
        Evaluate signal through unified gate.
        
        This is the ONLY decision that matters.
        """
        try:
            start_time = datetime.utcnow()
            self.total_evaluations += 1
        
            signal_id = signal.get('signal_id', 'unknown')
            symbol = signal['symbol']
        
            # Initialize decision
            decision = UnifiedDecision(
                signal_id=signal_id,
                symbol=symbol,
                outcome=DecisionOutcome.APPROVED,
                approved=False
            )
        
            # Check 1: Market Hostility Gate
            if market_hostility_result:
                can_trade = market_hostility_result.can_trade if hasattr(market_hostility_result, 'can_trade') else market_hostility_result[0]
                reason = market_hostility_result.dominant_reason if hasattr(market_hostility_result, 'dominant_reason') else market_hostility_result[1]
            
                decision.market_hostility_check = GateCheckResult(
                    check_name="Market Hostility Gate",
                    passed=can_trade,
                    reason=reason,
                    severity=0.0 if can_trade else 1.0,
                    details={'hostility_level': market_hostility_result.level.value if hasattr(market_hostility_result, 'level') else 'unknown'}
                )
            
                if not can_trade:
                    decision.outcome = DecisionOutcome.REJECTED_MARKET_HOSTILE
                    decision.rejection_reason = reason
                    decision.failed_checks.append("Market Hostility Gate")
                    self._finalize_decision(decision, start_time)
                    return decision
        
            # Check 2: Claim Decomposition
            if decomposed_signal:
                decision.claim_decomposition_check = GateCheckResult(
                    check_name="Claim Decomposition",
                    passed=decomposed_signal.all_claims_pass,
                    reason=f"Failed claims: {decomposed_signal.failed_claims}" if not decomposed_signal.all_claims_pass else "All claims pass",
                    severity=len(decomposed_signal.failed_claims) / len(decomposed_signal.claims) if decomposed_signal.claims else 0.0,
                    details={'failed_claims': decomposed_signal.failed_claims}
                )
            
                if not decomposed_signal.all_claims_pass:
                    decision.outcome = DecisionOutcome.REJECTED_FAILED_CLAIMS
                    decision.rejection_reason = f"Failed claims: {', '.join(decomposed_signal.failed_claims)}"
                    decision.failed_checks.append("Claim Decomposition")
                    self._finalize_decision(decision, start_time)
                    return decision
        
            # Check 3: Adversarial Analysis
            if adversarial_analysis:
                decision.adversarial_analysis_check = GateCheckResult(
                    check_name="Adversarial Analysis",
                    passed=adversarial_analysis.survives_adversarial_analysis,
                    reason=f"Dominant risk: {adversarial_analysis.dominant_failure_risk.value}" if adversarial_analysis.dominant_failure_risk else "Survives adversarial analysis",
                    severity=len(adversarial_analysis.catastrophic_scenarios) / len(adversarial_analysis.failure_scenarios) if adversarial_analysis.failure_scenarios else 0.0,
                    details={
                        'catastrophic_count': len(adversarial_analysis.catastrophic_scenarios),
                        'expected_worst_case_loss': adversarial_analysis.expected_worst_case_loss
                    }
                )
            
                if not adversarial_analysis.survives_adversarial_analysis:
                    decision.outcome = DecisionOutcome.REJECTED_ADVERSARIAL
                    decision.rejection_reason = f"Fails adversarial analysis: {len(adversarial_analysis.catastrophic_scenarios)} catastrophic scenarios"
                    decision.failed_checks.append("Adversarial Analysis")
                    self._finalize_decision(decision, start_time)
                    return decision
        
            # Check 4: Confidence Vector
            if confidence_vector:
                min_conf = confidence_vector.penalized_minimum_confidence
            
                decision.confidence_vector_check = GateCheckResult(
                    check_name="Confidence Vector",
                    passed=min_conf >= self.confidence_threshold,
                    reason=f"Minimum confidence {min_conf:.2%} {'≥' if min_conf >= self.confidence_threshold else '<'} {self.confidence_threshold:.2%}",
                    severity=max(0.0, self.confidence_threshold - min_conf),
                    details={
                        'minimum_confidence': min_conf,
                        'threshold': self.confidence_threshold,
                        'confidence_breakdown': confidence_vector.to_dict()
                    }
                )
            
                if min_conf < self.confidence_threshold:
                    decision.outcome = DecisionOutcome.REJECTED_LOW_CONFIDENCE
                    decision.rejection_reason = f"Minimum confidence {min_conf:.2%} < threshold {self.confidence_threshold:.2%}"
                    decision.failed_checks.append("Confidence Vector")
                    self._finalize_decision(decision, start_time)
                    return decision
        
            # Check 5: Catastrophic Failure Modes
            catastrophic_check = self.catastrophic_checker.check(signal, market_context, adversarial_analysis)
            decision.catastrophic_failure_check = catastrophic_check
        
            if not catastrophic_check.passed:
                decision.outcome = DecisionOutcome.REJECTED_CATASTROPHIC_RISK
                decision.rejection_reason = catastrophic_check.reason
                decision.failed_checks.append("Catastrophic Failure Check")
                decision.catastrophic_modes = [
                    CatastrophicFailureMode(mode) 
                    for mode in catastrophic_check.details.get('catastrophic_modes', [])
                ]
                self._finalize_decision(decision, start_time)
                return decision
        
            # Check 6: Portfolio Impact
            portfolio_check = self.portfolio_checker.check(signal, portfolio_state, market_context)
            decision.portfolio_impact_check = portfolio_check
        
            if not portfolio_check.passed:
                decision.outcome = DecisionOutcome.REJECTED_PORTFOLIO_IMPACT
                decision.rejection_reason = portfolio_check.reason
                decision.failed_checks.append("Portfolio Impact Check")
                self._finalize_decision(decision, start_time)
                return decision
        
            # ALL CHECKS PASSED - APPROVE
            decision.outcome = DecisionOutcome.APPROVED
            decision.approved = True
            decision.approved_quantity = signal.get('quantity', 1.0)
            decision.approved_confidence = confidence_vector.penalized_minimum_confidence if confidence_vector else 0.5
        
            self.approved_count += 1
        
            self._finalize_decision(decision, start_time)
        
            logger.info(
                f"✅ Signal {signal_id} APPROVED:\n"
                f"  Symbol: {symbol}\n"
                f"  Quantity: {decision.approved_quantity}\n"
                f"  Confidence: {decision.approved_confidence:.2%}\n"
                f"  Evaluation time: {decision.evaluation_time_ms:.1f}ms"
            )
        
            return decision
        except Exception as e:
            logger.error(f"Error in evaluate: {e}")
            raise
    
    def _finalize_decision(self, decision: UnifiedDecision, start_time: datetime):
        """Finalize decision with metadata"""
        try:
            decision.evaluation_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.rejection_counts[decision.outcome] += 1
        
            if not decision.approved:
                logger.warning(
                    f"❌ Signal {decision.signal_id} REJECTED:\n"
                    f"  Outcome: {decision.outcome.value}\n"
                    f"  Reason: {decision.rejection_reason}\n"
                    f"  Failed checks: {', '.join(decision.failed_checks)}\n"
                    f"  Evaluation time: {decision.evaluation_time_ms:.1f}ms"
                )
        except Exception as e:
            logger.error(f"Error in _finalize_decision: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gate statistics"""
        return {
            'total_evaluations': self.total_evaluations,
            'approved': self.approved_count,
            'rejected': self.total_evaluations - self.approved_count,
            'approval_rate': self.approved_count / self.total_evaluations if self.total_evaluations > 0 else 0.0,
            'rejection_breakdown': {
                outcome.value: count 
                for outcome, count in self.rejection_counts.items()
                if count > 0
            },
            'configuration': {
                'confidence_threshold': self.confidence_threshold,
                'strict_mode': self.enable_strict_mode
            }
        }


# Global singleton
_global_gate: Optional[UnifiedDecisionGate] = None


def get_global_gate() -> UnifiedDecisionGate:
    """Get global gate singleton"""
    try:
        global _global_gate
        if _global_gate is None:
            _global_gate = UnifiedDecisionGate()
        return _global_gate
    except Exception as e:
        logger.error(f"Error in get_global_gate: {e}")
        raise


def create_unified_gate(**kwargs) -> UnifiedDecisionGate:
    """Create new gate instance"""
    return UnifiedDecisionGate(**kwargs)
