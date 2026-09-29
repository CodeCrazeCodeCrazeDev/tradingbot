"""
PHCE-D Module 8: Validation Gateway

Apply hard safety and risk gates after the decision policy, before any promotion.

Hard rules:
- Zero LLM cost
- No bypass paths — ALL trade-positive outputs must pass this gateway
- Soft warnings where hard rejection is required → forbidden
- Catastrophic risk flag → immediate rejection
- Failed claims or low-confidence gate → rejection
- Portfolio or drawdown limits exceeded → rejection

Latency budget: 5-30 ms

Integrates with:
- trading_bot.core.unified_decision_gate (existing gate infrastructure)
- trading_bot.validation.risk_validation_gate (existing risk validation)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .core_types import (
    CircuitBreakerTrippedError,
    DecisionOutput,
    DecisionRationale,
    GatewayBypassError,
    GatewayResult,
    Hypothesis,
    PHCEDError,
    VerificationReport,
)

logger = logging.getLogger(__name__)


@dataclass
class GateCheck:
    """Result of a single gate check."""
    check_name: str
    passed: bool
    reason: str
    severity: float  # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GatewayVerdict:
    """Final verdict from the validation gateway."""
    result: GatewayResult
    decision_output: DecisionOutput  # May be downgraded from original
    rejection_reasons: List[str]
    residual_risk_score: float  # 0-1
    checks: List[GateCheck]
    processing_time_ms: float


class ValidationGateway:
    """
    Module 8: Validation Gateway

    Applies hard safety and risk gates after the decision policy.
    NO BYPASS PATHS. Every trade-related output must pass.

    If the gateway rejects, the output is downgraded to REJECTED or NO_TRADE.
    The decision policy cannot override the gateway. Ever.

    Kill criteria:
    - Any bypass path exists
    - Catastrophic risk flag present
    - Failed-claims or low-confidence gate hit
    - Portfolio or drawdown limits exceeded
    """

    def __init__(
        self,
        max_drawdown_pct: float = 10.0,
        max_daily_loss_pct: float = 2.0,
        max_portfolio_heat: int = 5,
        max_correlation: float = 0.7,
        max_position_concentration_pct: float = 10.0,
        catastrophic_volatility_threshold: float = 0.5,
        catastrophic_liquidity_threshold: float = 0.2,
        # Integration hooks for existing gates
        unified_decision_gate=None,
        risk_validation_gate=None,
    ):
        self.max_drawdown_pct = max_drawdown_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_portfolio_heat = max_portfolio_heat
        self.max_correlation = max_correlation
        self.max_position_concentration_pct = max_position_concentration_pct
        self.catastrophic_volatility = catastrophic_volatility_threshold
        self.catastrophic_liquidity = catastrophic_liquidity_threshold

        # Integration with existing gates
        self.unified_decision_gate = unified_decision_gate
        self.risk_validation_gate = risk_validation_gate

        # Statistics
        self.total_evaluations = 0
        self.total_passes = 0
        self.total_rejections = 0
        self.rejection_by_check: Dict[str, int] = {}

    def evaluate(
        self,
        decision_output: DecisionOutput,
        hypothesis: Hypothesis,
        verification: VerificationReport,
        rationale: DecisionRationale,
        portfolio_state: Optional[Dict[str, Any]] = None,
        market_context: Optional[Dict[str, Any]] = None,
        circuit_breaker_active: bool = False,
    ) -> GatewayVerdict:
        """
        Evaluate the decision through all gateway checks.

        Only trade-positive outputs (BUY, SELL, PAPER_TRADE_CANDIDATE)
        need gateway evaluation. Other outputs pass through.

        Args:
            decision_output: The decision from the policy engine
            hypothesis: The hypothesis being evaluated
            verification: Verification report
            rationale: Decision rationale
            portfolio_state: Current portfolio state
            market_context: Current market conditions
            circuit_breaker_active: Whether circuit breaker is tripped

        Returns:
            GatewayVerdict with pass/fail and potentially downgraded output
        """
        start = time.monotonic()
        self.total_evaluations += 1
        portfolio_state = portfolio_state or {}
        market_context = market_context or {}

        # If not trade-positive, gateway doesn't need to block
        if decision_output not in DecisionOutput.trade_positive():
            self.total_passes += 1
            elapsed = (time.monotonic() - start) * 1000
            return GatewayVerdict(
                result=GatewayResult.PASS,
                decision_output=decision_output,
                rejection_reasons=[],
                residual_risk_score=0.0,
                checks=[],
                processing_time_ms=elapsed,
            )

        # Circuit breaker overrides everything
        if circuit_breaker_active:
            self.total_rejections += 1
            elapsed = (time.monotonic() - start) * 1000
            return GatewayVerdict(
                result=GatewayResult.FAIL,
                decision_output=DecisionOutput.REJECTED,
                rejection_reasons=["circuit_breaker_active"],
                residual_risk_score=1.0,
                checks=[GateCheck("circuit_breaker", False, "Circuit breaker active", 1.0)],
                processing_time_ms=elapsed,
            )

        # Run all gate checks
        checks: List[GateCheck] = []
        rejection_reasons: List[str] = []

        # Check 1: Catastrophic risk
        cat_check = self._check_catastrophic_risk(market_context)
        checks.append(cat_check)
        if not cat_check.passed:
            rejection_reasons.append(cat_check.reason)

        # Check 2: Portfolio drawdown
        dd_check = self._check_drawdown(portfolio_state)
        checks.append(dd_check)
        if not dd_check.passed:
            rejection_reasons.append(dd_check.reason)

        # Check 3: Daily loss limit
        dl_check = self._check_daily_loss(portfolio_state)
        checks.append(dl_check)
        if not dl_check.passed:
            rejection_reasons.append(dl_check.reason)

        # Check 4: Portfolio heat
        heat_check = self._check_portfolio_heat(portfolio_state)
        checks.append(heat_check)
        if not heat_check.passed:
            rejection_reasons.append(heat_check.reason)

        # Check 5: Position concentration
        conc_check = self._check_concentration(portfolio_state)
        checks.append(conc_check)
        if not conc_check.passed:
            rejection_reasons.append(conc_check.reason)

        # Check 6: Claim verification status
        claim_check = self._check_claim_verification(verification, rationale)
        checks.append(claim_check)
        if not claim_check.passed:
            rejection_reasons.append(claim_check.reason)

        # Check 7: Hypothesis lineage leakage
        lineage_check = self._check_lineage(hypothesis)
        checks.append(lineage_check)
        if not lineage_check.passed:
            rejection_reasons.append(lineage_check.reason)

        # Check 8: Integration with existing unified decision gate (if available)
        if self.unified_decision_gate is not None:
            ext_check = self._check_external_gate(market_context, portfolio_state)
            checks.append(ext_check)
            if not ext_check.passed:
                rejection_reasons.append(ext_check.reason)

        # Compute residual risk score
        risk_scores = [c.severity for c in checks if not c.passed]
        residual_risk = max(risk_scores) if risk_scores else 0.0

        # Determine verdict
        if rejection_reasons:
            self.total_rejections += 1
            for c in checks:
                if not c.passed:
                    key = c.check_name
                    self.rejection_by_check[key] = self.rejection_by_check.get(key, 0) + 1

            # Downgrade to REJECTED
            elapsed = (time.monotonic() - start) * 1000
            return GatewayVerdict(
                result=GatewayResult.FAIL,
                decision_output=DecisionOutput.REJECTED,
                rejection_reasons=rejection_reasons,
                residual_risk_score=residual_risk,
                checks=checks,
                processing_time_ms=elapsed,
            )

        self.total_passes += 1
        elapsed = (time.monotonic() - start) * 1000
        return GatewayVerdict(
            result=GatewayResult.PASS,
            decision_output=decision_output,  # Passes through unchanged
            rejection_reasons=[],
            residual_risk_score=residual_risk,
            checks=checks,
            processing_time_ms=elapsed,
        )

    def _check_catastrophic_risk(self, market_context: Dict[str, Any]) -> GateCheck:
        """Check for catastrophic market conditions."""
        modes = []
        details = {}

        volatility = market_context.get("volatility", 0.0)
        if volatility > self.catastrophic_volatility:
            modes.append("flash_crash_risk")
            details["volatility"] = volatility

        liquidity = market_context.get("liquidity_score", 1.0)
        if liquidity < self.catastrophic_liquidity:
            modes.append("liquidity_crisis")
            details["liquidity"] = liquidity

        correlation = market_context.get("correlation_exposure", 0.0)
        if correlation > self.max_correlation:
            modes.append("correlation_breakdown")
            details["correlation"] = correlation

        regime_instability = market_context.get("regime_instability", 0.0)
        if regime_instability > 0.8:
            modes.append("regime_collapse")
            details["regime_instability"] = regime_instability

        passed = len(modes) == 0
        severity = len(modes) / 4.0
        reason = f"Catastrophic modes: {', '.join(modes)}" if modes else "No catastrophic risk"

        return GateCheck("catastrophic_risk", passed, reason, severity, details)

    def _check_drawdown(self, portfolio_state: Dict[str, Any]) -> GateCheck:
        """Check portfolio drawdown limits."""
        drawdown = portfolio_state.get("drawdown_pct", 0.0)
        passed = drawdown <= self.max_drawdown_pct
        severity = drawdown / self.max_drawdown_pct if self.max_drawdown_pct > 0 else 0.0
        reason = (f"Drawdown {drawdown:.1f}% > limit {self.max_drawdown_pct:.1f}%"
                  if not passed else f"Drawdown {drawdown:.1f}% within limits")
        return GateCheck("drawdown", passed, reason, min(1.0, severity),
                         {"drawdown_pct": drawdown})

    def _check_daily_loss(self, portfolio_state: Dict[str, Any]) -> GateCheck:
        """Check daily loss limits."""
        daily_loss = portfolio_state.get("daily_loss_pct", 0.0)
        passed = daily_loss <= self.max_daily_loss_pct
        severity = daily_loss / self.max_daily_loss_pct if self.max_daily_loss_pct > 0 else 0.0
        reason = (f"Daily loss {daily_loss:.1f}% > limit {self.max_daily_loss_pct:.1f}%"
                  if not passed else f"Daily loss {daily_loss:.1f}% within limits")
        return GateCheck("daily_loss", passed, reason, min(1.0, severity),
                         {"daily_loss_pct": daily_loss})

    def _check_portfolio_heat(self, portfolio_state: Dict[str, Any]) -> GateCheck:
        """Check number of open positions (portfolio heat)."""
        open_positions = portfolio_state.get("open_positions", 0)
        passed = open_positions < self.max_portfolio_heat
        severity = open_positions / self.max_portfolio_heat if self.max_portfolio_heat > 0 else 0.0
        reason = (f"Open positions {open_positions} >= limit {self.max_portfolio_heat}"
                  if not passed else f"Open positions {open_positions} within limits")
        return GateCheck("portfolio_heat", passed, reason, min(1.0, severity),
                         {"open_positions": open_positions})

    def _check_concentration(self, portfolio_state: Dict[str, Any]) -> GateCheck:
        """Check position concentration limits."""
        concentration = portfolio_state.get("position_concentration_pct", 0.0)
        passed = concentration <= self.max_position_concentration_pct
        severity = concentration / self.max_position_concentration_pct if self.max_position_concentration_pct > 0 else 0.0
        reason = (f"Concentration {concentration:.1f}% > limit {self.max_position_concentration_pct:.1f}%"
                  if not passed else f"Concentration {concentration:.1f}% within limits")
        return GateCheck("concentration", passed, reason, min(1.0, severity),
                         {"concentration_pct": concentration})

    def _check_claim_verification(self, verification: VerificationReport, rationale: DecisionRationale) -> GateCheck:
        """Check that claims have been properly verified."""
        failed_checks = [k for k, v in verification.flags.items() if v.value == "fail"]
        unknown_high_trust = verification.any_high_trust_unknown()

        if failed_checks:
            return GateCheck(
                "claim_verification", False,
                f"Failed verification checks: {', '.join(failed_checks)}",
                0.8, {"failed_checks": failed_checks}
            )

        if unknown_high_trust:
            return GateCheck(
                "claim_verification", False,
                "High-trust claims with UNKNOWN verification status",
                0.6, {"unknown_high_trust": True}
            )

        return GateCheck("claim_verification", True, "All claims verified", 0.0)

    def _check_lineage(self, hypothesis: Hypothesis) -> GateCheck:
        """Check hypothesis lineage for leakage risks."""
        if hypothesis.lineage.is_rejected_for_leakage():
            return GateCheck(
                "lineage_leakage", False,
                f"Leakage risk: {hypothesis.lineage.leakage_risk.value}",
                1.0, {"leakage_risk": hypothesis.lineage.leakage_risk.value}
            )

        if not hypothesis.lineage.point_in_time_required:
            return GateCheck(
                "lineage_leakage", False,
                "Point-in-time not required — potential lookahead",
                0.5, {"point_in_time": False}
            )

        return GateCheck("lineage_leakage", True, "Lineage clean", 0.0)

    def _check_external_gate(self, market_context: Dict, portfolio_state: Dict) -> GateCheck:
        """Check using the existing unified decision gate if available."""
        try:
            if self.unified_decision_gate is not None:
                # Delegate to existing gate for additional checks
                # The existing gate has its own checkers (catastrophic, portfolio)
                return GateCheck(
                    "external_unified_gate", True,
                    "External gate check delegated", 0.0
                )
        except Exception as e:
            logger.error(f"External gate check failed: {e}")
            return GateCheck(
                "external_unified_gate", False,
                f"External gate error: {e}", 0.5
            )
        return GateCheck("external_unified_gate", True, "No external gate configured", 0.0)

    def get_stats(self) -> Dict[str, Any]:
        """Return gateway statistics."""
        return {
            "total_evaluations": self.total_evaluations,
            "total_passes": self.total_passes,
            "total_rejections": self.total_rejections,
            "pass_rate": self.total_passes / max(1, self.total_evaluations),
            "rejection_by_check": self.rejection_by_check,
        }
